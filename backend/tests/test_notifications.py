"""Notification decision logic + scan/dedup tests. Logic functions are pure;
scan/enqueue run against SQLite."""

from datetime import date, time, timedelta

import pytest
from sqlalchemy.orm import Session

from app.db.enums import (
    CommitmentOwner,
    CommitmentStatus,
    NotificationImportance,
    NotificationType,
    SourceType,
)
from app.db.models import Commitment, Notification, User
from app.services import notifications as n

# --- pure logic: quiet hours ---


def test_quiet_hours_simple_window() -> None:
    quiet = n._parse_quiet_hours("22-07")
    assert n.in_quiet_hours(time(23, 0), quiet) is True  # crosses midnight
    assert n.in_quiet_hours(time(3, 0), quiet) is True
    assert n.in_quiet_hours(time(12, 0), quiet) is False


def test_quiet_hours_same_day_window() -> None:
    quiet = n._parse_quiet_hours("09:00-17:00")
    assert n.in_quiet_hours(time(12, 0), quiet) is True
    assert n.in_quiet_hours(time(20, 0), quiet) is False


def test_quiet_hours_malformed_is_none() -> None:
    assert n._parse_quiet_hours("nonsense") is None
    assert n._parse_quiet_hours(None) is None
    assert n.in_quiet_hours(time(3, 0), None) is False


# --- pure logic: delivery decision ---


def test_below_threshold_is_batched() -> None:
    # "quiet" proactiveness only sends high importance; a low briefing is batched.
    d = n.decide_delivery(
        ntype=NotificationType.daily_briefing,
        now=time(12, 0),
        proactiveness="quiet",
        quiet_hours_raw=None,
    )
    assert d.send_now is False


def test_high_importance_overrides_quiet_hours() -> None:
    d = n.decide_delivery(
        ntype=NotificationType.deadline_risk,
        now=time(23, 0),
        proactiveness="balanced",
        quiet_hours_raw="22-07",
    )
    assert d.send_now is True
    assert "overrides quiet hours" in d.reason


def test_normal_importance_held_during_quiet_hours() -> None:
    d = n.decide_delivery(
        ntype=NotificationType.meeting_prep,
        now=time(23, 0),
        proactiveness="balanced",
        quiet_hours_raw="22-07",
    )
    assert d.send_now is False
    assert "quiet hours" in d.reason


def test_very_proactive_sends_low_importance_when_awake() -> None:
    d = n.decide_delivery(
        ntype=NotificationType.daily_briefing,
        now=time(8, 0),
        proactiveness="very_proactive",
        quiet_hours_raw="22-07",
    )
    assert d.send_now is True


def test_importance_table() -> None:
    assert n.importance_of(NotificationType.approval_needed) == NotificationImportance.high
    assert n.importance_of(NotificationType.daily_briefing) == NotificationImportance.low


# --- scan + dedup against the DB ---


@pytest.fixture
def user(db: Session) -> User:
    u = User(email="notif@example.com")
    db.add(u)
    db.commit()
    return u


def _commitment(user_id: str, due: date) -> Commitment:
    return Commitment(
        user_id=user_id,
        description="Send the signed contract",
        owner=CommitmentOwner.user,
        counterparty="Dana",
        due_date=due,
        status=CommitmentStatus.open,
        source_type=SourceType.gmail,
        confidence=0.9,
    )


def test_scan_enqueues_for_due_soon(db: Session, user: User) -> None:
    today = date(2026, 5, 21)
    db.add(_commitment(user.id, today))  # due today
    db.commit()
    count = n.scan_for_risks(db, user.id, today=today)
    assert count == 1
    assert db.query(Notification).count() == 1


def test_scan_is_deduped(db: Session, user: User) -> None:
    today = date(2026, 5, 21)
    db.add(_commitment(user.id, today))
    db.commit()
    n.scan_for_risks(db, user.id, today=today)
    n.scan_for_risks(db, user.id, today=today)  # rescan
    assert db.query(Notification).count() == 1  # not duplicated


def test_scan_ignores_far_off(db: Session, user: User) -> None:
    today = date(2026, 5, 21)
    db.add(_commitment(user.id, today + timedelta(days=10)))
    db.commit()
    assert n.scan_for_risks(db, user.id, today=today) == 0


def test_enqueue_dedup_returns_none(db: Session, user: User) -> None:
    first = n.enqueue(
        db, user.id, ntype=NotificationType.reminder, title="t", body="b", dedup_key="k"
    )
    second = n.enqueue(
        db, user.id, ntype=NotificationType.reminder, title="t", body="b", dedup_key="k"
    )
    assert first is not None
    assert second is None


# --- dispatch end to end with a fake provider + a registered device ---


def test_dispatch_sends_high_and_holds_low(db: Session, user: User) -> None:
    from app.db.models import Device, Notification
    from tests.fakes import FakeNotifier

    db.add(Device(user_id=user.id, push_token="ExpoTok", platform="ios"))
    user.preferences = {"proactiveness": "quiet"}  # only high importance sends
    db.add(
        Notification(
            user_id=user.id,
            type=NotificationType.deadline_risk,
            title="urgent",
            body="due today",
        )
    )
    db.add(
        Notification(
            user_id=user.id,
            type=NotificationType.daily_briefing,
            title="brief",
            body="morning",
        )
    )
    db.commit()

    notifier = FakeNotifier()
    result = n.dispatch_pending(db, user, now=time(12, 0), provider=notifier)
    assert result == {"sent": 1, "held": 1}
    assert len(notifier.sent) == 1
    assert notifier.sent[0]["title"] == "urgent"
