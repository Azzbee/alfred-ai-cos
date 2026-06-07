"""Background tasks. The API runs sync synchronously for the slice demo; in
production it enqueues sync_user so ingestion + extraction run off the request
path (PRD 13.4 near-real-time ingestion)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from app.db.base import SessionLocal
from app.db.enums import NotificationType
from app.db.models import User
from app.notifications import get_notifier
from app.services import (
    briefing,
    extraction,
    ingestion,
    notifications,
    outbound_tracking,
    snooze,
)
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


@celery_app.task(name="albert.dispatch_due_briefings")  # type: ignore[untyped-decorator]
def dispatch_due_briefings() -> dict[str, int]:
    """Beat entry point (hourly): generate the morning briefing for each user whose
    local time has entered the morning window and who has no briefing yet for their
    local today. Pushes a daily_briefing notification (deep link /today) after each.

    Per-user idempotency comes from briefing.due_briefing_date returning None once a
    row exists, plus the notification dedup_key on the briefing id."""
    db = SessionLocal()
    generated = pushed = 0
    try:
        users = list(db.scalars(select(User)))
        now_utc = datetime.now(UTC)
        for user in users:
            target_date = briefing.due_briefing_date(db, user, now_utc=now_utc)
            if target_date is None:
                continue
            result = briefing.generate_briefing(db, user.id, today=target_date)
            generated += 1
            created = notifications.enqueue(
                db,
                user.id,
                ntype=NotificationType.daily_briefing,
                title="Your morning briefing is ready",
                body=result.summary[:160],
                payload={"briefing_id": result.id, "deep_link": "/today"},
                dedup_key=f"briefing:{result.id}",
            )
            if created is not None:
                pushed += 1
    finally:
        db.close()
    return {"generated": generated, "pushed": pushed}


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
            enqueued += notifications.scan_upcoming_meetings(db, user.id, now=now_dt)
            enqueued += notifications.scan_waiting_aging(db, user.id, now=now_dt)
            enqueued += notifications.scan_schedule_conflicts(db, user.id, now=now_dt)
            enqueued += outbound_tracking.scan_silent_threads(db, user, now=now_dt)
            # Re-open snoozed commitments whose wake condition has fired BEFORE
            # we run the priority scanner so newly-awake items can be re-ranked.
            snooze.scan_wakes(db, user.id, today=today)
            enqueued += notifications.scan_top_priorities(db, user, today=today)
            result = notifications.dispatch_pending(db, user, now=now_t, provider=notifier)
            sent += result["sent"]
            held += result["held"]
    finally:
        db.close()
    return {"enqueued": enqueued, "sent": sent, "held": held}


@celery_app.task(name="albert.scan_recurring")  # type: ignore[untyped-decorator]
def scan_recurring() -> dict[str, int]:
    """Beat entry point (every 5 min): fire any RecurringRule whose
    next_run_at has passed."""
    from app.services import recurring as recurring_service

    db = SessionLocal()
    try:
        fired = recurring_service.scan_and_fire(db)
    finally:
        db.close()
    return {"fired": fired}
