"""RecurringRule (PRD Phase 3 "recurring workflows").

Each row is a cron-scheduled invocation of a named workflow under the
user's account. The worker fires rules whose `next_run_at` has passed,
runs the named workflow, advances `next_run_at` to the next cron tick,
and stamps `last_run_at`.

Workflows are registered by name in `app/services/recurring.py`. To add
a new one, write the function and register it in WORKFLOWS — no model
change needed."""

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RecurringRule(Base):
    __tablename__ = "recurring_rules"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # Human-friendly label for the People-screen view.
    name: Mapped[str] = mapped_column(String(120))

    # Registered workflow handler key (e.g. "weekly_digest", "thread_cleanup").
    workflow: Mapped[str] = mapped_column(String(64))

    # Cron expression in 5-field form: "minute hour day month weekday".
    # The user's timezone is applied at evaluation time.
    cron: Mapped[str] = mapped_column(String(120))

    # Optional workflow-specific parameters (kwargs passed to the handler).
    params: Mapped[dict | None] = mapped_column(JSON)

    # The next time this rule should fire (UTC). The worker reads ANY rule
    # where next_run_at <= now and runs it. Set to None to pause.
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # User can toggle a rule off without deleting it.
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Most-recent error message, when last_run failed. Cleared on success.
    last_error: Mapped[str | None] = mapped_column(Text)
