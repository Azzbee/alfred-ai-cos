"""Trigger ingestion + extraction (PRD 12.2, 12.5).

Synchronous for the slice so the flow is easy to demo end to end. In production
this enqueues a Celery task (app.workers.tasks.sync_user) instead; the worker path
is wired and ready (see docs/ARCHITECTURE.md)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.db.models import User
from app.schemas.api import SyncResponse
from app.services import extraction, ingestion

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("", response_model=SyncResponse)
def sync_now(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SyncResponse:
    messages = ingestion.ingest_recent_messages(db, user.id)
    commitments_found = 0
    for message in messages:
        commitments_found += len(extraction.process_message(db, message))
    return SyncResponse(ingested=len(messages), commitments_found=commitments_found)
