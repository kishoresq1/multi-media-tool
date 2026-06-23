"""
Keyword matching for scrapers, APIs, and SQLite table inserts.

Priority:
  1. SEARCH_KEYWORDS (primary) — used for scraper/API search and table inserts
  2. VENDOR + VULNERABILITY + THREAT keywords (fallback) — optional, disabled by default
"""

from datetime import datetime, timedelta, timezone

from app.config.keywords import (
    SEARCH_KEYWORDS,
    THREAT_ACTIVITY_KEYWORDS,
    VENDOR_KEYWORDS,
    VULNERABILITY_KEYWORDS,
)


def _find_in_text(text: str, keywords: list[str]) -> list[str]:
    lower = text.lower()
    return [kw for kw in keywords if kw.lower() in lower]


def match_primary(text: str) -> list[str]:
    """PRIMARY: SEARCH_KEYWORDS — used first by scrapers/APIs."""
    return _find_in_text(text, SEARCH_KEYWORDS)


def match_fallback(text: str) -> dict[str, list[str]]:
    """FALLBACK: vendor + vulnerability + threat — only when primary has no match."""
    return {
        "vendors": _find_in_text(text, VENDOR_KEYWORDS),
        "vulnerability": _find_in_text(text, VULNERABILITY_KEYWORDS),
        "threat": _find_in_text(text, THREAT_ACTIVITY_KEYWORDS),
    }


def has_fallback_match(text: str) -> bool:
    fb = match_fallback(text)
    return bool(fb["vendors"] or fb["vulnerability"] or fb["threat"])


def is_within_lookback(
    published_at: datetime | None,
    lookback_days: int = 30,
) -> bool:
    """Only store posts published within the lookback window."""
    if published_at is None:
        return False
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    return published_at >= cutoff


def should_store(
    text: str,
    requested_vendors: list[str] | None = None,
    *,
    allow_cve: bool = True,
    primary_only: bool = True,
) -> tuple[bool, str, list[str]]:
    """
    Decide if a scraped/API result should be inserted into a table.

    Returns: (should_insert, tier, matched_keywords)
      tier = "primary" | "fallback" | ""
    """
    import re

    primary = match_primary(text)
    if primary:
        if requested_vendors:
            lower = text.lower()
            if not any(v.lower() in lower for v in requested_vendors):
                return False, "", []
        return True, "primary", primary

    if primary_only:
        return False, "", []

    # FALLBACK — only when SEARCH_KEYWORDS found nothing (if enabled)
    fb = match_fallback(text)
    fb_hits = fb["vendors"] + fb["vulnerability"] + fb["threat"]
    if allow_cve and re.search(r"CVE-\d{4}-\d{4,}", text, re.I):
        fb_hits = fb_hits + ["CVE"]

    if fb_hits:
        if requested_vendors:
            lower = text.lower()
            vendor_ok = any(v.lower() in lower for v in requested_vendors)
            vendor_ok = vendor_ok or any(v in fb["vendors"] for v in requested_vendors)
            if not vendor_ok:
                return False, "", []
        return True, "fallback", list(dict.fromkeys(fb_hits))

    return False, "", []


def get_matched_for_storage(text: str) -> dict[str, list[str]]:
    """Return matched keyword lists for DB columns (primary first in vuln list)."""
    primary = match_primary(text)
    fb = match_fallback(text)
    vuln = primary + [k for k in fb["vulnerability"] if k not in primary]
    return {
        "matched_vendors": fb["vendors"],
        "matched_vuln_keywords": vuln,
        "matched_threat_keywords": fb["threat"],
        "keyword_tier": "primary" if primary else ("fallback" if vuln or fb["threat"] or fb["vendors"] else ""),
    }


def build_scraper_queries(
    vendors: list[str] | None = None,
    max_queries: int = 60,
) -> list[str]:
    """
    Build scraper/API search queries using PRIMARY SEARCH_KEYWORDS only.
    Format: [VENDOR] + [SEARCH_KEYWORD]
    """
    vendor_list = vendors if vendors else VENDOR_KEYWORDS[:15]
    queries: list[str] = []

    for vendor in vendor_list:
        for kw in SEARCH_KEYWORDS:
            queries.append(f"{vendor} {kw}")
            if len(queries) >= max_queries:
                return _dedupe(queries)

    return _dedupe(queries)[:max_queries]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out
