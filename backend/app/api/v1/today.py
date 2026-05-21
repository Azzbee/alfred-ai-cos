"""GET /api/v1/today (PRD 10.1, 19.1)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.db.models import User
from app.schemas.today import TodayDashboard
from app.services.today import build_today

router = APIRouter(prefix="/today", tags=["today"])


@router.get("", response_model=TodayDashboard)
def get_today(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TodayDashboard:
    today = datetime.now(UTC).date()
    return build_today(db, user.id, today=today)
