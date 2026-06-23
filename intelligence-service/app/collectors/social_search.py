import logging
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from app.config.keywords import SEARCH_KEYWORDS
from app.config.query_builder import (
    build_hackernews_queries,
    build_linkedin_queries,
    build_reddit_queries,
    to_pullpush_query,
)
from app.config.settings import settings
from app.models.schemas import CollectionMethod, RawSignal, SourceCategory

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _signal(
    platform: str,
    source_name: str,
    title: str,
    content: str,
    url: str | None,
    author: str | None,
    published_at: datetime | None,
    method: CollectionMethod,
    search_query: str,
    metadata: dict | None = None,
) -> RawSignal:
    return RawSignal(
        source_id=platform,
        source_name=source_name,
        source_category=SourceCategory.RESEARCHER_SOCIAL,
        collection_method=method,
        title=title,
        url=url,
        content=content,
        published_at=published_at,
        author=author,
        raw_metadata={"search_query": search_query, "platform": platform, **(metadata or {})},
    )


def _query_matches_content(query: str, title: str, content: str) -> bool:
    """Ensure [VENDOR] + [SEARCH_KEYWORD] from query appears in post."""
    text_lower = f"{title} {content}".lower()
    q = query.lower().strip()

    phrases = sorted(SEARCH_KEYWORDS, key=len, reverse=True)
    matched_phrases = [p for p in phrases if p.lower() in q]

    vendor_part = q
    for phrase in matched_phrases:
        vendor_part = vendor_part.replace(phrase.lower(), " ")
    vendor_part = " ".join(vendor_part.split()).strip()

    if vendor_part and vendor_part not in text_lower:
        return False
    if matched_phrases:
        return any(p.lower() in text_lower for p in matched_phrases)
    return bool(vendor_part)


class TwitterSearchCollector:
    """Search X/Twitter via Nitter using [VENDOR] + [VULNERABILITY KEYWORD]."""

    async def search(
        self,
        queries: list[str],
        lookback_days: int,
        vendors: list[str] | None = None,
    ) -> list[RawSignal]:
        from app.collectors.nitter import NitterClient

        signals: list[RawSignal] = []
        search_queries = queries[: settings.max_results_per_source]

        try:
            tweets = await NitterClient().search(search_queries, lookback_days)
            for tweet in tweets:
                if not _query_matches_content(
                    tweet["search_query"], tweet["title"], tweet["content"]
                ):
                    continue
                signals.append(
                    _signal(
                        platform="twitter",
                        source_name="X/Twitter (Nitter)",
                        title=tweet["title"],
                        content=tweet["content"],
                        url=tweet["url"],
                        author=tweet.get("author"),
                        published_at=tweet.get("published_at"),
                        method=CollectionMethod.RSS,
                        search_query=tweet["search_query"],
                        metadata={"nitter_instance": tweet.get("nitter_instance")},
                    )
                )
        except Exception as exc:
            logger.warning("Nitter Twitter search failed: %s", exc)

        return _sort_latest(_dedupe(signals))


class RedditSearchCollector:
    """
    Search Reddit using [VENDOR] + [VULNERABILITY KEYWORD].
    PullPush API (no key) → OAuth API → DuckDuckGo scraper fallback.
    """

    async def search(
        self,
        queries: list[str],
        lookback_days: int,
        vendors: list[str] | None = None,
    ) -> list[RawSignal]:
        reddit_queries = build_reddit_queries(
            vendors=vendors,
            max_queries=settings.max_results_per_source,
        )

        results = await self._search_pullpush(reddit_queries, lookback_days)
        if results:
            return results

        if settings.reddit_client_id and settings.reddit_client_secret:
            results = await self._search_oauth(
                [q for q, _ in reddit_queries], lookback_days
            )
            if results:
                return results

        return await self._search_scraper([q for q, _ in reddit_queries])

    async def _search_pullpush(
        self,
        reddit_queries: list[tuple[str, str | None]],
        lookback_days: int,
    ) -> list[RawSignal]:
        signals: list[RawSignal] = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                for query, subreddit in reddit_queries:
                    params: dict = {
                        "q": to_pullpush_query(query),
                        "sort": "desc",
                        "size": 25,
                    }
                    if subreddit:
                        params["subreddit"] = subreddit

                    response = await client.get(
                        "https://api.pullpush.io/reddit/search/submission/",
                        params=params,
                    )
                    if response.status_code != 200:
                        continue

                    data = response.json()
                    posts = data.get("data", []) if isinstance(data, dict) else data
                    for post in posts:
                        title = post.get("title", "")
                        content = post.get("selftext", "") or title
                        if not _query_matches_content(query, title, content):
                            continue
                        created = post.get("created_utc", 0)
                        published = None
                        if created:
                            try:
                                published = datetime.fromtimestamp(
                                    float(created), tz=timezone.utc
                                )
                            except (TypeError, ValueError, OSError):
                                published = None
                        if published and published < cutoff:
                            continue
                        signals.append(
                            _signal(
                                platform="reddit",
                                source_name="Reddit",
                                title=title,
                                content=content,
                                url=f"https://reddit.com{post.get('permalink', '')}",
                                author=post.get("author"),
                                published_at=published,
                                method=CollectionMethod.API,
                                search_query=query,
                                metadata={
                                    "subreddit": post.get("subreddit"),
                                    "score": post.get("score"),
                                    "source": "pullpush",
                                },
                            )
                        )
        except Exception as exc:
            logger.warning("Reddit PullPush search failed: %s", exc)
            return []

        return _sort_latest(_dedupe(signals))

    async def _search_oauth(self, queries: list[str], lookback_days: int) -> list[RawSignal]:
        signals: list[RawSignal] = []
        time_filter = "week" if lookback_days <= 7 else "month" if lookback_days <= 30 else "year"

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                token_resp = await client.post(
                    "https://www.reddit.com/api/v1/access_token",
                    data={"grant_type": "client_credentials"},
                    auth=(settings.reddit_client_id, settings.reddit_client_secret),
                    headers={"User-Agent": settings.reddit_user_agent},
                )
                token_resp.raise_for_status()
                token = token_resp.json()["access_token"]

                for query in queries:
                    response = await client.get(
                        "https://oauth.reddit.com/search",
                        params={
                            "q": query,
                            "sort": "new",
                            "t": time_filter,
                            "limit": 25,
                            "type": "link",
                        },
                        headers={
                            "Authorization": f"Bearer {token}",
                            "User-Agent": settings.reddit_user_agent,
                        },
                    )
                    if response.status_code != 200:
                        continue
                    signals.extend(self._parse_reddit_posts(response.json(), query, CollectionMethod.API))
        except Exception as exc:
            logger.warning("Reddit OAuth search failed: %s", exc)

        return _sort_latest(_dedupe(signals))

    async def _search_scraper(self, queries: list[str]) -> list[RawSignal]:
        signals: list[RawSignal] = []
        try:
            async with httpx.AsyncClient(
                timeout=settings.request_timeout_seconds, follow_redirects=True
            ) as client:
                for query in queries:
                    ddg_query = f"site:reddit.com {query}"
                    url = f"https://html.duckduckgo.com/html/?q={quote_plus(ddg_query)}"
                    response = await client.get(url, headers={"User-Agent": USER_AGENT})
                    if response.status_code != 200:
                        continue
                    soup = BeautifulSoup(response.text, "lxml")
                    for result in soup.select(".result")[:10]:
                        link_el = result.select_one("a.result__a")
                        if not link_el:
                            continue
                        href = link_el.get("href", "")
                        if "reddit.com" not in href:
                            continue
                        title = link_el.get_text(strip=True)
                        snippet_el = result.select_one(".result__snippet")
                        content = snippet_el.get_text(strip=True) if snippet_el else title
                        if not _query_matches_content(query, title, content):
                            continue
                        signals.append(
                            _signal(
                                platform="reddit",
                                source_name="Reddit",
                                title=title[:300],
                                content=content[:500],
                                url=href,
                                author=None,
                                published_at=None,
                                method=CollectionMethod.HTML_SCRAPER,
                                search_query=query,
                            )
                        )
        except Exception as exc:
            logger.warning("Reddit scraper failed: %s", exc)

        return _sort_latest(_dedupe(signals))

    def _parse_reddit_posts(self, data: dict, query: str, method: CollectionMethod) -> list[RawSignal]:
        signals = []
        for post in data.get("data", {}).get("children", []):
            d = post.get("data", {})
            title = d.get("title", "")
            content = d.get("selftext", "") or title
            if not _query_matches_content(query, title, content):
                continue
            signals.append(
                _signal(
                    platform="reddit",
                    source_name="Reddit",
                    title=title,
                    content=content,
                    url=f"https://reddit.com{d.get('permalink', '')}",
                    author=d.get("author"),
                    published_at=datetime.fromtimestamp(
                        d.get("created_utc", 0), tz=timezone.utc
                    ),
                    method=method,
                    search_query=query,
                    metadata={"subreddit": d.get("subreddit"), "score": d.get("score")},
                )
            )
        return signals


class HackerNewsSearchCollector:
    """Search HackerNews using [VENDOR] + [VULNERABILITY KEYWORD] via Algolia API."""

    async def search(
        self,
        queries: list[str],
        lookback_days: int,
        vendors: list[str] | None = None,
    ) -> list[RawSignal]:
        hn_queries = build_hackernews_queries(
            vendors=vendors,
            max_queries=settings.max_results_per_source,
        )
        signals: list[RawSignal] = []
        cutoff_ts = int(
            (datetime.now(timezone.utc) - timedelta(days=lookback_days)).timestamp()
        )

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                for query in hn_queries:
                    response = await client.get(
                        "https://hn.algolia.com/api/v1/search",
                        params={
                            "query": query,
                            "tags": "story",
                            "numericFilters": f"created_at_i>{cutoff_ts}",
                            "hitsPerPage": 20,
                        },
                    )
                    if response.status_code != 200:
                        continue
                    for hit in response.json().get("hits", []):
                        title = hit.get("title", "")
                        content = hit.get("story_text", "") or title
                        if not _query_matches_content(query, title, content):
                            continue
                        url = hit.get("url") or (
                            f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                        )
                        published = datetime.fromtimestamp(
                            hit.get("created_at_i", 0), tz=timezone.utc
                        )
                        signals.append(
                            _signal(
                                platform="hackernews",
                                source_name="Hacker News",
                                title=title,
                                content=content,
                                url=url,
                                author=hit.get("author"),
                                published_at=published,
                                method=CollectionMethod.API,
                                search_query=query,
                                metadata={
                                    "points": hit.get("points"),
                                    "num_comments": hit.get("num_comments"),
                                },
                            )
                        )
        except Exception as exc:
            logger.warning("HackerNews search failed: %s", exc)

        return _sort_latest(_dedupe(signals))


class LinkedInSearchCollector:
    """Search LinkedIn posts using [VENDOR] + [VULNERABILITY KEYWORD] via search engine."""

    LINKEDIN_SEARCH_PATTERNS = [
        'site:linkedin.com/posts "{query}"',
        'site:linkedin.com/pulse "{query}"',
        'site:linkedin.com "{query}" vulnerability OR exploit',
    ]

    async def search(
        self,
        queries: list[str],
        lookback_days: int,
        vendors: list[str] | None = None,
    ) -> list[RawSignal]:
        li_queries = build_linkedin_queries(
            vendors=vendors,
            max_queries=settings.max_results_per_source,
        )
        signals: list[RawSignal] = []

        try:
            async with httpx.AsyncClient(
                timeout=settings.request_timeout_seconds, follow_redirects=True
            ) as client:
                for query in li_queries:
                    try:
                        ddg_query = self.LINKEDIN_SEARCH_PATTERNS[0].format(query=query)
                        url = f"https://html.duckduckgo.com/html/?q={quote_plus(ddg_query)}"
                        response = await client.get(url, headers={"User-Agent": USER_AGENT})
                        if response.status_code != 200:
                            continue
                        soup = BeautifulSoup(response.text, "lxml")
                        for result in soup.select(".result")[:8]:
                            link_el = result.select_one("a.result__a")
                            if not link_el:
                                continue
                            href = link_el.get("href", "")
                            if "linkedin.com" not in href:
                                continue
                            title = link_el.get_text(strip=True)
                            snippet_el = result.select_one(".result__snippet")
                            content = snippet_el.get_text(strip=True) if snippet_el else title
                            if not _query_matches_content(query, title, content):
                                continue
                            signals.append(
                                _signal(
                                    platform="linkedin",
                                    source_name="LinkedIn",
                                    title=title[:300],
                                    content=content[:500],
                                    url=href,
                                    author=_extract_linkedin_author(href),
                                    published_at=None,
                                    method=CollectionMethod.HTML_SCRAPER,
                                    search_query=query,
                                )
                            )
                    except Exception as exc:
                        logger.debug("LinkedIn query failed for %s: %s", query, exc)
        except Exception as exc:
            logger.warning("LinkedIn search failed: %s", exc)

        return _sort_latest(_dedupe(signals))


def _extract_linkedin_author(url: str) -> str | None:
    match = re.search(r"linkedin\.com/in/([^/?]+)", url)
    return match.group(1) if match else None


def _dedupe(signals: list[RawSignal]) -> list[RawSignal]:
    seen: set[str] = set()
    unique: list[RawSignal] = []
    for s in signals:
        key = (s.url or s.title).lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(s)
    return unique


def _sort_latest(signals: list[RawSignal]) -> list[RawSignal]:
    return sorted(
        signals,
        key=lambda s: s.published_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
