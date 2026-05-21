"""Google Calendar API wrapper. Read-only (calendar.readonly scope).

Lists upcoming events from the primary calendar and normalizes them into the shape
CalendarEvent expects. Like the Gmail wrapper, this is the only place the Calendar
API surface is touched, so the rest of the app stays provider-agnostic about Google."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from googleapiclient.discovery import build

from app.services.google_oauth import credentials_from_payload


def _service(token_payload: dict[str, Any]) -> Any:
    """Return a Calendar API client. googleapiclient is untyped, hence Any."""
    creds = credentials_from_payload(token_payload)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def list_upcoming_events(
    token_payload: dict[str, Any], *, days_ahead: int = 14, max_results: int = 50
) -> list[dict[str, Any]]:
    """Return normalized upcoming events from now to now + days_ahead.

    Each dict: external_id, title, start_time (datetime|None), end_time, location,
    description, attendees (list[str] of emails). All-day events have date-only
    start/end, which we coerce to midnight UTC so the model's DateTime columns hold.
    """
    svc = _service(token_payload)
    now = datetime.now(UTC)
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days_ahead)).isoformat()

    resp = (
        svc.events()
        .list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            maxResults=max_results,
        )
        .execute()
    )
    return [_normalize(item) for item in resp.get("items", [])]


def _normalize(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "external_id": item["id"],
        "title": item.get("summary"),
        "start_time": _parse_when(item.get("start", {})),
        "end_time": _parse_when(item.get("end", {})),
        "location": item.get("location"),
        "description": item.get("description"),
        "attendees": [
            a["email"] for a in item.get("attendees", []) or [] if a.get("email")
        ],
    }


def _parse_when(when: dict[str, Any]) -> datetime | None:
    """Parse a Google event start/end. 'dateTime' is RFC3339; 'date' is all-day."""
    if "dateTime" in when:
        return datetime.fromisoformat(when["dateTime"])
    if "date" in when:
        return datetime.fromisoformat(when["date"]).replace(tzinfo=UTC)
    return None
