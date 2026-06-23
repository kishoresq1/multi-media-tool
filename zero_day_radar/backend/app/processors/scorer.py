import hashlib

from app.config.sources import SOURCE_REGISTRY, SourceCategory
from app.models.schemas import RawSignal, ThreatFinding
from app.processors.threat_scoring_engine import ThreatScoringEngine


class ConfidenceScorer:
    """
    SAINT Threat Scoring Engine wrapper for hunter/pipeline flows.

    Uses 0-100 confidence scores with risk levels.
    """

    def __init__(self) -> None:
        self.engine = ThreatScoringEngine()

    def score_signal(
        self,
        signal: RawSignal,
        enrichment: dict,
        query_products: list[str],
    ) -> ThreatFinding:
        source_type = self._source_type(signal.source_id, signal.source_category)
        saint = self.engine.score_signal(
            signal.source_id,
            signal.source_name,
            source_type,
            {
                "vendor_name": (enrichment.get("vendors") or query_products or [""])[0],
                "product_name": (enrichment.get("products") or query_products or [""])[0]
                if query_products
                else "",
                "cve_present": bool(enrichment.get("cves")),
                "poc_available": bool(enrichment.get("has_poc")),
                "actively_exploited": bool(
                    enrichment.get("active_exploitation") or enrichment.get("in_cisa_kev")
                ),
                "signal_count": 1,
            },
        )

        finding_id = self._generate_id(signal)
        breakdown = saint["score_breakdown"]

        return ThreatFinding(
            id=finding_id,
            title=signal.title,
            url=signal.url,
            summary=signal.content[:500] if signal.content else signal.title,
            published_at=signal.published_at,
            vendors=enrichment.get("vendors", []),
            products=enrichment.get("products", []),
            cves=enrichment.get("cves", []),
            vulnerability_types=enrichment.get("vulnerability_types", []),
            threat_indicators=enrichment.get("threat_indicators", []),
            has_poc=enrichment.get("has_poc", False),
            active_exploitation=enrichment.get("active_exploitation", False),
            in_cisa_kev=enrichment.get("in_cisa_kev", False),
            is_vendor_advisory=enrichment.get("is_vendor_advisory", False),
            confidence_score=float(saint["confidence_score"]),
            source_trust_score=float(breakdown["source_score"]),
            recency_score=0.0,
            keyword_match_score=float(breakdown["bonus_score"]),
            sources=[signal.source_name],
            source_categories=[signal.source_category],
            collection_methods=[signal.collection_method],
            matched_keywords=enrichment.get("matched_keywords", []),
            matched_products=enrichment.get("matched_products", []),
            risk_level=saint["risk_level"],
            score_breakdown=breakdown,
            score_reason=saint["reason"],
        )

    def _source_type(self, source_id: str, category: SourceCategory) -> str:
        source = SOURCE_REGISTRY.get(source_id)
        if source and source.category == SourceCategory.VENDOR_ADVISORY:
            return "Vendor Advisory"
        if source_id == "cisa_kev":
            return "Active Exploitation"
        if source_id in ("github_poc", "exploit_db", "metasploit", "packetstorm"):
            return "Exploit"
        if category == SourceCategory.RESEARCHER_SOCIAL:
            return "Researcher Social"
        if category == SourceCategory.RESEARCHER_BLOG:
            return "Researcher Blog"
        if category == SourceCategory.CONFERENCE:
            return "Conference"
        return category.value.replace("_", " ").title()

    def _generate_id(self, signal: RawSignal) -> str:
        key = f"{signal.source_id}:{signal.title}:{signal.url or ''}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]
