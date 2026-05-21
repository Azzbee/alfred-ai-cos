"""WhatsApp message capability (level 3) via the official Business Cloud API.

Sandbox-oriented: sends to verified test numbers. The official API only permits
template messages outside a 24-hour customer-initiated session window, so this provider
sends templates by default. Unofficial automation (driving WhatsApp Web, unapproved bulk
messaging) is not built and never will be: it violates Meta's terms and gets numbers
banned. See docs/integrations/whatsapp.md. The only place the WhatsApp API is touched."""

from __future__ import annotations

from typing import Any, cast

import httpx
from sqlalchemy.orm import Session

from app.capabilities.base import (
    CapabilityDescription,
    CapabilityError,
    ExecutionResult,
)
from app.core.config import get_settings
from app.db.enums import ActionType, RiskLevel
from app.db.models import User

settings = get_settings()


def _endpoint() -> str:
    return f"https://graph.facebook.com/v21.0/{settings.whatsapp_phone_number_id}/messages"


class WhatsAppMessageCapability:
    def describe(self) -> CapabilityDescription:
        return CapabilityDescription(
            action_type=ActionType.send_message,
            risk_level=RiskLevel.external_comm,
            title="Send a WhatsApp message",
            summary="Send a WhatsApp message via the official Business API.",
        )

    def validate(self, db: Session, user: User, payload: dict[str, Any]) -> None:  # noqa: ARG002
        if not settings.whatsapp_access_token or not settings.whatsapp_phone_number_id:
            raise CapabilityError("WhatsApp is not configured.")
        if not payload.get("to"):
            raise CapabilityError("A recipient 'to' number is required.")
        # Either a template name or, within a session window, a body.
        if not payload.get("template") and not payload.get("body"):
            raise CapabilityError("Provide a 'template' or a 'body' (session message).")

    def execute(self, db: Session, user: User, payload: dict[str, Any]) -> ExecutionResult:  # noqa: ARG002
        body = self._build_body(payload)
        resp = httpx.post(
            _endpoint(),
            headers={"Authorization": f"Bearer {settings.whatsapp_access_token}"},
            json=body,
            timeout=30,
        )
        if resp.status_code >= 400:
            raise CapabilityError(f"WhatsApp error: {resp.text}")
        data = resp.json()
        message_id = ""
        messages = data.get("messages")
        if isinstance(messages, list) and messages:
            message_id = cast(str, messages[0].get("id", ""))
        return ExecutionResult(
            detail="WhatsApp message sent", reversible=False, data={"message_id": message_id}
        )

    @staticmethod
    def _build_body(payload: dict[str, Any]) -> dict[str, Any]:
        to = payload["to"]
        if payload.get("template"):
            return {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": payload["template"],
                    "language": {"code": payload.get("language", "en_US")},
                },
            }
        return {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": payload["body"]},
        }
