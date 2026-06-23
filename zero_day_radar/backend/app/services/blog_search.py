import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.research_blog import ResearchBlogFetcher
from app.config.keyword_matcher import is_within_lookback, should_store
from app.config.research_blogs import RESEARCH_BLOG_SOURCE_IDS
from app.services.score_fields import normalize_min_score, parse_score_breakdown, saint_fields
from app.config.sources import SOURCE_REGISTRY
from app.db.blog_repository import BlogRepository
from app.db.repository import content_hash
from app.models.schemas import (
    BlogIntelResponse,
    BlogSearchRequest,
    BlogSearchResponse,
)
from app.services.blog_scorer import BlogScorer

logger = logging.getLogger(__name__)


class BlogSearchService:
    """
    Fetch latest vulnerability research from high-trust researcher blogs
    via RSS / HTML scraper. Filter by SEARCH_KEYWORDS first, fallback keywords second.
    """

    def __init__(self) -> None:
        self.fetcher = ResearchBlogFetcher()
        self.scorer = BlogScorer()

    async def search_and_store(
        self,
        session: AsyncSession,
        request: BlogSearchRequest,
    ) -> BlogSearchResponse:
        started_at = datetime.now(timezone.utc)
        search_id = str(uuid.uuid4())
        repo = BlogRepository(session)

        source_ids = request.source_ids or RESEARCH_BLOG_SOURCE_IDS
        sources = [
            SOURCE_REGISTRY[sid]
            for sid in source_ids
            if sid in SOURCE_REGISTRY and SOURCE_REGISTRY[sid].enabled
        ]

        source_stats: dict[str, dict] = {}
        all_signals = []

        tasks = [
            self.fetcher.fetch(source, ["*"], request.lookback_days)
            for source in sources
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for source, result in zip(sources, results):
            if isinstance(result, Exception):
                source_stats[source.id] = {
                    "name": source.name,
                    "found": 0,
                    "saved": 0,
                    "method": source.primary_method.value,
                    "error": str(result),
                }
                continue

            matched = [
                s for s in result.signals
                if self._matches_blog_post(s, request.vendors, request.lookback_days)
            ]
            source_stats[source.id] = {
                "name": source.name,
                "found": len(matched),
                "saved": 0,
                "method": (result.method_used or source.primary_method).value,
                "error": result.error,
            }
            all_signals.extend(matched)

        saved: list[BlogIntelResponse] = []
        min_score = normalize_min_score(request.min_confidence, default=35.0)

        for signal in all_signals:
            if not is_within_lookback(signal.published_at, request.lookback_days):
                continue

            scores = self.scorer.score(
                signal.title,
                signal.content,
                signal.source_id,
                signal.published_at,
            )

            if scores["confidence_score"] < min_score and not request.include_low_confidence:
                continue

            ch = content_hash(signal.title, signal.url)
            data = {
                "id": str(uuid.uuid4()),
                "source_id": signal.source_id,
                "source_name": signal.source_name,
                "collection_method": signal.collection_method.value,
                "title": signal.title,
                "content": signal.content[:3000],
                "url": signal.url,
                "author": signal.author,
                "published_at": signal.published_at,
                "matched_vendors": json.dumps(scores["matched_vendors"]),
                "matched_vuln_keywords": json.dumps(scores["matched_vuln_keywords"]),
                "matched_threat_keywords": json.dumps(scores["matched_threat_keywords"]),
                "cves": json.dumps(scores["cves"]),
                "has_poc": scores["has_poc"],
                "active_exploitation": scores["active_exploitation"],
                **saint_fields(scores),
                "content_hash": ch,
            }

            row = await repo.upsert(data)
            if row:
                source_stats[signal.source_id]["saved"] = (
                    source_stats.get(signal.source_id, {}).get("saved", 0) + 1
                )
                saved.append(blog_to_response(row))

        def _sort_key(p: BlogIntelResponse) -> tuple:
            pub = p.published_at
            if pub and pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            return (pub or datetime.min.replace(tzinfo=timezone.utc), p.confidence_score)

        saved.sort(key=_sort_key, reverse=True)

        completed_at = datetime.now(timezone.utc)
        total_in_db = await repo.count(
            min_score=min_score if not request.include_low_confidence else 0.0
        )

        return BlogSearchResponse(
            search_id=search_id,
            sources_searched=[s.id for s in sources],
            source_stats=source_stats,
            posts_found=len(all_signals),
            posts_saved=len(saved),
            total_in_database=total_in_db,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=round((completed_at - started_at).total_seconds(), 2),
            posts=saved[: request.result_limit],
        )

    def _matches_blog_post(
        self,
        signal,
        requested_vendors: list[str] | None,
        lookback_days: int,
    ) -> bool:
        combined = f"{signal.title} {signal.content}"
        store_ok, _, _ = should_store(combined, requested_vendors, primary_only=True)
        if not store_ok:
            return False
        return is_within_lookback(signal.published_at, lookback_days)


def blog_to_response(row) -> BlogIntelResponse:
    return BlogIntelResponse(
        id=row.id,
        source_id=row.source_id,
        source_name=row.source_name,
        collection_method=row.collection_method,
        title=row.title,
        content=row.content,
        url=row.url,
        author=row.author,
        published_at=row.published_at,
        matched_vendors=json.loads(row.matched_vendors),
        matched_vuln_keywords=json.loads(row.matched_vuln_keywords),
        matched_threat_keywords=json.loads(row.matched_threat_keywords),
        cves=json.loads(row.cves),
        has_poc=row.has_poc,
        active_exploitation=row.active_exploitation,
        confidence_score=row.confidence_score,
        risk_level=getattr(row, "risk_level", "LOW") or "LOW",
        score_breakdown=parse_score_breakdown(getattr(row, "score_breakdown", None)),
        score_reason=getattr(row, "score_reason", "") or "",
        source_trust_score=row.source_trust_score,
        keyword_match_score=row.keyword_match_score,
        recency_score=row.recency_score,
        created_at=row.created_at,
    )
