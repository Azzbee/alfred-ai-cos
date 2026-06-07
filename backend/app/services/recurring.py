"""Recurring workflows (PRD Phase 3).

A small scheduler-on-top-of-the-DB. RecurringRule rows describe a named
workflow + a cron expression in the user's timezone. A Celery beat task
(`scan_recurring_rules`) runs every 5 minutes, picks up rules whose
`next_run_at` has passed, runs the matching handler, advances the next
fire time using croniter, and stamps `last_run_at`.

Add a workflow by writing a function and registering it in WORKFLOWS.
Workflows receive (db, user, params) — params is the JSON dict from the
RecurringRule row. They should be idempotent or at least safe to re-run
(the scheduler doesn't double-fire, but a crash + retry might)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from croniter import croniter
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import RecurringRule, User

WorkflowFn = Callable[[Session, User, dict], dict]


# ---------- workflow registry ----------


def _weekly_digest(db: Session, user: User, params: dict) -> dict:
    """Generate a digest of the user's open + recent commitments and stash
    it as a Notification with deep_link=/today. Lightweight on purpose:
    the rich content is already on the Today screen."""
    from sqlalchemy import func

    from app.db.enums import CommitmentStatus, NotificationType
    from app.db.models import Commitment
    from app.services import notifications

    open_count = (
        db.scalar(
            select(func.count(Commitment.id)).where(
                Commitment.user_id == user.id,
                Commitment.status == CommitmentStatus.open,
            )
        )
        or 0
    )
    waiting_on_user = (
        db.scalar(
            select(func.count(Commitment.id)).where(
                Commitment.user_id == user.id,
                Commitment.status == CommitmentStatus.open,
                Commitment.owner == "user",
            )
        )
        or 0
    )

    title = "Your weekly digest"
    body = f"{open_count} open loops; {waiting_on_user} are on you."
    notifications.enqueue(
        db,
        user.id,
        ntype=NotificationType.daily_briefing,
        title=title,
        body=body,
        payload={"deep_link": "/today"},
        dedup_key=f"digest:{datetime.now(UTC).date().isoformat()}",
    )
    return {"open": open_count, "owed": waiting_on_user}


def _project_propose(db: Session, user: User, params: dict) -> dict:
    """Run the projects.propose_projects clustering pass."""
    from app.services import projects

    proposed = projects.propose_projects(db, user)
    return {"proposed": len(proposed)}


WORKFLOWS: dict[str, WorkflowFn] = {
    "weekly_digest": _weekly_digest,
    "project_propose": _project_propose,
}


# ---------- scheduling ----------


def _user_tz(user: User) -> ZoneInfo:
    try:
        return ZoneInfo(user.timezone or "UTC")
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def next_run(cron: str, user: User, *, after: datetime | None = None) -> datetime:
    """Next fire time for `cron` interpreted in the user's timezone.
    Returned as an aware UTC datetime, ready to store on next_run_at."""
    base_local = (after or datetime.now(UTC)).astimezone(_user_tz(user))
    itr = croniter(cron, base_local)
    nxt_local = itr.get_next(datetime)
    if nxt_local.tzinfo is None:
        nxt_local = nxt_local.replace(tzinfo=_user_tz(user))
    return nxt_local.astimezone(UTC)


# ---------- CRUD ----------


def create_rule(
    db: Session,
    user: User,
    *,
    name: str,
    workflow: str,
    cron: str,
    params: dict | None = None,
    enabled: bool = True,
) -> RecurringRule:
    if workflow not in WORKFLOWS:
        raise ValueError(f"Unknown workflow: {workflow}")
    # Validate the cron expression up front by attempting to compute the
    # next fire — croniter raises on malformed input.
    nxt = next_run(cron, user)
    rule = RecurringRule(
        user_id=user.id,
        name=name,
        workflow=workflow,
        cron=cron,
        params=params or {},
        next_run_at=nxt if enabled else None,
        enabled=enabled,
    )
    db.add(rule)
    db.commit()
    return rule


def set_enabled(db: Session, rule: RecurringRule, *, enabled: bool, user: User) -> RecurringRule:
    rule.enabled = enabled
    if enabled and rule.next_run_at is None:
        rule.next_run_at = next_run(rule.cron, user)
    elif not enabled:
        rule.next_run_at = None
    db.commit()
    return rule


def update_rule(
    db: Session,
    rule: RecurringRule,
    *,
    user: User,
    name: str | None = None,
    cron: str | None = None,
    params: dict | None = None,
) -> RecurringRule:
    if name is not None:
        rule.name = name
    if params is not None:
        rule.params = params
    if cron is not None:
        rule.cron = cron
        # Cron changed → re-compute next_run_at unless paused.
        if rule.enabled:
            rule.next_run_at = next_run(cron, user)
    db.commit()
    return rule


def delete_rule(db: Session, rule: RecurringRule) -> None:
    db.delete(rule)
    db.commit()


# ---------- scanner ----------


def scan_and_fire(db: Session, *, now: datetime | None = None) -> int:
    """Fire every enabled rule whose next_run_at has passed. Returns the
    number of rules that fired (regardless of success — failures land in
    `last_error`)."""
    now = now or datetime.now(UTC)
    due = list(
        db.scalars(
            select(RecurringRule).where(
                RecurringRule.enabled.is_(True),
                RecurringRule.next_run_at.is_not(None),
                RecurringRule.next_run_at <= now,
            )
        )
    )
    fired = 0
    for rule in due:
        user = db.get(User, rule.user_id)
        if user is None:
            # User was deleted mid-flight; remove the rule so it doesn't loop.
            db.delete(rule)
            continue
        handler = WORKFLOWS.get(rule.workflow)
        if handler is None:
            rule.last_error = f"Unknown workflow {rule.workflow!r}"
            rule.next_run_at = None  # pause until reconfigured
        else:
            try:
                handler(db, user, rule.params or {})
                rule.last_error = None
            except Exception as exc:  # noqa: BLE001 — capture for the user UI
                rule.last_error = str(exc)
            # Advance regardless of success — a perpetual failure shouldn't
            # block the rule from trying again next tick.
            rule.next_run_at = next_run(rule.cron, user, after=now)
            rule.last_run_at = now
            fired += 1
    db.commit()
    return fired
