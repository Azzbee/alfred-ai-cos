"""Celery app. Broker + result backend are Redis. Run a worker with:
    uv run celery -A app.workers.celery_app worker --loglevel=info
And the beat scheduler (periodic sync, daily briefing) with:
    uv run celery -A app.workers.celery_app beat --loglevel=info
"""

from celery import Celery
from celery.schedules import crontab

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
    beat_schedule={
        # Generate every user's morning briefing at 06:00 UTC. Per-user timezone
        # delivery is a later refinement (briefing carries a date, not a send time).
        "daily-briefings": {
            "task": "albert.generate_all_briefings",
            "schedule": crontab(hour=6, minute=0),
        },
        # Scan for at-risk loops and dispatch notifications every 30 minutes. The
        # per-user quiet-hours + threshold logic decides what actually sends.
        "notification-scan": {
            "task": "albert.scan_notifications",
            "schedule": crontab(minute="*/30"),
        },
    },
)
