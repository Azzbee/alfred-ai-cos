"""Tests for the Memory Agent (PRD 14.1 agent 7).

Covers tone learning, the preferred-tone lookup that draft generation
consults, and the organization helper."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.db.models import Message, Person, User
from app.services import memory
from app.services import people as people_service

NOW = datetime(2026, 6, 7, 12, 0, tzinfo=UTC)


@pytest.fixture
def user(db: Session) -> User:
    u = User(email="adam@adam.dev")
    db.add(u)
    db.commit()
    return u


def _seed_person(db: Session, user: User, email: str, name: str = "") -> Person:
    msg = Message(
        user_id=user.id,
        external_id=f"seed-{email}",
        sender=f"{name} <{email}>" if name else email,
        recipients=["adam@adam.dev"],
        subject="hi",
        snippet="hi",
        sent_at=NOW - timedelta(days=1),
        sender_classification="person",
    )
    db.add(msg)
    db.commit()
    person = people_service.upsert_from_message(db, user, msg)
    assert person is not None
    return person


# --- record_tone ---


def test_record_tone_creates_counts(db: Session, user: User) -> None:
    _seed_person(db, user, "mary@buyer.co", name="Mary")
    person = memory.record_tone(db, user, recipient_email="mary@buyer.co", tone="warm")
    assert person is not None
    assert person.learned_tone == {"warm": 1}


def test_record_tone_accumulates(db: Session, user: User) -> None:
    _seed_person(db, user, "mary@buyer.co", name="Mary")
    for _ in range(3):
        memory.record_tone(db, user, recipient_email="mary@buyer.co", tone="formal")
    memory.record_tone(db, user, recipient_email="mary@buyer.co", tone="warm")
    person = db.query(Person).filter(Person.email_lower == "mary@buyer.co").one()
    assert person.learned_tone == {"formal": 3, "warm": 1}


def test_record_tone_ignores_invalid_tone(db: Session, user: User) -> None:
    _seed_person(db, user, "mary@buyer.co")
    assert memory.record_tone(db, user, recipient_email="mary@buyer.co", tone="zany") is None


def test_record_tone_returns_none_for_unknown_recipient(db: Session, user: User) -> None:
    # No Person row exists for this address — tone vote is silently dropped.
    assert memory.record_tone(db, user, recipient_email="ghost@nope.io", tone="warm") is None


def test_record_tone_caps_growth(db: Session, user: User) -> None:
    _seed_person(db, user, "vip@board.co")
    for _ in range(50):
        memory.record_tone(db, user, recipient_email="vip@board.co", tone="formal")
    person = db.query(Person).filter(Person.email_lower == "vip@board.co").one()
    # Cap at 20 — preference is sticky but not infinite.
    assert person.learned_tone["formal"] == 20


# --- preferred_tone ---


def test_preferred_tone_returns_default_when_no_signal(db: Session, user: User) -> None:
    _seed_person(db, user, "mary@buyer.co")
    assert memory.preferred_tone(db, user, recipient_email="mary@buyer.co") == "concise"


def test_preferred_tone_uses_top_count(db: Session, user: User) -> None:
    _seed_person(db, user, "mary@buyer.co")
    memory.record_tone(db, user, recipient_email="mary@buyer.co", tone="warm")
    memory.record_tone(db, user, recipient_email="mary@buyer.co", tone="warm")
    memory.record_tone(db, user, recipient_email="mary@buyer.co", tone="formal")
    assert memory.preferred_tone(db, user, recipient_email="mary@buyer.co") == "warm"


def test_preferred_tone_falls_back_for_unknown_recipient(db: Session, user: User) -> None:
    assert memory.preferred_tone(db, user, recipient_email="ghost@nope.io") == "concise"


def test_preferred_tone_no_email_returns_default(db: Session, user: User) -> None:
    assert memory.preferred_tone(db, user, recipient_email=None) == "concise"


# --- organization_for ---


def test_organization_lookup(db: Session, user: User) -> None:
    _seed_person(db, user, "mary@buyer.co")
    assert memory.organization_for(db, user, email="mary@buyer.co") == "buyer.co"


def test_organization_returns_none_for_free_mail(db: Session, user: User) -> None:
    _seed_person(db, user, "bob@gmail.com")
    # bob exists, but his org is None because gmail.com is free-mail.
    assert memory.organization_for(db, user, email="bob@gmail.com") is None
