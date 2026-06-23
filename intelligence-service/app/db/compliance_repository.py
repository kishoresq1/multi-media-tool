from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ComplianceIntel


class ComplianceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, data: dict) -> ComplianceIntel | None:
        ch = data["content_hash"]
        existing = await self.session.execute(
            select(ComplianceIntel).where(ComplianceIntel.content_hash == ch)
        )
        row = existing.scalar_one_or_none()

        if row:
            if data["confidence_score"] > row.confidence_score:
                row.confidence_score = data["confidence_score"]
                row.risk_level = data.get("risk_level", row.risk_level)
                row.score_breakdown = data.get("score_breakdown", row.score_breakdown)
                row.score_reason = data.get("score_reason", row.score_reason)
                row.keyword_match_score = data["keyword_match_score"]
                row.recency_score = data["recency_score"]
                row.source_trust_score = data["source_trust_score"]
                row.matched_compliance_keywords = data["matched_compliance_keywords"]
                row.matched_framework_keywords = data["matched_framework_keywords"]
                row.frameworks = data["frameworks"]
                row.framework_versions = data["framework_versions"]
                row.effective_dates = data["effective_dates"]
                row.compliance_deadlines = data["compliance_deadlines"]
                row.impacted_controls = data["impacted_controls"]
                row.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(row)
            return row

        row = ComplianceIntel(**data)
        self.session.add(row)
        try:
            await self.session.commit()
            await self.session.refresh(row)
            return row
        except Exception:
            await self.session.rollback()
            return None

    async def list_items(
        self,
        source_id: str | None = None,
        organization: str | None = None,
        framework: str | None = None,
        source_tier: int | None = None,
        min_score: float = 0.0,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ComplianceIntel]:
        query = (
            select(ComplianceIntel)
            .where(ComplianceIntel.confidence_score >= min_score)
            .order_by(
                ComplianceIntel.source_tier.asc(),
                ComplianceIntel.published_at.desc().nullslast(),
                ComplianceIntel.confidence_score.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        if source_id:
            query = query.where(ComplianceIntel.source_id == source_id)
        if organization:
            query = query.where(ComplianceIntel.organization == organization)
        if source_tier is not None:
            query = query.where(ComplianceIntel.source_tier == source_tier)
        if framework:
            query = query.where(ComplianceIntel.frameworks.contains(f'"{framework}"'))

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        source_id: str | None = None,
        organization: str | None = None,
        source_tier: int | None = None,
        min_score: float = 0.0,
    ) -> int:
        query = (
            select(func.count())
            .select_from(ComplianceIntel)
            .where(ComplianceIntel.confidence_score >= min_score)
        )
        if source_id:
            query = query.where(ComplianceIntel.source_id == source_id)
        if organization:
            query = query.where(ComplianceIntel.organization == organization)
        if source_tier is not None:
            query = query.where(ComplianceIntel.source_tier == source_tier)
        return (await self.session.execute(query)).scalar() or 0

    async def get(self, item_id: str) -> ComplianceIntel | None:
        return await self.session.get(ComplianceIntel, item_id)
