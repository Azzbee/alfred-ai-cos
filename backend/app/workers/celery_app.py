"""Celery app. Broker + result backend are Redis. Run a worker with:
    uv run celery -A app.workers.celery_app worker --loglevel=info
And the beat scheduler (periodic sync, daily briefing) with:
    uv run celery -A app.workers.celery_app beat --loglevel=info
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "albert",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
