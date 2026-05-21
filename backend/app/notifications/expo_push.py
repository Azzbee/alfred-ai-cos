"""Expo Push provider. The only place the Expo Push API is called. No credentials
needed for development; production needs APNs/FCM configured in the Expo project."""

from __future__ import annotations

from typing import Any

import httpx

_ENDPOINT = "https://exp.host/--/api/v2/push/send"


class ExpoPushProvider:
    """Implements app.services.notifications.NotificationProvider."""

    def send(self, *, push_token: str, title: str, body: str, data: dict[str, Any]) -> None:
        resp = httpx.post(
            _ENDPOINT,
            json={"to": push_token, "title": title, "body": body, "data": data},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
