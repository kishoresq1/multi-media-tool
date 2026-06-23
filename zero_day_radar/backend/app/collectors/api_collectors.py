import logging
from datetime import datetime, timedelta, timezone

import httpx

from app.collectors.base import BaseCollector, CollectorResult
from app.config.settings import settings
from app.models.schemas import CollectionMethod

logger = logging.getLogger(__name__)


class HackerNewsCollector(BaseCollector):
    async def collect(
        self,
        query_terms: list[str],
        lookback_days: int = 30,
    ) -> CollectorResult:
        signals = []
        cutoff_ts = int(
            (datetime.now(timezone.utc) - timedelta(days=lookback_days)).timestamp()
        )

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                for term in query_terms[:5]:
                    response = await client.get(
                        "https://hn.algolia.com/api/v1/search",
                        params={
                            "query": term,
                            "tags": "story",
                            "numericFilters": f"created_at_i>{cutoff_ts}",
                            "hitsPerPage": 20,
                        },
                    )
                    response.raise_for_status()
                    hits = response.json().get("hits", [])

                    for hit in hits:
                        title = hit.get("title", "")
                        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                        published = datetime.fromtimestamp(
                            hit.get("created_at_i", 0), tz=timezone.utc
                        )
                        signals.append(
                            self._make_signal(
                                title=title,
                                content=hit.get("story_text", "") or title,
                                url=url,
                                published_at=published,
                                author=hit.get("author"),
                                method=CollectionMethod.API,
                                metadata={"points": hit.get("points"), "num_comments": hit.get("num_comments")},
                            )
                        )
        except Exception as exc:
            logger.warning("HackerNews API failed: %s", exc)
            return CollectorResult(success=False, error=str(exc))

        return CollectorResult(
            signals=self._dedupe_signals(signals)[: settings.max_results_per_source],
            success=True,
            method_used=CollectionMethod.API,
        )

    def _dedupe_signals(self, signals: list) -> list:
        seen: set[str] = set()
        unique = []
        for s in signals:
            key = s.url or s.title
            if key not in seen:
                seen.add(key)
                unique.append(s)
        return unique


class RedditCollector(BaseCollector):
    async def collect(
        self,
        query_terms: list[str],
        lookback_days: int = 30,
    ) -> CollectorResult:
        if not settings.reddit_client_id or not settings.reddit_client_secret:
            return CollectorResult(
                success=False,
                error="Reddit API credentials not configured (ZDR_REDDIT_CLIENT_ID, ZDR_REDDIT_CLIENT_SECRET)",
            )

        signals = []
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

                for term in query_terms[:5]:
                    response = await client.get(
                        "https://oauth.reddit.com/search",
                        params={
                            "q": term,
                            "sort": "new",
                            "t": "month" if lookback_days <= 30 else "year",
                            "limit": 25,
                            "type": "link",
                        },
                        headers={
                            "Authorization": f"Bearer {token}",
                            "User-Agent": settings.reddit_user_agent,
                        },
                    )
                    response.raise_for_status()
                    posts = response.json().get("data", {}).get("children", [])

                    for post in posts:
                        d = post.get("data", {})
                        title = d.get("title", "")
                        content = d.get("selftext", "") or title
                        signals.append(
                            self._make_signal(
                                title=title,
                                content=content,
                                url=f"https://reddit.com{d.get('permalink', '')}",
                                published_at=datetime.fromtimestamp(
                                    d.get("created_utc", 0), tz=timezone.utc
                                ),
                                author=d.get("author"),
                                method=CollectionMethod.API,
                                metadata={"subreddit": d.get("subreddit"), "score": d.get("score")},
                            )
                        )
        except Exception as exc:
            logger.warning("Reddit API failed: %s", exc)
            return CollectorResult(success=False, error=str(exc))

        return CollectorResult(
            signals=signals[: settings.max_results_per_source],
            success=True,
            method_used=CollectionMethod.API,
        )


class TwitterCollector(BaseCollector):
    async def collect(
        self,
        query_terms: list[str],
        lookback_days: int = 30,
    ) -> CollectorResult:
        if not settings.twitter_bearer_token:
            return CollectorResult(
                success=False,
                error="Twitter API bearer token not configured (ZDR_TWITTER_BEARER_TOKEN)",
            )

        signals = []
        start_time = (
            datetime.now(timezone.utc) - timedelta(days=lookback_days)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                for term in query_terms[:3]:
                    query = f'"{term}" (vulnerability OR exploit OR CVE OR "zero day") -is:retweet'
                    response = await client.get(
                        "https://api.twitter.com/2/tweets/search/recent",
                        params={
                            "query": query,
                            "max_results": 50,
                            "start_time": start_time,
                            "tweet.fields": "created_at,author_id,public_metrics",
                        },
                        headers={"Authorization": f"Bearer {settings.twitter_bearer_token}"},
                    )
                    response.raise_for_status()
                    tweets = response.json().get("data", [])

                    for tweet in tweets:
                        text = tweet.get("text", "")
                        signals.append(
                            self._make_signal(
                                title=text[:120],
                                content=text,
                                url=f"https://x.com/i/web/status/{tweet.get('id')}",
                                published_at=datetime.fromisoformat(
                                    tweet["created_at"].replace("Z", "+00:00")
                                )
                                if tweet.get("created_at")
                                else None,
                                method=CollectionMethod.API,
                                metadata=tweet,
                            )
                        )
        except Exception as exc:
            logger.warning("Twitter API failed: %s", exc)
            return CollectorResult(success=False, error=str(exc))

        return CollectorResult(
            signals=signals[: settings.max_results_per_source],
            success=True,
            method_used=CollectionMethod.API,
        )


class NVDCollector(BaseCollector):
    async def collect(
        self,
        query_terms: list[str],
        lookback_days: int = 30,
    ) -> CollectorResult:
        signals = []
        pub_start = (
            datetime.now(timezone.utc) - timedelta(days=lookback_days)
        ).strftime("%Y-%m-%dT00:00:00.000")
        pub_end = datetime.now(timezone.utc).strftime("%Y-%m-%dT23:59:59.999")

        headers = {}
        if settings.nvd_api_key:
            headers["apiKey"] = settings.nvd_api_key

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                terms = query_terms[:5] if query_terms != ["*"] else ["*"]
                for term in terms:
                    params: dict = {
                        "pubStartDate": pub_start,
                        "pubEndDate": pub_end,
                        "resultsPerPage": 200,
                    }
                    if term != "*":
                        params["keywordSearch"] = term

                    start_index = 0
                    while start_index < 2000:
                        params["startIndex"] = start_index
                        response = await client.get(
                            "https://services.nvd.nist.gov/rest/json/cves/2.0",
                            params=params,
                            headers=headers,
                        )
                        if response.status_code == 429:
                            logger.warning("NVD rate limited")
                            break
                        response.raise_for_status()
                        body = response.json()
                        vulns = body.get("vulnerabilities", [])
                        if not vulns:
                            break

                        for item in vulns:
                            cve = item.get("cve", {})
                            cve_id = cve.get("id", "")
                            descriptions = cve.get("descriptions", [])
                            desc = next(
                                (d["value"] for d in descriptions if d.get("lang") == "en"),
                                "",
                            )
                            metrics = cve.get("metrics", {})
                            cvss = self._extract_cvss(metrics)
                            title = f"{cve_id} - {desc[:80]}"
                            published = None
                            if cve.get("published"):
                                published = datetime.fromisoformat(
                                    cve["published"].replace("Z", "+00:00")
                                )

                            signals.append(
                                self._make_signal(
                                    title=title,
                                    content=desc,
                                    url=f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                                    published_at=published,
                                    method=CollectionMethod.API,
                                    metadata={
                                        "cve_id": cve_id,
                                        "cvss_score": cvss,
                                        "references": [
                                            r.get("url")
                                            for r in cve.get("references", [])[:5]
                                        ],
                                    },
                                )
                            )

                        total = body.get("totalResults", 0)
                        start_index += len(vulns)
                        if start_index >= total or len(vulns) < params["resultsPerPage"]:
                            break
                        if term != "*":
                            break
        except Exception as exc:
            logger.warning("NVD API failed: %s", exc)
            return CollectorResult(success=False, error=str(exc))

        return CollectorResult(
            signals=self._dedupe_nvd(signals)[: settings.max_results_per_source * 3],
            success=True,
            method_used=CollectionMethod.API,
        )

    def _dedupe_nvd(self, signals: list) -> list:
        seen: set[str] = set()
        out = []
        for s in signals:
            cve_id = s.raw_metadata.get("cve_id", s.title)
            if cve_id not in seen:
                seen.add(cve_id)
                out.append(s)
        return out

    def _extract_cvss(self, metrics: dict) -> float | None:
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            if key in metrics and metrics[key]:
                return metrics[key][0].get("cvssData", {}).get("baseScore")
        return None


class GitHubCollector(BaseCollector):
    async def collect(
        self,
        query_terms: list[str],
        lookback_days: int = 30,
    ) -> CollectorResult:
        signals = []
        headers = {"Accept": "application/vnd.github+json"}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"

        since = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).strftime(
            "%Y-%m-%d"
        )

        search_terms = (
            query_terms[:8]
            if query_terms and query_terms != ["*"]
            else ["RCE", "exploit", "PoC", "zero day", "CVE"]
        )

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                for term in search_terms:
                    if self.source.id == "metasploit":
                        query = f"{term} repo:rapid7/metasploit-framework"
                        endpoint = "https://api.github.com/search/code"
                    else:
                        query = (
                            f"{term} (PoC OR exploit OR vulnerability OR CVE) "
                            f"created:>{since}"
                        )
                        endpoint = "https://api.github.com/search/repositories"

                    response = await client.get(
                        endpoint,
                        params={"q": query, "per_page": 15, "sort": "updated"},
                        headers=headers,
                    )
                    if response.status_code == 403:
                        return CollectorResult(
                            success=False,
                            error="GitHub API rate limit exceeded",
                        )
                    response.raise_for_status()
                    items = response.json().get("items", [])

                    for item in items:
                        if self.source.id == "metasploit":
                            title = f"Metasploit module: {item.get('name', '')}"
                            url = item.get("html_url")
                            content = item.get("path", "")
                        else:
                            title = item.get("full_name", item.get("name", ""))
                            url = item.get("html_url")
                            content = item.get("description", "") or title

                        published = None
                        if item.get("updated_at"):
                            published = datetime.fromisoformat(
                                item["updated_at"].replace("Z", "+00:00")
                            )

                        signals.append(
                            self._make_signal(
                                title=title,
                                content=content,
                                url=url,
                                published_at=published,
                                author=item.get("owner", {}).get("login"),
                                method=CollectionMethod.GITHUB_API,
                                metadata={
                                    "stars": item.get("stargazers_count"),
                                    "is_poc_repo": True,
                                },
                            )
                        )
        except Exception as exc:
            logger.warning("GitHub API failed for %s: %s", self.source.id, exc)
            return CollectorResult(success=False, error=str(exc))

        return CollectorResult(
            signals=signals[: settings.max_results_per_source],
            success=True,
            method_used=CollectionMethod.GITHUB_API,
        )


class MSRCCollector(BaseCollector):
    """Microsoft Security Response Center CVRF API."""

    async def collect(
        self,
        query_terms: list[str],
        lookback_days: int = 30,
    ) -> CollectorResult:
        signals = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.get(
                    "https://api.msrc.microsoft.com/cvrf/v2.0/updates",
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
                updates = response.json().get("value", [])

                for update in updates:
                    update_id = update.get("ID", update.get("Title", ""))
                    title = update.get("Title", update_id)
                    content = f"{update_id} {update.get('DocumentTitle', '')}"
                    combined = f"{title} {content}"

                    if not self._matches_query(combined, query_terms):
                        continue

                    published = self._parse_msrc_date(update_id)
                    if published and published < cutoff:
                        continue

                    signals.append(
                        self._make_signal(
                            title=title,
                            content=content,
                            url=f"https://msrc.microsoft.com/update-guide/releaseNote/{update_id}",
                            published_at=published,
                            method=CollectionMethod.API,
                            metadata=update,
                        )
                    )
        except Exception as exc:
            logger.warning("MSRC API failed: %s", exc)
            return CollectorResult(success=False, error=str(exc))

        signals.sort(
            key=lambda s: s.published_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )

        return CollectorResult(
            signals=signals[: settings.max_results_per_source],
            success=True,
            method_used=CollectionMethod.API,
        )

    def _parse_msrc_date(self, update_id: str) -> datetime | None:
        """Parse MSRC IDs like '2024-Apr' into a datetime."""
        import re

        match = re.match(r"(\d{4})-(\w{3})", update_id)
        if not match:
            return None
        months = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        }
        year = int(match.group(1))
        month = months.get(match.group(2).lower())
        if not month:
            return None
        return datetime(year, month, 1, tzinfo=timezone.utc)
