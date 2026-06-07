"""AutoApprovePolicy (PRD Phase 3 "delegated workflows").

Each row is a user-defined rule that auto-approves an ActionProposal
matching its predicate. The execution spine (services/execution.py)
consults policies before requiring user approval; a matching policy
flips the proposal to approved + executes immediately.

Predicate fields are intentionally minimal — the safest delegation
surface only exists for narrow rules. The user must set at least one
specific match (action_type AND counterparty_email, or workflow_pattern).
Wildcard policies are refused at create time."""

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import ActionType


class AutoApprovePolicy(Base):
    __tablename__ = "auto_approve_policies"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # Required: must match this exact action type. Wildcards refused.
    action_type: Mapped[ActionType] = mapped_column(String(32))

    # Match by counterparty email (lowercased) OR by domain (no @). At
    # least one of these must be set — empty-everything policies are
    # rejected at create time.
    counterparty_email: Mapped[str | None] = mapped_column(String(320))
    counterparty_domain: Mapped[str | None] = mapped_column(String(200))

    # Cap, in cents, for financial actions (make_payment / place_order).
    # When the action is financial and the proposal exceeds max_cents, the
    # policy does NOT match — falls through to manual approval.
    max_cents: Mapped[int | None] = mapped_column(Integer)

    # Optional content-pattern filter — a substring that must appear in
    # proposed_content (case-insensitive). Useful for "auto-approve drafts
    # that include the phrase 'monthly invoice'." Empty = any content.
    content_substring: Mapped[str | None] = mapped_column(Text)

    # Free-form note the user attaches in the UI so they remember why.
    note: Mapped[str | None] = mapped_column(Text)

    # User can toggle a policy off without deleting it.
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Optional time-of-day window in "HH:MM-HH:MM" form, applied in the
    # user's timezone. Auto-approval is skipped outside the window so
    # delegated actions only fire when the user is reasonably awake.
    active_window: Mapped[str | None] = mapped_column(String(16))

    # Audit: every auto-approve fire bumps this counter so the UI can
    # show "this rule fired N times in the last week."
    fire_count: Mapped[int] = mapped_column(Integer, default=0)

    # Optional JSON for future extensions (per-action-type knobs).
    meta: Mapped[dict | None] = mapped_column(JSON)
