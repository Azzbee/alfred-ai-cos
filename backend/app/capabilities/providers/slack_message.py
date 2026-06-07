"""Slack message capability (PRD Phase 3). Level 3 external comm.

Posts a message to a Slack channel (or DM) the user has authorised via
ConnectedAccount(provider=slack). target = {"channel": str, "text":
str, "thread_ts": str | None}."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.capabilities.base import (
    CapabilityDescription,
    CapabilityError,
    ExecutionResult,
)
from app.db.enums import ActionType, Provider, RiskLevel
from app.db.models import ConnectedAccount, User
from app.services import slack
from app.services.crypto import decrypt_token


class SlackMessageCapability:
    def describe(self) -> CapabilityDescription:
        return CapabilityDescription(
            action_type=ActionType.send_slack_message,
            risk_level=RiskLevel.external_comm,
            title="Send Slack message",
            summary="Post a Slack message on your behalf.",
        )

    def validate(self, db: Session, user: User, payload: dict[str, Any]) -> None:
        if not payload.get("channel"):
            raise CapabilityError("Slack message requires `channel`")
        if not payload.get("text"):
            raise CapabilityError("Slack message requires `text`")
        if self._account(db, user) is None:
            raise CapabilityError("No Slack account connected. Connect Slack in Settings.")

    def execute(self, db: Session, user: User, payload: dict[str, Any]) -> ExecutionResult:
        account = self._account(db, user)
        if account is None:
            raise CapabilityError("No Slack account connected.")
        creds = decrypt_token(account.token_ciphertext)
        token = creds.get("access_token")
        if not token:
            raise CapabilityError("Slack account is missing access_token")
        try:
            result = slack.post_message(
                token,
                channel=str(payload["channel"]),
                text=str(payload["text"]),
                thread_ts=payload.get("thread_ts"),
            )
        except slack.SlackError as exc:
            raise CapabilityError(str(exc)) from exc
        return ExecutionResult(
            detail=f"Posted to Slack channel {payload['channel']}",
            reversible=False,
            data={"slack_ts": result.get("ts"), "channel": result.get("channel")},
        )

    def _account(self, db: Session, user: User) -> ConnectedAccount | None:
        return db.scalar(
            select(ConnectedAccount).where(
                ConnectedAccount.user_id == user.id,
                ConnectedAccount.provider == Provider.slack,
            )
        )
