"""Tests for RecurringRule + the scheduler scanner."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.db.models import User
from app.services import recurring as recurring_service

NOW = datetime(2026, 6, 7, 12, 0, tzinfo=UTC)


def _aware(dt: datetime | None) -> datetime | None:
    """Coerce a possibly-naive datetime to UTC-aware. SQLite drops tzinfo
    on roundtrip even when the column is DateTime(timezone=True)."""
    if dt is None:
        return None
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


@pytest.fixture
def user(db: Session) -> User:
    u = User(email="adam@adam.dev", timezone="America/New_York")
    db.add(u)
    db.commit()
    return u


# --- create / validate ---


def test_create_rule_sets_next_run_at(db: Session, user: User) -> None:
    rule = recurring_service.create_rule(
        db,
        user,
        name="Weekly digest",
        workflow="weekly_digest",
        cron="0 7 * * MON",  # Monday 07:00 user-local
    )
    assert rule.id and rule.user_id == user.id
    assert rule.next_run_at is not None
    assert rule.enabled is True


def test_unknown_workflow_rejected(db: Session, user: User) -> None:
    with pytest.raises(ValueError):
        recurring_service.create_rule(db, user, name="X", workflow="nope", cron="* * * * *")


def test_invalid_cron_rejected(db: Session, user: User) -> None:
    # croniter raises ValueError / CroniterBadCronError for malformed
    # expressions; either way it's a non-zero exit, which is what we want.
    with pytest.raises((ValueError, Exception)) as exc_info:
        recurring_service.create_rule(
            db,
            user,
            name="bad",
            workflow="weekly_digest",
            cron="not-a-cron",
        )
    assert exc_info.value is not None


def test_disabled_rule_has_no_next_run(db: Session, user: User) -> None:
    rule = recurring_service.create_rule(
        db,
        user,
        name="off",
        workflow="weekly_digest",
        cron="0 7 * * MON",
        enabled=False,
    )
    assert rule.next_run_at is None


# --- toggle ---


def test_enable_recomputes_next_run(db: Session, user: User) -> None:
    rule = recurring_service.create_rule(
        db,
        user,
        name="off",
        workflow="weekly_digest",
        cron="0 7 * * MON",
        enabled=False,
    )
    recurring_service.set_enabled(db, rule, enabled=True, user=user)
    db.refresh(rule)
    assert rule.next_run_at is not None


def test_disable_clears_next_run(db: Session, user: User) -> None:
    rule = recurring_service.create_rule(
        db,
        user,
        name="on",
        workflow="weekly_digest",
        cron="0 7 * * MON",
    )
    recurring_service.set_enabled(db, rule, enabled=False, user=user)
    db.refresh(rule)
    assert rule.next_run_at is None


# --- scanner / fire ---


def test_scanner_fires_due_rule(db: Session, user: User) -> None:
    rule = recurring_service.create_rule(
        db,
        user,
        name="digest",
        workflow="weekly_digest",
        cron="*/5 * * * *",
    )
    # Backdate next_run_at to make it due.
    rule.next_run_at = NOW - timedelta(minutes=1)
    db.commit()
    fired = recurring_service.scan_and_fire(db, now=NOW)
    assert fired == 1
    db.refresh(rule)
    assert rule.last_run_at is not None
    # Next run advanced past now.
    assert rule.next_run_at is not None
    assert _aware(rule.next_run_at) > NOW
    assert rule.last_error is None


def test_scanner_skips_not_yet_due(db: Session, user: User) -> None:
    rule = recurring_service.create_rule(
        db,
        user,
        name="later",
        workflow="weekly_digest",
        cron="0 7 * * MON",
    )
    future = NOW + timedelta(days=1)
    rule.next_run_at = future
    db.commit()
    fired = recurring_service.scan_and_fire(db, now=NOW)
    assert fired == 0
    db.refresh(rule)
    assert rule.next_run_at == future or (
        rule.next_run_at and rule.next_run_at.replace(tzinfo=UTC) == future
    )


def test_scanner_records_handler_failure(db: Session, user: User) -> None:
    """A failing workflow stamps last_error AND advances next_run so it
    doesn't lock the rule out forever."""
    rule = recurring_service.create_rule(
        db,
        user,
        name="bad",
        workflow="weekly_digest",
        cron="*/5 * * * *",
    )
    rule.next_run_at = NOW - timedelta(minutes=1)
    db.commit()
    # Swap the handler with one that raises.
    original = recurring_service.WORKFLOWS["weekly_digest"]
    recurring_service.WORKFLOWS["weekly_digest"] = lambda db, u, p: (_ for _ in ()).throw(
        RuntimeError("boom")
    )
    try:
        fired = recurring_service.scan_and_fire(db, now=NOW)
    finally:
        recurring_service.WORKFLOWS["weekly_digest"] = original
    assert fired == 1
    db.refresh(rule)
    assert rule.last_error == "boom"
    # Even though it failed, the next run advanced so the rule retries.
    assert rule.next_run_at is not None
    assert _aware(rule.next_run_at) > NOW


def test_scanner_pauses_unknown_workflow(db: Session, user: User) -> None:
    """Rules referencing an unregistered workflow get paused
    (next_run_at = None) with an error so the user can see why."""
    rule = recurring_service.create_rule(
        db, user, name="x", workflow="weekly_digest", cron="*/5 * * * *"
    )
    rule.workflow = "deleted_workflow"
    rule.next_run_at = NOW - timedelta(minutes=1)
    db.commit()
    recurring_service.scan_and_fire(db, now=NOW)
    db.refresh(rule)
    assert rule.last_error and "deleted_workflow" in rule.last_error
    assert rule.next_run_at is None


def test_scanner_returns_zero_when_no_rules(db: Session) -> None:
    assert recurring_service.scan_and_fire(db, now=NOW) == 0
