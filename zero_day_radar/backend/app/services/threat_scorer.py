"""Shared SAINT threat scorer used by all security intel pipelines."""

from datetime import datetime, timezone

from app.config.keyword_matcher import get_matched_for_storage
from app.config.sources import SOURCE_REGISTRY, SourceCategory
from app.processors.extractor import SignalExtractor
from app.processors.threat_scoring_engine import ThreatScoringEngine


class ThreatScorer:
    """
    Wraps ThreatScoringEngine with signal extraction for pipeline scorers.
    Returns 0-100 confidence_score with risk_level, score_breakdown, reason.
    """

    def __init__(self) -> None:
        self.extractor = SignalExtractor()
        self.engine = ThreatScoringEngine()

    def score(
        self,
        title: str,
        content: str,
        source_id: str,
        source_name: str,
        published_at: datetime | None = None,
        metadata: dict | None = None,
        platform: str | None = None,
    ) -> dict:
        combined = f"{title} {content}"
        matched = get_matched_for_storage(combined)
        meta = metadata or {}

        cves = self.extractor.extract_cves(combined)
        if meta.get("cve_id") and meta["cve_id"] not in cves:
            cves = [meta["cve_id"]] + cves

        has_poc = (
            self.extractor.has_poc(combined, meta)
            or source_id in ("github_poc", "exploit_db", "metasploit", "packetstorm")
            or bool(meta.get("is_poc_repo") or meta.get("has_exploit"))
        )
        actively_exploited = (
            self.extractor.has_active_exploitation(combined, meta)
            or bool(meta.get("cisa_kev"))
            or source_id == "cisa_kev"
        )

        resolve_id = platform or source_id
        source_type = self._source_type(source_id, platform)

        saint = self.engine.score_signal(
            resolve_id,
            source_name,
            source_type,
            {
                "vendor_name": (matched["matched_vendors"] or [""])[0] if matched["matched_vendors"] else "",
                "product_name": "",
                "cve_present": bool(cves),
                "poc_available": has_poc,
                "actively_exploited": actively_exploited,
                "signal_count": 1,
            },
        )

        return {
            **matched,
            "cves": cves,
            "has_poc": has_poc,
            "active_exploitation": actively_exploited,
            "in_cisa_kev": bool(meta.get("cisa_kev")) or source_id == "cisa_kev",
            "confidence_score": float(saint["confidence_score"]),
            "risk_level": saint["risk_level"],
            "score_breakdown": saint["score_breakdown"],
            "score_reason": saint["reason"],
            "source_trust_score": float(saint["score_breakdown"]["source_score"]),
            "keyword_match_score": float(len(matched.get("matched_vuln_keywords", [])) * 5),
            "recency_score": self._recency_factor(published_at),
            "threat_score": float(saint["score_breakdown"]["bonus_score"]),
        }

    def _source_type(self, source_id: str, platform: str | None) -> str:
        if platform:
            return "Researcher Social"
        source = SOURCE_REGISTRY.get(source_id)
        if not source:
            if source_id == "cisa_kev":
                return "Active Exploitation"
            return ""
        cat = source.category
        if cat == SourceCategory.RESEARCHER_SOCIAL:
            return "Researcher Social"
        if cat == SourceCategory.RESEARCHER_BLOG:
            return "Researcher Blog"
        if cat == SourceCategory.VENDOR_ADVISORY:
            return "Vendor Advisory"
        if cat == SourceCategory.VULNERABILITY:
            if source_id == "cisa_kev":
                return "Active Exploitation"
            if source_id in ("github_poc", "exploit_db", "metasploit", "packetstorm"):
                return "Exploit"
            return "Official"
        if cat == SourceCategory.CONFERENCE:
            return "Conference"
        return cat.value.replace("_", " ").title()

    def _recency_factor(self, published_at: datetime | None) -> float:
        if not published_at:
            return 50.0
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - published_at).days
        if age_days <= 1:
            return 100.0
        if age_days <= 7:
            return 90.0
        if age_days <= 30:
            return 75.0
        if age_days <= 90:
            return 50.0
        return 25.0
