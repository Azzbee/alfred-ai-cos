"""A fake LLMClient for service-level tests. Returns deterministic structured output
without calling Anthropic, so tests are fast and offline."""

from __future__ import annotations

from datetime import date

from app.db.enums import CommitmentOwner, MessageClassification, Priority
from app.schemas.llm import (
    CaptureResult,
    ClassificationResult,
    DraftResult,
    ExtractedCommitment,
    MeetingContextSummary,
    ParsedTask,
)


class FakeLLM:
    """Implements app.llm.base.LLMClient with canned responses."""

    def __init__(
        self,
        *,
        commitments: list[ExtractedCommitment] | None = None,
        capture_tasks: list[ParsedTask] | None = None,
        detected_project: str | None = None,
    ) -> None:
        self._commitments = commitments or []
        self._capture_tasks = capture_tasks or []
        self._detected_project = detected_project
        self.briefing_calls: list[dict] = []

    def classify_message(
        self, *, subject: str | None, body: str, sender: str
    ) -> ClassificationResult:
        return ClassificationResult(
            classification=MessageClassification.needs_reply,
            priority=Priority.medium,
            action_required=True,
            reason="fake classification",
        )

    def extract_commitments(
        self,
        *,
        subject: str | None,
        body: str,
        sender: str,
        user_email: str,
        reference_date: date,
    ) -> list[ExtractedCommitment]:
        return self._commitments

    def draft_reply(
        self, *, thread_context: str, instruction: str | None, tone: str, user_name: str | None
    ) -> DraftResult:
        sig = f"\n{user_name}" if user_name else ""
        return DraftResult(subject="Re: test", body=f"[{tone}] drafted reply{sig}")

    def generate_daily_briefing(self, *, today_payload: dict) -> str:
        self.briefing_calls.append(today_payload)
        return "Good morning. 1 thing matters today."

    def summarize_meeting_context(
        self, *, event_title: str, related_messages: list[str]
    ) -> MeetingContextSummary:
        return MeetingContextSummary(
            summary=f"Context for {event_title}",
            open_commitments=["confirm timing"],
            suggested_questions=["what is the location?"],
        )

    def parse_capture(self, *, text: str, reference_date: date) -> CaptureResult:
        return CaptureResult(tasks=self._capture_tasks, detected_project=self._detected_project)


class FakeNotifier:
    """Implements app.services.notifications.NotificationProvider; records sends."""

    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []

    def send(self, *, push_token: str, title: str, body: str, data: dict) -> None:
        self.sent.append({"push_token": push_token, "title": title, "body": body, "data": data})


def fake_commitment(**kwargs: object) -> ExtractedCommitment:
    defaults: dict[str, object] = {
        "description": "Send the report",
        "owner": CommitmentOwner.user,
        "counterparty": "Dana",
        "due_date": None,
        "priority": Priority.high,
        "evidence": "please send the report",
        "confidence": 0.9,
    }
    defaults.update(kwargs)
    return ExtractedCommitment(**defaults)  # type: ignore[arg-type]
