"""Planning endpoint (PRD 14.1 agent 4).

GET /api/v1/plan?date=YYYY-MM-DD → daily plan with time-blocked activities.
Defaults to the user's local today when date is omitted."""

from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.db.models import User
from app.services import planning

router = APIRouter(prefix="/plan", tags=["plan"])


class PlanBlockOut(BaseModel):
    start: datetime
    end: datetime
    kind: Literal[
        "calendar",
        "meeting_prep",
        "focus",
        "comms",
        "quick_wins",
        "break",
    ]
    title: str
    why: str
    item_ids: list[str]


class PlanOut(BaseModel):
    plan_date: date_type
    timezone: str
    summary: str
    blocks: list[PlanBlockOut]


def _user_today(user: User) -> date_type:
    """Today in the user's local timezone (consistent with the briefing
    scheduler's notion of 'today')."""
    try:
        tz = ZoneInfo(user.timezone or "UTC")
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")
    return datetime.now(tz).date()


@router.get("", response_model=PlanOut)
def get_plan(
    plan_date: date_type | None = Query(
        default=None,
        alias="date",
        description="Defaults to the user's local today.",
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlanOut:
    target = plan_date or _user_today(user)
    plan = planning.build_plan(db, user, plan_date=target)
    return PlanOut(
        plan_date=plan.plan_date,
        timezone=plan.timezone,
        summary=plan.summary,
        blocks=[
            PlanBlockOut(
                start=b.start,
                end=b.end,
                kind=b.kind,
                title=b.title,
                why=b.why,
                item_ids=b.item_ids,
            )
            for b in plan.blocks
        ],
    )
