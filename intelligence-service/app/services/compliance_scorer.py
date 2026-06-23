from datetime import datetime, timezone

from app.config.compliance_keyword_matcher import get_compliance_matched_for_storage
from app.config.compliance_sources import SOURCE_ORG_MAP, SOURCE_TIER_MAP, TIER_1_COMPLIANCE_SOURCE_IDS
from app.processors.compliance_extractor import ComplianceExtractor
from app.processors.compliance_scoring_engine import ComplianceScoringEngine


class ComplianceScorer:
    """
    SAINT Compliance Scorer — wraps ComplianceScoringEngine for pipeline use.

    Returns 0-100 confidence_score with risk_level, score_breakdown, and reason.
    """

    def __init__(self) -> None:
        self.extractor = ComplianceExtractor()
        self.engine = ComplianceScoringEngine()

    def score(
        self,
        title: str,
        content: str,
        source_id: str,
        source_name: str,
        published_at: datetime | None,
        requested_frameworks: list[str] | None = None,
    ) -> dict:
        combined = f"{title} {content}"
        matched = get_compliance_matched_for_storage(combined)
        enrichment = self.extractor.enrich(title, content)
        enrichment["organization"] = SOURCE_ORG_MAP.get(source_id, "")

        saint = self.engine.score_signal(source_id, source_name, enrichment)

        tier = SOURCE_TIER_MAP.get(source_id, 2)
        if source_id in TIER_1_COMPLIANCE_SOURCE_IDS:
            tier = 1

        recency_factor = self._recency_factor(published_at)

        return {
            **matched,
            **enrichment,
            "source_tier": tier,
            "confidence_score": float(saint["confidence_score"]),
            "risk_level": saint["risk_level"],
            "score_breakdown": saint["score_breakdown"],
            "score_reason": saint["reason"],
            "source_trust_score": float(saint["score_breakdown"]["source_score"]),
            "keyword_match_score": float(len(matched.get("matched_compliance_keywords", [])) * 5),
            "recency_score": recency_factor,
        }

    def _recency_factor(self, published_at: datetime | None) -> float:
        """0-100 recency helper for display; not used in SAINT score."""
        if not published_at:
            return 50.0
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - published_at).days
        if age_days <= 7:
            return 100.0
        if age_days <= 30:
            return 85.0
        if age_days <= 90:
            return 65.0
        if age_days <= 180:
            return 45.0
        return 25.0
