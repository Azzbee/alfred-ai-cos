"""Tests for the Todoist capability provider."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.capabilities.base import CapabilityError
from app.capabilities.providers.todoist_task import TodoistTaskCapability
from app.db.enums import Provider, SyncStatus
from app.db.models import ConnectedAccount, User
from app.services import todoist
from app.services.crypto import encrypt_token


@pytest.fixture
def user(db: Session) -> User:
    u = User(email="adam@adam.dev")
    db.add(u)
    db.commit()
    return u


def _connect(db: Session, user: User, *, token: str = "td-secret") -> None:
    db.add(
        ConnectedAccount(
            user_id=user.id,
            provider=Provider.todoist,
            provider_account_email=user.email,
            scopes=["data:read_write"],
            token_ciphertext=encrypt_token({"access_token": token}),
            sync_status=SyncStatus.ok,
        )
    )
    db.commit()


def test_validate_requires_content(db: Session, user: User) -> None:
    _connect(db, user)
    with pytest.raises(CapabilityError, match="content"):
        TodoistTaskCapability().validate(db, user, {})


def test_validate_requires_account(db: Session, user: User) -> None:
    with pytest.raises(CapabilityError, match="No Todoist account"):
        TodoistTaskCapability().validate(db, user, {"content": "x"})


def test_execute_calls_todoist(db: Session, user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    _connect(db, user)
    seen: dict[str, object] = {}

    def fake_create(token: str, **kw):
        seen.update(token=token, **kw)
        return {"id": "task_123", "url": "https://todoist.com/showTask?id=task_123"}

    monkeypatch.setattr(todoist, "create_task", fake_create)
    result = TodoistTaskCapability().execute(
        db,
        user,
        {"content": "Sign contract", "due_string": "tomorrow", "priority": 3},
    )
    assert seen["token"] == "td-secret"
    assert seen["content"] == "Sign contract"
    assert seen["due_string"] == "tomorrow"
    assert seen["priority"] == 3
    assert result.data["todoist_task_id"] == "task_123"


def test_execute_handles_api_error(
    db: Session, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _connect(db, user)

    def boom(*a, **kw):
        raise todoist.TodoistError("HTTP 403")

    monkeypatch.setattr(todoist, "create_task", boom)
    with pytest.raises(CapabilityError, match="403"):
        TodoistTaskCapability().execute(db, user, {"content": "x"})


def test_describe_is_level_2() -> None:
    desc = TodoistTaskCapability().describe()
    assert desc.action_type.value == "create_todoist_task"
    assert desc.risk_level.value == 2
