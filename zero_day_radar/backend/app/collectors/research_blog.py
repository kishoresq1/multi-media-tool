import logging

from app.collectors.base import BaseCollector, CollectorResult
from app.collectors.registry import get_collector_for_source
from app.collectors.rss import RSSCollector
from app.collectors.scraper import HTMLScraperCollector
from app.config.research_blogs import BLOG_FEED_OVERRIDES
from app.config.sources import CollectionMethod, SourceConfig

logger = logging.getLogger(__name__)


class ResearchBlogFetcher:
    """Fetch researcher blogs via RSS with HTML scraper fallback."""

    async def fetch(
        self,
        source: SourceConfig,
        query_terms: list[str],
        lookback_days: int,
    ) -> CollectorResult:
        src = self._prepare_source(source)

        collector = get_collector_for_source(src)
        result = await self._safe_collect(collector, query_terms, lookback_days)

        if result.success and result.signals:
            return result

        # Try alternate feed URL
        alt_feed = BLOG_FEED_OVERRIDES.get(source.id)
        if alt_feed and alt_feed != src.feed_url:
            alt_src = src.model_copy(update={
                "feed_url": alt_feed,
                "primary_method": CollectionMethod.RSS,
            })
            alt_result = await self._safe_collect(
                RSSCollector(alt_src), query_terms, lookback_days
            )
            if alt_result.success and alt_result.signals:
                return alt_result

        # HTML scraper fallback
        scraper_src = src.model_copy(update={"primary_method": CollectionMethod.HTML_SCRAPER})
        scraper_result = await self._safe_collect(
            HTMLScraperCollector(scraper_src), query_terms, lookback_days
        )
        if scraper_result.success and scraper_result.signals:
            return scraper_result

        return result if result.success else scraper_result

    def _prepare_source(self, source: SourceConfig) -> SourceConfig:
        feed = source.feed_url or BLOG_FEED_OVERRIDES.get(source.id)
        if feed:
            return source.model_copy(update={"feed_url": feed})
        return source

    async def _safe_collect(
        self,
        collector: BaseCollector,
        query_terms: list[str],
        lookback_days: int,
    ) -> CollectorResult:
        try:
            return await collector.collect(query_terms, lookback_days)
        except Exception as exc:
            logger.warning("Blog collector %s failed: %s", collector.source.id, exc)
            return CollectorResult(success=False, error=str(exc))
