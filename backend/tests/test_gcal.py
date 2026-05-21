"""Tests for Google Calendar event normalization. Pure logic, no API calls."""

from datetime import UTC

from app.services.gcal import _normalize, _parse_when


def test_parse_datetime_event() -> None:
    when = {"dateTime": "2026-05-22T14:00:00+00:00"}
    parsed = _parse_when(when)
    assert parsed is not None
    assert parsed.hour == 14
    assert parsed.tzinfo is not None


def test_parse_all_day_event_coerces_to_utc_midnight() -> None:
    parsed = _parse_when({"date": "2026-05-22"})
    assert parsed is not None
    assert parsed.hour == 0
    assert parsed.tzinfo == UTC


def test_parse_missing_when_is_none() -> None:
    assert _parse_when({}) is None


def test_normalize_extracts_attendee_emails() -> None:
    item = {
        "id": "evt_1",
        "summary": "Call with Celine",
        "start": {"dateTime": "2026-05-22T14:00:00+00:00"},
        "end": {"dateTime": "2026-05-22T14:30:00+00:00"},
        "location": "Google Meet",
        "description": "Discuss timing.",
        "attendees": [{"email": "celine@example.com"}, {"email": "self@example.com"}, {}],
    }
    norm = _normalize(item)
    assert norm["external_id"] == "evt_1"
    assert norm["title"] == "Call with Celine"
    assert norm["attendees"] == ["celine@example.com", "self@example.com"]
    assert norm["start_time"] is not None


def test_normalize_handles_missing_optional_fields() -> None:
    item = {"id": "evt_2", "start": {}, "end": {}}
    norm = _normalize(item)
    assert norm["external_id"] == "evt_2"
    assert norm["title"] is None
    assert norm["attendees"] == []
    assert norm["start_time"] is None
