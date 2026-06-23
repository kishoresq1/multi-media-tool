from datetime import datetime

from app.config.sources import SOURCE_REGISTRY
from app.services.threat_scorer import ThreatScorer


class AdvisoryScorer:
    """SAINT threat score for vendor advisories (0-100)."""

    def __init__(self) -> None:
        self._scorer = ThreatScorer()

    def score(
        self,
        title: str,
        content: str,
        source_id: str,
        published_at: datetime | None,
        requested_vendors: list[str] | None = None,
    ) -> dict:
        source = SOURCE_REGISTRY.get(source_id)
        source_name = source.name if source else source_id
        result = self._scorer.score(
            title=title,
            content=content,
            source_id=source_id,
            source_name=source_name,
            published_at=published_at,
        )
        result["severity"] = self._detect_severity(f"{title} {content}")
        return result

    def _detect_severity(self, text: str) -> str | None:
        lower = text.lower()
        if "critical" in lower:
            return "critical"
        if "high" in lower:
            return "high"
        if "medium" in lower or "moderate" in lower:
            return "medium"
        if "low" in lower:
            return "low"
        return None
