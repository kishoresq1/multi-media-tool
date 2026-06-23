import json
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UnifiedIntel


class UnifiedIntelRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, data: dict) -> UnifiedIntel | None:
        key = data["cluster_key"]
        existing = await self.session.execute(
            select(UnifiedIntel).where(UnifiedIntel.cluster_key == key)
        )
        row = existing.scalar_one_or_none()

        if row:
            if data["confidence_score"] >= row.confidence_score:
                for field, value in data.items():
                    if field != "id":
                        setattr(row, field, value)
                row.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(row)
            return row

        row = UnifiedIntel(**data)
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
        vendor: str | None = None,
        product: str | None = None,
        min_score: float = 0.0,
        classification: str | None = None,
        unclassified_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[UnifiedIntel]:
        query = (
            select(UnifiedIntel)
            .where(UnifiedIntel.confidence_score >= min_score)
            .order_by(
                UnifiedIntel.latest_date.desc().nullslast(),
                UnifiedIntel.confidence_score.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        if vendor:
            query = query.where(
                or_(
                    UnifiedIntel.vendor_name.contains(vendor),
                    UnifiedIntel.company_name.contains(vendor),
                )
            )
        if product:
            query = query.where(UnifiedIntel.product_name.contains(product))
        if unclassified_only:
            query = query.where(UnifiedIntel.classification.is_(None))
        elif classification is not None:
            query = query.where(UnifiedIntel.classification == classification)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        vendor: str | None = None,
        min_score: float = 0.0,
        classification: str | None = None,
        unclassified_only: bool = False,
    ) -> int:
        query = (
            select(func.count())
            .select_from(UnifiedIntel)
            .where(UnifiedIntel.confidence_score >= min_score)
        )
        if vendor:
            query = query.where(
                or_(
                    UnifiedIntel.vendor_name.contains(vendor),
                    UnifiedIntel.company_name.contains(vendor),
                )
            )
        if unclassified_only:
            query = query.where(UnifiedIntel.classification.is_(None))
        elif classification is not None:
            query = query.where(UnifiedIntel.classification == classification)
        return (await self.session.execute(query)).scalar() or 0

    async def get(self, item_id: str) -> UnifiedIntel | None:
        return await self.session.get(UnifiedIntel, item_id)

    async def clear_all(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(UnifiedIntel))
        count = result.scalar() or 0
        from sqlalchemy import delete

        await self.session.execute(delete(UnifiedIntel))
        await self.session.commit()
        return count
