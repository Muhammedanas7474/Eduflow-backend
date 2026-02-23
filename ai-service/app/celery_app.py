"""
Celery application configuration for background tasks.
Uses Redis as the broker (same Redis instance as Django).
"""

from app.core.config import settings
from celery import Celery

celery_app = Celery(
    "eduflow-ai",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # One task at a time (heavy processing)
)
