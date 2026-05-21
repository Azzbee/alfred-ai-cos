"""Response shapes for the Today dashboard. Mirrors packages/shared-types Today types."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.db.enums import Priority


class TodayPriority(BaseModel):
    id: str
    title: str
    priority: Priority
    reason: str
    due_date: date | None
    counterparty: str | None
    confidence: float


class WaitingItem(BaseModel):
    id: str
    description: str
    person: str | None


class MeetingToPrepare(BaseModel):
    id: str
    title: str | None
    start_time: str | None


class TodayDashboard(BaseModel):
    summary: str
    top_priorities: list[TodayPriority]
    people_waiting_on_you: list[WaitingItem]
    you_are_waiting_on: list[WaitingItem]
    meetings_to_prepare: list[MeetingToPrepare]
