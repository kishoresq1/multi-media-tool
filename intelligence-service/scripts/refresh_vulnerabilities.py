"""
Fetch vulnerability intel (last 30 days) into vulnerability_intel table.

Sources: CVE Program, GitHub, Exploit-DB, Metasploit, CISA KEV, NVD

Usage (from backend/):
    python -m scripts.refresh_vulnerabilities
"""

import asyncio
import logging
import sys

from sqlalchemy import delete, func, select

from app.db.database import init_db
from app.db.models import VulnerabilityIntel
from app.models.schemas import VulnerabilitySearchRequest
from app.services.vulnerability_search import VulnerabilitySearchService

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
        before = await session.scalar(select(func.count()).select_from(VulnerabilityIntel))
        await session.execute(delete(VulnerabilityIntel))
        await session.commit()
        logger.info("Cleared vulnerability_intel (%d rows)", before or 0)

        req = VulnerabilitySearchRequest(
            lookback_days=LOOKBACK_DAYS,
            min_confidence=0.2,
            include_low_confidence=True,
            result_limit=500,
        )
        result = await VulnerabilitySearchService().search_and_store(session, req)

        logger.info("Source stats:")
        for sid, stats in result.source_stats.items():
            logger.info(
                "  %s: found=%s saved=%s error=%s",
                sid, stats.get("found"), stats.get("saved"), stats.get("error"),
            )
        print(
            f"\nDone: {result.items_saved} vulnerability records saved "
            f"(last {LOOKBACK_DAYS} days)"
        )
    finally:
        await session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
