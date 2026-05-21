from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CalendarEvent(Base):
    """A normalized Google Calendar event.

    Calendar ingestion is part of the slice's data foundation so meeting-prep
    and free-time planning (PRD 12.3) can build on it without a re-sync.
    """

    __tablename__ = "calendar_events"
    __table_args__ = (
        UniqueConstraint("user_id", "external_id", name="uq_event_user_external"),
    )

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    external_id: Mapped[str] = mapped_column(String(256), index=True)

    title: Mapped[str | None] = mapped_column(Text)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    location: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    attendees: Mapped[list[str]] = mapped_column(JSON, default=list)

    prep_required: Mapped[bool] = mapped_column(Boolean, default=False)
