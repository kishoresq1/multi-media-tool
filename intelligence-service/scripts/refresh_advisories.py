"""
Fetch vendor advisories (last 30 days, SEARCH_KEYWORDS only) into vendor_advisory_intel.

Usage (from backend/):
    python -m scripts.refresh_advisories
"""

import asyncio
import logging
import sys

from sqlalchemy import delete, func, select

from app.db.database import init_db
from app.db.models import VendorAdvisoryIntel
from app.models.schemas import AdvisorySearchRequest
from app.services.advisory_search import AdvisorySearchService

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
        before = await session.scalar(select(func.count()).select_from(VendorAdvisoryIntel))
        await session.execute(delete(VendorAdvisoryIntel))
        await session.commit()
        logger.info("Cleared vendor_advisory_intel (%d rows)", before or 0)

        req = AdvisorySearchRequest(
            lookback_days=LOOKBACK_DAYS,
            min_confidence=0.25,
            include_low_confidence=True,
            result_limit=200,
        )
        result = await AdvisorySearchService().search_and_store(session, req)
        logger.info(
            "Advisory search done: found=%d saved=%d (%.1fs)",
            result.advisories_found,
            result.advisories_saved,
            result.duration_seconds,
        )
        print(f"\nDone: {result.advisories_saved} advisories saved (last {LOOKBACK_DAYS} days)")
    finally:
        await session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
