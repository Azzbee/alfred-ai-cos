from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import Priority, SourceType, TaskStatus


class Task(Base):
    """A user-actionable task. Every task links back to its origin via
    source_type/source_id so the UI can show evidence (PRD 12.4)."""

    __tablename__ = "tasks"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[date | None] = mapped_column(Date)
    priority: Mapped[Priority] = mapped_column(String(16), default=Priority.medium)
    status: Mapped[TaskStatus] = mapped_column(String(16), default=TaskStatus.open)

    source_type: Mapped[SourceType] = mapped_column(String(16), default=SourceType.manual)
    source_id: Mapped[str | None] = mapped_column(String(64), index=True)
    confidence: Mapped[float | None] = mapped_column(Float)
