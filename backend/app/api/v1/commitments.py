"""List and update commitments (PRD 12.5 feedback loop)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.db.enums import CommitmentStatus
from app.db.models import Commitment, User
from app.schemas.api import CommitmentOut

router = APIRouter(prefix="/commitments", tags=["commitments"])


@router.get("", response_model=list[CommitmentOut])
def list_commitments(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Commitment]:
    return list(
        db.scalars(select(Commitment).where(Commitment.user_id == user.id))
    )


@router.post("/{commitment_id}/status", response_model=CommitmentOut)
def update_status(
    commitment_id: str,
    status: CommitmentStatus,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Commitment:
    """Mark done / snooze / dismiss. This is the user feedback signal (PRD 20.1)."""
    commitment = db.get(Commitment, commitment_id)
    if commitment is None or commitment.user_id != user.id:
        raise HTTPException(status_code=404, detail="Commitment not found")
    commitment.status = status
    db.commit()
    return commitment
