"""Keyword and lookback rules for company breach intel."""

from datetime import datetime, timedelta, timezone

from app.config.company_breach_keywords import BREACH_SEARCH_KEYWORDS
from app.config.company_breach_sources import TIER_1_COMPANY_BREACH_SOURCE_IDS
from app.config.keyword_matcher import match_primary, match_fallback


def _find_breach_keywords(text: str) -> list[str]:
    lower = text.lower()
    return [kw for kw in BREACH_SEARCH_KEYWORDS if kw.lower() in lower]


def is_within_lookback(
    published_at: datetime | None,
    lookback_days: int = 30,
) -> bool:
    if published_at is None:
        return False
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    return published_at >= cutoff


def should_store_breach(
    text: str,
    source_id: str,
) -> tuple[bool, str, list[str]]:
    """
  Tier 1 breach outlets: store all items within lookback (site is breach-focused).
  Others: require breach keyword or primary search keyword match.
  """
    if source_id in TIER_1_COMPANY_BREACH_SOURCE_IDS:
        breach_hits = _find_breach_keywords(text)
        return True, "tier1", breach_hits

    breach_hits = _find_breach_keywords(text)
    if breach_hits:
        return True, "breach", breach_hits

    primary = match_primary(text)
    if primary:
        return True, "primary", primary

    fb = match_fallback(text)
    if fb["threat"]:
        return True, "threat", fb["threat"]

    return False, "", []
