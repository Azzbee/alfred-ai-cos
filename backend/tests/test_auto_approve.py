"""Tests for AutoApprovePolicy + matching."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from app.db.enums import ActionStatus, ActionType, RiskLevel
from app.db.models import ActionProposal, User
from app.services import auto_approve

NOW = datetime(2026, 6, 7, 14, 0, tzinfo=UTC)  # 10:00 AM in New York


@pytest.fixture
def user(db: Session) -> User:
    u = User(email="adam@adam.dev", timezone="America/New_York")
    db.add(u)
    db.commit()
    return u


def _proposal(
    user_id: str,
    *,
    action_type: ActionType,
    risk: RiskLevel = RiskLevel.external_comm,
    target: dict | None = None,
    content: str | None = None,
) -> ActionProposal:
    return ActionProposal(
        user_id=user_id,
        action_type=action_type,
        risk_level=risk.value,
        target=target or {},
        proposed_content=content,
        approval_required=True,
        status=ActionStatus.proposed,
    )


# --- create / validate ---


def test_create_requires_counterparty(db: Session, user: User) -> None:
    with pytest.raises(ValueError):
        auto_approve.create_policy(db, user, action_type=ActionType.send_email)


def test_create_lowercases_email(db: Session, user: User) -> None:
    p = auto_approve.create_policy(
        db,
        user,
        action_type=ActionType.send_email,
        counterparty_email="Mary@Buyer.CO",
    )
    assert p.counterparty_email == "mary@buyer.co"


def test_create_financial_requires_max_cents(db: Session, user: User) -> None:
    with pytest.raises(ValueError):
        auto_approve.create_policy(
            db,
            user,
            action_type=ActionType.make_payment,
            counterparty_email="vendor@x.io",
        )


def test_create_financial_requires_specific_email(db: Session, user: User) -> None:
    """Domain-only auto-approval for money actions is rejected."""
    with pytest.raises(ValueError):
        auto_approve.create_policy(
            db,
            user,
            action_type=ActionType.make_payment,
            counterparty_domain="x.io",
            max_cents=5000,
        )


def test_create_validates_active_window(db: Session, user: User) -> None:
    with pytest.raises(ValueError):
        auto_approve.create_policy(
            db,
            user,
            action_type=ActionType.send_email,
            counterparty_email="x@y.co",
            active_window="garbage",
        )


# --- matching ---


def test_email_match_fires(db: Session, user: User) -> None:
    auto_approve.create_policy(
        db,
        user,
        action_type=ActionType.send_email,
        counterparty_email="mary@buyer.co",
    )
    proposal = _proposal(
        user.id,
        action_type=ActionType.send_email,
        target={"to": "Mary <mary@buyer.co>"},
    )
    db.add(proposal)
    db.commit()
    matched = auto_approve.find_matching(db, user, proposal, now=NOW)
    assert matched is not None


def test_domain_match_fires(db: Session, user: User) -> None:
    auto_approve.create_policy(
        db,
        user,
        action_type=ActionType.send_email,
        counterparty_domain="buyer.co",
    )
    proposal = _proposal(
        user.id,
        action_type=ActionType.send_email,
        target={"to": "alice@buyer.co"},
    )
    db.add(proposal)
    db.commit()
    assert auto_approve.find_matching(db, user, proposal, now=NOW) is not None


def test_no_match_when_email_differs(db: Session, user: User) -> None:
    auto_approve.create_policy(
        db,
        user,
        action_type=ActionType.send_email,
        counterparty_email="mary@buyer.co",
    )
    proposal = _proposal(
        user.id,
        action_type=ActionType.send_email,
        target={"to": "someone@else.io"},
    )
    db.add(proposal)
    db.commit()
    assert auto_approve.find_matching(db, user, proposal, now=NOW) is None


def test_no_match_when_action_type_differs(db: Session, user: User) -> None:
    auto_approve.create_policy(
        db,
        user,
        action_type=ActionType.create_task,
        counterparty_email="mary@buyer.co",
    )
    proposal = _proposal(
        user.id,
        action_type=ActionType.send_email,
        target={"to": "mary@buyer.co"},
    )
    db.add(proposal)
    db.commit()
    assert auto_approve.find_matching(db, user, proposal, now=NOW) is None


def test_financial_match_under_cap(db: Session, user: User) -> None:
    auto_approve.create_policy(
        db,
        user,
        action_type=ActionType.make_payment,
        counterparty_email="vendor@x.io",
        max_cents=5000,
    )
    proposal = _proposal(
        user.id,
        action_type=ActionType.make_payment,
        risk=RiskLevel.financial_legal,
        target={"to": "vendor@x.io", "amount_cents": 3000},
    )
    db.add(proposal)
    db.commit()
    assert auto_approve.find_matching(db, user, proposal, now=NOW) is not None


def test_financial_no_match_over_cap(db: Session, user: User) -> None:
    auto_approve.create_policy(
        db,
        user,
        action_type=ActionType.make_payment,
        counterparty_email="vendor@x.io",
        max_cents=5000,
    )
    proposal = _proposal(
        user.id,
        action_type=ActionType.make_payment,
        risk=RiskLevel.financial_legal,
        target={"to": "vendor@x.io", "amount_cents": 8000},
    )
    db.add(proposal)
    db.commit()
    assert auto_approve.find_matching(db, user, proposal, now=NOW) is None


def test_content_substring_required(db: Session, user: User) -> None:
    auto_approve.create_policy(
        db,
        user,
        action_type=ActionType.send_email,
        counterparty_email="mary@buyer.co",
        content_substring="monthly invoice",
    )
    # Match: content contains the substring.
    p1 = _proposal(
        user.id,
        action_type=ActionType.send_email,
        target={"to": "mary@buyer.co"},
        content="Here's the monthly invoice for June.",
    )
    db.add(p1)
    # No match: content doesn't contain the substring.
    p2 = _proposal(
        user.id,
        action_type=ActionType.send_email,
        target={"to": "mary@buyer.co"},
        content="Just confirming.",
    )
    db.add(p2)
    db.commit()
    assert auto_approve.find_matching(db, user, p1, now=NOW) is not None
    assert auto_approve.find_matching(db, user, p2, now=NOW) is None


def test_active_window_blocks_off_hours(db: Session, user: User) -> None:
    auto_approve.create_policy(
        db,
        user,
        action_type=ActionType.send_email,
        counterparty_email="mary@buyer.co",
        active_window="09:00-17:00",
    )
    proposal = _proposal(
        user.id,
        action_type=ActionType.send_email,
        target={"to": "mary@buyer.co"},
    )
    db.add(proposal)
    db.commit()
    # 10:00 NY local (in window) — fires.
    in_window = datetime(2026, 6, 7, 14, 0, tzinfo=UTC)
    assert auto_approve.find_matching(db, user, proposal, now=in_window) is not None
    # 03:00 NY local (out of window) — doesn't fire.
    out_window = datetime(2026, 6, 7, 7, 0, tzinfo=UTC)  # 3 AM in NY
    assert auto_approve.find_matching(db, user, proposal, now=out_window) is None


def test_disabled_policy_does_not_match(db: Session, user: User) -> None:
    policy = auto_approve.create_policy(
        db,
        user,
        action_type=ActionType.send_email,
        counterparty_email="mary@buyer.co",
    )
    auto_approve.set_enabled(db, policy, enabled=False)
    proposal = _proposal(
        user.id,
        action_type=ActionType.send_email,
        target={"to": "mary@buyer.co"},
    )
    db.add(proposal)
    db.commit()
    assert auto_approve.find_matching(db, user, proposal, now=NOW) is None


def test_record_fire_increments_counter(db: Session, user: User) -> None:
    policy = auto_approve.create_policy(
        db,
        user,
        action_type=ActionType.send_email,
        counterparty_email="mary@buyer.co",
    )
    assert policy.fire_count == 0
    auto_approve.record_fire(db, policy)
    auto_approve.record_fire(db, policy)
    assert policy.fire_count == 2


def test_cross_user_isolation(db: Session) -> None:
    a = User(email="a@x.io", timezone="UTC")
    b = User(email="b@x.io", timezone="UTC")
    db.add_all([a, b])
    db.commit()
    auto_approve.create_policy(
        db,
        a,
        action_type=ActionType.send_email,
        counterparty_email="mary@buyer.co",
    )
    proposal = _proposal(
        b.id,
        action_type=ActionType.send_email,
        target={"to": "mary@buyer.co"},
    )
    db.add(proposal)
    db.commit()
    # Policy belongs to A; B's proposal must NOT match.
    assert auto_approve.find_matching(db, b, proposal, now=NOW) is None
