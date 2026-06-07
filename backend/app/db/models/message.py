from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import MessageClassification, Priority


class Message(Base):
    """A normalized email. `external_id` is the Gmail message id.

    Body is summarized for storage (PRD 15.1: body_summary), keeping the full
    raw body out of the database to minimize sensitive data at rest.
    """

    __tablename__ = "messages"
    __table_args__ = (UniqueConstraint("user_id", "external_id", name="uq_message_user_external"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(16), default="gmail")
    external_id: Mapped[str] = mapped_column(String(128), index=True)
    thread_id: Mapped[str | None] = mapped_column(String(128), index=True)

    sender: Mapped[str] = mapped_column(String(320))
    recipients: Mapped[list[str]] = mapped_column(JSON, default=list)
    subject: Mapped[str | None] = mapped_column(Text)
    body_summary: Mapped[str | None] = mapped_column(Text)
    snippet: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Filled by the extraction pipeline; null until classified.
    classification: Mapped[MessageClassification | None] = mapped_column(String(32))
    priority: Mapped[Priority | None] = mapped_column(String(16))
    action_required: Mapped[bool] = mapped_column(Boolean, default=False)

    # Spam-relevant headers preserved as a small dict so the ranker can read
    # List-Unsubscribe, Precedence, Auto-Submitted, Reply-To, CC, BCC, X-Mailer,
    # X-Auto-Response-Suppress, Feedback-ID, etc. without re-fetching Gmail.
    # Keys are lowercased header names; values are the header strings.
    headers: Mapped[dict | None] = mapped_column(JSON)

    # Deterministic sender class computed at ingest. One of:
    #   "person" | "role_account" | "automated" | "bulk" | "suspicious" | "vip" | "muted"
    # Stored so per-commitment scoring is O(1) and the dashboard renders the
    # same answer the ranker uses.
    sender_classification: Mapped[str | None] = mapped_column(String(32))

    # PRD 15.1 link back to the Person memory entity. Set by the people
    # service when ingestion runs, so the People screen and the Memory Agent
    # can reach every message a given person ever sent without re-parsing
    # the `sender` header.
    sender_person_id: Mapped[str | None] = mapped_column(
        ForeignKey("people.id", ondelete="SET NULL"), index=True
    )
