"""People memory endpoints (PRD 15.1 Person).

The People screen on mobile reads:
  - GET  /api/v1/people                 → list, ordered by recent + important
  - GET  /api/v1/people/{id}            → one person + their open commitments
  - POST /api/v1/people/{id}/relationship → user override (colleague/friend/...)
  - POST /api/v1/people/{id}/notes      → attach free-text notes

The list is intentionally narrow: it excludes automated / suspicious people so
the screen reads as "humans in my life" and not "everyone who's ever emailed me."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.db.enums import CommitmentStatus, RelationshipType
from app.db.models import Commitment, Person, User
from app.services import people as people_service

router = APIRouter(prefix="/people", tags=["people"])


class PersonOut(BaseModel):
    id: str
    email: str
    name: str | None
    organization: str | None
    relationship_type: RelationshipType
    relationship_locked: bool
    importance_weight: float
    inbound_count: int
    outbound_count: int
    last_interaction_at: datetime | None
    notes: str | None

    model_config = {"from_attributes": True}


class PersonDetailOut(PersonOut):
    open_commitments: list[dict] = Field(default_factory=list)


class RelationshipUpdate(BaseModel):
    relationship: RelationshipType


class NotesUpdate(BaseModel):
    notes: str | None = None


def _to_out(person: Person) -> PersonOut:
    return PersonOut(
        id=person.id,
        email=person.email_lower,
        name=person.name,
        organization=person.organization,
        relationship_type=person.relationship_type,
        relationship_locked=person.relationship_locked,
        importance_weight=person.importance_weight,
        inbound_count=person.inbound_count or 0,
        outbound_count=person.outbound_count or 0,
        last_interaction_at=person.last_interaction_at,
        notes=person.notes,
    )


@router.get("", response_model=list[PersonOut])
def list_people(
    include: Literal["humans", "all"] = "humans",
    limit: int = 100,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PersonOut]:
    """List people for the People screen.

    `include=humans` (default): excludes `automated` and `suspicious` so the
    screen reads as a contact book, not an inbox dump.
    `include=all`: returns everything for debugging / admin views."""
    stmt = (
        select(Person)
        .where(Person.user_id == user.id)
        .order_by(
            Person.last_interaction_at.desc().nulls_last(),
            Person.importance_weight.desc(),
        )
        .limit(max(1, min(limit, 500)))
    )
    if include == "humans":
        stmt = stmt.where(
            Person.relationship_type.notin_(
                [RelationshipType.automated, RelationshipType.suspicious]
            )
        )
    rows = list(db.scalars(stmt))
    return [_to_out(p) for p in rows]


@router.get("/{person_id}", response_model=PersonDetailOut)
def get_person(
    person_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PersonDetailOut:
    """One person + their open commitments (counterparty or owner=user with
    this person as counterparty). Drives the Person detail screen."""
    person = db.get(Person, person_id)
    if person is None or person.user_id != user.id:
        raise HTTPException(status_code=404, detail="Person not found")
    open_commits = list(
        db.scalars(
            select(Commitment)
            .where(
                Commitment.user_id == user.id,
                Commitment.counterparty_person_id == person.id,
                Commitment.status == CommitmentStatus.open,
            )
            .order_by(Commitment.due_date.asc().nulls_last(), Commitment.created_at.desc())
        )
    )
    base = _to_out(person)
    return PersonDetailOut(
        **base.model_dump(),
        open_commitments=[
            {
                "id": c.id,
                "description": c.description,
                "due_date": c.due_date.isoformat() if c.due_date else None,
                "owner": c.owner.value,
                "priority": c.priority.value,
            }
            for c in open_commits
        ],
    )


@router.post("/{person_id}/relationship", response_model=PersonOut)
def update_relationship(
    person_id: str,
    payload: RelationshipUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PersonOut:
    """Lock a relationship_type to the user's chosen value. The heuristic
    update path skips locked rows, so this sticks."""
    person = db.get(Person, person_id)
    if person is None or person.user_id != user.id:
        raise HTTPException(status_code=404, detail="Person not found")
    people_service.set_relationship(db, person, relationship=payload.relationship)
    return _to_out(person)


@router.post("/{person_id}/notes", response_model=PersonOut)
def update_notes(
    person_id: str,
    payload: NotesUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PersonOut:
    """Attach (or clear) free-text notes."""
    person = db.get(Person, person_id)
    if person is None or person.user_id != user.id:
        raise HTTPException(status_code=404, detail="Person not found")
    people_service.set_notes(db, person, notes=payload.notes)
    return _to_out(person)
