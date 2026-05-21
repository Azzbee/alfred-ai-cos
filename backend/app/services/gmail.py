"""Gmail API wrapper for the slice: list recent messages, fetch one, create a draft.

Sending is intentionally absent. The slice never sends; it only creates Gmail drafts
(gmail.compose scope). Sending would be a level-3 action gated by ActionProposal and
would require the gmail.send scope, added when that path is built (see docs/TODO.md)."""

from __future__ import annotations

import base64
from email.message import EmailMessage
from typing import Any, cast

from googleapiclient.discovery import build

from app.services.google_oauth import credentials_from_payload


def _service(token_payload: dict[str, Any]) -> Any:
    """Return a Gmail API client. googleapiclient is untyped, hence Any."""
    creds = credentials_from_payload(token_payload)
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def list_recent_message_ids(token_payload: dict[str, Any], *, max_results: int = 25) -> list[str]:
    """Return ids of recent inbox messages, newest first."""
    svc = _service(token_payload)
    resp = (
        svc.users()
        .messages()
        .list(userId="me", labelIds=["INBOX"], maxResults=max_results)
        .execute()
    )
    return [m["id"] for m in resp.get("messages", [])]


def get_message(token_payload: dict[str, Any], message_id: str) -> dict[str, Any]:
    """Fetch a normalized message: id, threadId, sender, recipients, subject, snippet, body."""
    svc = _service(token_payload)
    raw = svc.users().messages().get(userId="me", id=message_id, format="full").execute()
    headers = {h["name"].lower(): h["value"] for h in raw.get("payload", {}).get("headers", [])}
    return {
        "external_id": raw["id"],
        "thread_id": raw.get("threadId"),
        "sender": headers.get("from", ""),
        "recipients": [r.strip() for r in headers.get("to", "").split(",") if r.strip()],
        "subject": headers.get("subject"),
        "snippet": raw.get("snippet"),
        "body": _extract_body(raw.get("payload", {})),
        "internal_date_ms": raw.get("internalDate"),
    }


def _extract_body(payload: dict[str, Any]) -> str:
    """Walk the MIME tree and return the first text/plain body, decoded."""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    for part in payload.get("parts", []) or []:
        body = _extract_body(part)
        if body:
            return body
    return ""


def create_draft(
    token_payload: dict[str, Any],
    *,
    to: str,
    subject: str,
    body: str,
    thread_id: str | None = None,
) -> str:
    """Create a Gmail draft and return its draft id. Does not send."""
    svc = _service(token_payload)
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    encoded = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    draft_body: dict[str, Any] = {"message": {"raw": encoded}}
    if thread_id:
        draft_body["message"]["threadId"] = thread_id
    created = svc.users().drafts().create(userId="me", body=draft_body).execute()
    return cast(str, created["id"])
