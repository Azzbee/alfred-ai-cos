"""Todoist task capability (PRD Phase 2). Level 2 reversible write.

Creates a Todoist task from `target = {"content": str, "description":
str | None, "due_string": str | None, "priority": int | None,
"project_id": str | None}` using the user's ConnectedAccount token."""

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
from app.services import todoist
from app.services.crypto import decrypt_token


class TodoistTaskCapability:
    def describe(self) -> CapabilityDescription:
        return CapabilityDescription(
            action_type=ActionType.create_todoist_task,
            risk_level=RiskLevel.reversible_write,
            title="Create Todoist task",
            summary="Create a task in your Todoist.",
        )

    def validate(self, db: Session, user: User, payload: dict[str, Any]) -> None:
        if not payload.get("content"):
            raise CapabilityError("Todoist task requires `content`")
        if self._account(db, user) is None:
            raise CapabilityError("No Todoist account connected. Connect Todoist in Settings.")

    def execute(self, db: Session, user: User, payload: dict[str, Any]) -> ExecutionResult:
        account = self._account(db, user)
        if account is None:
            raise CapabilityError("No Todoist account connected.")
        creds = decrypt_token(account.token_ciphertext)
        token = creds.get("access_token")
        if not token:
            raise CapabilityError("Todoist account is missing access_token")
        try:
            task = todoist.create_task(
                token,
                content=str(payload["content"]),
                description=payload.get("description"),
                project_id=payload.get("project_id"),
                due_string=payload.get("due_string"),
                priority=payload.get("priority"),
            )
        except todoist.TodoistError as exc:
            raise CapabilityError(str(exc)) from exc
        return ExecutionResult(
            detail=f"Created Todoist task {task.get('id')}",
            reversible=True,
            data={"todoist_task_id": task.get("id"), "url": task.get("url")},
        )

    def _account(self, db: Session, user: User) -> ConnectedAccount | None:
        return db.scalar(
            select(ConnectedAccount).where(
                ConnectedAccount.user_id == user.id,
                ConnectedAccount.provider == Provider.todoist,
            )
        )
