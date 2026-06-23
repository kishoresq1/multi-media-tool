import logging
from datetime import datetime, timedelta, timezone

import httpx

from app.collectors.base import BaseCollector, CollectorResult
from app.config.settings import settings
from app.models.schemas import CollectionMethod

logger = logging.getLogger(__name__)


class JSONFeedCollector(BaseCollector):
    """Collector for JSON API feeds like CISA KEV."""

    async def collect(
        self,
        query_terms: list[str],
        lookback_days: int = 30,
    ) -> CollectorResult:
        endpoint = self.source.api_endpoint
        if not endpoint:
            return CollectorResult(
                success=False,
                error=f"No API endpoint for {self.source.id}",
            )

        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        signals = []

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.get(endpoint)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            logger.warning("JSON feed failed for %s: %s", self.source.id, exc)
            return CollectorResult(success=False, error=str(exc))

        if self.source.id == "cisa_kev":
            signals = self._parse_cisa_kev(data, query_terms, cutoff)
        else:
            for item in data if isinstance(data, list) else data.get("items", []):
                title = str(item.get("title", item.get("cveID", "")))
                content = str(item.get("description", item.get("shortDescription", "")))
                combined = f"{title} {content}"
                if self._matches_query(combined, query_terms):
                    signals.append(
                        self._make_signal(
                            title=title,
                            content=content,
                            url=item.get("url"),
                            method=CollectionMethod.JSON_FEED,
                            metadata=item,
                        )
                    )

        return CollectorResult(
            signals=signals[: settings.max_results_per_source],
            success=True,
            method_used=CollectionMethod.JSON_FEED,
        )

    def _parse_cisa_kev(
        self,
        data: dict,
        query_terms: list[str],
        cutoff: datetime,
    ) -> list:
        signals = []
        for vuln in data.get("vulnerabilities", []):
            cve_id = vuln.get("cveID", "")
            vendor = vuln.get("vendorProject", "")
            product = vuln.get("product", "")
            title = f"{cve_id}: {vendor} {product}"
            content = (
                f"{vuln.get('vulnerabilityName', '')} "
                f"{vuln.get('shortDescription', '')} "
                f"Required action: {vuln.get('requiredAction', '')}"
            )
            combined = f"{title} {content} {vendor} {product}"

            if not self._matches_query(combined, query_terms):
                continue

            date_added = vuln.get("dateAdded")
            published = None
            if date_added:
                try:
                    published = datetime.strptime(date_added, "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    pass

            if published and published < cutoff:
                continue

            signals.append(
                self._make_signal(
                    title=title,
                    content=content,
                    url=f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                    published_at=published,
                    method=CollectionMethod.JSON_FEED,
                    metadata={
                        "cve_id": cve_id,
                        "vendor": vendor,
                        "product": product,
                        "cisa_kev": True,
                        "known_ransomware": vuln.get("knownRansomwareCampaignUse", "Unknown"),
                        "due_date": vuln.get("dueDate"),
                    },
                )
            )
        return signals
