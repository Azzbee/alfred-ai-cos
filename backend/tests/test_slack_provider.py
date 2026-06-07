"""Tests for the Slack capability provider."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.capabilities.base import CapabilityError
from app.capabilities.providers.slack_message import SlackMessageCapability
from app.db.enums import Provider, SyncStatus
from app.db.models import ConnectedAccount, User
from app.services import slack
from app.services.crypto import encrypt_token


@pytest.fixture
def user(db: Session) -> User:
    u = User(email="adam@adam.dev")
    db.add(u)
    db.commit()
    return u


def _connect(db: Session, user: User, *, token: str = "xoxb-test") -> None:
    db.add(
        ConnectedAccount(
            user_id=user.id,
            provider=Provider.slack,
            provider_account_email=user.email,
            scopes=["chat:write"],
            token_ciphertext=encrypt_token({"access_token": token}),
            sync_status=SyncStatus.ok,
        )
    )
    db.commit()


def test_validate_needs_channel_and_text(db: Session, user: User) -> None:
    _connect(db, user)
    cap = SlackMessageCapability()
    with pytest.raises(CapabilityError, match="channel"):
        cap.validate(db, user, {"text": "x"})
    with pytest.raises(CapabilityError, match="text"):
        cap.validate(db, user, {"channel": "C1"})


def test_validate_requires_account(db: Session, user: User) -> None:
    cap = SlackMessageCapability()
    with pytest.raises(CapabilityError, match="No Slack account"):
        cap.validate(db, user, {"channel": "C1", "text": "x"})


def test_execute_calls_slack(db: Session, user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    _connect(db, user)
    seen: dict[str, object] = {}

    def fake_post(token: str, **kw):
        seen.update(token=token, **kw)
        return {"ok": True, "ts": "1717000000.000100", "channel": "C1"}

    monkeypatch.setattr(slack, "post_message", fake_post)
    result = SlackMessageCapability().execute(
        db,
        user,
        {"channel": "C1", "text": "hi", "thread_ts": "1717000000.000050"},
    )
    assert seen["token"] == "xoxb-test"
    assert seen["channel"] == "C1"
    assert seen["text"] == "hi"
    assert seen["thread_ts"] == "1717000000.000050"
    assert result.reversible is False  # send is not reversible
    assert result.data["slack_ts"] == "1717000000.000100"


def test_execute_handles_slack_error(
    db: Session, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _connect(db, user)

    def boom(*a, **kw):
        raise slack.SlackError("channel_not_found")

    monkeypatch.setattr(slack, "post_message", boom)
    with pytest.raises(CapabilityError, match="channel_not_found"):
        SlackMessageCapability().execute(db, user, {"channel": "C1", "text": "hi"})


def test_describe_is_level_3() -> None:
    desc = SlackMessageCapability().describe()
    assert desc.action_type.value == "send_slack_message"
    assert desc.risk_level.value == 3
