from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CompanyBreachIntel


class BreachRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, data: dict) -> CompanyBreachIntel | None:
        ch = data["content_hash"]
        existing = await self.session.execute(
            select(CompanyBreachIntel).where(CompanyBreachIntel.content_hash == ch)
        )
        row = existing.scalar_one_or_none()

        if row:
            if data["confidence_score"] > row.confidence_score:
                for field in (
                    "confidence_score",
                    "risk_level",
                    "score_breakdown",
                    "score_reason",
                    "keyword_match_score",
                    "recency_score",
                    "source_trust_score",
                    "matched_breach_keywords",
                    "matched_vendors",
                    "matched_vuln_keywords",
                    "matched_threat_keywords",
                    "cves",
                    "affected_company",
                    "breach_type",
                    "is_ransomware",
                ):
                    if field in data:
                        setattr(row, field, data[field])
                row.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(row)
            return row

        row = CompanyBreachIntel(**data)
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
        breach_type: str | None = None,
        min_score: float = 0.0,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CompanyBreachIntel]:
        query = (
            select(CompanyBreachIntel)
            .where(CompanyBreachIntel.confidence_score >= min_score)
            .order_by(
                CompanyBreachIntel.source_tier.asc(),
                CompanyBreachIntel.published_at.desc().nullslast(),
                CompanyBreachIntel.confidence_score.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        if source_id:
            query = query.where(CompanyBreachIntel.source_id == source_id)
        if breach_type:
            query = query.where(CompanyBreachIntel.breach_type == breach_type)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        source_id: str | None = None,
        breach_type: str | None = None,
        min_score: float = 0.0,
    ) -> int:
        query = (
            select(func.count())
            .select_from(CompanyBreachIntel)
            .where(CompanyBreachIntel.confidence_score >= min_score)
        )
        if source_id:
            query = query.where(CompanyBreachIntel.source_id == source_id)
        if breach_type:
            query = query.where(CompanyBreachIntel.breach_type == breach_type)
        return (await self.session.execute(query)).scalar() or 0

    async def get(self, item_id: str) -> CompanyBreachIntel | None:
        return await self.session.get(CompanyBreachIntel, item_id)
