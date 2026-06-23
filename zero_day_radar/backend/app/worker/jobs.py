"""
Shared intel refresh jobs used by Celery tasks and the FastAPI trigger API.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from app.models.schemas import (
    AdvisorySearchRequest,
    BlogSearchRequest,
    BreachSearchRequest,
    ComplianceSearchRequest,
    SocialSearchRequest,
    VulnerabilitySearchRequest,
)
from app.services.advisory_search import AdvisorySearchService
from app.services.blog_search import BlogSearchService
from app.services.breach_search import BreachSearchService
from app.services.compliance_search import ComplianceSearchService
from app.services.social_search import SocialSearchService
from app.services.vulnerability_search import VulnerabilitySearchService
from app.worker.async_runner import with_session

logger = logging.getLogger(__name__)

LOOKBACK_DAYS = 30

# All social sources including Nitter/Twitter for background runs
SOCIAL_SOURCES = ["twitter", "reddit", "hackernews", "linkedin"]


async def refresh_social(session, lookback_days: int = LOOKBACK_DAYS) -> dict[str, Any]:
    request = SocialSearchRequest(
        lookback_days=lookback_days,
        sources=SOCIAL_SOURCES,
        max_queries=60,
        min_confidence=25,
        include_low_confidence=True,
        result_limit=200,
    )
    result = await SocialSearchService().search_and_store(session, request)
    return {
        "pipeline": "social",
        "posts_found": result.posts_found,
        "posts_saved": result.posts_saved,
        "sources": result.sources_searched,
        "source_stats": result.source_stats,
        "duration_seconds": result.duration_seconds,
    }


async def refresh_advisories(session, lookback_days: int = LOOKBACK_DAYS) -> dict[str, Any]:
    request = AdvisorySearchRequest(
        lookback_days=lookback_days,
        min_confidence=25,
        include_low_confidence=True,
        result_limit=200,
    )
    result = await AdvisorySearchService().search_and_store(session, request)
    return {
        "pipeline": "advisories",
        "items_found": result.advisories_found,
        "items_saved": result.advisories_saved,
        "source_stats": result.source_stats,
        "duration_seconds": result.duration_seconds,
    }


async def refresh_blogs(session, lookback_days: int = LOOKBACK_DAYS) -> dict[str, Any]:
    request = BlogSearchRequest(
        lookback_days=lookback_days,
        min_confidence=25,
        include_low_confidence=True,
        result_limit=200,
    )
    result = await BlogSearchService().search_and_store(session, request)
    return {
        "pipeline": "blogs",
        "items_found": result.posts_found,
        "items_saved": result.posts_saved,
        "source_stats": result.source_stats,
        "duration_seconds": result.duration_seconds,
    }


async def refresh_vulnerabilities(session, lookback_days: int = LOOKBACK_DAYS) -> dict[str, Any]:
    request = VulnerabilitySearchRequest(
        lookback_days=lookback_days,
        min_confidence=20,
        include_low_confidence=True,
        result_limit=500,
    )
    result = await VulnerabilitySearchService().search_and_store(session, request)
    return {
        "pipeline": "vulnerabilities",
        "items_found": result.items_found,
        "items_saved": result.items_saved,
        "source_stats": result.source_stats,
        "duration_seconds": result.duration_seconds,
    }


async def refresh_breaches(session, lookback_days: int = LOOKBACK_DAYS) -> dict[str, Any]:
    request = BreachSearchRequest(
        lookback_days=lookback_days,
        min_confidence=25,
        include_low_confidence=True,
        result_limit=300,
    )
    result = await BreachSearchService().search_and_store(session, request)
    return {
        "pipeline": "breaches",
        "items_found": result.items_found,
        "items_saved": result.items_saved,
        "source_stats": result.source_stats,
        "duration_seconds": result.duration_seconds,
    }


async def refresh_compliance(session, lookback_days: int = LOOKBACK_DAYS) -> dict[str, Any]:
    request = ComplianceSearchRequest(
        lookback_days=lookback_days,
        min_confidence=35,
        include_low_confidence=True,
        result_limit=200,
    )
    result = await ComplianceSearchService().search_and_store(session, request)
    return {
        "pipeline": "compliance",
        "items_found": result.items_found,
        "items_saved": result.items_saved,
        "source_stats": result.source_stats,
        "duration_seconds": result.duration_seconds,
    }



async def run_unified_pipeline(
    session,
    lookback_days: int = LOOKBACK_DAYS,
    *,
    run_collections: bool = True,
    replace_existing: bool = False,
) -> dict[str, Any]:
    from app.models.schemas import UnifiedRunRequest
    from app.services.unified_intel_service import UnifiedIntelService

    request = UnifiedRunRequest(
        lookback_days=lookback_days,
        run_collections=run_collections,
        use_llm=True,
        replace_existing=replace_existing,
        min_confidence=25,
        result_limit=200,
    )
    result = await UnifiedIntelService().run_pipeline(session, request)
    return {
        "pipeline": "unified_full",
        "collections_ran": result.collections_ran,
        "items_saved": result.items_saved,
        "clusters_processed": result.clusters_processed,
        "ollama_used": result.ollama_used,
        "duration_seconds": result.duration_seconds,
        "collection_stats": result.collection_stats,
    }


async def refresh_unified(session, lookback_days: int = LOOKBACK_DAYS) -> dict[str, Any]:
    from app.models.schemas import UnifiedRunRequest
    from app.services.unified_intel_service import UnifiedIntelService

    request = UnifiedRunRequest(
        lookback_days=lookback_days,
        run_collections=False,
        use_llm=True,
        replace_existing=False,
        min_confidence=25,
        result_limit=200,
    )
    result = await UnifiedIntelService().run_pipeline(session, request)
    return {
        "pipeline": "unified",
        "items_saved": result.items_saved,
        "clusters_processed": result.clusters_processed,
        "ollama_used": result.ollama_used,
        "duration_seconds": result.duration_seconds,
    }


async def refresh_all(lookback_days: int = LOOKBACK_DAYS) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    results: dict[str, Any] = {}
    errors: dict[str, str] = {}

    pipelines = [
        ("social", refresh_social),
        ("advisories", refresh_advisories),
        ("blogs", refresh_blogs),
        ("vulnerabilities", refresh_vulnerabilities),
        ("breaches", refresh_breaches),
        ("compliance", refresh_compliance),
    ]

    for name, fn in pipelines:
        try:
            logger.info("Background job: starting %s", name)
            results[name] = await with_session(fn, lookback_days=lookback_days)
            logger.info("Background job: %s saved=%s", name, results[name].get("items_saved") or results[name].get("posts_saved"))
        except Exception as exc:
            logger.exception("Background job %s failed: %s", name, exc)
            errors[name] = str(exc)
            results[name] = {"pipeline": name, "error": str(exc)}

    try:
        logger.info("Background job: starting unified (aggregate + LLM)")
        results["unified"] = await with_session(refresh_unified, lookback_days=lookback_days)
    except Exception as exc:
        logger.exception("Background job unified failed: %s", exc)
        errors["unified"] = str(exc)
        results["unified"] = {"pipeline": "unified", "error": str(exc)}

    completed = datetime.now(timezone.utc)
    return {
        "status": "completed" if not errors else "partial",
        "started_at": started.isoformat(),
        "completed_at": completed.isoformat(),
        "duration_seconds": round((completed - started).total_seconds(), 2),
        "pipelines": results,
        "errors": errors,
    }
