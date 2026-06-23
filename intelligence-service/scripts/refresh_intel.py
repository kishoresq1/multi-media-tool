"""
Clear intel tables and re-fetch last 30 days using SEARCH_KEYWORDS only.

Usage (from backend/):
    python -m scripts.refresh_intel
"""

import asyncio
import logging
import sys

from sqlalchemy import delete, func, select

from app.db.database import init_db
from app.db.models import IntelPost, ResearchBlogIntel, VendorAdvisoryIntel
from app.models.schemas import AdvisorySearchRequest, BlogSearchRequest, SocialSearchRequest
from app.services.advisory_search import AdvisorySearchService
from app.services.blog_search import BlogSearchService
from app.services.social_search import SocialSearchService

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

LOOKBACK_DAYS = 30


async def _get_session():
    from app.db.database import _session_factory

    if _session_factory is None:
        await init_db()
    from app.db.database import _session_factory as factory

    return factory()


async def clear_intel_tables(session) -> dict[str, int]:
    counts = {}
    for model, name in (
        (IntelPost, "intel_posts"),
        (VendorAdvisoryIntel, "vendor_advisory_intel"),
        (ResearchBlogIntel, "research_blog_intel"),
    ):
        before = await session.scalar(select(func.count()).select_from(model))
        await session.execute(delete(model))
        counts[name] = before or 0
    await session.commit()
    return counts


async def refresh() -> None:
    await init_db()
    session = await _get_session()

    try:
        deleted = await clear_intel_tables(session)
        logger.info("Deleted rows: %s", deleted)

        social_svc = SocialSearchService()
        advisory_svc = AdvisorySearchService()
        blog_svc = BlogSearchService()

        social_req = SocialSearchRequest(
            lookback_days=LOOKBACK_DAYS,
            min_confidence=0.25,
            include_low_confidence=True,
            max_queries=60,
            result_limit=200,
            sources=["reddit", "hackernews", "linkedin"],  # skip twitter/nitter
        )
        advisory_req = AdvisorySearchRequest(
            lookback_days=LOOKBACK_DAYS,
            min_confidence=0.3,
            include_low_confidence=True,
            result_limit=200,
        )
        blog_req = BlogSearchRequest(
            lookback_days=LOOKBACK_DAYS,
            min_confidence=0.25,
            include_low_confidence=True,
            result_limit=200,
        )

        logger.info("Running social search (last %d days, SEARCH_KEYWORDS only)...", LOOKBACK_DAYS)
        social = await social_svc.search_and_store(session, social_req)
        logger.info("Social: found=%d saved=%d", social.posts_found, social.posts_saved)

        logger.info("Running advisory search...")
        advisory = await advisory_svc.search_and_store(session, advisory_req)
        logger.info("Advisory: found=%d saved=%d", advisory.advisories_found, advisory.advisories_saved)

        logger.info("Running blog search...")
        blog = await blog_svc.search_and_store(session, blog_req)
        logger.info("Blog: found=%d saved=%d", blog.posts_found, blog.posts_saved)

        total = social.posts_saved + advisory.advisories_saved + blog.posts_saved
        logger.info("Refresh complete — %d rows saved across 3 tables", total)
        print(
            f"\nDone: social={social.posts_saved}, "
            f"advisories={advisory.advisories_saved}, blogs={blog.posts_saved}"
        )
    finally:
        await session.close()


if __name__ == "__main__":
    try:
        asyncio.run(refresh())
    except KeyboardInterrupt:
        sys.exit(130)
