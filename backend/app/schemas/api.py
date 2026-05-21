"""Request/response schemas for API routes outside the Today dashboard."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.db.enums import ActionStatus, CommitmentOwner, CommitmentStatus, Priority


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
