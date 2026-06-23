import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.social_search import (
    HackerNewsSearchCollector,
    LinkedInSearchCollector,
    RedditSearchCollector,
    TwitterSearchCollector,
)
from app.config.keyword_matcher import is_within_lookback, should_store
from app.config.query_builder import build_search_queries
from app.services.score_fields import normalize_min_score, parse_score_breakdown, saint_fields
from app.db.intel_repository import IntelPostRepository
from app.db.repository import content_hash
from app.models.schemas import IntelPostResponse, SocialSearchRequest, SocialSearchResponse
from app.services.social_scorer import SocialPostScorer

logger = logging.getLogger(__name__)

COLLECTORS = {
    "twitter": TwitterSearchCollector(),
    "reddit": RedditSearchCollector(),
    "hackernews": HackerNewsSearchCollector(),
    "linkedin": LinkedInSearchCollector(),
}


class SocialSearchService:
    """
    Search X/Twitter, Reddit, LinkedIn, HackerNews using:
      PRIMARY: [VENDOR] + [SEARCH_KEYWORD]
      FALLBACK: vendor/vuln/threat keywords when primary finds nothing

    Store latest posts in single `intel_posts` SQLite table with scores.
    """

    def __init__(self) -> None:
        self.scorer = SocialPostScorer()

    async def search_and_store(
        self,
        session: AsyncSession,
        request: SocialSearchRequest,
    ) -> SocialSearchResponse:
        started_at = datetime.now(timezone.utc)
        search_id = str(uuid.uuid4())
        repo = IntelPostRepository(session)

        queries = build_search_queries(
            vendors=request.vendors,
            max_queries=request.max_queries,
        )
        # Twitter/Nitter skipped by default (public instances often 403)
        sources = request.sources or ["reddit", "hackernews", "linkedin"]
        lookback = request.lookback_days

        source_stats: dict[str, dict] = {}
        all_signals = []

        tasks = []
        active_sources = [s for s in sources if s in COLLECTORS]
        for source_id in active_sources:
            collector = COLLECTORS[source_id]
            tasks.append((
                source_id,
                collector.search(queries, lookback, vendors=request.vendors),
            ))

        results = await asyncio.gather(
            *[t[1] for t in tasks],
            return_exceptions=True,
        )

        for (source_id, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                logger.warning("Source %s failed: %s", source_id, result)
                source_stats[source_id] = {"found": 0, "saved": 0, "error": str(result)}
                continue
            source_stats[source_id] = {"found": len(result), "saved": 0, "error": None}
            all_signals.extend(result)

        saved_posts: list[IntelPostResponse] = []
        min_score = normalize_min_score(request.min_confidence, default=30.0)
        saved_by_platform: dict[str, int] = {}

        for signal in all_signals:
            platform = signal.raw_metadata.get("platform", signal.source_id)
            scores = self.scorer.score(signal.title, signal.content, platform, signal.published_at)

            text = f"{signal.title} {signal.content}"
            store_ok, _, _ = should_store(text, request.vendors, primary_only=True)
            if not store_ok:
                continue
            if not is_within_lookback(signal.published_at, lookback):
                continue

            if scores["confidence_score"] < min_score and not request.include_low_confidence:
                continue

            ch = content_hash(signal.title, signal.url)
            post_data = {
                "id": str(uuid.uuid4()),
                "platform": platform,
                "source_id": signal.source_id,
                "source_name": signal.source_name,
                "collection_method": signal.collection_method.value,
                "title": signal.title,
                "content": signal.content,
                "url": signal.url,
                "author": signal.author,
                "published_at": signal.published_at,
                "search_query": signal.raw_metadata.get("search_query"),
                "matched_vendors": json.dumps(scores["matched_vendors"]),
                "matched_vuln_keywords": json.dumps(scores["matched_vuln_keywords"]),
                "matched_threat_keywords": json.dumps(scores["matched_threat_keywords"]),
                "cves": json.dumps(scores["cves"]),
                "has_poc": scores["has_poc"],
                "active_exploitation": scores["active_exploitation"],
                "threat_score": scores["threat_score"],
                **saint_fields(scores),
                "content_hash": ch,
            }

            saved = await repo.upsert_post(post_data)
            if saved:
                saved_by_platform[platform] = saved_by_platform.get(platform, 0) + 1
                saved_posts.append(intel_post_to_response(saved))

        for platform, count in saved_by_platform.items():
            if platform in source_stats:
                source_stats[platform]["saved"] = count

        saved_posts.sort(
            key=lambda p: (p.published_at or datetime.min.replace(tzinfo=timezone.utc), p.confidence_score),
            reverse=True,
        )

        completed_at = datetime.now(timezone.utc)
        total_in_db = await repo.count_posts(min_score=min_score if not request.include_low_confidence else 0.0)

        return SocialSearchResponse(
            search_id=search_id,
            queries_used=len(queries),
            sources_searched=active_sources,
            source_stats=source_stats,
            posts_found=len(all_signals),
            posts_saved=len(saved_posts),
            total_in_database=total_in_db,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=round((completed_at - started_at).total_seconds(), 2),
            posts=saved_posts[: request.result_limit],
        )


def intel_post_to_response(post) -> IntelPostResponse:
    return IntelPostResponse(
        id=post.id,
        platform=post.platform,
        source_name=post.source_name,
        collection_method=post.collection_method,
        title=post.title,
        content=post.content,
        url=post.url,
        author=post.author,
        published_at=post.published_at,
        search_query=post.search_query,
        matched_vendors=json.loads(post.matched_vendors),
        matched_vuln_keywords=json.loads(post.matched_vuln_keywords),
        matched_threat_keywords=json.loads(post.matched_threat_keywords),
        cves=json.loads(post.cves),
        has_poc=post.has_poc,
        active_exploitation=post.active_exploitation,
        confidence_score=post.confidence_score,
        risk_level=getattr(post, "risk_level", "LOW") or "LOW",
        score_breakdown=parse_score_breakdown(getattr(post, "score_breakdown", None)),
        score_reason=getattr(post, "score_reason", "") or "",
        keyword_match_score=post.keyword_match_score,
        recency_score=post.recency_score,
        threat_score=post.threat_score,
        created_at=post.created_at,
    )
