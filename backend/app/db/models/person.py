"""The Person entity (PRD 15.1).

Albert's people memory. Every distinct email address the user has interacted
with becomes a Person row. The interesting data:

  - `importance_weight`: a learned -1..+1 score that the priority ranker
    consults. Acts on emails from this person → it lifts. Dismisses → it drops.
  - `relationship_type`: a deterministic best-guess at who this person is
    (colleague, client, vendor, investor, family, friend, automated). The
    user can override per-Person; the override wins.
  - `organization`: derived from the email domain when it's not a free-mail
    provider. The Project entity uses this to group commitments by company.
  - `last_interaction_at`: most recent inbound or outbound timestamp. Powers
    "haven't heard from Mary in 3 weeks" detection.
  - `notes`: free-text the user can attach.

Lookup is by `(user_id, email_lower)` — every person belongs to exactly one
user (no global people table) and their email is canonicalised on write."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import RelationshipType


class Person(Base):
    __tablename__ = "people"
    __table_args__ = (UniqueConstraint("user_id", "email_lower", name="uq_person_user_email"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    # The canonical, lowercased email — the natural key for matching back to
    # Message.sender / Commitment.counterparty.
    email_lower: Mapped[str] = mapped_column(String(320), index=True)

    # Display name (best-effort from the most recent header value we've seen).
    name: Mapped[str | None] = mapped_column(String(200))

    # Inferred organization from the email domain (None for free-mail).
    organization: Mapped[str | None] = mapped_column(String(200), index=True)

    # Best-guess relationship class; the user can override and the override sticks.
    relationship_type: Mapped[RelationshipType] = mapped_column(
        String(32), default=RelationshipType.unknown
    )
    # True when the user has explicitly set relationship_type — locks it from
    # being overwritten by the heuristic update path.
    relationship_locked: Mapped[bool] = mapped_column(Boolean, default=False)

    # Bounded -1..+1 importance signal the priority ranker mixes in. Updated by
    # the importance-learning loop on act / dismiss events.
    importance_weight: Mapped[float] = mapped_column(Float, default=0.0)

    # Interaction stats — useful for ranking AND for the People screen.
    inbound_count: Mapped[int] = mapped_column(Integer, default=0)
    outbound_count: Mapped[int] = mapped_column(Integer, default=0)
    last_interaction_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )

    # Free-text notes the user attaches via the People screen.
    notes: Mapped[str | None] = mapped_column(Text)
