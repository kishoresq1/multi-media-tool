from app.collectors.api_collectors import (
    GitHubCollector,
    HackerNewsCollector,
    MSRCCollector,
    NVDCollector,
    RedditCollector,
)
from app.collectors.cve_program import CVEProgramCollector
from app.collectors.base import BaseCollector
from app.collectors.json_feed import JSONFeedCollector
from app.collectors.rss import RSSCollector
from app.collectors.scraper import HTMLScraperCollector, TelegramCollector
from app.collectors.social_scraper import LinkedInScraperCollector, TwitterScraperCollector
from app.config.sources import CollectionMethod, SourceConfig

_COLLECTOR_MAP: dict[str, type[BaseCollector]] = {
    "hackernews": HackerNewsCollector,
    "reddit": RedditCollector,
    "twitter": TwitterScraperCollector,
    "nvd": NVDCollector,
    "github_poc": GitHubCollector,
    "metasploit": GitHubCollector,
    "msrc": MSRCCollector,
    "linkedin": LinkedInScraperCollector,
    "telegram": TelegramCollector,
    "cisa_kev": JSONFeedCollector,
    "cve_program": CVEProgramCollector,
    "exploit_db": RSSCollector,
}


def get_collector_for_source(source: SourceConfig) -> BaseCollector:
    if source.id in _COLLECTOR_MAP:
        return _COLLECTOR_MAP[source.id](source)

    method = source.primary_method
    if method == CollectionMethod.RSS:
        return RSSCollector(source)
    if method == CollectionMethod.JSON_FEED:
        return JSONFeedCollector(source)
    if method == CollectionMethod.HTML_SCRAPER:
        return HTMLScraperCollector(source)
    if method == CollectionMethod.GITHUB_API:
        return GitHubCollector(source)
    if method == CollectionMethod.API:
        return HTMLScraperCollector(source)

    return RSSCollector(source)
