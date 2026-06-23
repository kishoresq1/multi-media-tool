import json
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import IntelPost
from app.db.repository import content_hash


class IntelPostRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_post(self, data: dict) -> IntelPost | None:
        ch = data["content_hash"]
        existing = await self.session.execute(
            select(IntelPost).where(IntelPost.content_hash == ch)
        )
        post = existing.scalar_one_or_none()

        if post:
            if data["confidence_score"] > post.confidence_score:
                post.confidence_score = data["confidence_score"]
                post.risk_level = data.get("risk_level", post.risk_level)
                post.score_breakdown = data.get("score_breakdown", post.score_breakdown)
                post.score_reason = data.get("score_reason", post.score_reason)
                post.keyword_match_score = data["keyword_match_score"]
                post.recency_score = data["recency_score"]
                post.threat_score = data["threat_score"]
                post.matched_vendors = data["matched_vendors"]
                post.matched_vuln_keywords = data["matched_vuln_keywords"]
                post.matched_threat_keywords = data["matched_threat_keywords"]
                post.cves = data["cves"]
                post.has_poc = data["has_poc"]
                post.active_exploitation = data["active_exploitation"]
                post.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(post)
            return post

        post = IntelPost(**data)
        self.session.add(post)
        try:
            await self.session.commit()
            await self.session.refresh(post)
            return post
        except Exception:
            await self.session.rollback()
            return None

    async def list_posts(
        self,
        platform: str | None = None,
        min_score: float = 0.0,
        limit: int = 50,
        offset: int = 0,
    ) -> list[IntelPost]:
        query = (
            select(IntelPost)
            .where(IntelPost.confidence_score >= min_score)
            .order_by(
                IntelPost.published_at.desc().nullslast(),
                IntelPost.confidence_score.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        if platform:
            query = query.where(IntelPost.platform == platform)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_posts(
        self,
        platform: str | None = None,
        min_score: float = 0.0,
    ) -> int:
        query = (
            select(func.count())
            .select_from(IntelPost)
            .where(IntelPost.confidence_score >= min_score)
        )
        if platform:
            query = query.where(IntelPost.platform == platform)
        return (await self.session.execute(query)).scalar() or 0

    async def get_post(self, post_id: str) -> IntelPost | None:
        return await self.session.get(IntelPost, post_id)
