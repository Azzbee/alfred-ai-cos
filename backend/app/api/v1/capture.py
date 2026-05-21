"""Capture routes (PRD 10.3). Text capture here; voice capture added in A7."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.db.models import User
from app.schemas.api import CaptureRequest, CaptureResponse, TaskOut
from app.services import capture as capture_service

router = APIRouter(prefix="/capture", tags=["capture"])


@router.post("", response_model=CaptureResponse)
def capture(
    payload: CaptureRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CaptureResponse:
    tasks, project = capture_service.capture_text(
        db, user.id, text=payload.text, reference_date=datetime.now(UTC).date()
    )
    return CaptureResponse(
        tasks=[TaskOut.model_validate(t) for t in tasks], detected_project=project
    )
