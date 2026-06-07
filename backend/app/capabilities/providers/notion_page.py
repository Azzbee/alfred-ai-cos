"""Notion page capability (PRD Phase 2). Level 2 reversible write.

Creates a page in a Notion database the user has connected via OAuth.
The capability reads:
  - The Notion access token from the user's ConnectedAccount
    (provider=notion, token_ciphertext stores {"access_token": "...",
    "database_id": "..."}).
  - target = {"title": str, "body": str | None, "properties": dict | None}.

A real Notion API call goes out; the page id comes back in
ExecutionResult.data so the user can navigate to the created page."""

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
from app.services import notion
from app.services.crypto import decrypt_token


class NotionPageCapability:
    def describe(self) -> CapabilityDescription:
        return CapabilityDescription(
            action_type=ActionType.create_notion_page,
            risk_level=RiskLevel.reversible_write,
            title="Create Notion page",
            summary="Create a page in your Notion workspace.",
        )

    def validate(self, db: Session, user: User, payload: dict[str, Any]) -> None:
        if not payload.get("title"):
            raise CapabilityError("Notion page requires a title")
        account = self._account(db, user)
        if account is None:
            raise CapabilityError("No Notion account connected. Connect Notion in Settings.")

    def execute(self, db: Session, user: User, payload: dict[str, Any]) -> ExecutionResult:
        account = self._account(db, user)
        if account is None:
            raise CapabilityError("No Notion account connected.")
        creds = decrypt_token(account.token_ciphertext)
        token = creds.get("access_token")
        database_id = creds.get("database_id")
        if not token or not database_id:
            raise CapabilityError("Notion account is missing access_token or database_id")
        try:
            page = notion.create_page(
                token,
                database_id=database_id,
                title=str(payload["title"]),
                properties=payload.get("properties"),
                body_text=payload.get("body"),
            )
        except notion.NotionError as exc:
            raise CapabilityError(str(exc)) from exc
        page_id = page.get("id")
        url = page.get("url")
        return ExecutionResult(
            detail=f"Created Notion page {page_id}",
            reversible=True,
            data={"notion_page_id": page_id, "url": url},
        )

    def _account(self, db: Session, user: User) -> ConnectedAccount | None:
        return db.scalar(
            select(ConnectedAccount).where(
                ConnectedAccount.user_id == user.id,
                ConnectedAccount.provider == Provider.notion,
            )
        )
