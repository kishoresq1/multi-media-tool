#!/usr/bin/env python3
"""Fetch Tier 1 company breach news (last 30 days) into company_breach_intel."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select

from app.db.database import init_db
from app.db.models import CompanyBreachIntel
from app.models.schemas import BreachSearchRequest
from app.services.breach_search import BreachSearchService
from app.worker.async_runner import with_session


async def main() -> None:
    await init_db()

    async def _run(session):
        before = await session.scalar(select(func.count()).select_from(CompanyBreachIntel))
        print(f"Records before: {before}")
        request = BreachSearchRequest(
            lookback_days=30,
            min_confidence=20,
            include_low_confidence=True,
            result_limit=300,
        )
        result = await BreachSearchService().search_and_store(session, request)
        after = await session.scalar(select(func.count()).select_from(CompanyBreachIntel))
        print(f"Found: {result.items_found} | Saved this run: {result.items_saved} | Total in DB: {after}")
        for sid, stats in result.source_stats.items():
            print(f"  {sid}: found={stats.get('found')} saved={stats.get('saved')} err={stats.get('error')}")

    await with_session(_run)


if __name__ == "__main__":
    asyncio.run(main())
