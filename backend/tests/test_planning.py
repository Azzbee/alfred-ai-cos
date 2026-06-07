"""Tests for the Planning Agent (PRD 14.1 agent 4)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.orm import Session

from app.db.enums import CommitmentOwner, CommitmentStatus, Priority, SourceType
from app.db.models import CalendarEvent, Commitment, Message, User
from app.services import planning

# Planning a fixed date in NY so we can reason concretely about block times.
PLAN_DATE = date(2026, 6, 8)  # Monday
TZ = "America/New_York"


def _ny(h: int, m: int = 0) -> datetime:
    """Build a NY-local datetime on PLAN_DATE."""
    return datetime(2026, 6, 8, h, m, tzinfo=ZoneInfo(TZ))


def _utc(local: datetime) -> datetime:
    """Convert a local datetime to UTC for storage."""
    return local.astimezone(UTC)


@pytest.fixture
def user(db: Session) -> User:
    u = User(email="adam@adam.dev", timezone=TZ, preferences={})
    db.add(u)
    db.commit()
    return u


def _event(
    user_id: str,
    *,
    start_local: datetime,
    end_local: datetime,
    title: str = "Meeting",
    prep: bool = False,
    ext: str = "e",
) -> CalendarEvent:
    return CalendarEvent(
        user_id=user_id,
        external_id=ext,
        title=title,
        start_time=_utc(start_local),
        end_time=_utc(end_local),
        prep_required=prep,
    )


def _msg(user_id: str, ext: str = "m") -> Message:
    return Message(
        user_id=user_id,
        external_id=ext,
        sender="someone@buyer.co",
        recipients=["adam@adam.dev"],
        subject="hi",
        snippet="hi",
        sent_at=datetime(2026, 6, 7, tzinfo=UTC),
        sender_classification="person",
    )


def _commit(
    user_id: str,
    *,
    description: str,
    priority: Priority = Priority.medium,
    owner: CommitmentOwner = CommitmentOwner.user,
    due: date | None = None,
    source_id: str | None = None,
) -> Commitment:
    return Commitment(
        user_id=user_id,
        description=description,
        evidence=description,
        owner=owner,
        counterparty="Mary",
        due_date=due,
        priority=priority,
        status=CommitmentStatus.open,
        source_type=SourceType.gmail,
        source_id=source_id,
        confidence=0.9,
    )


# --- empty-day baseline ---


def test_empty_day_is_a_single_gap(db: Session, user: User) -> None:
    plan = planning.build_plan(db, user, plan_date=PLAN_DATE)
    assert plan.plan_date == PLAN_DATE
    # No commitments, no events → no blocks scheduled.
    assert plan.blocks == []
    assert plan.summary == "Your day is clear."


# --- calendar respect ---


def test_calendar_events_become_calendar_blocks(db: Session, user: User) -> None:
    db.add(
        _event(
            user.id,
            start_local=_ny(10),
            end_local=_ny(11),
            title="Team standup",
            ext="e1",
        )
    )
    db.commit()
    plan = planning.build_plan(db, user, plan_date=PLAN_DATE)
    cal = [b for b in plan.blocks if b.kind == "calendar"]
    assert len(cal) == 1
    assert cal[0].title == "Team standup"


def test_calendar_blocks_outside_working_hours_are_clipped(db: Session, user: User) -> None:
    # Event 8:00-09:30 — clipped to 09:00 day start.
    db.add(
        _event(
            user.id,
            start_local=_ny(8),
            end_local=_ny(9, 30),
            ext="e1",
        )
    )
    db.commit()
    plan = planning.build_plan(db, user, plan_date=PLAN_DATE)
    cal = [b for b in plan.blocks if b.kind == "calendar"]
    assert len(cal) == 1
    assert cal[0].start.hour == 9
    assert cal[0].start.minute == 0


# --- meeting-prep blocks ---


def test_meeting_prep_block_inserted_before_prep_required_event(db: Session, user: User) -> None:
    db.add(
        _event(
            user.id,
            start_local=_ny(14),
            end_local=_ny(15),
            title="Quarterly with Mary",
            prep=True,
            ext="e1",
        )
    )
    db.commit()
    plan = planning.build_plan(db, user, plan_date=PLAN_DATE)
    prep = [b for b in plan.blocks if b.kind == "meeting_prep"]
    assert len(prep) == 1
    assert prep[0].end == _ny(14)
    assert prep[0].end - prep[0].start == timedelta(minutes=15)


def test_meeting_prep_skipped_when_back_to_back(db: Session, user: User) -> None:
    # Two events back-to-back; second needs prep but there's no room.
    db.add(_event(user.id, start_local=_ny(13), end_local=_ny(14), ext="e1"))
    db.add(
        _event(
            user.id,
            start_local=_ny(14),
            end_local=_ny(15),
            prep=True,
            ext="e2",
        )
    )
    db.commit()
    plan = planning.build_plan(db, user, plan_date=PLAN_DATE)
    prep = [b for b in plan.blocks if b.kind == "meeting_prep"]
    assert prep == []


# --- focus blocks ---


def test_critical_user_owed_commit_becomes_focus_block(db: Session, user: User) -> None:
    msg = _msg(user.id, ext="src")
    db.add(msg)
    db.commit()
    db.add(
        _commit(
            user.id,
            description="Sign the contract today",
            priority=Priority.critical,
            owner=CommitmentOwner.user,
            due=PLAN_DATE,
            source_id=msg.id,
        )
    )
    db.commit()
    plan = planning.build_plan(db, user, plan_date=PLAN_DATE)
    focus = [b for b in plan.blocks if b.kind == "focus"]
    assert len(focus) == 1
    assert focus[0].end - focus[0].start >= timedelta(minutes=45)


def test_focus_block_caps_at_max_duration(db: Session, user: User) -> None:
    msg = _msg(user.id, ext="src")
    db.add(msg)
    db.commit()
    db.add(
        _commit(
            user.id,
            description="Big work item",
            priority=Priority.critical,
            owner=CommitmentOwner.user,
            due=PLAN_DATE,
            source_id=msg.id,
        )
    )
    db.commit()
    plan = planning.build_plan(db, user, plan_date=PLAN_DATE)
    focus = [b for b in plan.blocks if b.kind == "focus"]
    assert len(focus) == 1
    assert focus[0].end - focus[0].start <= timedelta(minutes=90)


# --- comms + quick wins ---


def test_email_sourced_medium_commits_become_comms(db: Session, user: User) -> None:
    msg = _msg(user.id, ext="src")
    db.add(msg)
    db.commit()
    # A due-this-week deadline lifts these into the medium bucket (not high
    # enough for focus), where the planner batches them as a comms block.
    for i in range(3):
        db.add(
            _commit(
                user.id,
                description=f"Reply to thread {i}",
                priority=Priority.medium,
                owner=CommitmentOwner.user,
                due=PLAN_DATE + timedelta(days=2),
                source_id=msg.id,
            )
        )
    db.commit()
    plan = planning.build_plan(db, user, plan_date=PLAN_DATE)
    comms = [b for b in plan.blocks if b.kind == "comms"]
    assert len(comms) == 1
    assert len(comms[0].item_ids) >= 1


def test_low_priority_items_become_quick_wins(db: Session, user: User) -> None:
    for i in range(3):
        db.add(
            _commit(
                user.id,
                description=f"Trivial task {i}",
                priority=Priority.low,
                owner=CommitmentOwner.user,
            )
        )
    db.commit()
    plan = planning.build_plan(db, user, plan_date=PLAN_DATE)
    qw = [b for b in plan.blocks if b.kind == "quick_wins"]
    assert len(qw) == 1
    assert len(qw[0].item_ids) >= 1


def test_counterparty_owed_items_become_quick_wins_not_focus(db: Session, user: User) -> None:
    """'You are waiting on Mary' isn't a focus block — nothing for the
    user to do. It belongs in quick wins (a sweep)."""
    msg = _msg(user.id, ext="src")
    db.add(msg)
    db.commit()
    db.add(
        _commit(
            user.id,
            description="Waiting on Mary's revision",
            priority=Priority.high,
            owner=CommitmentOwner.counterparty,
            source_id=msg.id,
        )
    )
    db.commit()
    plan = planning.build_plan(db, user, plan_date=PLAN_DATE)
    focus = [b for b in plan.blocks if b.kind == "focus"]
    qw = [b for b in plan.blocks if b.kind == "quick_wins"]
    assert focus == []
    assert len(qw) == 1


# --- break insertion ---


def test_break_inserted_after_focus_block(db: Session, user: User) -> None:
    msg = _msg(user.id, ext="src")
    db.add(msg)
    db.commit()
    db.add(
        _commit(
            user.id,
            description="Deep work",
            priority=Priority.critical,
            owner=CommitmentOwner.user,
            due=PLAN_DATE,
            source_id=msg.id,
        )
    )
    db.commit()
    plan = planning.build_plan(db, user, plan_date=PLAN_DATE)
    break_blocks = [b for b in plan.blocks if b.kind == "break"]
    # With a 9-hour empty day there's plenty of room for a break.
    assert len(break_blocks) >= 1


# --- working-hours override ---


def test_user_working_hours_override(db: Session, user: User) -> None:
    user.preferences = {"working_hours": "07:00-12:00"}
    db.add(user)
    db.commit()
    msg = _msg(user.id, ext="src")
    db.add(msg)
    db.commit()
    db.add(
        _commit(
            user.id,
            description="Morning person",
            priority=Priority.critical,
            owner=CommitmentOwner.user,
            due=PLAN_DATE,
            source_id=msg.id,
        )
    )
    db.commit()
    plan = planning.build_plan(db, user, plan_date=PLAN_DATE)
    # Earliest focus block should start at or after 07:00 local.
    focus = [b for b in plan.blocks if b.kind == "focus"]
    assert focus[0].start.hour >= 7
    # And the day ends at noon.
    last = max(plan.blocks, key=lambda b: b.end)
    assert last.end.hour <= 12


# --- summary ---


def test_summary_is_non_empty_when_blocks_exist(db: Session, user: User) -> None:
    db.add(_event(user.id, start_local=_ny(10), end_local=_ny(11), ext="e1"))
    db.commit()
    plan = planning.build_plan(db, user, plan_date=PLAN_DATE)
    assert "1 meeting" in plan.summary


# --- timezone correctness ---


def test_plan_respects_user_timezone(db: Session, user: User) -> None:
    """A 10:00 NY event should produce a block whose `start.hour == 10`
    when read in NY time. We store events in UTC; the planner converts
    them to local for the user."""
    db.add(_event(user.id, start_local=_ny(10), end_local=_ny(11), ext="e1"))
    db.commit()
    plan = planning.build_plan(db, user, plan_date=PLAN_DATE)
    cal = [b for b in plan.blocks if b.kind == "calendar"][0]
    # Convert plan block back to NY local for the comparison.
    cal_start_ny = cal.start.astimezone(ZoneInfo(TZ))
    assert cal_start_ny.hour == 10


# --- gap planning ---


def test_no_focus_in_too_small_gap(db: Session, user: User) -> None:
    """The 20-min gap between two back-to-back events must not host a focus
    block (focus blocks need 45 min). The focus block ends up in the
    afternoon gap instead."""
    # Pack the morning: 9-11 + 11:20-12 + 13-18 leaves only the 11→11:20
    # and 12→13 gaps.
    db.add(_event(user.id, start_local=_ny(9), end_local=_ny(11), ext="e0"))
    db.add(_event(user.id, start_local=_ny(11, 20), end_local=_ny(12), ext="e1"))
    db.add(_event(user.id, start_local=_ny(13), end_local=_ny(18), ext="e2"))
    msg = _msg(user.id, ext="src")
    db.add(msg)
    db.commit()
    db.add(
        _commit(
            user.id,
            description="Focus work",
            priority=Priority.critical,
            owner=CommitmentOwner.user,
            due=PLAN_DATE,
            source_id=msg.id,
        )
    )
    db.commit()
    plan = planning.build_plan(db, user, plan_date=PLAN_DATE)
    focus = [b for b in plan.blocks if b.kind == "focus"]
    # The only gap that fits a 45-min focus is the 12-13 lunch window.
    assert len(focus) == 1
    assert focus[0].start.hour == 12
