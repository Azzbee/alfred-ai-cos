"""WhatsApp provider tests. Mocks httpx; no network or real WhatsApp touched."""

from typing import Any

import httpx
import pytest
from sqlalchemy.orm import Session

from app.capabilities.base import CapabilityError
from app.capabilities.providers import whatsapp_message
from app.db.enums import ActionType, RiskLevel
from app.db.models import User


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self) -> dict[str, Any]:
        return self._payload


@pytest.fixture
def user(db: Session) -> User:
    u = User(email="wa@example.com")
    db.add(u)
    db.commit()
    return u


def _configure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(whatsapp_message.settings, "whatsapp_access_token", "tok")
    monkeypatch.setattr(whatsapp_message.settings, "whatsapp_phone_number_id", "12345")


def test_describe_is_level_3() -> None:
    desc = whatsapp_message.WhatsAppMessageCapability().describe()
    assert desc.action_type == ActionType.send_message
    assert desc.risk_level == RiskLevel.external_comm


def test_unconfigured_validate_raises(db: Session, user: User) -> None:
    cap = whatsapp_message.WhatsAppMessageCapability()
    with pytest.raises(CapabilityError, match="not configured"):
        cap.validate(db, user, {"to": "15551234567", "template": "x"})


def test_requires_recipient_and_content(
    db: Session, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure(monkeypatch)
    cap = whatsapp_message.WhatsAppMessageCapability()
    with pytest.raises(CapabilityError, match="recipient"):
        cap.validate(db, user, {"template": "x"})
    with pytest.raises(CapabilityError, match="template' or a 'body"):
        cap.validate(db, user, {"to": "15551234567"})


def test_template_message_sends(
    db: Session, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure(monkeypatch)
    captured: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> _FakeResponse:
        captured["json"] = kwargs.get("json")
        captured["headers"] = kwargs.get("headers")
        return _FakeResponse(200, {"messages": [{"id": "wamid.123"}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    cap = whatsapp_message.WhatsAppMessageCapability()
    payload = {"to": "15551234567", "template": "reminder", "language": "en_US"}
    cap.validate(db, user, payload)
    result = cap.execute(db, user, payload)

    assert result.data["message_id"] == "wamid.123"
    assert captured["json"]["type"] == "template"
    assert captured["json"]["template"]["name"] == "reminder"
    assert captured["headers"]["Authorization"] == "Bearer tok"


def test_session_body_message_sends(
    db: Session, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure(monkeypatch)
    captured: dict[str, Any] = {}
    monkeypatch.setattr(
        httpx,
        "post",
        lambda url, **k: (captured.update(k), _FakeResponse(200, {"messages": [{"id": "m"}]}))[1],
    )
    cap = whatsapp_message.WhatsAppMessageCapability()
    cap.execute(db, user, {"to": "15551234567", "body": "hello"})
    assert captured["json"]["type"] == "text"
    assert captured["json"]["text"]["body"] == "hello"


def test_api_error_surfaces(db: Session, user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    _configure(monkeypatch)
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _FakeResponse(400, {"error": "bad"}))
    cap = whatsapp_message.WhatsAppMessageCapability()
    with pytest.raises(CapabilityError, match="WhatsApp error"):
        cap.execute(db, user, {"to": "15551234567", "body": "hi"})
