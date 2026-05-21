from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import ActionStatus, ActionType, RiskLevel


class ActionProposal(Base):
    """The human-in-the-loop spine (PRD 12.10, 17). Any action at risk level 3+
    must exist as an ActionProposal and be approved before execution.

    For the slice, the only level-3 action is sending a draft reply. Albert
    creates the proposal; the user approves; the execution agent acts and writes
    an ExecutionLog row.
    """

    __tablename__ = "action_proposals"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    action_type: Mapped[ActionType] = mapped_column(String(32))
    risk_level: Mapped[int] = mapped_column(Integer, default=RiskLevel.external_comm.value)

    # What the action targets and its content, e.g. {"draft_reply_id": "...", "to": "..."}.
    target: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    proposed_content: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)

    approval_required: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[ActionStatus] = mapped_column(String(16), default=ActionStatus.proposed)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ExecutionLog(Base):
    """Append-only audit record for every executed action (PRD 12.10, 13.2)."""

    __tablename__ = "execution_logs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    action_proposal_id: Mapped[str] = mapped_column(
        ForeignKey("action_proposals.id", ondelete="CASCADE"), index=True
    )
    action_type: Mapped[ActionType] = mapped_column(String(32))
    result: Mapped[str] = mapped_column(String(16))  # success | error
    error: Mapped[str | None] = mapped_column(Text)
    rollback_available: Mapped[bool] = mapped_column(Boolean, default=False)
