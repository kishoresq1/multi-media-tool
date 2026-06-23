import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.compliance_fetcher import ComplianceFetcher
from app.config.compliance_keyword_matcher import is_within_lookback, should_store_compliance
from app.config.compliance_sources import COMPLIANCE_SOURCE_IDS, SOURCE_ORG_MAP
from app.config.sources import SOURCE_REGISTRY
from app.db.compliance_repository import ComplianceRepository
from app.db.repository import content_hash
from app.models.schemas import (
    ComplianceIntelResponse,
    ComplianceSearchRequest,
    ComplianceSearchResponse,
)
from app.services.compliance_scorer import ComplianceScorer

logger = logging.getLogger(__name__)


class ComplianceSearchService:
    """
    Fetch compliance intel from regulators, standards bodies, research, vendors,
    privacy authorities, and AI governance sources.

    Extracts frameworks, versions, effective dates, deadlines, and impacted controls.
    Stores in `compliance_intel` SQLite table with Tier 1 sources prioritized.
    """

    def __init__(self) -> None:
        self.fetcher = ComplianceFetcher()
        self.scorer = ComplianceScorer()

    async def search_and_store(
        self,
        session: AsyncSession,
        request: ComplianceSearchRequest,
    ) -> ComplianceSearchResponse:
        started_at = datetime.now(timezone.utc)
        search_id = str(uuid.uuid4())
        repo = ComplianceRepository(session)

        source_ids = request.source_ids or COMPLIANCE_SOURCE_IDS
        sources = [
            SOURCE_REGISTRY[sid]
            for sid in source_ids
            if sid in SOURCE_REGISTRY and SOURCE_REGISTRY[sid].enabled
        ]
        sources.sort(key=lambda s: (0 if s.id in COMPLIANCE_SOURCE_IDS[:8] else 1, -s.trust_weight))

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
                if self._matches_compliance(s, request.frameworks, request.lookback_days)
            ]
            source_stats[source.id] = {
                "name": source.name,
                "found": len(matched),
                "saved": 0,
                "method": (result.method_used or source.primary_method).value,
                "tier": SOURCE_ORG_MAP.get(source.id, ""),
                "error": result.error,
            }
            all_signals.extend(matched)

        saved: list[ComplianceIntelResponse] = []
        min_score = request.min_confidence if request.min_confidence is not None else 50.0

        for signal in all_signals:
            if not is_within_lookback(signal.published_at, request.lookback_days):
                continue

            scores = self.scorer.score(
                signal.title,
                signal.content,
                signal.source_id,
                signal.source_name,
                signal.published_at,
                request.frameworks,
            )

            if scores["confidence_score"] < min_score and not request.include_low_confidence:
                continue

            org = SOURCE_ORG_MAP.get(signal.source_id)
            ch = content_hash(signal.title, signal.url)
            subtype = self._subtype_for_source(signal.source_id)

            data = {
                "id": str(uuid.uuid4()),
                "source_id": signal.source_id,
                "source_name": signal.source_name,
                "organization": org,
                "source_tier": scores["source_tier"],
                "source_subtype": subtype,
                "collection_method": signal.collection_method.value,
                "title": signal.title,
                "content": signal.content[:3000],
                "url": signal.url,
                "author": signal.author,
                "published_at": signal.published_at,
                "matched_compliance_keywords": json.dumps(scores["matched_compliance_keywords"]),
                "matched_privacy_keywords": json.dumps(scores["matched_privacy_keywords"]),
                "matched_audit_keywords": json.dumps(scores["matched_audit_keywords"]),
                "matched_ai_keywords": json.dumps(scores["matched_ai_keywords"]),
                "matched_framework_keywords": json.dumps(scores["matched_framework_keywords"]),
                "frameworks": json.dumps(scores["frameworks"]),
                "framework_versions": json.dumps(scores["framework_versions"]),
                "effective_dates": json.dumps(scores["effective_dates"]),
                "compliance_deadlines": json.dumps(scores["compliance_deadlines"]),
                "impacted_controls": json.dumps(scores["impacted_controls"]),
                "is_new_requirement": scores["is_new_requirement"],
                "is_framework_update": scores["is_framework_update"],
                "confidence_score": scores["confidence_score"],
                "risk_level": scores["risk_level"],
                "score_breakdown": json.dumps(scores["score_breakdown"]),
                "score_reason": scores["score_reason"],
                "source_trust_score": scores["source_trust_score"],
                "keyword_match_score": scores["keyword_match_score"],
                "recency_score": scores["recency_score"],
                "content_hash": ch,
            }

            row = await repo.upsert(data)
            if row:
                source_stats[signal.source_id]["saved"] = (
                    source_stats.get(signal.source_id, {}).get("saved", 0) + 1
                )
                saved.append(compliance_to_response(row))

        saved.sort(
            key=lambda item: (
                item.source_tier,
                -(item.published_at.timestamp() if item.published_at else 0),
                item.confidence_score,
            ),
        )

        completed_at = datetime.now(timezone.utc)
        total_in_db = await repo.count(min_score=min_score if not request.include_low_confidence else 0.0)

        return ComplianceSearchResponse(
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

    def _matches_compliance(
        self,
        signal,
        requested_frameworks: list[str] | None,
        lookback_days: int,
    ) -> bool:
        combined = f"{signal.title} {signal.content}"
        store_ok, _, _ = should_store_compliance(
            combined, requested_frameworks, primary_only=False
        )
        if not store_ok:
            return False
        return is_within_lookback(signal.published_at, lookback_days)

    def _subtype_for_source(self, source_id: str) -> str:
        if source_id in {"edpb", "ico_uk", "iapp"}:
            return "privacy"
        if source_id in {"eu_ai_act", "nist_ai_rmf", "iso_42001"}:
            return "ai_governance"
        if source_id in {"gartner_compliance", "forrester_compliance", "sans_compliance", "iapp"}:
            return "research"
        if source_id in {
            "microsoft_compliance", "microsoft_compliance_blog", "microsoft_service_trust",
            "aws_compliance", "aws_compliance_blog", "gcp_compliance", "oracle_compliance",
            "sap_trust_center", "salesforce_compliance", "servicenow_compliance",
        }:
            return "vendor"
        if source_id in {"iso_compliance", "pci_ssc", "csa", "cis_controls", "owasp_compliance", "isaca"}:
            return "standards"
        return "regulatory"


def compliance_to_response(row) -> ComplianceIntelResponse:
    return ComplianceIntelResponse(
        id=row.id,
        source_id=row.source_id,
        source_name=row.source_name,
        organization=row.organization,
        source_tier=row.source_tier,
        source_subtype=row.source_subtype,
        collection_method=row.collection_method,
        title=row.title,
        content=row.content,
        url=row.url,
        author=row.author,
        published_at=row.published_at,
        matched_compliance_keywords=json.loads(row.matched_compliance_keywords),
        matched_privacy_keywords=json.loads(row.matched_privacy_keywords),
        matched_audit_keywords=json.loads(row.matched_audit_keywords),
        matched_ai_keywords=json.loads(row.matched_ai_keywords),
        matched_framework_keywords=json.loads(row.matched_framework_keywords),
        frameworks=json.loads(row.frameworks),
        framework_versions=json.loads(row.framework_versions),
        effective_dates=json.loads(row.effective_dates),
        compliance_deadlines=json.loads(row.compliance_deadlines),
        impacted_controls=json.loads(row.impacted_controls),
        is_new_requirement=row.is_new_requirement,
        is_framework_update=row.is_framework_update,
        confidence_score=row.confidence_score,
        risk_level=getattr(row, "risk_level", "LOW") or "LOW",
        score_breakdown=json.loads(getattr(row, "score_breakdown", None) or "{}"),
        score_reason=getattr(row, "score_reason", "") or "",
        source_trust_score=row.source_trust_score,
        keyword_match_score=row.keyword_match_score,
        recency_score=row.recency_score,
        created_at=row.created_at,
    )
