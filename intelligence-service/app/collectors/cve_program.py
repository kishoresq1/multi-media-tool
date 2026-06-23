import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx

from app.collectors.base import BaseCollector, CollectorResult
from app.config.settings import settings
from app.models.schemas import CollectionMethod

logger = logging.getLogger(__name__)


class CVEProgramCollector(BaseCollector):
    """
    Fetch CVE Records from the CVE Program API (public per-CVE endpoint).
    Bulk list requires CNA credentials; we discover recent CVE IDs via NVD date query.
    """

    async def collect(
        self,
        query_terms: list[str],
        lookback_days: int = 30,
    ) -> CollectorResult:
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        pub_start = cutoff.strftime("%Y-%m-%dT00:00:00.000")
        pub_end = datetime.now(timezone.utc).strftime("%Y-%m-%dT23:59:59.999")
        signals = []

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                cve_ids = await self._recent_cve_ids(client, pub_start, pub_end)
                logger.info("CVE Program: fetching %d recent CVE records", len(cve_ids))

                for cve_id in cve_ids[:150]:
                    signal = await self._fetch_cve_record(client, cve_id, query_terms, cutoff)
                    if signal:
                        signals.append(signal)
                    await asyncio.sleep(0.15)

        except Exception as exc:
            logger.warning("CVE Program collection failed: %s", exc)
            return CollectorResult(success=False, error=str(exc))

        return CollectorResult(
            signals=self._dedupe(signals),
            success=True,
            method_used=CollectionMethod.API,
        )

    async def _recent_cve_ids(
        self,
        client: httpx.AsyncClient,
        pub_start: str,
        pub_end: str,
    ) -> list[str]:
        headers = {}
        if settings.nvd_api_key:
            headers["apiKey"] = settings.nvd_api_key

        response = await client.get(
            "https://services.nvd.nist.gov/rest/json/cves/2.0",
            params={
                "pubStartDate": pub_start,
                "pubEndDate": pub_end,
                "resultsPerPage": 200,
                "startIndex": 0,
            },
            headers=headers,
        )
        if response.status_code == 429:
            logger.warning("NVD rate limited while resolving CVE IDs for CVE Program")
            return []
        response.raise_for_status()

        ids = []
        for item in response.json().get("vulnerabilities", []):
            cve_id = item.get("cve", {}).get("id")
            if cve_id:
                ids.append(cve_id)
        return ids

    async def _fetch_cve_record(
        self,
        client: httpx.AsyncClient,
        cve_id: str,
        query_terms: list[str],
        cutoff: datetime,
    ):
        response = await client.get(f"https://cveawg.mitre.org/api/cve/{cve_id}")
        if response.status_code != 200:
            return None

        record = response.json()
        meta = record.get("cveMetadata", {})
        cna = record.get("containers", {}).get("cna", {})

        title = cna.get("title") or cve_id
        desc = ""
        for d in cna.get("descriptions", []):
            if d.get("lang") == "en":
                desc = d.get("value", "")
                break

        combined = f"{title} {desc} {cve_id}"
        if not self._matches_query(combined, query_terms):
            return None

        published = None
        for field in ("datePublished", "dateUpdated"):
            raw = meta.get(field)
            if raw:
                try:
                    published = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                    break
                except ValueError:
                    pass

        if published and published < cutoff:
            return None

        return self._make_signal(
            title=f"{cve_id} - {title}" if title != cve_id else cve_id,
            content=desc,
            url=f"https://www.cve.org/CVERecord?id={cve_id}",
            published_at=published,
            method=CollectionMethod.API,
            metadata={
                "cve_id": cve_id,
                "assigner": meta.get("assignerShortName"),
                "source": "cve_program",
            },
        )

    def _dedupe(self, signals: list) -> list:
        seen: set[str] = set()
        out = []
        for s in signals:
            cve_id = s.raw_metadata.get("cve_id", s.title)
            if cve_id not in seen:
                seen.add(cve_id)
                out.append(s)
        return out[: settings.max_results_per_source * 2]
