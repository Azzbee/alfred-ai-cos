"""Development-only seeding so the backend slice can be exercised without Google.

Inserts realistic mock emails and runs them through the real extraction + priority
pipeline. Disabled outside ENVIRONMENT=development. Not part of the product surface;
the production path is /sync against a connected Gmail account."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_current_user
from app.db.base import get_db
from app.db.enums import Provider, SyncStatus
from app.db.models import ConnectedAccount, Message, User
from app.schemas.api import SyncResponse
from app.services import calendar, extraction
from app.services.crypto import encrypt_token

router = APIRouter(prefix="/dev", tags=["dev"])
settings = get_settings()

# Five seeded emails chosen to cover the slice's classification + commitment cases.
# Bodies are passed straight to extraction; nothing is fetched from Gmail.
_SEED_EMAILS: list[dict[str, str]] = [
    {
        "external_id": "seed-urgent-commitment",
        "thread_id": "thread-barnes",
        "sender": "Chaker Zeraiki <chaker@example.com>",
        "subject": "Barnes financial clarification — need this before tomorrow",
        "body": (
            "Hi, the acquisition review is blocked on your end. Could you send the "
            "financial clarification questions to me before tomorrow? We cannot move "
            "the Barnes deal forward without them. Thanks."
        ),
    },
    {
        "external_id": "seed-meeting-prep",
        "thread_id": "thread-celine",
        "sender": "Celine Kasparian <celine@example.com>",
        "subject": "Our call tomorrow at 14:00",
        "body": (
            "Looking forward to our call tomorrow at 2pm. Last time we left the lunch "
            "timing open and there may be a scheduling conflict on my side. Can you "
            "confirm the time and the location when you get a chance?"
        ),
    },
    {
        "external_id": "seed-waiting-for",
        "thread_id": "thread-cbre",
        "sender": "You <self@example.com>",
        "subject": "Re: CBRE valuation — sent, awaiting your review",
        "body": (
            "Hi Marc, I sent over the CBRE valuation last week and asked you to review "
            "the pellet line offer. Still waiting to hear back from you on both before I "
            "can proceed. Let me know."
        ),
    },
    {
        "external_id": "seed-low-priority",
        "thread_id": "thread-newsletter",
        "sender": "Industry Weekly <news@example.com>",
        "subject": "This week in manufacturing: 7 trends to watch",
        "body": (
            "Your weekly digest is here. No action needed — just the latest headlines, "
            "market moves, and a few long reads for the weekend."
        ),
    },
    {
        "external_id": "seed-needs-draft",
        "thread_id": "thread-intro",
        "sender": "Sofia Martins <sofia@example.com>",
        "subject": "Quick intro and a question on the partnership",
        "body": (
            "Hi, great meeting you at the conference. Could you reply with your "
            "availability next week for a 30-minute call to discuss the partnership? "
            "Happy to work around your schedule."
        ),
    },
]


@router.get("/messages")
def list_messages(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, str | None]]:
    """Dev-only: list the user's messages with ids so you can pick one to draft against."""
    if settings.environment != "development":
        raise HTTPException(status_code=404, detail="Not found")
    rows = db.scalars(select(Message).where(Message.user_id == user.id))
    return [
        {
            "id": m.id,
            "external_id": m.external_id,
            "sender": m.sender,
            "subject": m.subject,
            "classification": m.classification,
            "priority": m.priority,
        }
        for m in rows
    ]


@router.post("/seed", response_model=SyncResponse)
def seed_emails(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SyncResponse:
    """Insert the seed emails and run extraction over them. Idempotent per user."""
    if settings.environment != "development":
        raise HTTPException(status_code=404, detail="Not found")

    # A stub connected account so ownership checks elsewhere behave. The token is
    # a placeholder; the seed path never calls Gmail.
    account = db.scalar(
        select(ConnectedAccount).where(
            ConnectedAccount.user_id == user.id, ConnectedAccount.provider == Provider.google
        )
    )
    if account is None:
        db.add(
            ConnectedAccount(
                user_id=user.id,
                provider=Provider.google,
                provider_account_email=user.email,
                scopes=["seed"],
                token_ciphertext=encrypt_token({"seed": True}),
                sync_status=SyncStatus.ok,
                last_synced_at=datetime.now(UTC),
            )
        )
        db.commit()

    ingested = 0
    commitments_found = 0
    for seed in _SEED_EMAILS:
        exists = db.scalar(
            select(Message).where(
                Message.user_id == user.id, Message.external_id == seed["external_id"]
            )
        )
        if exists:
            continue
        message = Message(
            user_id=user.id,
            source="gmail",
            external_id=seed["external_id"],
            thread_id=seed["thread_id"],
            sender=seed["sender"],
            recipients=[user.email],
            subject=seed["subject"],
            snippet=seed["body"][:120],
            sent_at=datetime.now(UTC),
        )
        db.add(message)
        db.flush()
        ingested += 1
        commitments_found += len(extraction.process_message(db, message, body=seed["body"]))

    events_synced = _seed_calendar(db, user)
    return SyncResponse(
        ingested=ingested, commitments_found=commitments_found, events_synced=events_synced
    )


def _seed_calendar(db: Session, user: User) -> int:
    """Seed two upcoming events. The Celine meeting shares an attendee with the
    seeded meeting-prep email so A3 meeting prep can find related context."""
    tomorrow = datetime.now(UTC) + timedelta(days=1)
    events: list[dict[str, Any]] = [
        {
            "external_id": "seed-event-celine",
            "title": "Call with Celine",
            "start_time": tomorrow.replace(hour=14, minute=0, second=0, microsecond=0),
            "end_time": tomorrow.replace(hour=14, minute=30, second=0, microsecond=0),
            "location": "Google Meet",
            "description": "Discuss lunch timing and the scheduling conflict.",
            "attendees": ["celine@example.com", user.email],
        },
        {
            "external_id": "seed-event-internal",
            "title": "Focus block",
            "start_time": tomorrow.replace(hour=9, minute=0, second=0, microsecond=0),
            "end_time": tomorrow.replace(hour=10, minute=0, second=0, microsecond=0),
            "location": None,
            "description": None,
            "attendees": [],
        },
    ]
    for raw in events:
        calendar.upsert_seed_event(db, user.id, raw, user.email)
    return len(events)
