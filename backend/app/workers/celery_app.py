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
        # Hourly tick: generate the morning briefing for every user whose local time
        # has entered their morning window (07:00-09:59) and who has no briefing yet
        # for their local today. Per-user idempotency makes the overlap safe.
        "due-briefings": {
            "task": "albert.dispatch_due_briefings",
            "schedule": crontab(minute=0),
        },
        # Scan for at-risk loops and dispatch notifications every 30 minutes. The
        # per-user quiet-hours + threshold logic decides what actually sends.
        "notification-scan": {
            "task": "albert.scan_notifications",
            "schedule": crontab(minute="*/30"),
        },
        # Fire any due RecurringRule. 5-minute granularity is the finest the
        # PRD asks for (weekly_digest, project_propose); a tighter beat would
        # just chew through DB queries.
        "recurring-scan": {
            "task": "albert.scan_recurring",
            "schedule": crontab(minute="*/5"),
        },
    },
)
