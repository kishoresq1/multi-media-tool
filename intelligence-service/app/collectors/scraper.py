import logging
import re
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector, CollectorResult
from app.config.settings import settings
from app.models.schemas import CollectionMethod

logger = logging.getLogger(__name__)


class HTMLScraperCollector(BaseCollector):
    """Generic HTML scraper for sources without RSS/API."""

    async def collect(
        self,
        query_terms: list[str],
        lookback_days: int = 30,
    ) -> CollectorResult:
        signals = []
        url = self.source.url

        try:
            verify_ssl = self.source.id not in ("ransomware_live",)
            async with httpx.AsyncClient(
                timeout=settings.request_timeout_seconds,
                verify=verify_ssl,
            ) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "ZeroDayRadar/0.1 CTI Collector"},
                    follow_redirects=True,
                )
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "lxml")
        except Exception as exc:
            logger.warning("HTML scraper failed for %s: %s", self.source.id, exc)
            return CollectorResult(success=False, error=str(exc))

        articles = self._extract_articles(soup)

        for article in articles[: settings.max_results_per_source]:
            combined = f"{article['title']} {article.get('content', '')}"
            if not self._matches_query(combined, query_terms):
                continue

            signals.append(
                self._make_signal(
                    title=article["title"],
                    content=article.get("content", ""),
                    url=article.get("url"),
                    published_at=article.get("published_at"),
                    method=CollectionMethod.HTML_SCRAPER,
                    metadata={"scraped_from": url},
                )
            )

        return CollectorResult(
            signals=signals,
            success=True,
            method_used=CollectionMethod.HTML_SCRAPER,
        )

    def _extract_articles(self, soup: BeautifulSoup) -> list[dict]:
        articles: list[dict] = []

        selectors = [
            ("article", None),
            ("div", {"class": re.compile(r"post|article|entry|advisory|bulletin", re.I)}),
            ("li", {"class": re.compile(r"post|article|item", re.I)}),
            ("tr", None),
            ("a", {"class": re.compile(r"title|heading", re.I)}),
        ]

        for tag, attrs in selectors:
            elements = soup.find_all(tag, attrs) if attrs else soup.find_all(tag)
            for el in elements[:50]:
                title_el = el.find(["h1", "h2", "h3", "h4", "a"]) or el
                title = title_el.get_text(strip=True)
                if not title or len(title) < 10:
                    continue

                link = el.find("a")
                href = link.get("href") if link else None
                if href and href.startswith("/"):
                    from urllib.parse import urljoin

                    href = urljoin(self.source.url, href)

                content = el.get_text(separator=" ", strip=True)[:500]
                articles.append(
                    {
                        "title": title[:300],
                        "content": content,
                        "url": href,
                        "published_at": None,
                    }
                )

            if articles:
                break

        if not articles:
            for link in soup.find_all("a", href=True)[:100]:
                text = link.get_text(strip=True)
                if len(text) > 15 and any(
                    kw in text.lower()
                    for kw in ("security", "advisory", "cve", "vulnerability", "bulletin")
                ):
                    href = link["href"]
                    if href.startswith("/"):
                        from urllib.parse import urljoin

                        href = urljoin(self.source.url, href)
                    articles.append({"title": text[:300], "content": text, "url": href})

        seen: set[str] = set()
        unique = []
        for a in articles:
            key = a["title"]
            if key not in seen:
                seen.add(key)
                unique.append(a)
        return unique


class LinkedInCollector(BaseCollector):
    """LinkedIn scraper placeholder — requires authenticated session for production."""

    async def collect(
        self,
        query_terms: list[str],
        lookback_days: int = 30,
    ) -> CollectorResult:
        return CollectorResult(
            success=False,
            error=(
                "LinkedIn scraping requires authenticated session. "
                "Configure LinkedIn credentials or use official API."
            ),
        )


class TelegramCollector(BaseCollector):
    async def collect(
        self,
        query_terms: list[str],
        lookback_days: int = 30,
    ) -> CollectorResult:
        return CollectorResult(
            success=False,
            error=(
                "Telegram channel monitoring requires Bot API token and channel IDs. "
                "Configure TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNELS."
            ),
        )
