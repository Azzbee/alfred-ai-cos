"""Anthropic implementation of LLMClient. The only place the anthropic SDK is imported.

Structured extraction uses tool-use: we hand Claude a single tool whose input schema
is the target Pydantic model's JSON schema, force that tool, then validate the tool
input back into the model. System prompts are marked cache-eligible so repeated calls
in a sync batch reuse the prompt prefix (Anthropic prompt caching, 5-minute TTL)."""

from __future__ import annotations

import json
from datetime import date
from typing import Any, cast

from anthropic import Anthropic
from anthropic.types import (
    MessageParam,
    TextBlockParam,
    ToolChoiceToolParam,
    ToolParam,
)
from pydantic import BaseModel

from app.core.config import get_settings
from app.schemas.llm import (
    CaptureResult,
    ClassificationResult,
    DraftResult,
    ExtractedCommitment,
    MeetingContextSummary,
)

settings = get_settings()

_CLASSIFY_SYSTEM = (
    "You are Albert's classification agent. Classify a single email into exactly one "
    "category and a priority. Optimize for precision: prefer low_priority over a false "
    "urgent. Always explain your reasoning in one sentence."
)
_EXTRACT_SYSTEM = (
    "You are Albert's extraction agent. Find commitments (open loops) in an email: things "
    "the user owes someone, or someone owes the user. Quote verbatim evidence for each. "
    "If unsure, lower the confidence rather than inventing a commitment. Return an empty "
    "list when there is nothing actionable.\n"
    "Always set due_date when the email implies any deadline. Resolve relative dates "
    "('tomorrow', 'by Friday', 'end of week', 'before Thursday') against the reference "
    "date given in the message, and return them as absolute YYYY-MM-DD. Set the priority "
    "field: 'critical' or 'high' when a near deadline meets a waiting counterparty or a "
    "blocked deal, 'medium' for routine asks, 'low' for soft or open-ended ones.\n"
    "Set from_automated=true when the sender is automated (no-reply, marketing, "
    "newsletter, notification, security alert, receipt). A 'subscription expires' or "
    "'verify your login' nudge from a service is from_automated=true, not a person "
    "waiting on the user. Set it false only for a real human who expects a response."
)
_DRAFT_SYSTEM = (
    "You are Albert's drafting agent. Write a reply that matches the requested tone, is "
    "concise by default, and never invents facts not present in the thread. Sign off as "
    "the user whose name is given; if no name is given, omit the signature line entirely "
    "rather than inventing one. Do not send; you only draft."
)
_CAPTURE_SYSTEM = (
    "You are Albert's capture agent. The user dumped a messy note (typed or transcribed "
    "speech). Split it into distinct, actionable tasks with concise titles. Resolve "
    "relative dates ('tomorrow', 'Friday', 'next week') against the reference date as "
    "absolute YYYY-MM-DD. Infer priority from urgency words. If the note clearly belongs "
    "to one project, set detected_project. Do not invent tasks the user did not imply."
)


def _tool_for(model: type[BaseModel], name: str, description: str) -> ToolParam:
    return ToolParam(name=name, description=description, input_schema=model.model_json_schema())


class AnthropicLLMClient:
    """Implements app.llm.base.LLMClient."""

    def __init__(self) -> None:
        self._client = Anthropic(api_key=settings.anthropic_api_key)

    def _structured(
        self,
        *,
        model: str,
        system: str,
        user_content: str,
        tool: ToolParam,
    ) -> dict[str, Any]:
        """Force a single tool and return its validated raw input dict."""
        response = self._client.messages.create(
            model=model,
            max_tokens=2048,
            system=[TextBlockParam(type="text", text=system, cache_control={"type": "ephemeral"})],
            tools=[tool],
            tool_choice=ToolChoiceToolParam(type="tool", name=tool["name"]),
            messages=[MessageParam(role="user", content=user_content)],
        )
        for block in response.content:
            if block.type == "tool_use":
                return cast(dict[str, Any], block.input)
        raise ValueError("Anthropic response contained no tool_use block")

    def classify_message(
        self, *, subject: str | None, body: str, sender: str
    ) -> ClassificationResult:
        raw = self._structured(
            model=settings.llm_classify_model,
            system=_CLASSIFY_SYSTEM,
            user_content=f"From: {sender}\nSubject: {subject or '(none)'}\n\n{body}",
            tool=_tool_for(ClassificationResult, "classify", "Record the classification."),
        )
        return ClassificationResult.model_validate(raw)

    def extract_commitments(
        self,
        *,
        subject: str | None,
        body: str,
        sender: str,
        user_email: str,
        reference_date: date,
    ) -> list[ExtractedCommitment]:
        # Wrap the list in an object: tool input schemas must be objects, not arrays.
        class _Wrapper(BaseModel):
            commitments: list[ExtractedCommitment]

        raw = self._structured(
            model=settings.llm_extract_model,
            system=_EXTRACT_SYSTEM,
            user_content=(
                f"Reference date (today): {reference_date.isoformat()}.\n"
                f"The user's email address is {user_email}.\n"
                f"From: {sender}\nSubject: {subject or '(none)'}\n\n{body}"
            ),
            tool=_tool_for(_Wrapper, "record_commitments", "Record extracted commitments."),
        )
        return _Wrapper.model_validate(raw).commitments

    def draft_reply(
        self, *, thread_context: str, instruction: str | None, tone: str, user_name: str | None
    ) -> DraftResult:
        instruction_line = f"\nUser instruction: {instruction}" if instruction else ""
        name_line = (
            f"\nSign off as: {user_name}"
            if user_name
            else "\nThe user's name is unknown; omit the signature line."
        )
        raw = self._structured(
            model=settings.llm_draft_model,
            system=_DRAFT_SYSTEM,
            user_content=f"Tone: {tone}{name_line}{instruction_line}\n\nThread:\n{thread_context}",
            tool=_tool_for(DraftResult, "record_draft", "Record the drafted reply."),
        )
        return DraftResult.model_validate(raw)

    def generate_daily_briefing(self, *, today_payload: dict[str, Any]) -> str:
        response = self._client.messages.create(
            model=settings.llm_extract_model,
            max_tokens=600,
            system=[
                TextBlockParam(
                    type="text",
                    text=(
                        "You are Albert. Write a calm morning briefing in under 90 seconds of "
                        "reading. Lead with what matters today. No more than 5 priorities."
                    ),
                    cache_control={"type": "ephemeral"},
                )
            ],
            messages=[MessageParam(role="user", content=json.dumps(today_payload, default=str))],
        )
        return "".join(b.text for b in response.content if b.type == "text")

    def summarize_meeting_context(
        self, *, event_title: str, related_messages: list[str]
    ) -> MeetingContextSummary:
        joined = "\n---\n".join(related_messages) or "(no related messages found)"
        raw = self._structured(
            model=settings.llm_extract_model,
            system=(
                "You are Albert's meeting-prep agent. Summarize context for an upcoming meeting."
            ),
            user_content=f"Meeting: {event_title}\n\nRelated messages:\n{joined}",
            tool=_tool_for(MeetingContextSummary, "record_summary", "Record the meeting summary."),
        )
        return MeetingContextSummary.model_validate(raw)

    def parse_capture(self, *, text: str, reference_date: date) -> CaptureResult:
        raw = self._structured(
            model=settings.llm_extract_model,
            system=_CAPTURE_SYSTEM,
            user_content=f"Reference date (today): {reference_date.isoformat()}.\n\nNote:\n{text}",
            tool=_tool_for(CaptureResult, "record_tasks", "Record the parsed tasks."),
        )
        return CaptureResult.model_validate(raw)
