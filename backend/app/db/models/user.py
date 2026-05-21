from typing import Any

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(200))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")

    # Onboarding calibration + notification/approval settings (PRD 9.1, 12.1).
    # Kept as JSON for the slice; promote to columns when the shape stabilizes.
    preferences: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
