"""
Run full unified pipeline: all collectors → aggregate → Ollama → unified_intel.

Usage (from backend/):
    python -m scripts.run_unified_pipeline
    python -m scripts.run_unified_pipeline --skip-collections
"""

import argparse
import asyncio
import logging
import sys

from app.db.database import init_db
from app.models.schemas import UnifiedRunRequest
from app.services.unified_intel_service import UnifiedIntelService

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def _session():
    await init_db()
    from app.db.database import _session_factory

    return _session_factory()


async def main(skip_collections: bool, replace: bool) -> None:
    session = await _session()
    try:
        req = UnifiedRunRequest(
            lookback_days=30,
            run_collections=not skip_collections,
            use_llm=True,
            replace_existing=replace,
            min_confidence=25,
            result_limit=100,
        )
        result = await UnifiedIntelService().run_pipeline(session, req)
        logger.info(
            "Unified pipeline done: loaded=%d clusters=%d saved=%d ollama=%s (%.1fs)",
            result.source_records_loaded,
            result.clusters_processed,
            result.items_saved,
            result.ollama_used,
            result.duration_seconds,
        )
        print(f"\nDone: {result.items_saved} rows in unified_intel")
    finally:
        await session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-collections", action="store_true")
    parser.add_argument("--replace", action="store_true", help="Clear unified_intel first")
    args = parser.parse_args()
    try:
        asyncio.run(main(args.skip_collections, args.replace))
    except KeyboardInterrupt:
        sys.exit(130)
