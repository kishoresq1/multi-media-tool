"""Load and group normalized records from all intel tables."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    CompanyBreachIntel,
    ComplianceIntel,
    IntelPost,
    ResearchBlogIntel,
    VendorAdvisoryIntel,
    VulnerabilityIntel,
)
from app.services.unified.normalizer import (
    NormalizedRecord,
    cluster_key_for,
    normalize_advisory,
    normalize_blog,
    normalize_breach,
    normalize_compliance,
    normalize_intel_post,
    normalize_vulnerability,
)


class UnifiedAggregator:
    async def load_all_records(self, session: AsyncSession) -> list[NormalizedRecord]:
        records: list[NormalizedRecord] = []

        for row in (await session.execute(select(IntelPost))).scalars():
            records.append(normalize_intel_post(row))
        for row in (await session.execute(select(VendorAdvisoryIntel))).scalars():
            records.append(normalize_advisory(row))
        for row in (await session.execute(select(ResearchBlogIntel))).scalars():
            records.append(normalize_blog(row))
        for row in (await session.execute(select(VulnerabilityIntel))).scalars():
            records.append(normalize_vulnerability(row))
        for row in (await session.execute(select(ComplianceIntel))).scalars():
            records.append(normalize_compliance(row))
        for row in (await session.execute(select(CompanyBreachIntel))).scalars():
            records.append(normalize_breach(row))

        return records

    def group_records(
        self,
        records: list[NormalizedRecord],
    ) -> dict[str, list[NormalizedRecord]]:
        groups: dict[str, list[NormalizedRecord]] = defaultdict(list)
        for rec in records:
            groups[cluster_key_for(rec)].append(rec)
        return dict(groups)

    @staticmethod
    def latest_date(records: list[NormalizedRecord]) -> datetime | None:
        dates = [r.published_at for r in records if r.published_at]
        return max(dates) if dates else None

    @staticmethod
    def pick_title(records: list[NormalizedRecord]) -> str:
        return max(records, key=lambda r: (r.confidence_score, r.published_at or datetime.min)).title
