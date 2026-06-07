"""Share-sheet receiver (PRD Phase 2).

Accepts a URL or text payload from the iOS Share Sheet (via a Shortcut
that posts to this endpoint) and creates a Task on the user's behalf.

  - POST /api/v1/share → {"url": str | None, "text": str | None, "title": str | None}

Either url or text is required. The endpoint is authenticated like
every other route — the Shortcut puts the session JWT in the
Authorization header (the user copies it from Settings)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.db.enums import Priority, SourceType, TaskStatus
from app.db.models import Task, User

router = APIRouter(prefix="/share", tags=["share"])


class ShareRequest(BaseModel):
    url: str | None = None
    text: str | None = None
    title: str | None = None


class ShareOut(BaseModel):
    task_id: str
    title: str


@router.post("", response_model=ShareOut)
def receive_share(
    payload: ShareRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShareOut:
    """Create a Task from a shared URL or text snippet.

    Title resolution:
      - explicit `title` wins;
      - otherwise the first line of `text`;
      - otherwise the URL host;
      - otherwise "Shared item".
    """
    if not payload.url and not payload.text:
        raise HTTPException(status_code=400, detail="url or text required")

    title = (payload.title or "").strip()
    if not title and payload.text:
        first_line = payload.text.strip().splitlines()[0]
        title = first_line[:120]
    if not title and payload.url:
        try:
            from urllib.parse import urlparse

            parsed = urlparse(payload.url)
            title = parsed.netloc or "Shared link"
        except Exception:
            title = "Shared link"
    if not title:
        title = "Shared item"

    # Stash the URL + body in description so the Task screen can render
    # the source. Cap at 4KB to keep DB rows small.
    description_parts: list[str] = []
    if payload.url:
        description_parts.append(payload.url)
    if payload.text:
        description_parts.append(payload.text)
    description = "\n\n".join(description_parts)[:4000]

    task = Task(
        user_id=user.id,
        title=title[:120],
        description=description,
        priority=Priority.medium,
        status=TaskStatus.open,
        source_type=SourceType.manual,
        source_id=None,
        confidence=1.0,
    )
    db.add(task)
    db.commit()
    return ShareOut(task_id=task.id, title=task.title)
