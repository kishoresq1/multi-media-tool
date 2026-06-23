"""
Fetch compliance intel (last 30 days) into compliance_intel.

Usage (from backend/):
    python -m scripts.refresh_compliance
"""

import asyncio
import logging
import sys

from sqlalchemy import func, select

from app.db.database import init_db
from app.db.models import ComplianceIntel
from app.models.schemas import ComplianceSearchRequest
from app.services.compliance_search import ComplianceSearchService

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

LOOKBACK_DAYS = 30


async def _session():
    await init_db()
    from app.db.database import _session_factory

    return _session_factory()


async def main() -> None:
    session = await _session()
    try:
        before = await session.scalar(select(func.count()).select_from(ComplianceIntel))
        logger.info("Existing compliance_intel rows: %d", before or 0)

        req = ComplianceSearchRequest(
            lookback_days=LOOKBACK_DAYS,
            min_confidence=35,
            include_low_confidence=True,
            result_limit=200,
        )
        result = await ComplianceSearchService().search_and_store(session, req)
        logger.info(
            "Compliance search done: found=%d saved=%d (%.1fs)",
            result.items_found,
            result.items_saved,
            result.duration_seconds,
        )
        print(f"\nDone: {result.items_saved} compliance items saved (last {LOOKBACK_DAYS} days)")
    finally:
        await session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
