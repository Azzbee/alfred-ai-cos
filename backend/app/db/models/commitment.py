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

    # Smart-snooze wake conditions. Either or both can be set; the first one to
    # fire re-opens the commitment.
    #   snooze_until: parsed date — re-open on/after this date.
    #   snooze_until_reply: True → re-open when ingestion sees a new inbound on
    #     the source thread (cheap: we already index thread_id on Message).
    snooze_until: Mapped[date | None] = mapped_column(Date)
    snooze_until_reply: Mapped[bool] = mapped_column(Boolean, default=False)

    # PRD 15.1 links to the memory entities. counterparty_person_id is filled
    # by the people service when the counterparty string parses to an email
    # that matches a Person row; project_id is filled by the project service
    # when the commitment clusters into a known project (Barnes deal, etc.).
    counterparty_person_id: Mapped[str | None] = mapped_column(
        ForeignKey("people.id", ondelete="SET NULL"), index=True
    )
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), index=True
    )
