import logging
from datetime import datetime, timedelta, timezone

import feedparser
import httpx

from app.collectors.base import BaseCollector, CollectorResult
from app.config.settings import settings
from app.models.schemas import CollectionMethod

logger = logging.getLogger(__name__)


class RSSCollector(BaseCollector):
    async def collect(
        self,
        query_terms: list[str],
        lookback_days: int = 30,
    ) -> CollectorResult:
        feed_url = self.source.feed_url
        if not feed_url:
            return CollectorResult(
                success=False,
                error=f"No feed URL configured for {self.source.id}",
            )

        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        signals = []

        try:
            verify_ssl = self.source.id not in ("exploit_db", "ransomware_live")
            async with httpx.AsyncClient(
                timeout=settings.request_timeout_seconds,
                verify=verify_ssl,
            ) as client:
                response = await client.get(
                    feed_url,
                    headers={"User-Agent": "ZeroDayRadar/0.1 CTI Collector"},
                    follow_redirects=True,
                )
                response.raise_for_status()
                feed = feedparser.parse(response.text)
        except Exception as exc:
            logger.warning("RSS fetch failed for %s: %s", self.source.id, exc)
            return CollectorResult(success=False, error=str(exc))

        for entry in feed.entries[: settings.max_results_per_source]:
            title = entry.get("title", "")
            summary = entry.get("summary", entry.get("description", ""))
            link = entry.get("link")
            combined = f"{title} {summary}"

            if not self._matches_query(combined, query_terms):
                continue

            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

            if published and published < cutoff:
                continue

            signals.append(
                self._make_signal(
                    title=title,
                    content=summary,
                    url=link,
                    published_at=published,
                    author=entry.get("author"),
                    method=CollectionMethod.RSS,
                    metadata={"feed_url": feed_url},
                )
            )

        return CollectorResult(
            signals=signals,
            success=True,
            method_used=CollectionMethod.RSS,
        )
