"""
Celery tasks — each pipeline + orchestrator for full refresh.
"""

import logging

from app.worker.async_runner import run_async, with_session
from app.worker.celery_app import celery_app
from app.worker.jobs import (
    LOOKBACK_DAYS,
    refresh_advisories,
    refresh_all,
    refresh_blogs,
    refresh_breaches,
    refresh_compliance,
    refresh_social,
    refresh_unified,
    refresh_vulnerabilities,
    run_unified_pipeline,
)

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="zdr.run_all_collections", queue="intel")
def run_all_collections(self, lookback_days: int = LOOKBACK_DAYS) -> dict:
    """Run social + advisories + blogs + vulnerabilities sequentially."""
    logger.info("Celery task zdr.run_all_collections started (id=%s)", self.request.id)
    return run_async(refresh_all(lookback_days=lookback_days))


@celery_app.task(bind=True, name="zdr.run_social_search", queue="intel")
def run_social_search(self, lookback_days: int = LOOKBACK_DAYS) -> dict:
    logger.info("Celery task zdr.run_social_search started (id=%s)", self.request.id)
    return run_async(with_session(refresh_social, lookback_days=lookback_days))


@celery_app.task(bind=True, name="zdr.run_advisory_search", queue="intel")
def run_advisory_search(self, lookback_days: int = LOOKBACK_DAYS) -> dict:
    logger.info("Celery task zdr.run_advisory_search started (id=%s)", self.request.id)
    return run_async(with_session(refresh_advisories, lookback_days=lookback_days))


@celery_app.task(bind=True, name="zdr.run_blog_search", queue="intel")
def run_blog_search(self, lookback_days: int = LOOKBACK_DAYS) -> dict:
    logger.info("Celery task zdr.run_blog_search started (id=%s)", self.request.id)
    return run_async(with_session(refresh_blogs, lookback_days=lookback_days))


@celery_app.task(bind=True, name="zdr.run_vulnerability_search", queue="intel")
def run_vulnerability_search(self, lookback_days: int = LOOKBACK_DAYS) -> dict:
    logger.info("Celery task zdr.run_vulnerability_search started (id=%s)", self.request.id)
    return run_async(with_session(refresh_vulnerabilities, lookback_days=lookback_days))


@celery_app.task(bind=True, name="zdr.run_breach_search", queue="intel")
def run_breach_search(self, lookback_days: int = LOOKBACK_DAYS) -> dict:
    logger.info("Celery task zdr.run_breach_search started (id=%s)", self.request.id)
    return run_async(with_session(refresh_breaches, lookback_days=lookback_days))


@celery_app.task(bind=True, name="zdr.run_compliance_search", queue="intel")
def run_compliance_search(self, lookback_days: int = LOOKBACK_DAYS) -> dict:
    logger.info("Celery task zdr.run_compliance_search started (id=%s)", self.request.id)
    return run_async(with_session(refresh_compliance, lookback_days=lookback_days))


@celery_app.task(bind=True, name="zdr.run_unified_pipeline", queue="intel")
def run_unified_pipeline_task(self, lookback_days: int = LOOKBACK_DAYS) -> dict:
    """Run all collectors + Ollama + unified_intel table."""
    logger.info("Celery task zdr.run_unified_pipeline started (id=%s)", self.request.id)
    return run_async(with_session(run_unified_pipeline, lookback_days=lookback_days))
