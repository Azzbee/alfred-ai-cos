"""Notification decision logic + scan/dedup tests. Logic functions are pure;
scan/enqueue run against SQLite."""

from datetime import UTC, date, datetime, time, timedelta

import pytest
from sqlalchemy.orm import Session

from app.db.enums import (
    ActionStatus,
    ActionType,
    CommitmentOwner,
    CommitmentStatus,
    NotificationImportance,
    NotificationType,
    SourceType,
)
from app.db.models import ActionProposal, Commitment, Notification, User
from app.services import notifications as n


def _proposal(
    user_id: str, *, created_at: datetime, approval_required: bool = True
) -> ActionProposal:
    return ActionProposal(
        user_id=user_id,
        action_type=ActionType.send_email,
        risk_level=3,
        target={"draft_reply_id": "x"},
        reason="Send a reply",
        approval_required=approval_required,
        status=ActionStatus.proposed,
        created_at=created_at,
    )


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


# --- approval push: only fires once the grace window has passed ---


def test_pending_approval_within_grace_does_not_push(db: Session, user: User) -> None:
    now = datetime(2026, 6, 2, 12, 0, tzinfo=UTC)
    # 30s old: well inside the 2-min grace window — the user just hit Send, no push.
    db.add(_proposal(user.id, created_at=now - timedelta(seconds=30)))
    db.commit()
    assert n.scan_pending_approvals(db, user.id, now=now) == 0
    assert db.query(Notification).count() == 0


def test_pending_approval_past_grace_enqueues(db: Session, user: User) -> None:
    now = datetime(2026, 6, 2, 12, 0, tzinfo=UTC)
    db.add(_proposal(user.id, created_at=now - timedelta(minutes=5)))
    db.commit()
    assert n.scan_pending_approvals(db, user.id, now=now) == 1
    notif = db.query(Notification).one()
    assert notif.type == NotificationType.approval_needed
    assert notif.payload["deep_link"] == "/approvals"
    assert notif.payload["action_id"]


def test_pending_approval_is_deduped(db: Session, user: User) -> None:
    now = datetime(2026, 6, 2, 12, 0, tzinfo=UTC)
    db.add(_proposal(user.id, created_at=now - timedelta(minutes=5)))
    db.commit()
    n.scan_pending_approvals(db, user.id, now=now)
    n.scan_pending_approvals(db, user.id, now=now + timedelta(minutes=30))
    assert db.query(Notification).count() == 1


def test_pending_approval_skipped_when_not_required(db: Session, user: User) -> None:
    # Auto-approved proposals (level 1-2 with no approval requirement) never push.
    now = datetime(2026, 6, 2, 12, 0, tzinfo=UTC)
    db.add(_proposal(user.id, created_at=now - timedelta(minutes=10), approval_required=False))
    db.commit()
    assert n.scan_pending_approvals(db, user.id, now=now) == 0
