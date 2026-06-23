from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from app.config.sources import SourceConfig
from app.models.schemas import CollectionMethod, RawSignal, SourceCategory


@dataclass
class CollectorResult:
    signals: list[RawSignal] = field(default_factory=list)
    success: bool = True
    error: str | None = None
    method_used: CollectionMethod | None = None


class BaseCollector(ABC):
    def __init__(self, source: SourceConfig):
        self.source = source

    @abstractmethod
    async def collect(
        self,
        query_terms: list[str],
        lookback_days: int = 30,
    ) -> CollectorResult:
        pass

    def _make_signal(
        self,
        title: str,
        content: str = "",
        url: str | None = None,
        published_at: datetime | None = None,
        author: str | None = None,
        method: CollectionMethod | None = None,
        metadata: dict | None = None,
    ) -> RawSignal:
        return RawSignal(
            source_id=self.source.id,
            source_name=self.source.name,
            source_category=SourceCategory(self.source.category.value),
            collection_method=method or CollectionMethod(self.source.primary_method.value),
            title=title,
            url=url,
            content=content,
            published_at=published_at,
            author=author,
            raw_metadata=metadata or {},
        )

    def _matches_query(self, text: str, query_terms: list[str]) -> bool:
        if not query_terms or query_terms == ["*"]:
            return True
        text_lower = text.lower()
        return any(term.lower() in text_lower for term in query_terms)
