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
