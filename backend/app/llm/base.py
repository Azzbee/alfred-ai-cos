"""Provider-agnostic LLM interface.

Application services depend on this Protocol only. Provider SDK code is isolated
in app/llm/providers/. To add OpenAI or Mistral, implement this Protocol in a new
provider module and wire it in app/llm/__init__.py. Do not import a provider SDK
anywhere outside app/llm/providers/.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Protocol

from app.schemas.llm import (
    CaptureResult,
    ClassificationResult,
    DraftResult,
    ExtractedCommitment,
    MeetingContextSummary,
)


class LLMClient(Protocol):
    """The full contract Albert's AI pipeline relies on.

    Methods that extract structure must return validated Pydantic models; the
    provider implementation is responsible for using structured outputs
    (Anthropic tool-use, OpenAI JSON mode) and validating before returning.
    """

    def classify_message(
        self, *, subject: str | None, body: str, sender: str
    ) -> ClassificationResult:
        """Classify one email into a category + priority (PRD 12.2)."""
        ...

    def extract_commitments(
        self,
        *,
        subject: str | None,
        body: str,
        sender: str,
        user_email: str,
        reference_date: date,
    ) -> list[ExtractedCommitment]:
        """Extract open-loop commitments from a message (PRD 12.5).

        reference_date anchors relative deadlines ("tomorrow", "by Friday") so the
        model can resolve them to absolute dates. Pass the email's sent date.
        """
        ...

    def draft_reply(
        self, *, thread_context: str, instruction: str | None, tone: str, user_name: str | None
    ) -> DraftResult:
        """Draft a reply to an email thread in the requested tone (PRD 12.9).

        user_name is the signature the draft should sign off as; None means omit the
        signature rather than invent one."""
        ...

    def generate_daily_briefing(self, *, today_payload: dict[str, Any]) -> str:
        """Produce a short morning briefing from the Today payload (PRD 12.7)."""
        ...

    def summarize_meeting_context(
        self, *, event_title: str, related_messages: list[str]
    ) -> MeetingContextSummary:
        """Summarize context for an upcoming meeting (PRD 12.3 / 10.5)."""
        ...

    def parse_capture(self, *, text: str, reference_date: date) -> CaptureResult:
        """Turn a messy voice/text note into structured tasks (PRD 10.3, journey 6).

        reference_date anchors relative dates ("tomorrow", "Friday") to absolute dates.
        """
        ...
