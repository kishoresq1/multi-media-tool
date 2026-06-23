# openosint/tools/track_post.py
"""
Post tracking module.

Searches Reddit for the same cybersecurity story to identify who else has
posted it and measure their engagement. Never raises on failure.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_REDDIT_SEARCH = "https://www.reddit.com/search.json"
_HEADERS = {"User-Agent": "SQ1-OSINT-Bot/1.0 (security research)"}


async def _search_reddit(client: httpx.AsyncClient, query: str, limit: int) -> list[str]:
    """Search Reddit for posts matching the given query."""
    results: list[str] = []
    try:
        params = {
            "q": query,
            "sort": "new",
            "limit": limit,
            "restrict_sr": "false",
            "type": "link",
        }
        resp = await client.get(_REDDIT_SEARCH, params=params)
        if resp.status_code == 200:
            posts = resp.json().get("data", {}).get("children", [])
            for post in posts:
                d = post.get("data", {})
                created_utc = d.get("created_utc", 0)
                posted = (
                    datetime.fromtimestamp(created_utc, tz=timezone.utc).strftime(
                        "%Y-%m-%d %H:%M UTC"
                    )
                    if created_utc
                    else "unknown"
                )
                subreddit = d.get("subreddit", "unknown")
                author = d.get("author", "unknown")
                score = d.get("score", 0)
                comments = d.get("num_comments", 0)
                url = (d.get("url") or "")[:100]
                results.append(
                    f"[Reddit][r/{subreddit}] "
                    f"Posted: {posted} | "
                    f"Score: {score} | "
                    f"Comments: {comments} | "
                    f"Author: u/{author} | "
                    f"URL: {url}"
                )
        elif resp.status_code == 429:
            results.append("[Reddit] Rate limited — try again in a moment.")
        else:
            results.append(f"[Reddit] HTTP {resp.status_code}")
    except Exception as exc:
        results.append(f"[Reddit ERROR] {exc}")
    return results


async def run_track_post_osint(
    story_title: str,
    cve_id: str = "",
    limit: int = 5,
    timeout_seconds: int = 15,
) -> str:
    """
    Search Reddit for the same cybersecurity story.

    Returns who posted it, when, and their engagement stats.

    Parameters
    ----------
    story_title:
        Headline or description of the story.
    cve_id:
        Optional CVE identifier — used as the search query when provided.
    limit:
        Maximum posts to return per source.
    timeout_seconds:
        HTTP request timeout in seconds.

    Returns
    -------
    str
        Formatted tracking results or a descriptive message if none found.
    """
    query = cve_id.strip() if cve_id.strip() else story_title[:100]
    logger.info("Tracking story: %r", query)

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds, headers=_HEADERS) as client:
            results = await _search_reddit(client, query, limit)
    except Exception as exc:
        logger.exception("Unexpected error during post tracking.")
        return f"Internal error: {exc}"

    if not results:
        return f"No competing posts found for: {query}"

    output = f"Competitor post tracking for '{query}':\n\n"
    output += "\n".join(f"[+] {r}" for r in results)
    logger.info("Post tracking complete: %d results", len(results))
    return output
