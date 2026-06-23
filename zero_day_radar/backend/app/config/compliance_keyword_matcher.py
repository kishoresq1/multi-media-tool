"""
Compliance keyword matching for scrapers, APIs, and SQLite table inserts.

Priority:
  1. COMPLIANCE_SEARCH_KEYWORDS (primary)
  2. Privacy + audit + AI governance + framework keywords (fallback)
"""

from app.config.compliance_keywords import (
    AI_GOVERNANCE_KEYWORDS,
    AUDIT_KEYWORDS,
    COMPLIANCE_SEARCH_KEYWORDS,
    FRAMEWORK_KEYWORDS,
    PRIVACY_KEYWORDS,
)
from app.config.keyword_matcher import is_within_lookback

__all__ = [
    "is_within_lookback",
    "match_compliance_primary",
    "match_compliance_fallback",
    "should_store_compliance",
    "get_compliance_matched_for_storage",
]


def _find_in_text(text: str, keywords: list[str]) -> list[str]:
    lower = text.lower()
    return [kw for kw in keywords if kw.lower() in lower]


def match_compliance_primary(text: str) -> list[str]:
    return _find_in_text(text, COMPLIANCE_SEARCH_KEYWORDS)


def match_compliance_fallback(text: str) -> dict[str, list[str]]:
    return {
        "privacy": _find_in_text(text, PRIVACY_KEYWORDS),
        "audit": _find_in_text(text, AUDIT_KEYWORDS),
        "ai_governance": _find_in_text(text, AI_GOVERNANCE_KEYWORDS),
        "framework": _find_in_text(text, FRAMEWORK_KEYWORDS),
    }


def has_compliance_fallback_match(text: str) -> bool:
    fb = match_compliance_fallback(text)
    return any(fb.values())


def should_store_compliance(
    text: str,
    requested_frameworks: list[str] | None = None,
    *,
    primary_only: bool = False,
) -> tuple[bool, str, list[str]]:
    """
    Decide if a compliance signal should be stored.

    Returns: (should_insert, tier, matched_keywords)
    """
    primary = match_compliance_primary(text)
    if primary:
        if requested_frameworks and not _frameworks_match(text, requested_frameworks):
            return False, "", []
        return True, "primary", primary

    if primary_only:
        return False, "", []

    fb = match_compliance_fallback(text)
    fb_hits: list[str] = []
    for group in fb.values():
        fb_hits.extend(group)
    fb_hits = list(dict.fromkeys(fb_hits))

    if fb_hits:
        if requested_frameworks and not _frameworks_match(text, requested_frameworks):
            return False, "", []
        return True, "fallback", fb_hits

    return False, "", []


def _frameworks_match(text: str, requested: list[str]) -> bool:
    lower = text.lower()
    return any(fw.lower() in lower for fw in requested)


def get_compliance_matched_for_storage(text: str) -> dict[str, list[str]]:
    primary = match_compliance_primary(text)
    fb = match_compliance_fallback(text)
    return {
        "matched_compliance_keywords": primary,
        "matched_privacy_keywords": fb["privacy"],
        "matched_audit_keywords": fb["audit"],
        "matched_ai_keywords": fb["ai_governance"],
        "matched_framework_keywords": fb["framework"] + [
            k for k in primary if k not in fb["framework"]
        ],
        "keyword_tier": "primary" if primary else ("fallback" if has_compliance_fallback_match(text) else ""),
    }
