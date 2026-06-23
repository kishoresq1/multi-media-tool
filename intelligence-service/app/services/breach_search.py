import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.company_breach_fetcher import CompanyBreachFetcher
from app.config.company_breach_keyword_matcher import is_within_lookback, should_store_breach
from app.config.company_breach_sources import (
    COMPANY_BREACH_SOURCE_IDS,
    TIER_1_COMPANY_BREACH_SOURCE_IDS,
)
from app.config.sources import SOURCE_REGISTRY
from app.db.breach_repository import BreachRepository
from app.db.repository import content_hash
from app.models.schemas import (
    BreachIntelResponse,
    BreachSearchRequest,
    BreachSearchResponse,
)
from app.services.breach_scorer import BreachScorer
from app.services.score_fields import normalize_min_score, parse_score_breakdown, saint_fields

logger = logging.getLogger(__name__)


class BreachSearchService:
    """
    Fetch company breach / ransomware news from Tier 1 outlets via RSS/scraper.
    Stores last 30 days in `company_breach_intel`.
    """

    def __init__(self) -> None:
        self.fetcher = CompanyBreachFetcher()
        self.scorer = BreachScorer()

    async def search_and_store(
        self,
        session: AsyncSession,
        request: BreachSearchRequest,
    ) -> BreachSearchResponse:
        started_at = datetime.now(timezone.utc)
        search_id = str(uuid.uuid4())
        repo = BreachRepository(session)

        source_ids = request.source_ids or COMPANY_BREACH_SOURCE_IDS
        sources = [
            SOURCE_REGISTRY[sid]
            for sid in source_ids
            if sid in SOURCE_REGISTRY and SOURCE_REGISTRY[sid].enabled
        ]
        sources.sort(
            key=lambda s: (
                0 if s.id in TIER_1_COMPANY_BREACH_SOURCE_IDS else 1,
                -s.trust_weight,
            )
        )

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
                    "tier": 1 if source.id in TIER_1_COMPANY_BREACH_SOURCE_IDS else 2,
                    "error": str(result),
                }
                continue

            matched = [
                s for s in result.signals
                if self._matches_breach(s, request.lookback_days)
            ]
            source_stats[source.id] = {
                "name": source.name,
                "found": len(matched),
                "saved": 0,
                "method": (result.method_used or source.primary_method).value,
                "tier": 1 if source.id in TIER_1_COMPANY_BREACH_SOURCE_IDS else 2,
                "error": result.error,
            }
            all_signals.extend(matched)

        saved: list[BreachIntelResponse] = []
        min_score = normalize_min_score(request.min_confidence, default=30.0)

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
            tier = 1 if signal.source_id in TIER_1_COMPANY_BREACH_SOURCE_IDS else 2
            _, _, breach_kws = should_store_breach(
                f"{signal.title} {signal.content}",
                signal.source_id,
            )

            data = {
                "id": str(uuid.uuid4()),
                "source_id": signal.source_id,
                "source_name": signal.source_name,
                "source_tier": tier,
                "collection_method": signal.collection_method.value,
                "title": signal.title,
                "content": signal.content[:3000],
                "url": signal.url,
                "author": signal.author,
                "published_at": signal.published_at,
                "affected_company": scores.get("affected_company"),
                "breach_type": scores.get("breach_type"),
                "matched_breach_keywords": json.dumps(breach_kws),
                "matched_vendors": json.dumps(scores["matched_vendors"]),
                "matched_vuln_keywords": json.dumps(scores["matched_vuln_keywords"]),
                "matched_threat_keywords": json.dumps(scores["matched_threat_keywords"]),
                "cves": json.dumps(scores["cves"]),
                "has_poc": scores["has_poc"],
                "active_exploitation": scores["active_exploitation"],
                "is_ransomware": scores.get("is_ransomware", False),
                **saint_fields(scores),
                "content_hash": ch,
            }

            row = await repo.upsert(data)
            if row:
                source_stats[signal.source_id]["saved"] = (
                    source_stats.get(signal.source_id, {}).get("saved", 0) + 1
                )
                saved.append(breach_to_response(row))

        def _sort_key(item: BreachIntelResponse) -> tuple:
            pub = item.published_at
            if pub and pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            pub_ts = (pub or datetime.min.replace(tzinfo=timezone.utc)).timestamp()
            return (item.source_tier, -pub_ts, item.confidence_score)

        saved.sort(key=_sort_key)

        completed_at = datetime.now(timezone.utc)
        total_in_db = await repo.count(
            min_score=min_score if not request.include_low_confidence else 0.0
        )

        return BreachSearchResponse(
            search_id=search_id,
            sources_searched=[s.id for s in sources],
            source_stats=source_stats,
            items_found=len(all_signals),
            items_saved=len(saved),
            total_in_database=total_in_db,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=round((completed_at - started_at).total_seconds(), 2),
            items=saved[: request.result_limit],
        )

    def _matches_breach(self, signal, lookback_days: int) -> bool:
        combined = f"{signal.title} {signal.content}"
        store_ok, _, _ = should_store_breach(combined, signal.source_id)
        if not store_ok:
            return False
        return is_within_lookback(signal.published_at, lookback_days)


def breach_to_response(row) -> BreachIntelResponse:
    return BreachIntelResponse(
        id=row.id,
        source_id=row.source_id,
        source_name=row.source_name,
        source_tier=row.source_tier,
        collection_method=row.collection_method,
        title=row.title,
        content=row.content,
        url=row.url,
        author=row.author,
        published_at=row.published_at,
        affected_company=row.affected_company,
        breach_type=row.breach_type,
        matched_breach_keywords=json.loads(row.matched_breach_keywords),
        matched_vendors=json.loads(row.matched_vendors),
        matched_vuln_keywords=json.loads(row.matched_vuln_keywords),
        matched_threat_keywords=json.loads(row.matched_threat_keywords),
        cves=json.loads(row.cves),
        has_poc=row.has_poc,
        active_exploitation=row.active_exploitation,
        is_ransomware=row.is_ransomware,
        confidence_score=row.confidence_score,
        risk_level=getattr(row, "risk_level", "LOW") or "LOW",
        score_breakdown=parse_score_breakdown(getattr(row, "score_breakdown", None)),
        score_reason=getattr(row, "score_reason", "") or "",
        source_trust_score=row.source_trust_score,
        keyword_match_score=row.keyword_match_score,
        recency_score=row.recency_score,
        created_at=row.created_at,
    )
