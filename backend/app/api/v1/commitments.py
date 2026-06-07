"""List and update commitments (PRD 12.5 feedback loop)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.db.enums import CommitmentStatus, SourceType
from app.db.models import Commitment, DraftReply, Message, User
from app.llm import get_llm
from app.schemas.api import (
    CommitmentDraftOut,
    CommitmentDraftRequest,
    CommitmentOut,
    SnoozeOut,
    SnoozeRequest,
)
from app.services import learning
from app.services import snooze as snooze_service

router = APIRouter(prefix="/commitments", tags=["commitments"])


@router.get("", response_model=list[CommitmentOut])
def list_commitments(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Commitment]:
    return list(db.scalars(select(Commitment).where(Commitment.user_id == user.id)))


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
    # Feed the learning loop AFTER the commit so the recorded behavior reflects
    # what's actually persisted. done = act (positive); dismissed = vote "not
    # this"; snoozed = parked (neutral, but tracked for visibility).
    event: learning.Event | None = None
    if status == CommitmentStatus.done:
        event = "act"
    elif status == CommitmentStatus.dismissed:
        event = "dismiss"
    elif status == CommitmentStatus.snoozed:
        event = "snooze"
    if event is not None:
        learning.record_event(db, user, event=event, commitment=commitment)
    return commitment


@router.post("/{commitment_id}/draft", response_model=CommitmentDraftOut)
def draft_for_commitment(
    commitment_id: str,
    payload: CommitmentDraftRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CommitmentDraftOut:
    """Draft a reply for a commitment (the 'Act' button on a Today priority).

    Internal preparation (risk level 1): the draft is generated and returned, not sent.
    Context is the commitment's own description + verbatim source evidence — not a
    separate Gmail thread — so this works for any priority, with or without a message.
    """
    commitment = db.get(Commitment, commitment_id)
    if commitment is None or commitment.user_id != user.id:
        raise HTTPException(status_code=404, detail="Commitment not found")

    context_parts = [f"Task: {commitment.description}"]
    if commitment.counterparty:
        context_parts.append(f"Counterparty: {commitment.counterparty}")
    if commitment.evidence:
        context_parts.append(f"Source (verbatim): {commitment.evidence}")
    context = "\n".join(context_parts)

    # Memory Agent: tone defaults to the learned per-recipient preference
    # when the client didn't override it. We extract the bare email from
    # `commitment.counterparty` (it may carry a "Name <email>" form).
    from app.services import memory

    recipient_email: str | None = None
    if commitment.counterparty and "@" in commitment.counterparty:
        recipient_email = commitment.counterparty.split("<")[-1].rstrip(">").strip()
    chosen_tone = payload.tone or memory.preferred_tone(db, user, recipient_email=recipient_email)

    result = get_llm().draft_reply(
        thread_context=context,
        instruction=payload.instruction,
        tone=chosen_tone,
        user_name=user.name,
    )

    subject = result.subject or f"Re: {commitment.description}".strip()

    # If this commitment came from an email, persist a real DraftReply tied to that
    # message so the reply can be SENT (threaded). Otherwise it's save/review only.
    draft_reply_id: str | None = None
    if commitment.source_type == SourceType.gmail and commitment.source_id:
        message = db.scalar(
            select(Message).where(
                Message.user_id == user.id,
                Message.external_id == commitment.source_id,
            )
        )
        if message is not None:
            draft = DraftReply(
                user_id=user.id,
                message_id=message.id,
                subject=subject,
                body=result.body,
                tone=chosen_tone,
            )
            db.add(draft)
            db.commit()
            draft_reply_id = draft.id

    return CommitmentDraftOut(
        recipient=commitment.counterparty,
        subject=subject,
        body=result.body,
        tone=chosen_tone,
        evidence=commitment.evidence,
        draft_reply_id=draft_reply_id,
    )


@router.post("/{commitment_id}/snooze", response_model=SnoozeOut)
def snooze_commitment(
    commitment_id: str,
    payload: SnoozeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SnoozeOut:
    """Smart snooze with wake conditions. Accepts a natural-language phrase
    (parsed in-house), an explicit ISO date, or an until-reply flag. Either
    parameter wins over the others in the order: explicit until > until_reply >
    phrase. If nothing parses, 400."""
    from datetime import datetime as _dt

    commitment = db.get(Commitment, commitment_id)
    if commitment is None or commitment.user_id != user.id:
        raise HTTPException(status_code=404, detail="Commitment not found")

    spec: snooze_service.SnoozeSpec | None = None
    today = _dt.now().date()
    if payload.until is not None or payload.until_reply:
        spec = snooze_service.SnoozeSpec(
            until_date=payload.until,
            until_reply=payload.until_reply,
            interpreted_as=(payload.until.isoformat() if payload.until else "when they reply"),
        )
    elif payload.phrase:
        spec = snooze_service.parse(payload.phrase, today=today)

    if spec is None or (spec.until_date is None and not spec.until_reply):
        raise HTTPException(
            status_code=400,
            detail="Could not interpret snooze condition — pass a date or 'until reply'",
        )

    snooze_service.snooze(db, commitment, spec=spec)
    return SnoozeOut(
        commitment=CommitmentOut.model_validate(commitment),
        interpreted_as=spec.interpreted_as,
    )
