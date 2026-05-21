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


# --- Notifications ---
class DeviceRegisterRequest(BaseModel):
    push_token: str
    platform: str | None = None


class NotificationOut(BaseModel):
    id: str
    type: str
    title: str
    body: str
    status: str
    useful: bool | None

    model_config = {"from_attributes": True}


class NotificationFeedbackRequest(BaseModel):
    useful: bool


class NotificationPrefs(BaseModel):
    # Stored in User.preferences. quiet_hours is "HH-HH" or "HH:MM-HH:MM".
    quiet_hours: str | None = None


# --- Onboarding / account ---
class OnboardingPrefs(BaseModel):
    # PRD 9.1 calibration questions. Free-form strings so the option set can evolve
    # without a migration; the mobile app supplies the choices.
    focus: str | None = None  # work | school | personal | founder | all
    optimize_for: str | None = None  # deadlines | priorities | follow_ups | meetings | inbox
    proactiveness: str | None = None  # quiet | balanced | very_proactive


class MeOut(BaseModel):
    id: str
    email: str
    name: str | None
    timezone: str
    preferences: dict[str, object]
    onboarded: bool


# --- Waiting-for ---
class WaitingEntryOut(BaseModel):
    id: str
    description: str
    counterparty: str | None
    due_date: date | None
    age_days: int
    source_type: SourceType
    source_id: str | None


class WaitingView(BaseModel):
    waiting_on_you: list[WaitingEntryOut]
    you_are_waiting_on: list[WaitingEntryOut]


# --- Capture ---
class CaptureRequest(BaseModel):
    text: str


class CaptureResponse(BaseModel):
    tasks: list[TaskOut]
    detected_project: str | None
