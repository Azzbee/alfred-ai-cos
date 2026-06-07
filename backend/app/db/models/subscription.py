"""Subscription (PRD Phase 2 monetization).

One row per user. Tracks the user's current Stripe customer/subscription
ids plus the active plan + status, populated and updated by the Stripe
webhook. Free-tier users get a row with plan='free' so the gating code
always has a current view.

`current_period_end` lets gating refuse paid features after the period
ends, even if the webhook misses an event."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )

    # Plan slug (free | pro | team). Read by feature-gating helpers.
    plan: Mapped[str] = mapped_column(String(32), default="free")

    # Stripe object ids — set on first checkout completion.
    stripe_customer_id: Mapped[str | None] = mapped_column(String(64), index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(64), index=True)

    # Mirrored Stripe status: trialing | active | past_due | canceled | incomplete | etc.
    status: Mapped[str] = mapped_column(String(32), default="inactive")

    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
