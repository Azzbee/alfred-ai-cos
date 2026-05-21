from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import NotificationStatus, NotificationType


class Device(Base):
    """A registered push target (PRD 12.8). One row per device push token."""

    __tablename__ = "devices"
    __table_args__ = (UniqueConstraint("push_token", name="uq_device_push_token"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    push_token: Mapped[str] = mapped_column(String(256))
    platform: Mapped[str | None] = mapped_column(String(16))  # ios | android


class Notification(Base):
    """A notification Albert decided to surface (PRD 12.8). Recorded whether or not
    it was sent, so batching/quiet-hours decisions and usefulness feedback are auditable."""

    __tablename__ = "notifications"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[NotificationType] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    status: Mapped[NotificationStatus] = mapped_column(
        String(16), default=NotificationStatus.pending
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Dedup key so the same risk does not notify twice (PRD 12.8 reduce noise).
    dedup_key: Mapped[str | None] = mapped_column(String(128), index=True)

    # User feedback on whether the notification was useful (trust metric, PRD 20.1).
    useful: Mapped[bool | None] = mapped_column(Boolean)
