"""Slack Web API client (PRD Phase 3 integration).

Two operations: post a message to a channel, and a read helper for
listing DMs. The capability provider wraps `post_message`.

Slack auth lives in ConnectedAccount.token_ciphertext as
{"access_token": "xoxb-..."}. The OAuth registration flow is documented
in `docs/integrations/slack.md`."""

from __future__ import annotations

from typing import Any

import httpx

SLACK_API = "https://slack.com/api"


class SlackError(Exception):
    pass


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }


def post_message(
    token: str,
    *,
    channel: str,
    text: str,
    thread_ts: str | None = None,
) -> dict[str, Any]:
    """Post `text` to `channel`. `channel` may be a channel id ("C123…"),
    a DM id ("D123…"), or a user id ("U123…") in which case Slack opens
    an IM. `thread_ts` makes the post a thread reply."""
    payload: dict[str, Any] = {"channel": channel, "text": text[:40000]}
    if thread_ts:
        payload["thread_ts"] = thread_ts
    with httpx.Client(timeout=15) as client:
        resp = client.post(
            f"{SLACK_API}/chat.postMessage",
            headers=_headers(token),
            json=payload,
        )
    body = resp.json()
    if not body.get("ok"):
        raise SlackError(f"Slack post_message failed: {body.get('error')}")
    return body


def conversations_list(token: str, *, limit: int = 50) -> list[dict[str, Any]]:
    """Read the user's DM list (im channels). Used by the Slack message
    source so DMs can be ingested as Messages."""
    with httpx.Client(timeout=15) as client:
        resp = client.get(
            f"{SLACK_API}/conversations.list",
            headers=_headers(token),
            params={"types": "im", "limit": limit},
        )
    body = resp.json()
    if not body.get("ok"):
        raise SlackError(f"Slack conversations.list failed: {body.get('error')}")
    return body.get("channels", [])
