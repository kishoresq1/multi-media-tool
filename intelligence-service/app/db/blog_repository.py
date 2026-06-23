from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ResearchBlogIntel


class BlogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, data: dict) -> ResearchBlogIntel | None:
        ch = data["content_hash"]
        existing = await self.session.execute(
            select(ResearchBlogIntel).where(ResearchBlogIntel.content_hash == ch)
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
                row.matched_vendors = data["matched_vendors"]
                row.matched_vuln_keywords = data["matched_vuln_keywords"]
                row.cves = data["cves"]
                row.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(row)
            return row

        row = ResearchBlogIntel(**data)
        self.session.add(row)
        try:
            await self.session.commit()
            await self.session.refresh(row)
            return row
        except Exception:
            await self.session.rollback()
            return None

    async def list_posts(
        self,
        source_id: str | None = None,
        min_score: float = 0.0,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ResearchBlogIntel]:
        query = (
            select(ResearchBlogIntel)
            .where(ResearchBlogIntel.confidence_score >= min_score)
            .order_by(
                ResearchBlogIntel.published_at.desc().nullslast(),
                ResearchBlogIntel.confidence_score.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        if source_id:
            query = query.where(ResearchBlogIntel.source_id == source_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, source_id: str | None = None, min_score: float = 0.0) -> int:
        query = (
            select(func.count())
            .select_from(ResearchBlogIntel)
            .where(ResearchBlogIntel.confidence_score >= min_score)
        )
        if source_id:
            query = query.where(ResearchBlogIntel.source_id == source_id)
        return (await self.session.execute(query)).scalar() or 0

    async def get(self, post_id: str) -> ResearchBlogIntel | None:
        return await self.session.get(ResearchBlogIntel, post_id)
