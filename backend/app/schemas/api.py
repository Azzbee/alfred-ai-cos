"""Request/response schemas for API routes outside the Today dashboard."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from app.db.enums import (
    ActionStatus,
    CommitmentOwner,
    CommitmentStatus,
    Priority,
    SourceType,
    TaskStatus,
)


# --- Auth ---
class AuthStartResponse(BaseModel):
    authorization_url: str
    state: str


class SessionToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Commitments ---
class CommitmentOut(BaseModel):
    id: str
    description: str
    owner: CommitmentOwner
    counterparty: str | None
    due_date: date | None
    priority: Priority
    status: CommitmentStatus
    evidence: str | None
    confidence: float

    model_config = {"from_attributes": True}


# --- Drafts ---
class DraftCreateRequest(BaseModel):
    message_id: str
    tone: str = "concise"
    instruction: str | None = None


class DraftOut(BaseModel):
    id: str
    message_id: str
    subject: str | None
    body: str
    tone: str
    gmail_draft_id: str | None

    model_config = {"from_attributes": True}


# --- Action approval (the level-3 spine) ---
class ActionProposalOut(BaseModel):
    id: str
    action_type: str
    risk_level: int
    reason: str | None
    status: ActionStatus

    model_config = {"from_attributes": True}


class SyncResponse(BaseModel):
    ingested: int
    commitments_found: int
    events_synced: int = 0


# --- Meetings ---
class UpcomingMeeting(BaseModel):
    id: str
    title: str | None
    start_time: datetime | None
    end_time: datetime | None
    location: str | None
    attendees: list[str]
    prep_required: bool

    model_config = {"from_attributes": True}


class MeetingPrepOut(BaseModel):
    event: UpcomingMeeting
    summary: str
    open_commitments: list[str]
    suggested_questions: list[str]
    related_message_count: int


# --- Briefing ---
class BriefingOut(BaseModel):
    id: str
    date: date
    summary: str
    user_feedback: str | None

    model_config = {"from_attributes": True}


class BriefingFeedbackRequest(BaseModel):
    useful: bool


# --- Tasks ---
class TaskCreateRequest(BaseModel):
    title: str
    description: str | None = None
    due_date: date | None = None
    priority: Priority = Priority.medium


class TaskOut(BaseModel):
    id: str
    title: str
    description: str | None
    due_date: date | None
    priority: Priority
    status: TaskStatus
    source_type: SourceType
    source_id: str | None

    model_config = {"from_attributes": True}


# --- Capture ---
class CaptureRequest(BaseModel):
    text: str


class CaptureResponse(BaseModel):
    tasks: list[TaskOut]
    detected_project: str | None
