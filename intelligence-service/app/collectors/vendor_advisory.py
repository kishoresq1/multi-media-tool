import logging

from app.collectors.api_collectors import MSRCCollector
from app.collectors.base import BaseCollector, CollectorResult
from app.collectors.registry import get_collector_for_source
from app.collectors.rss import RSSCollector
from app.collectors.scraper import HTMLScraperCollector
from app.config.sources import CollectionMethod, SourceConfig
from app.config.vendor_advisories import ADVISORY_FEED_OVERRIDES

logger = logging.getLogger(__name__)


class VendorAdvisoryFetcher:
    """
    Fetch vendor advisories using primary method (RSS/API) with fallback (scraper).
    """

    async def fetch(
        self,
        source: SourceConfig,
        query_terms: list[str],
        lookback_days: int,
    ) -> CollectorResult:
        if source.id in ADVISORY_FEED_OVERRIDES and not source.feed_url:
            source = source.model_copy(
                update={"feed_url": ADVISORY_FEED_OVERRIDES[source.id]}
            )

        collector = get_collector_for_source(source)
        result = await self._safe_collect(collector, query_terms, lookback_days)

        if result.success and result.signals:
            return result

        if source.fallback_method:
            fallback = self._get_fallback_collector(source)
            if fallback:
                fb_result = await self._safe_collect(fallback, query_terms, lookback_days)
                if fb_result.success and fb_result.signals:
                    return fb_result
                if not result.success:
                    return fb_result

        return result

    async def _safe_collect(
        self,
        collector: BaseCollector,
        query_terms: list[str],
        lookback_days: int,
    ) -> CollectorResult:
        try:
            return await collector.collect(query_terms, lookback_days)
        except Exception as exc:
            logger.warning("Collector %s failed: %s", collector.source.id, exc)
            return CollectorResult(success=False, error=str(exc))

    def _get_fallback_collector(self, source: SourceConfig) -> BaseCollector | None:
        method = source.fallback_method
        if method == CollectionMethod.RSS:
            fb_source = source.model_copy(update={
                "primary_method": CollectionMethod.RSS,
                "feed_url": source.feed_url or ADVISORY_FEED_OVERRIDES.get(source.id),
            })
            if fb_source.feed_url:
                return RSSCollector(fb_source)
        if method == CollectionMethod.HTML_SCRAPER:
            fb_source = source.model_copy(update={"primary_method": CollectionMethod.HTML_SCRAPER})
            return HTMLScraperCollector(fb_source)
        if method == CollectionMethod.API and source.id == "msrc":
            return MSRCCollector(source)
        return HTMLScraperCollector(source.model_copy(
            update={"primary_method": CollectionMethod.HTML_SCRAPER}
        ))
