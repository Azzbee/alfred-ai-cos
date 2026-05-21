from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import CommitmentOwner, CommitmentStatus, Priority, SourceType


class Commitment(Base):
    """Albert's most important object (PRD 12.5, 15.1).

    A commitment always carries its `evidence` (a verbatim quote from the source)
    and a `confidence` score. Low-confidence commitments surface as suggestions,
    not facts, in the UI.
    """

    __tablename__ = "commitments"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    description: Mapped[str] = mapped_column(Text)
    owner: Mapped[CommitmentOwner] = mapped_column(String(16))
    counterparty: Mapped[str | None] = mapped_column(String(320))
    due_date: Mapped[date | None] = mapped_column(Date)

    priority: Mapped[Priority] = mapped_column(String(16), default=Priority.medium)
    status: Mapped[CommitmentStatus] = mapped_column(String(16), default=CommitmentStatus.open)

    # Provenance: which message/event this was extracted from.
    source_type: Mapped[SourceType] = mapped_column(String(16))
    source_id: Mapped[str | None] = mapped_column(String(64), index=True)
    evidence: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # True when the counterparty is an automated/marketing/notification sender, not a
    # real person. Such items are not surfaced as "people waiting on you".
    from_automated: Mapped[bool] = mapped_column(Boolean, default=False)

    # Human-readable priority explanation (PRD principle 3). Set by the priority engine.
    reason: Mapped[str | None] = mapped_column(Text)
