"""Calendar ingestion (PRD 12.3). Pulls upcoming Google Calendar events and upserts
CalendarEvent rows. An event is flagged prep_required when it has external attendees,
which is the signal meeting-prep (A3) keys off."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.enums import Provider
from app.db.models import CalendarEvent, ConnectedAccount, User
from app.services import gcal
from app.services.crypto import decrypt_token


def _account(db: Session, user_id: str) -> ConnectedAccount:
    account = db.scalar(
        select(ConnectedAccount).where(
            ConnectedAccount.user_id == user_id,
            ConnectedAccount.provider == Provider.google,
        )
    )
    if account is None:
        raise ValueError("No connected Google account for user")
    return account


def _prep_required(event: dict[str, Any], user_email: str) -> bool:
    """True when the event has at least one attendee other than the user."""
    others = [a for a in event.get("attendees", []) if a and a != user_email]
    return len(others) > 0


def sync_calendar(db: Session, user_id: str, *, days_ahead: int = 14) -> list[CalendarEvent]:
    """Fetch upcoming events and upsert them. Returns the rows touched (new + updated)."""
    account = _account(db, user_id)
    user = db.get(User, user_id)
    user_email = user.email if user else ""
    token = decrypt_token(account.token_ciphertext)

    touched: list[CalendarEvent] = []
    for raw in gcal.list_upcoming_events(token, days_ahead=days_ahead):
        touched.append(_upsert_event(db, user_id, raw, user_email))
    db.commit()
    return touched


def upsert_seed_event(
    db: Session, user_id: str, raw: dict[str, Any], user_email: str
) -> CalendarEvent:
    """Upsert a single normalized event. Used by the dev seed path (no Google call)."""
    event = _upsert_event(db, user_id, raw, user_email)
    db.commit()
    return event


def _upsert_event(db: Session, user_id: str, raw: dict[str, Any], user_email: str) -> CalendarEvent:
    existing = db.scalar(
        select(CalendarEvent).where(
            CalendarEvent.user_id == user_id,
            CalendarEvent.external_id == raw["external_id"],
        )
    )
    prep = _prep_required(raw, user_email)
    if existing is None:
        event = CalendarEvent(
            user_id=user_id,
            external_id=raw["external_id"],
            title=raw["title"],
            start_time=raw["start_time"],
            end_time=raw["end_time"],
            location=raw["location"],
            description=raw["description"],
            attendees=raw["attendees"],
            prep_required=prep,
        )
        db.add(event)
        return event
    existing.title = raw["title"]
    existing.start_time = raw["start_time"]
    existing.end_time = raw["end_time"]
    existing.location = raw["location"]
    existing.description = raw["description"]
    existing.attendees = raw["attendees"]
    existing.prep_required = prep
    return existing
