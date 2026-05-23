"""Priority Inbox (PRD 12.4). Lists the user's synced, classified messages for the
Inbox screen, collapsing the fine-grained MessageClassification into the four UI
categories and filtering spam/noise (surfaced only as a count)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.db.enums import MessageClassification
from app.db.models import Message, User
from app.schemas.api import InboxMessageOut, InboxOut

router = APIRouter(prefix="/messages", tags=["messages"])

# Backend classification → the Inbox screen's four buckets.
_CATEGORY = {
    MessageClassification.needs_reply: "Needs Reply",
    MessageClassification.follow_up_needed: "Needs Reply",
    MessageClassification.needs_decision: "Needs Decision",
    MessageClassification.meeting_scheduling: "Needs Decision",
    MessageClassification.deadline: "Needs Decision",
    MessageClassification.waiting_for_response: "Waiting",
    MessageClassification.informational: "FYI",
    MessageClassification.low_priority: "FYI",
    MessageClassification.sensitive: "FYI",
}
# Classifications that should not appear in the inbox at all (counted as "filtered").
_FILTERED = {MessageClassification.spam_noise}


@router.get("", response_model=InboxOut)
def list_inbox(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InboxOut:
    rows = list(
        db.scalars(
            select(Message)
            .where(Message.user_id == user.id)
            .order_by(Message.sent_at.desc().nullslast())
        )
    )

    messages: list[InboxMessageOut] = []
    filtered = 0
    for m in rows:
        if m.classification in _FILTERED:
            filtered += 1
            continue
        # Unclassified (sync ran, extraction pending) → default to FYI rather than drop.
        category = _CATEGORY.get(m.classification, "FYI") if m.classification else "FYI"
        messages.append(
            InboxMessageOut(
                id=m.id,
                sender=m.sender,
                subject=m.subject,
                snippet=m.snippet,
                take=m.body_summary,
                category=category,
                sent_at=m.sent_at,
                action_required=m.action_required,
            )
        )

    return InboxOut(messages=messages, filtered_count=filtered)
