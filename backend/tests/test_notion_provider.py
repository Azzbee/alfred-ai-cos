"""Tests for the Notion capability provider."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.capabilities.base import CapabilityError
from app.capabilities.providers.notion_page import NotionPageCapability
from app.db.enums import Provider, SyncStatus
from app.db.models import ConnectedAccount, User
from app.services import notion
from app.services.crypto import encrypt_token


@pytest.fixture
def user(db: Session) -> User:
    u = User(email="adam@adam.dev")
    db.add(u)
    db.commit()
    return u


def _connect(
    db: Session, user: User, *, token: str = "notion-secret", database_id: str = "db_123"
) -> None:
    account = ConnectedAccount(
        user_id=user.id,
        provider=Provider.notion,
        provider_account_email=user.email,
        scopes=["insert_content"],
        token_ciphertext=encrypt_token({"access_token": token, "database_id": database_id}),
        sync_status=SyncStatus.ok,
    )
    db.add(account)
    db.commit()


def test_validate_requires_title(db: Session, user: User) -> None:
    _connect(db, user)
    cap = NotionPageCapability()
    with pytest.raises(CapabilityError, match="title"):
        cap.validate(db, user, {})


def test_validate_requires_connected_account(db: Session, user: User) -> None:
    cap = NotionPageCapability()
    with pytest.raises(CapabilityError, match="No Notion account"):
        cap.validate(db, user, {"title": "x"})


def test_execute_calls_notion_api(db: Session, user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    _connect(db, user)
    seen: dict[str, object] = {}

    def fake_create(token: str, *, database_id: str, title: str, **kw):
        seen.update(token=token, database_id=database_id, title=title, **kw)
        return {"id": "page_abc", "url": "https://notion.so/page_abc"}

    monkeypatch.setattr(notion, "create_page", fake_create)
    result = NotionPageCapability().execute(
        db,
        user,
        {"title": "Sign the contract", "body": "Due Friday"},
    )
    assert seen["token"] == "notion-secret"
    assert seen["database_id"] == "db_123"
    assert seen["title"] == "Sign the contract"
    assert result.data["notion_page_id"] == "page_abc"
    assert result.reversible is True


def test_execute_propagates_notion_error(
    db: Session, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _connect(db, user)

    def boom(*args, **kw):
        raise notion.NotionError("HTTP 401")

    monkeypatch.setattr(notion, "create_page", boom)
    with pytest.raises(CapabilityError, match="HTTP 401"):
        NotionPageCapability().execute(db, user, {"title": "x"})


def test_describe_is_level_2(db: Session) -> None:
    desc = NotionPageCapability().describe()
    assert desc.action_type.value == "create_notion_page"
    assert desc.risk_level.value == 2
