"""
Celery application — scheduled intel refresh every 20 minutes via Redis.
"""

from datetime import timedelta

from celery import Celery

from app.config.settings import settings

celery_app = Celery(
    "zero_day_radar",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60 * 45,
    task_soft_time_limit=60 * 40,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    result_expires=60 * 60 * 24,
)

_interval = settings.celery_beat_interval_minutes

celery_app.conf.beat_schedule = {
    "refresh-all-intel": {
        "task": "zdr.run_all_collections",
        "schedule": timedelta(days=1),
        "options": {"queue": "intel"},
    },
}
