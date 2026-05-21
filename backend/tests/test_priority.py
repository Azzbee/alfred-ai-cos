"""Tests for the priority engine. Pure logic, no DB or network."""

from datetime import date, timedelta

from app.db.enums import CommitmentOwner, Priority
from app.db.models import Commitment
from app.services.priority import score_commitment

TODAY = date(2026, 5, 21)


def _commitment(**kwargs) -> Commitment:
    defaults = dict(
        user_id="u1",
        description="Send the signed document",
        owner=CommitmentOwner.user,
        counterparty="Celine",
        due_date=TODAY,
        confidence=0.9,
    )
    defaults.update(kwargs)
    return Commitment(**defaults)


def test_due_today_owed_by_user_is_high_or_critical() -> None:
    scored = score_commitment(_commitment(), today=TODAY)
    assert scored.priority in (Priority.high, Priority.critical)
    assert "due today" in scored.reason
    assert "Celine is waiting on you" in scored.reason


def test_overdue_outranks_future() -> None:
    overdue = score_commitment(
        _commitment(due_date=TODAY - timedelta(days=2)), today=TODAY
    )
    future = score_commitment(
        _commitment(due_date=TODAY + timedelta(days=10)), today=TODAY
    )
    assert overdue.score > future.score
    assert "overdue by 2 day(s)" in overdue.reason


def test_low_confidence_is_flagged_and_dampened() -> None:
    high_conf = score_commitment(_commitment(confidence=0.95), today=TODAY)
    low_conf = score_commitment(_commitment(confidence=0.3), today=TODAY)
    assert low_conf.score < high_conf.score
    assert "low confidence" in low_conf.reason


def test_waiting_on_someone_else_is_lower_priority() -> None:
    user_owes = score_commitment(_commitment(owner=CommitmentOwner.user), today=TODAY)
    other_owes = score_commitment(
        _commitment(owner=CommitmentOwner.counterparty), today=TODAY
    )
    assert user_owes.score > other_owes.score
    assert "you are waiting on Celine" in other_owes.reason


def test_no_due_date_no_urgency() -> None:
    scored = score_commitment(
        _commitment(due_date=None, counterparty=None), today=TODAY
    )
    assert scored.priority in (Priority.low, Priority.medium, Priority.noise)
