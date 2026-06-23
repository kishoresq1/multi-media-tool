"""Helpers for SAINT score fields stored in SQLite."""

import json
from typing import Any


def saint_fields(scores: dict[str, Any]) -> dict[str, Any]:
    """Extract DB/API fields from a scorer result dict."""
    return {
        "confidence_score": scores["confidence_score"],
        "risk_level": scores.get("risk_level", "LOW"),
        "score_breakdown": json.dumps(scores.get("score_breakdown", {})),
        "score_reason": scores.get("score_reason", scores.get("reason", "")),
        "source_trust_score": scores.get("source_trust_score", 0.0),
        "keyword_match_score": scores.get("keyword_match_score", 0.0),
        "recency_score": scores.get("recency_score", 0.0),
    }


def parse_score_breakdown(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def normalize_min_score(value: float | None, default: float = 50.0) -> float:
    """Accept 0-100 SAINT scale; legacy 0-1 values are scaled up."""
    if value is None:
        return default
    if value <= 1.0:
        return value * 100.0
    return value
