"""API routes to trigger and monitor Celery background jobs."""

from enum import Enum

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config.settings import settings
from app.worker.celery_app import celery_app
from app.worker.jobs import LOOKBACK_DAYS
from app.worker.tasks import (
    run_advisory_search,
    run_all_collections,
    run_blog_search,
    run_breach_search,
    run_compliance_search,
    run_social_search,
    run_unified_pipeline_task,
    run_vulnerability_search,
)

router = APIRouter(prefix="/jobs", tags=["Background Jobs"])


class PipelineName(str, Enum):
    all = "all"
    social = "social"
    advisories = "advisories"
    blogs = "blogs"
    vulnerabilities = "vulnerabilities"
    compliance = "compliance"
    breaches = "breaches"
    unified = "unified"


class JobTriggerRequest(BaseModel):
    lookback_days: int = Field(default=LOOKBACK_DAYS, ge=1, le=365)


class JobTriggerResponse(BaseModel):
    task_id: str
    pipeline: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    task_id: str
    status: str
    ready: bool
    successful: bool | None = None
    result: dict | None = None
    error: str | None = None


_TASK_MAP = {
    PipelineName.all: run_all_collections,
    PipelineName.social: run_social_search,
    PipelineName.advisories: run_advisory_search,
    PipelineName.blogs: run_blog_search,
    PipelineName.vulnerabilities: run_vulnerability_search,
    PipelineName.compliance: run_compliance_search,
    PipelineName.breaches: run_breach_search,
    PipelineName.unified: run_unified_pipeline_task,
}


def _redis_available() -> tuple[bool, str | None]:
    if not settings.celery_enabled:
        return False, "Celery is disabled"
    try:
        import redis

        client = redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)
        client.ping()
        return True, None
    except Exception as exc:
        return False, str(exc)


@router.get("/config")
async def job_config() -> dict:
    return {
        "celery_enabled": settings.celery_enabled,
        "redis_url": settings.redis_url.split("@")[-1] if "@" in settings.redis_url else settings.redis_url,
        "beat_interval_minutes": settings.celery_beat_interval_minutes,
        "lookback_days_default": LOOKBACK_DAYS,
        "pipelines": [p.value for p in PipelineName],
        "scheduled_task": "zdr.run_all_collections",
        "social_sources_background": ["twitter", "reddit", "hackernews", "linkedin"],
    }


@router.post("/run/{pipeline}", response_model=JobTriggerResponse)
async def trigger_job(pipeline: PipelineName, request: JobTriggerRequest) -> JobTriggerResponse:
    if not settings.celery_enabled:
        raise HTTPException(status_code=503, detail="Celery background jobs are disabled")

    redis_ok, redis_error = _redis_available()
    if not redis_ok:
        raise HTTPException(
            status_code=503,
            detail=(
                "Redis is not reachable — background jobs cannot start. "
                "Install and start Redis, then run the Celery worker. "
                f"({redis_error})"
            ),
        )

    task_fn = _TASK_MAP[pipeline]
    async_result = task_fn.delay(lookback_days=request.lookback_days)

    return JobTriggerResponse(
        task_id=async_result.id,
        pipeline=pipeline.value,
        status="queued",
        message=f"Background job queued on Celery worker (lookback={request.lookback_days}d)",
    )


@router.get("/status/{task_id}", response_model=JobStatusResponse)
async def job_status(task_id: str) -> JobStatusResponse:
    result = AsyncResult(task_id, app=celery_app)
    payload: dict | None = None
    error: str | None = None

    if result.ready():
        if result.successful():
            payload = result.result if isinstance(result.result, dict) else {"data": result.result}
        else:
            error = str(result.result) if result.result else "Task failed"

    return JobStatusResponse(
        task_id=task_id,
        status=result.status,
        ready=result.ready(),
        successful=result.successful() if result.ready() else None,
        result=payload,
        error=error,
    )
