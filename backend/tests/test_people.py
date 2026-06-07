"""Tests for the Person entity and the people service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.db.enums import CommitmentOwner, CommitmentStatus, RelationshipType, SourceType
from app.db.models import Commitment, Message, Person, User
from app.services import people as people_service

NOW = datetime(2026, 6, 7, 12, 0, tzinfo=UTC)


@pytest.fixture
def user(db: Session) -> User:
    u = User(email="adam@adam.dev")
    db.add(u)
    db.commit()
    return u


def _msg(
    user_id: str,
    *,
    sender: str,
    recipients: list[str] | None = None,
    ext: str = "m1",
    sent_at: datetime | None = None,
    classification: str | None = "person",
) -> Message:
    return Message(
        user_id=user_id,
        external_id=ext,
        sender=sender,
        recipients=recipients or ["adam@adam.dev"],
        subject="hi",
        snippet="hi",
        sent_at=sent_at or NOW - timedelta(days=1),
        sender_classification=classification,
    )


def _commit(user_id: str, *, counterparty: str | None) -> Commitment:
    return Commitment(
        user_id=user_id,
        description="Reply to them",
        owner=CommitmentOwner.user,
        counterparty=counterparty,
        status=CommitmentStatus.open,
        source_type=SourceType.gmail,
        confidence=0.9,
    )


# --- get_or_create ---


def test_creates_person_on_first_email(db: Session, user: User) -> None:
    msg = _msg(user.id, sender="Mary <mary@buyer.co>")
    db.add(msg)
    db.commit()
    person = people_service.upsert_from_message(db, user, msg)
    assert person is not None
    assert person.email_lower == "mary@buyer.co"
    assert person.name == "Mary"
    assert person.organization == "buyer.co"


def test_idempotent_on_second_email(db: Session, user: User) -> None:
    msg1 = _msg(user.id, sender="Mary <mary@buyer.co>", ext="m1")
    msg2 = _msg(user.id, sender="Mary <mary@buyer.co>", ext="m2")
    db.add_all([msg1, msg2])
    db.commit()
    p1 = people_service.upsert_from_message(db, user, msg1)
    p2 = people_service.upsert_from_message(db, user, msg2)
    assert p1 is not None and p2 is not None
    assert p1.id == p2.id
    assert db.query(Person).count() == 1


def test_inbound_count_bumps_per_message(db: Session, user: User) -> None:
    for i in range(3):
        msg = _msg(user.id, sender="Mary <mary@buyer.co>", ext=f"m{i}")
        db.add(msg)
        db.commit()
        people_service.upsert_from_message(db, user, msg)
    person = db.query(Person).one()
    assert person.inbound_count == 3
    assert person.outbound_count == 0


def test_outbound_when_user_is_sender(db: Session, user: User) -> None:
    out = _msg(
        user.id,
        sender="adam@adam.dev",
        recipients=["mary@buyer.co"],
        ext="out",
    )
    db.add(out)
    db.commit()
    people_service.upsert_from_message(db, user, out)
    # The user-self person exists AND Mary received a bump.
    self_person = db.query(Person).filter(Person.email_lower == "adam@adam.dev").one()
    assert self_person.relationship_type == RelationshipType.self_
    assert self_person.relationship_locked is True
    mary = db.query(Person).filter(Person.email_lower == "mary@buyer.co").one()
    assert mary.outbound_count == 1
    assert mary.inbound_count == 0


def test_free_mail_skips_organization(db: Session, user: User) -> None:
    msg = _msg(user.id, sender="Bob <bob@gmail.com>")
    db.add(msg)
    db.commit()
    person = people_service.upsert_from_message(db, user, msg)
    assert person is not None
    assert person.organization is None


def test_classifier_carries_to_relationship(db: Session, user: User) -> None:
    msg = _msg(user.id, sender="newsletter@brand.io", classification="automated")
    db.add(msg)
    db.commit()
    person = people_service.upsert_from_message(db, user, msg)
    assert person is not None
    assert person.relationship_type == RelationshipType.automated


# --- relationship inference ---


def test_same_corporate_domain_is_colleague(db: Session) -> None:
    # User at a corporate domain — same domain person → colleague.
    user = User(email="adam@stratco.com")
    db.add(user)
    db.commit()
    msg = _msg(user.id, sender="Mary <mary@stratco.com>")
    db.add(msg)
    db.commit()
    person = people_service.upsert_from_message(db, user, msg)
    assert person is not None
    assert person.relationship_type == RelationshipType.colleague


def test_balanced_exchange_becomes_client(db: Session, user: User) -> None:
    # 3 inbound from mary + 3 outbound from user to mary.
    for i in range(3):
        inbound = _msg(user.id, sender="Mary <mary@buyer.co>", ext=f"in{i}")
        db.add(inbound)
        db.commit()
        people_service.upsert_from_message(db, user, inbound)
    for i in range(3):
        outbound = _msg(
            user.id,
            sender="adam@adam.dev",
            recipients=["mary@buyer.co"],
            ext=f"out{i}",
        )
        db.add(outbound)
        db.commit()
        people_service.upsert_from_message(db, user, outbound)
    person = db.query(Person).filter(Person.email_lower == "mary@buyer.co").one()
    assert person.relationship_type == RelationshipType.client


def test_one_way_traffic_becomes_vendor(db: Session, user: User) -> None:
    # 5 inbound, 0 outbound, real org domain → vendor.
    for i in range(5):
        msg = _msg(user.id, sender="Sales <sales@vendor.co>", ext=f"m{i}")
        db.add(msg)
        db.commit()
        people_service.upsert_from_message(db, user, msg)
    person = db.query(Person).filter(Person.email_lower == "sales@vendor.co").one()
    assert person.relationship_type == RelationshipType.vendor


def test_user_override_locks_relationship(db: Session, user: User) -> None:
    msg = _msg(user.id, sender="Cat <cat@buyer.co>")
    db.add(msg)
    db.commit()
    person = people_service.upsert_from_message(db, user, msg)
    assert person is not None
    people_service.set_relationship(db, person, relationship=RelationshipType.friend)
    # Now run a bunch more inbounds — heuristic must not override the lock.
    for i in range(8):
        m = _msg(user.id, sender="Cat <cat@buyer.co>", ext=f"more{i}")
        db.add(m)
        db.commit()
        people_service.upsert_from_message(db, user, m)
    db.refresh(person)
    assert person.relationship_type == RelationshipType.friend


# --- commitment linking ---


def test_link_commitment_finds_person(db: Session, user: User) -> None:
    # Seed person first.
    seed = _msg(user.id, sender="Mary <mary@buyer.co>")
    db.add(seed)
    db.commit()
    people_service.upsert_from_message(db, user, seed)
    # Commitment with the same counterparty.
    c = _commit(user.id, counterparty="Mary Smith <mary@buyer.co>")
    db.add(c)
    db.commit()
    linked = people_service.link_commitment(db, user, c)
    assert linked is not None
    assert c.counterparty_person_id == linked.id


def test_link_commitment_creates_person_if_missing(db: Session, user: User) -> None:
    c = _commit(user.id, counterparty="Stranger <stranger@new.co>")
    db.add(c)
    db.commit()
    linked = people_service.link_commitment(db, user, c)
    assert linked is not None
    assert c.counterparty_person_id == linked.id


def test_link_commitment_handles_string_counterparty_without_email(db: Session, user: User) -> None:
    c = _commit(user.id, counterparty="someone we met")  # no email
    db.add(c)
    db.commit()
    assert people_service.link_commitment(db, user, c) is None


# --- importance updates ---


def test_adjust_importance_bounded(db: Session, user: User) -> None:
    msg = _msg(user.id, sender="VIP <vip@board.co>")
    db.add(msg)
    db.commit()
    person = people_service.upsert_from_message(db, user, msg)
    assert person is not None
    for _ in range(20):
        people_service.adjust_importance(person, 0.2)
    assert person.importance_weight == 1.0
    for _ in range(40):
        people_service.adjust_importance(person, -0.1)
    assert person.importance_weight == -1.0


def test_last_interaction_at_tracks_latest(db: Session, user: User) -> None:
    old = _msg(user.id, sender="Mary <mary@buyer.co>", ext="old", sent_at=NOW - timedelta(days=10))
    new = _msg(user.id, sender="Mary <mary@buyer.co>", ext="new", sent_at=NOW)
    db.add_all([old, new])
    db.commit()
    people_service.upsert_from_message(db, user, old)
    people_service.upsert_from_message(db, user, new)
    person = db.query(Person).one()
    # SQLite drops tzinfo on roundtrip; compare on the naive form.
    seen = person.last_interaction_at
    if seen is not None and seen.tzinfo is not None:
        seen = seen.replace(tzinfo=None)
    assert seen == NOW.replace(tzinfo=None)
