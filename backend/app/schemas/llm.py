"""Structured-output schemas the LLM layer returns. These are the validated
shapes every provider implementation must produce (PRD 14.3)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.db.enums import CommitmentOwner, MessageClassification, Priority


class ClassificationResult(BaseModel):
    classification: MessageClassification
    priority: Priority
    action_required: bool
    reason: str = Field(description="Why this classification, in one sentence.")


class ExtractedCommitment(BaseModel):
    description: str
    owner: CommitmentOwner
    counterparty: str | None = None
    due_date: date | None = None
    priority: Priority = Priority.medium
    evidence: str = Field(description="Verbatim quote from the source supporting this commitment.")
    confidence: float = Field(ge=0.0, le=1.0)


class DraftResult(BaseModel):
    subject: str | None = None
    body: str


class MeetingContextSummary(BaseModel):
    summary: str
    open_commitments: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
