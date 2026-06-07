"""Recurring workflow rules (PRD Phase 3).

- GET    /api/v1/recurring                → list user's rules
- POST   /api/v1/recurring                → create
- PATCH  /api/v1/recurring/{id}           → update (name/cron/params/enabled)
- DELETE /api/v1/recurring/{id}           → delete
- GET    /api/v1/recurring/workflows      → list registered handler names
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.db.models import RecurringRule, User
from app.services import recurring as recurring_service

router = APIRouter(prefix="/recurring", tags=["recurring"])


class RuleOut(BaseModel):
    id: str
    name: str
    workflow: str
    cron: str
    params: dict = Field(default_factory=dict)
    enabled: bool
    next_run_at: datetime | None
    last_run_at: datetime | None
    last_error: str | None

    model_config = {"from_attributes": True}


class CreateRuleRequest(BaseModel):
    name: str
    workflow: str
    cron: str
    params: dict | None = None
    enabled: bool = True


class UpdateRuleRequest(BaseModel):
    name: str | None = None
    cron: str | None = None
    params: dict | None = None
    enabled: bool | None = None


def _to_out(rule: RecurringRule) -> RuleOut:
    return RuleOut(
        id=rule.id,
        name=rule.name,
        workflow=rule.workflow,
        cron=rule.cron,
        params=rule.params or {},
        enabled=rule.enabled,
        next_run_at=rule.next_run_at,
        last_run_at=rule.last_run_at,
        last_error=rule.last_error,
    )


@router.get("/workflows", response_model=list[str])
def list_workflows() -> list[str]:
    return sorted(recurring_service.WORKFLOWS.keys())


@router.get("", response_model=list[RuleOut])
def list_rules(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RuleOut]:
    rows = list(
        db.scalars(
            select(RecurringRule)
            .where(RecurringRule.user_id == user.id)
            .order_by(RecurringRule.created_at.desc())
        )
    )
    return [_to_out(r) for r in rows]


@router.post("", response_model=RuleOut)
def create_rule(
    payload: CreateRuleRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RuleOut:
    try:
        rule = recurring_service.create_rule(
            db,
            user,
            name=payload.name,
            workflow=payload.workflow,
            cron=payload.cron,
            params=payload.params,
            enabled=payload.enabled,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_out(rule)


@router.patch("/{rule_id}", response_model=RuleOut)
def update_rule(
    rule_id: str,
    payload: UpdateRuleRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RuleOut:
    rule = _owned(db, rule_id, user.id)
    if payload.enabled is not None:
        recurring_service.set_enabled(db, rule, enabled=payload.enabled, user=user)
    try:
        recurring_service.update_rule(
            db,
            rule,
            user=user,
            name=payload.name,
            cron=payload.cron,
            params=payload.params,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_out(rule)


@router.delete("/{rule_id}", status_code=204)
def delete_rule(
    rule_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    rule = _owned(db, rule_id, user.id)
    recurring_service.delete_rule(db, rule)


def _owned(db: Session, rule_id: str, user_id: str) -> RecurringRule:
    rule = db.get(RecurringRule, rule_id)
    if rule is None or rule.user_id != user_id:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule
