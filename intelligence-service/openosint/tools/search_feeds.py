# openosint/tools/search_feeds.py
"""
Cybersecurity RSS/Atom feed intelligence module for SQ1 OSINT.

Fetches articles from 19 trusted cybersecurity news sources, uses AI to
classify each into the SQ1 intel schema (VULNERABILITY / THREAT / BREACH /
COMPLIANCE / MISINFORMATION), extracts CVE IDs and severity, and returns
structured intel items ready for storage and marketing content generation.

Never raises on failure — errors are captured per-feed.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_USER_AGENT = (
    "Mozilla/5.0 (compatible; SQ1-OSINT-Bot/1.0; +https://github.com/LakshmanS27/SQ1INT)"
)
_FEED_TIMEOUT = 20
_MAX_ARTICLES_PER_FEED = 5
_MAX_SUMMARY_CHARS = 1500

_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)

# Keyword-based heuristic maps (fallback when no AI key is configured)
_CLASSIFICATION_KEYWORDS: dict[str, list[str]] = {
    "VULNERABILITY": [
        "cve", "vulnerability", "patch", "exploit", "rce", "zero-day", "0-day",
        "buffer overflow", "sql injection", "xss", "ssrf", "csrf", "privilege escalation",
        "remote code", "arbitrary code", "security flaw", "security update", "advisory",
        "nvd", "nist", "cisa", "kev", "poc", "proof of concept",
    ],
    "BREACH": [
        "breach", "leaked", "data leak", "data exposed", "stolen", "compromised",
        "hacked", "intrusion", "unauthorized access", "credential", "database dump",
        "personal data", "pii", "records exposed", "million users", "million accounts",
    ],
    "THREAT": [
        "ransomware", "malware", "phishing", "apt", "threat actor", "campaign",
        "trojan", "botnet", "backdoor", "c2", "command and control", "nation-state",
        "espionage", "cyber attack", "ddos", "wiper", "loader", "stealer",
    ],
    "COMPLIANCE": [
        "gdpr", "ccpa", "hipaa", "pci", "regulation", "compliance", "audit",
        "fine", "penalty", "law", "legislation", "framework", "nist csf",
        "iso 27001", "sec", "ftc", "enforcement", "ruling", "standard",
    ],
    "MISINFORMATION": [
        "fake", "false claim", "debunked", "misinformation", "disinformation",
        "hoax", "misleading", "fabricated", "unverified", "myth",
    ],
}

_SEVERITY_KEYWORDS: dict[str, list[str]] = {
    "CRITICAL": [
        "critical", "actively exploited", "zero-day", "0-day", "wormable",
        "no patch", "emergency", "ransomware", "nation-state", "widespread",
    ],
    "HIGH": [
        "high severity", "high-severity", "remote code execution", "rce",
        "privilege escalation", "unauthenticated", "pre-auth", "cvss 8", "cvss 9",
        "data breach", "millions affected", "apt",
    ],
    "MEDIUM": [
        "medium", "moderate", "authentication required", "local exploitation",
        "limited impact", "partial", "phishing",
    ],
    "LOW": [
        "low severity", "minor", "informational", "low impact",
    ],
}

# AI classification prompt
_AI_CLASSIFY_PROMPT = """You are a cybersecurity intelligence analyst for SQ1 OSINT.

Analyze this cybersecurity news article and return ONLY a JSON object (no markdown):

{
  "classification": "VULNERABILITY|THREAT|BREACH|COMPLIANCE|MISINFORMATION",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
  "summary": "2-3 sentence plain-English summary optimized for marketing content generation",
  "tags": ["up to 5 lowercase tags"],
  "cve_ids": ["CVE-XXXX-XXXXX if mentioned, else empty"],
  "is_misinformation": false,
  "content_hooks": {
    "headline": "punchy 10-word headline for social media",
    "blog_angle": "one sentence describing the blog post angle",
    "alert_type": "incident|advisory|threat-intel|compliance|misinformation"
  }
}

Classification rules:
- VULNERABILITY: CVEs, patches, exploits, security flaws in software/hardware
- THREAT: Active attacks, APT campaigns, malware, ransomware, phishing
- BREACH: Data breaches, leaks, unauthorized access, exposed databases
- COMPLIANCE: Regulations, fines, standards, audits, policy changes
- MISINFORMATION: False/misleading cybersecurity claims, debunked stories

Severity rules:
- CRITICAL: Actively exploited, zero-day, no patch available, mass impact
- HIGH: RCE, privilege escalation, large-scale breach, nation-state activity
- MEDIUM: Limited exploitation, authenticated attacks, smaller breach
- LOW: Minor issues, theoretical risks, informational
- INFO: News/analysis with no direct threat rating"""


# ---------------------------------------------------------------------------
# RSS parsing helpers (no external deps — pure httpx + regex)
# ---------------------------------------------------------------------------


def _extract_text(tag_content: str) -> str:
    """Strip HTML tags and decode basic HTML entities."""
    text = re.sub(r"<[^>]+>", " ", tag_content)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_feed_xml(xml: str, source_name: str, source_domain: str) -> list[dict]:
    """
    Parse RSS 2.0 or Atom feed XML into a list of article dicts.
    Returns at most _MAX_ARTICLES_PER_FEED items.
    """
    articles: list[dict] = []

    # Try RSS <item> elements first, then Atom <entry>
    item_pattern = re.compile(
        r"<(?:item|entry)>(.*?)</(?:item|entry)>", re.DOTALL | re.IGNORECASE
    )

    for match in item_pattern.finditer(xml):
        block = match.group(1)

        def _tag(name: str) -> str:
            m = re.search(
                rf"<{name}(?:\s[^>]*)?>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{name}>",
                block,
                re.DOTALL | re.IGNORECASE,
            )
            return _extract_text(m.group(1)).strip() if m else ""

        def _attr_or_tag(name: str, attr: str = "href") -> str:
            # Atom <link href="..."/> vs RSS <link>url</link>
            m = re.search(
                rf'<{name}\s[^>]*{attr}=["\']([^"\']+)["\']',
                block,
                re.IGNORECASE,
            )
            if m:
                return m.group(1).strip()
            return _tag(name)

        title = _tag("title") or "(no title)"
        link = _attr_or_tag("link") or _tag("link") or ""
        pub = _tag("pubDate") or _tag("published") or _tag("updated") or ""
        summary = _tag("description") or _tag("summary") or _tag("content") or ""

        if not title or not link:
            continue

        articles.append(
            {
                "title": title[:200],
                "link": link,
                "published_raw": pub,
                "summary_raw": summary[:_MAX_SUMMARY_CHARS],
                "source_name": source_name,
                "source_domain": source_domain,
            }
        )
        if len(articles) >= _MAX_ARTICLES_PER_FEED:
            break

    return articles


# ---------------------------------------------------------------------------
# Heuristic classifier (fallback when no AI key is set)
# ---------------------------------------------------------------------------


def _heuristic_classify(article: dict) -> dict:
    """Classify an article using keyword matching — no AI required."""
    text = (article["title"] + " " + article["summary_raw"]).lower()

    # Classification
    scores: dict[str, int] = {k: 0 for k in _CLASSIFICATION_KEYWORDS}
    for cls, keywords in _CLASSIFICATION_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[cls] += 1
    classification = max(scores, key=lambda k: scores[k])
    if scores[classification] == 0:
        classification = "THREAT"

    # Severity
    severity = "INFO"
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        if any(kw in text for kw in _SEVERITY_KEYWORDS[sev]):
            severity = sev
            break

    cve_ids = list(set(_CVE_RE.findall(article["title"] + " " + article["summary_raw"])))

    # Tags: top 3 matching keywords across all classes
    all_hits: list[str] = []
    for keywords in _CLASSIFICATION_KEYWORDS.values():
        all_hits.extend(kw for kw in keywords if kw in text and len(kw) > 4)
    tags = list(dict.fromkeys(all_hits))[:5]

    is_misinfo = classification == "MISINFORMATION"

    return {
        "classification": classification,
        "severity": severity,
        "summary": (article["summary_raw"] or article["title"])[:400],
        "tags": tags,
        "cve_ids": cve_ids,
        "is_misinformation": is_misinfo,
        "content_hooks": {
            "headline": article["title"][:100],
            "blog_angle": f"Analysis: {article['title'][:80]}",
            "alert_type": "threat-intel",
        },
    }


# ---------------------------------------------------------------------------
# AI classifier
# ---------------------------------------------------------------------------


async def _ai_classify(article: dict) -> dict:
    """Classify an article using the configured AI provider."""
    from openosint.llm import detect_provider, llm_complete

    if detect_provider() is None:
        return _heuristic_classify(article)

    user_msg = (
        f"Source: {article['source_name']} ({article['source_domain']})\n"
        f"Title: {article['title']}\n"
        f"URL: {article['link']}\n"
        f"Summary: {article['summary_raw'][:800]}"
    )

    try:
        raw = await llm_complete(
            system=_AI_CLASSIFY_PROMPT,
            user=user_msg,
            max_tokens=400,
        )
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)
        # Ensure required keys exist; fill any missing with heuristic
        heuristic = _heuristic_classify(article)
        for key in ("classification", "severity", "summary", "tags", "cve_ids",
                    "is_misinformation", "content_hooks"):
            if key not in result:
                result[key] = heuristic[key]
        # Merge CVE IDs found by regex with AI-extracted ones
        regex_cves = list(set(_CVE_RE.findall(article["title"] + " " + article["summary_raw"])))
        combined = list(set(result.get("cve_ids", []) + regex_cves))
        result["cve_ids"] = combined
        return result
    except Exception as exc:
        logger.debug("AI classification failed (%s), using heuristic.", exc)
        return _heuristic_classify(article)


# ---------------------------------------------------------------------------
# Feed fetcher
# ---------------------------------------------------------------------------


async def _fetch_one_feed(
    client: httpx.AsyncClient,
    feed: dict,
) -> list[dict]:
    """Fetch and parse a single RSS/Atom feed. Returns raw article dicts."""
    try:
        resp = await client.get(
            feed["url"],
            headers={"User-Agent": _USER_AGENT},
            follow_redirects=True,
            timeout=_FEED_TIMEOUT,
        )
        if resp.status_code != 200:
            logger.warning("[feeds] %s returned HTTP %d", feed["name"], resp.status_code)
            return []
        articles = _parse_feed_xml(resp.text, feed["name"], feed["domain"])
        logger.debug("[feeds] %s — %d articles parsed", feed["name"], len(articles))
        return articles
    except Exception as exc:
        logger.warning("[feeds] Failed to fetch %s: %s", feed["name"], exc)
        return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def fetch_and_classify_feeds(
    sources: list[dict] | None = None,
    limit_per_feed: int = _MAX_ARTICLES_PER_FEED,
    use_ai: bool = True,
    timeout_seconds: int = 30,
) -> list[dict]:
    """
    Fetch articles from cybersecurity news feeds and classify them with AI.

    Parameters
    ----------
    sources:
        List of feed source dicts from ``openosint.data.feeds.FEED_SOURCES``.
        If None, all registered sources are used.
    limit_per_feed:
        Max articles to pull from each feed (default 5).
    use_ai:
        If True (default), use the configured AI provider for classification.
        Falls back to heuristic automatically if no AI key is set.
    timeout_seconds:
        HTTP client timeout per request.

    Returns
    -------
    list[dict]
        List of structured intel items ready for ``store.insert_intel()``.
    """
    from openosint.data.feeds import FEED_SOURCES

    feed_list = sources or FEED_SOURCES
    now = datetime.now(tz=timezone.utc).isoformat()

    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        # Fetch all feeds concurrently
        fetch_tasks = [_fetch_one_feed(client, feed) for feed in feed_list]
        all_raw: list[list[dict]] = await asyncio.gather(*fetch_tasks)

    # Flatten and deduplicate by URL
    seen_links: set[str] = set()
    unique_articles: list[dict] = []
    for batch in all_raw:
        for article in batch[:limit_per_feed]:
            link = article.get("link", "")
            if link and link not in seen_links:
                seen_links.add(link)
                unique_articles.append(article)

    if not unique_articles:
        return []

    # Classify all articles (AI or heuristic) concurrently
    if use_ai:
        classify_tasks = [_ai_classify(a) for a in unique_articles]
    else:
        classify_tasks = [asyncio.coroutine(lambda a=a: _heuristic_classify(a))() for a in unique_articles]  # type: ignore

    classifications: list[dict] = await asyncio.gather(*classify_tasks)

    # Build structured intel items
    intel_items: list[dict] = []
    for article, cls_result in zip(unique_articles, classifications):
        # Stable ID based on URL so re-ingestion produces the same ID
        item_id = str(uuid.UUID(hashlib.md5(article["link"].encode()).hexdigest()))

        content_hooks = cls_result.get("content_hooks", {})
        item: dict[str, Any] = {
            "id": item_id,
            "title": article["title"],
            "classification": cls_result.get("classification", "THREAT"),
            "severity": cls_result.get("severity", "INFO"),
            "summary": cls_result.get("summary", article["summary_raw"])[:600],
            "cveIds": cls_result.get("cve_ids", []),
            "tags": cls_result.get("tags", []),
            "timestamp": now,
            "sourceVerified": True,
            "isMisinformation": cls_result.get("is_misinformation", False),
            "usedInMarketing": False,
            "source": article["source_domain"],
            "sourceName": article["source_name"],
            "sourceUrl": article["link"],
            # Content generation hooks consumed by the marketing module
            "contentHooks": {
                "headline": content_hooks.get("headline", article["title"][:100]),
                "blogAngle": content_hooks.get("blog_angle", ""),
                "alertType": content_hooks.get("alert_type", "threat-intel"),
            },
        }
        intel_items.append(item)

    return intel_items


async def run_feeds_osint(
    query: str = "",
    source_filter: str = "",
    limit: int = 20,
    timeout_seconds: int = 30,
) -> str:
    """
    Fetch and classify articles from cybersecurity news feeds.

    Parameters
    ----------
    query:
        Optional keyword to filter results by title/summary.
    source_filter:
        Optional source name substring to restrict which feeds are polled
        (e.g. "BleepingComputer", "Krebs").
    limit:
        Maximum number of results to return (across all feeds).
    timeout_seconds:
        HTTP request timeout per feed in seconds.

    Returns
    -------
    str
        Formatted result string or a descriptive error message.
    """
    from openosint.data.feeds import FEED_SOURCES

    logger.info("[feeds] Starting feed scan — query=%r source=%r", query, source_filter)

    sources = FEED_SOURCES
    if source_filter:
        sf = source_filter.lower()
        sources = [s for s in sources if sf in s["name"].lower() or sf in s["domain"].lower()]
        if not sources:
            return f"No feed sources match filter '{source_filter}'."

    try:
        items = await fetch_and_classify_feeds(
            sources=sources,
            limit_per_feed=_MAX_ARTICLES_PER_FEED,
            use_ai=True,
            timeout_seconds=timeout_seconds,
        )
    except Exception as exc:
        logger.exception("[feeds] Unexpected error during feed scan.")
        return f"Internal error: {exc}"

    if not items:
        return "No articles retrieved from feeds. Check network connectivity."

    # Filter by query if provided
    if query:
        ql = query.lower()
        items = [
            i for i in items
            if ql in i["title"].lower() or ql in i["summary"].lower()
        ]
        if not items:
            return f"No feed articles matched query '{query}'."

    items = items[:limit]

    lines = [
        f"Feed Intelligence — {len(items)} article(s)"
        + (f" matching '{query}'" if query else "")
        + f" from {len(sources)} source(s):\n"
    ]

    for item in items:
        sev = item["severity"]
        cls = item["classification"]
        cves = " | ".join(item["cveIds"]) if item["cveIds"] else ""
        misinfo = " ⚠ MISINFORMATION" if item["isMisinformation"] else ""
        lines.append(
            f"[{sev}][{cls}] {item['title']}{misinfo}\n"
            f"  Source : {item['sourceName']} — {item['sourceUrl']}\n"
            f"  Summary: {item['summary'][:200]}\n"
            + (f"  CVEs   : {cves}\n" if cves else "")
            + f"  Hooks  : headline='{item['contentHooks']['headline'][:60]}' "
            f"type={item['contentHooks']['alertType']}"
        )

    logger.info("[feeds] Feed scan complete — %d items returned.", len(items))
    return "\n\n".join(lines)
