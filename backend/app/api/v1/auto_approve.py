"""Auto-approve policy endpoints (PRD Phase 3).

  - GET    /api/v1/auto-approve              → list
  - POST   /api/v1/auto-approve              → create
  - PATCH  /api/v1/auto-approve/{id}         → enable/disable
  - DELETE /api/v1/auto-approve/{id}         → delete
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.db.enums import ActionType
from app.db.models import AutoApprovePolicy, User
from app.services import auto_approve as auto_approve_service

router = APIRouter(prefix="/auto-approve", tags=["auto-approve"])


class PolicyOut(BaseModel):
    id: str
    action_type: ActionType
    counterparty_email: str | None
    counterparty_domain: str | None
    max_cents: int | None
    content_substring: str | None
    note: str | None
    enabled: bool
    active_window: str | None
    fire_count: int

    model_config = {"from_attributes": True}


class CreatePolicyRequest(BaseModel):
    action_type: ActionType
    counterparty_email: str | None = None
    counterparty_domain: str | None = None
    max_cents: int | None = None
    content_substring: str | None = None
    note: str | None = None
    active_window: str | None = None
    enabled: bool = True


class UpdatePolicyRequest(BaseModel):
    enabled: bool | None = None
    note: str | None = None


def _to_out(policy: AutoApprovePolicy) -> PolicyOut:
    return PolicyOut(
        id=policy.id,
        action_type=policy.action_type,
        counterparty_email=policy.counterparty_email,
        counterparty_domain=policy.counterparty_domain,
        max_cents=policy.max_cents,
        content_substring=policy.content_substring,
        note=policy.note,
        enabled=policy.enabled,
        active_window=policy.active_window,
        fire_count=policy.fire_count or 0,
    )


@router.get("", response_model=list[PolicyOut])
def list_policies(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PolicyOut]:
    rows = list(
        db.scalars(
            select(AutoApprovePolicy)
            .where(AutoApprovePolicy.user_id == user.id)
            .order_by(AutoApprovePolicy.created_at.desc())
        )
    )
    return [_to_out(r) for r in rows]


@router.post("", response_model=PolicyOut)
def create_policy(
    payload: CreatePolicyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PolicyOut:
    try:
        policy = auto_approve_service.create_policy(
            db,
            user,
            action_type=payload.action_type,
            counterparty_email=payload.counterparty_email,
            counterparty_domain=payload.counterparty_domain,
            max_cents=payload.max_cents,
            content_substring=payload.content_substring,
            note=payload.note,
            active_window=payload.active_window,
            enabled=payload.enabled,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_out(policy)


@router.patch("/{policy_id}", response_model=PolicyOut)
def update_policy(
    policy_id: str,
    payload: UpdatePolicyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PolicyOut:
    policy = _owned(db, policy_id, user.id)
    if payload.enabled is not None:
        auto_approve_service.set_enabled(db, policy, enabled=payload.enabled)
    if payload.note is not None:
        policy.note = payload.note
        db.commit()
    return _to_out(policy)


@router.delete("/{policy_id}", status_code=204)
def delete_policy(
    policy_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    policy = _owned(db, policy_id, user.id)
    auto_approve_service.delete_policy(db, policy)


def _owned(db: Session, policy_id: str, user_id: str) -> AutoApprovePolicy:
    policy = db.get(AutoApprovePolicy, policy_id)
    if policy is None or policy.user_id != user_id:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy
