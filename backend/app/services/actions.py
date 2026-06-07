"""Action proposal helper (PRD 12.10). Builds an ActionProposal for a registered
capability with the right approval policy for its risk level, and persists it. Both the
/actions route and other callers (e.g. the assistant) propose through here so every
action shares one audited path."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.capabilities import get_capability
from app.db.enums import ActionStatus, ActionType
from app.db.models import ActionProposal, User
from app.services import execution


def propose_action_internal(
    db: Session,
    user: User,
    *,
    action_type: ActionType,
    target: dict[str, Any],
    reason: str | None = None,
    proposed_content: str | None = None,
) -> ActionProposal:
    """Create and persist an ActionProposal for `action_type`. Raises 400 if no
    capability is registered for it. The proposal's approval_required follows the
    capability's risk level.

    Auto-approve: when the proposal requires approval AND a user-defined
    AutoApprovePolicy matches the proposal, we flip it to approved + execute
    immediately. The execution result is still audited; the policy's
    fire_count is bumped so the UI can show how active a rule is."""
    from datetime import UTC, datetime

    from app.services import auto_approve

    provider = get_capability(action_type)
    if provider is None:
        raise HTTPException(status_code=400, detail=f"No capability for {action_type}")
    desc = provider.describe()
    policy = execution.approval_policy(desc.risk_level)
    proposal = ActionProposal(
        user_id=user.id,
        action_type=action_type,
        risk_level=desc.risk_level.value,
        target=target,
        proposed_content=proposed_content,
        reason=reason or desc.summary,
        approval_required=policy.approval_required,
        status=ActionStatus.proposed,
    )
    db.add(proposal)
    db.commit()

    # Delegated workflows: when this proposal would normally need approval,
    # consult the user's auto-approve policies. A match flips the proposal
    # to approved + executes via the audited spine.
    if policy.approval_required and not policy.strong_confirmation:
        matched = auto_approve.find_matching(db, user, proposal)
        if matched is not None:
            proposal.status = ActionStatus.approved
            proposal.approved_at = datetime.now(UTC)
            db.commit()
            try:
                execution.execute_proposal(db, user, proposal)
                auto_approve.record_fire(db, matched)
            except execution.ExecutionBlocked:
                # The execution spine already wrote the audit row and flipped
                # the proposal to failed. Don't double-count the policy fire.
                pass

    return proposal
