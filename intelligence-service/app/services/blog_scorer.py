from datetime import datetime

from app.config.sources import SOURCE_REGISTRY
from app.services.threat_scorer import ThreatScorer


class BlogScorer:
    """SAINT threat score for researcher blog posts (0-100)."""

    def __init__(self) -> None:
        self._scorer = ThreatScorer()

    def score(
        self,
        title: str,
        content: str,
        source_id: str,
        published_at: datetime | None,
    ) -> dict:
        source = SOURCE_REGISTRY.get(source_id)
        source_name = source.name if source else source_id
        return self._scorer.score(
            title=title,
            content=content,
            source_id=source_id,
            source_name=source_name,
            published_at=published_at,
        )
