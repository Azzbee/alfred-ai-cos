"""Draft reply generation (PRD 12.9, journey 3).

Generating a draft is internal preparation (risk level 1): no approval needed.
The draft is stored but not pushed to Gmail. Pushing or sending crosses to level 3
and is created as an ActionProposal in app/api/v1/actions.py."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.db.models import DraftReply, Message, User
from app.llm import get_llm
from app.schemas.api import DraftCreateRequest, DraftOut

router = APIRouter(prefix="/drafts", tags=["drafts"])


@router.post("", response_model=DraftOut)
def create_draft(
    payload: DraftCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DraftReply:
    message = db.get(Message, payload.message_id)
    if message is None or message.user_id != user.id:
        raise HTTPException(status_code=404, detail="Message not found")

    # Thread context for the slice is the stored snippet + subject. Full-thread
    # retrieval is a follow-up (see docs/TODO.md).
    context = f"Subject: {message.subject or '(none)'}\nFrom: {message.sender}\n\n{message.snippet}"
    result = get_llm().draft_reply(
        thread_context=context,
        instruction=payload.instruction,
        tone=payload.tone,
        user_name=user.name,
    )

    draft = DraftReply(
        user_id=user.id,
        message_id=message.id,
        subject=result.subject or f"Re: {message.subject or ''}".strip(),
        body=result.body,
        tone=payload.tone,
    )
    db.add(draft)
    db.commit()
    return draft
