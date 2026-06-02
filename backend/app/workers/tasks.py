"""Background tasks. The API runs sync synchronously for the slice demo; in
production it enqueues sync_user so ingestion + extraction run off the request
path (PRD 13.4 near-real-time ingestion)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from app.db.base import SessionLocal
from app.db.models import User
from app.notifications import get_notifier
from app.services import briefing, extraction, ingestion, notifications
from app.workers.celery_app import celery_app


@celery_app.task(name="albert.sync_user")  # type: ignore[untyped-decorator]
def sync_user(user_id: str, max_results: int = 25) -> dict[str, int]:
    """Ingest recent messages for a user and run extraction over the new ones."""
    db = SessionLocal()
    try:
        messages = ingestion.ingest_recent_messages(db, user_id, max_results=max_results)
        commitments = 0
        for message in messages:
            commitments += len(extraction.process_message(db, message))
        return {"ingested": len(messages), "commitments_found": commitments}
    finally:
        db.close()


@celery_app.task(name="albert.generate_briefing")  # type: ignore[untyped-decorator]
def generate_briefing(user_id: str) -> str:
    """Generate today's briefing for one user. Returns the briefing id."""
    db = SessionLocal()
    try:
        result = briefing.generate_briefing(db, user_id, today=datetime.now(UTC).date())
        return result.id
    finally:
        db.close()


@celery_app.task(name="albert.generate_all_briefings")  # type: ignore[untyped-decorator]
def generate_all_briefings() -> int:
    """Beat entry point: fan out briefing generation to every user. Returns the count.

    Per-user generation is dispatched as its own task so one slow/failing user does
    not block the rest (PRD 13.3 failures visible and isolated)."""
    db = SessionLocal()
    try:
        user_ids = list(db.scalars(select(User.id)))
    finally:
        db.close()
    for uid in user_ids:
        generate_briefing.delay(uid)
    return len(user_ids)


@celery_app.task(name="albert.scan_notifications")  # type: ignore[untyped-decorator]
def scan_notifications() -> dict[str, int]:
    """Beat entry point: scan every user for at-risk loops, enqueue notifications,
    and dispatch the ones that clear the threshold and quiet hours."""
    db = SessionLocal()
    notifier = get_notifier()
    enqueued = sent = held = 0
    try:
        users = list(db.scalars(select(User)))
        now_dt = datetime.now(UTC)
        now_t = now_dt.time()
        today = now_dt.date()
        for user in users:
            enqueued += notifications.scan_for_risks(db, user.id, today=today)
            enqueued += notifications.scan_pending_approvals(db, user.id, now=now_dt)
            result = notifications.dispatch_pending(db, user, now=now_t, provider=notifier)
            sent += result["sent"]
            held += result["held"]
    finally:
        db.close()
    return {"enqueued": enqueued, "sent": sent, "held": held}
