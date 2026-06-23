import logging
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus, urlparse

import feedparser
import httpx
from bs4 import BeautifulSoup

from app.config.settings import settings

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

NITTER_STATUS_RE = re.compile(r"/([^/]+)/status/(\d+)")
BOT_CHALLENGE_MARKERS = ("anubis_challenge", "not a bot", "cf-challenge", "just a moment")


def nitter_to_x_url(url: str) -> str:
    """Convert a Nitter tweet URL to an x.com URL."""
    if not url:
        return url
    parsed = urlparse(url)
    match = NITTER_STATUS_RE.search(parsed.path)
    if match:
        return f"https://x.com/{match.group(1)}/status/{match.group(2)}"
    return url.replace(parsed.netloc, "x.com") if "nitter" in parsed.netloc else url


def _is_bot_challenge(html: str) -> bool:
    lower = html.lower()
    return any(marker in lower for marker in BOT_CHALLENGE_MARKERS)


class NitterClient:
    """
    Search X/Twitter via Nitter — no API key required.

    Tries RSS search first, then HTML scrape. Rotates through configured instances.
    Set ZDR_NITTER_INSTANCES to your own Nitter instance if public ones are blocked.
    """

    def __init__(self, instances: list[str] | None = None) -> None:
        self.instances = instances or settings.nitter_instances

    async def search(
        self,
        queries: list[str],
        lookback_days: int = 7,
    ) -> list[dict]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        all_tweets: list[dict] = []

        async with httpx.AsyncClient(
            timeout=settings.nitter_timeout_seconds,
            follow_redirects=True,
            verify=settings.nitter_verify_ssl,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        ) as client:
            for query in queries:
                tweets = await self._search_query(client, query, cutoff)
                all_tweets.extend(tweets)

        if not all_tweets:
            logger.warning(
                "Nitter returned 0 tweets. Public instances may be down or blocking bots. "
                "Set ZDR_NITTER_INSTANCES to a working self-hosted Nitter URL."
            )

        return _dedupe_tweets(all_tweets)

    async def _search_query(
        self,
        client: httpx.AsyncClient,
        query: str,
        cutoff: datetime,
    ) -> list[dict]:
        for instance in self.instances:
            tweets = await self._search_rss(client, instance, query, cutoff)
            if tweets:
                logger.debug("Nitter RSS hit on %s for: %s", instance, query)
                return tweets

            tweets = await self._search_html(client, instance, query, cutoff)
            if tweets:
                logger.debug("Nitter HTML hit on %s for: %s", instance, query)
                return tweets

            logger.debug("Nitter instance %s unavailable for: %s", instance, query)

        return []

    async def _search_rss(
        self,
        client: httpx.AsyncClient,
        instance: str,
        query: str,
        cutoff: datetime,
    ) -> list[dict]:
        url = f"{instance.rstrip('/')}/search/rss?f=tweets&q={quote_plus(query)}"
        try:
            response = await client.get(url)
            if response.status_code != 200 or _is_bot_challenge(response.text):
                return []
            feed = feedparser.parse(response.text)
            if not feed.entries:
                return []
        except Exception as exc:
            logger.debug("Nitter RSS error %s: %s", instance, exc)
            return []

        return self._parse_feed_entries(feed, query, instance, cutoff)

    async def _search_html(
        self,
        client: httpx.AsyncClient,
        instance: str,
        query: str,
        cutoff: datetime,
    ) -> list[dict]:
        url = f"{instance.rstrip('/')}/search?f=tweets&q={quote_plus(query)}"
        try:
            response = await client.get(url)
            if response.status_code != 200 or _is_bot_challenge(response.text):
                return []
            soup = BeautifulSoup(response.text, "lxml")
        except Exception as exc:
            logger.debug("Nitter HTML error %s: %s", instance, exc)
            return []

        tweets = []
        for item in soup.select(".timeline-item")[: settings.max_results_per_source]:
            content_el = item.select_one(".tweet-content")
            if not content_el:
                continue
            content = content_el.get_text(separator=" ", strip=True)
            if not content:
                continue

            link_el = item.select_one(".tweet-link") or item.select_one("a[href*='/status/']")
            href = link_el.get("href", "") if link_el else ""
            if href and not href.startswith("http"):
                href = f"{instance.rstrip('/')}{href}"
            x_url = nitter_to_x_url(href)

            author_el = item.select_one(".username")
            author = author_el.get_text(strip=True) if author_el else None

            date_el = item.select_one(".tweet-date a") or item.select_one(".tweet-date")
            published = _parse_html_date(
                date_el.get("title") or date_el.get_text(strip=True) if date_el else None
            )

            if published and published < cutoff:
                continue

            tweets.append({
                "title": content[:300],
                "content": content[:1000],
                "url": x_url,
                "author": author,
                "published_at": published,
                "search_query": query,
                "nitter_instance": instance,
            })

        return tweets

    def _parse_feed_entries(
        self,
        feed,
        query: str,
        instance: str,
        cutoff: datetime,
    ) -> list[dict]:
        tweets = []
        for entry in feed.entries[: settings.max_results_per_source]:
            title = entry.get("title", "")
            content = entry.get("summary", entry.get("description", title))
            if "<" in content:
                content = BeautifulSoup(content, "lxml").get_text(separator=" ", strip=True)

            link = nitter_to_x_url(entry.get("link", ""))
            author = entry.get("author", "")
            published = _parse_feed_date(entry)

            if published and published < cutoff:
                continue

            tweets.append({
                "title": title[:300] or content[:300],
                "content": content[:1000],
                "url": link,
                "author": author,
                "published_at": published,
                "search_query": query,
                "nitter_instance": instance,
            })
        return tweets


def _parse_feed_date(entry) -> datetime | None:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
    return None


def _parse_html_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    for fmt in ("%b %d, %Y · %I:%M %p %Z", "%b %d, %Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _dedupe_tweets(tweets: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique: list[dict] = []
    for t in tweets:
        key = (t.get("url") or t.get("content", "")).lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(t)
    return sorted(
        unique,
        key=lambda t: t.get("published_at") or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
