from datetime import datetime

from app.services.threat_scorer import ThreatScorer


class SocialPostScorer:
    """SAINT threat score for social/researcher posts (0-100)."""

    def __init__(self) -> None:
        self._scorer = ThreatScorer()

    def score(
        self,
        title: str,
        content: str,
        platform: str,
        published_at: datetime | None,
    ) -> dict:
        return self._scorer.score(
            title=title,
            content=content,
            source_id=platform,
            source_name=platform.replace("_", " ").title(),
            published_at=published_at,
            platform=platform,
        )
