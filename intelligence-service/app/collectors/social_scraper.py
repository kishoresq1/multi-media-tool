import logging
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector, CollectorResult
from app.config.settings import settings
from app.models.schemas import CollectionMethod

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class LinkedInScraperCollector(BaseCollector):
    """
    Scrape public LinkedIn posts via search engine results.
    Searches site:linkedin.com/posts for product + vulnerability keywords.
    """

    async def collect(
        self,
        query_terms: list[str],
        lookback_days: int = 30,
    ) -> CollectorResult:
        signals = []
        search_queries = self._build_search_queries(query_terms)

        try:
            async with httpx.AsyncClient(
                timeout=settings.request_timeout_seconds,
                follow_redirects=True,
            ) as client:
                for query in search_queries[:8]:
                    results = await self._search_linkedin(client, query)
                    for item in results:
                        combined = f"{item['title']} {item['content']}"
                        if not self._matches_query(combined, query_terms):
                            continue
                        signals.append(
                            self._make_signal(
                                title=item["title"],
                                content=item["content"],
                                url=item["url"],
                                author=item.get("author"),
                                method=CollectionMethod.HTML_SCRAPER,
                                metadata={"search_query": query, "platform": "linkedin"},
                            )
                        )
        except Exception as exc:
            logger.warning("LinkedIn scraper failed: %s", exc)
            return CollectorResult(success=False, error=str(exc))

        return CollectorResult(
            signals=self._dedupe(signals)[: settings.max_results_per_source],
            success=True,
            method_used=CollectionMethod.HTML_SCRAPER,
        )

    def _build_search_queries(self, query_terms: list[str]) -> list[str]:
        queries = []
        for term in query_terms[:10]:
            queries.append(f'site:linkedin.com/posts "{term}" vulnerability OR exploit OR CVE')
            queries.append(f'site:linkedin.com/pulse "{term}" security')
        return queries

    async def _search_linkedin(self, client: httpx.AsyncClient, query: str) -> list[dict]:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        response = await client.get(url, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        results = []

        for result in soup.select(".result")[:15]:
            link_el = result.select_one("a.result__a")
            if not link_el:
                continue
            href = link_el.get("href", "")
            if "linkedin.com" not in href:
                continue
            title = link_el.get_text(strip=True)
            snippet_el = result.select_one(".result__snippet")
            snippet = snippet_el.get_text(strip=True) if snippet_el else title
            if len(title) < 10:
                continue
            results.append({"title": title[:300], "content": snippet[:500], "url": href})

        return results

    def _dedupe(self, signals: list) -> list:
        seen: set[str] = set()
        unique = []
        for s in signals:
            key = s.url or s.title
            if key not in seen:
                seen.add(key)
                unique.append(s)
        return unique


class TwitterScraperCollector(BaseCollector):
    """Search X/Twitter via Nitter — no API key required."""

    async def collect(
        self,
        query_terms: list[str],
        lookback_days: int = 30,
    ) -> CollectorResult:
        from app.collectors.nitter import NitterClient

        signals = []
        try:
            tweets = await NitterClient().search(query_terms, lookback_days)
            for tweet in tweets:
                combined = f"{tweet['title']} {tweet['content']}"
                if not self._matches_query(combined, query_terms):
                    continue
                signals.append(
                    self._make_signal(
                        title=tweet["title"],
                        content=tweet["content"],
                        url=tweet["url"],
                        author=tweet.get("author"),
                        published_at=tweet.get("published_at"),
                        method=CollectionMethod.RSS,
                        metadata={
                            "platform": "twitter",
                            "search_query": tweet["search_query"],
                            "nitter_instance": tweet.get("nitter_instance"),
                        },
                    )
                )
        except Exception as exc:
            logger.warning("Nitter Twitter collect failed: %s", exc)
            return CollectorResult(success=False, error=str(exc))

        return CollectorResult(
            signals=signals[: settings.max_results_per_source],
            success=True,
            method_used=CollectionMethod.RSS,
        )
