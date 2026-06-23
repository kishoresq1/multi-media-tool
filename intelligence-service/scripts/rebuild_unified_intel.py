#!/usr/bin/env python3
"""
Rebuild only the unified_intel table from existing intel tables.

Does NOT re-run collectors or touch other tables (except schema migrations).
"""

import argparse
import asyncio
import logging
import sys

from sqlalchemy import delete, func, select

from app.db.database import init_db
from app.db.models import UnifiedIntel
from app.models.schemas import UnifiedRunRequest
from app.services.unified_intel_service import UnifiedIntelService

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def main(use_llm: bool, min_confidence: float) -> None:
    await init_db()
    from app.db.database import _session_factory

    async with _session_factory() as session:
        before = await session.scalar(select(func.count()).select_from(UnifiedIntel))
        logger.info("Clearing unified_intel (%d rows)…", before or 0)
        await session.execute(delete(UnifiedIntel))
        await session.commit()

        req = UnifiedRunRequest(
            lookback_days=30,
            run_collections=False,
            use_llm=use_llm,
            replace_existing=False,
            min_confidence=min_confidence,
            result_limit=500,
        )
        result = await UnifiedIntelService().run_pipeline(session, req)

        after = await session.scalar(select(func.count()).select_from(UnifiedIntel))
        classified = await session.scalar(
            select(func.count()).select_from(UnifiedIntel).where(
                UnifiedIntel.classification.isnot(None),
                UnifiedIntel.classification != "UNKNOWN",
            )
        )

        print(f"\nunified_intel rebuilt: {after} rows")
        print(f"  source records loaded: {result.source_records_loaded}")
        print(f"  clusters processed: {result.clusters_processed}")
        print(f"  saved this run: {result.items_saved}")
        print(f"  classified (non-UNKNOWN): {classified}")
        print(f"  duration: {result.duration_seconds}s")

        if after:
            from sqlalchemy import text

            rows = (
                await session.execute(
                    text(
                        "SELECT classification, COUNT(*) FROM unified_intel "
                        "GROUP BY classification ORDER BY COUNT(*) DESC"
                    )
                )
            ).fetchall()
            print("  by classification:")
            for cls, cnt in rows:
                print(f"    {cls or 'NULL'}: {cnt}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rebuild unified_intel only")
    parser.add_argument("--no-llm", action="store_true", help="Skip Ollama enrichment")
    parser.add_argument("--min-confidence", type=float, default=25.0)
    args = parser.parse_args()
    try:
        asyncio.run(main(use_llm=not args.no_llm, min_confidence=args.min_confidence))
    except KeyboardInterrupt:
        sys.exit(130)
