"""Tests for the Project entity, projects service, and clustering."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.db.enums import CommitmentOwner, CommitmentStatus, ProjectStatus, SourceType
from app.db.models import Commitment, Message, Person, Project, User
from app.services import people as people_service
from app.services import projects as projects_service

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


def _commit(
    user_id: str,
    *,
    description: str,
    evidence: str | None = None,
    counterparty: str | None = None,
    counterparty_person_id: str | None = None,
) -> Commitment:
    return Commitment(
        user_id=user_id,
        description=description,
        evidence=evidence,
        owner=CommitmentOwner.user,
        counterparty=counterparty,
        counterparty_person_id=counterparty_person_id,
        status=CommitmentStatus.open,
        source_type=SourceType.gmail,
        confidence=0.9,
    )


# --- user-driven CRUD ---


def test_create_project(db: Session, user: User) -> None:
    p = projects_service.create(db, user, name="Barnes Acquisition")
    assert p.id and p.user_id == user.id and p.name == "Barnes Acquisition"
    assert p.status == ProjectStatus.active
    assert p.is_proposed is False


def test_create_is_idempotent_on_name(db: Session, user: User) -> None:
    p1 = projects_service.create(db, user, name="Q3 launch")
    p2 = projects_service.create(db, user, name="Q3 launch")
    assert p1.id == p2.id
    assert db.query(Project).count() == 1


def test_attach_commitments(db: Session, user: User) -> None:
    p = projects_service.create(db, user, name="X")
    c1 = _commit(user.id, description="A")
    c2 = _commit(user.id, description="B")
    db.add_all([c1, c2])
    db.commit()
    n = projects_service.attach_commitments(db, p, commitment_ids=[c1.id, c2.id])
    assert n == 2
    db.refresh(c1)
    db.refresh(c2)
    assert c1.project_id == p.id
    assert c2.project_id == p.id


def test_attach_ignores_other_users(db: Session, user: User) -> None:
    other = User(email="other@x.io")
    db.add(other)
    db.commit()
    p = projects_service.create(db, user, name="X")
    foreign = _commit(other.id, description="not mine")
    db.add(foreign)
    db.commit()
    n = projects_service.attach_commitments(db, p, commitment_ids=[foreign.id])
    assert n == 0


def test_archive_via_status_update(db: Session, user: User) -> None:
    p = projects_service.create(db, user, name="Old project")
    projects_service.update_status(db, p, status=ProjectStatus.archived)
    db.refresh(p)
    assert p.status == ProjectStatus.archived


def test_reject_only_proposed(db: Session, user: User) -> None:
    p = projects_service.create(db, user, name="X")
    with pytest.raises(ValueError):
        projects_service.reject(db, p)


# --- auto-clustering ---


def test_propose_clusters_by_shared_person(db: Session, user: User) -> None:
    """5 open commitments all pointing at the same Person + sharing tokens
    should produce one proposed Project."""
    mary = _seed_person(db, user, "mary@buyer.co", name="Mary")
    for i in range(5):
        c = _commit(
            user.id,
            description=f"Sign the contract part {i}",
            evidence="contract signing for Barnes deal",
            counterparty="Mary <mary@buyer.co>",
            counterparty_person_id=mary.id,
        )
        db.add(c)
    db.commit()
    proposed = projects_service.propose_projects(db, user)
    assert len(proposed) == 1
    p = proposed[0]
    assert p.is_proposed is True
    assert p.name in {"buyer.co", "Mary"}
    # Commitments should be attached to the proposed project for review.
    assert db.query(Commitment).filter(Commitment.project_id == p.id).count() == 5


def test_propose_skips_singletons(db: Session, user: User) -> None:
    mary = _seed_person(db, user, "mary@buyer.co", name="Mary")
    c = _commit(
        user.id,
        description="Sign the contract",
        evidence="contract for Barnes",
        counterparty="Mary <mary@buyer.co>",
        counterparty_person_id=mary.id,
    )
    db.add(c)
    db.commit()
    assert projects_service.propose_projects(db, user) == []


def test_propose_is_idempotent(db: Session, user: User) -> None:
    """Running the proposal scan twice doesn't duplicate the proposal."""
    mary = _seed_person(db, user, "mary@buyer.co", name="Mary")
    for i in range(4):
        c = _commit(
            user.id,
            description=f"Sign the contract step {i}",
            evidence="contract for Barnes acquisition",
            counterparty="Mary <mary@buyer.co>",
            counterparty_person_id=mary.id,
        )
        db.add(c)
    db.commit()
    first = projects_service.propose_projects(db, user)
    second = projects_service.propose_projects(db, user)
    assert len(first) == 1 and len(second) == 0
    assert db.query(Project).count() == 1


def test_accept_promotes_proposed(db: Session, user: User) -> None:
    mary = _seed_person(db, user, "mary@buyer.co", name="Mary")
    for i in range(3):
        c = _commit(
            user.id,
            description=f"Sign contract step {i}",
            evidence="contract barnes deal",
            counterparty="Mary <mary@buyer.co>",
            counterparty_person_id=mary.id,
        )
        db.add(c)
    db.commit()
    proposed = projects_service.propose_projects(db, user)
    assert proposed
    p = proposed[0]
    assert p.is_proposed is True
    projects_service.accept(db, p)
    db.refresh(p)
    assert p.is_proposed is False


def test_detach_commitment_clears_link(db: Session, user: User) -> None:
    p = projects_service.create(db, user, name="X")
    c = _commit(user.id, description="A")
    db.add(c)
    db.commit()
    projects_service.attach_commitments(db, p, commitment_ids=[c.id])
    db.refresh(c)
    assert c.project_id == p.id
    projects_service.detach_commitment(db, c)
    db.refresh(c)
    assert c.project_id is None
