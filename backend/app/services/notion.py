"""Notion REST client (PRD Phase 2 integration).

Thin wrapper around the Notion API. Public surface is two functions
plus an error class — the capability provider in
`app/capabilities/providers/notion_page.py` wraps these. Real SDK code
stays here so swapping for an alternate provider later means writing one
new module."""

from __future__ import annotations

from typing import Any

import httpx

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


class NotionError(Exception):
    """Raised on any non-2xx response from Notion."""


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def whoami(token: str) -> dict[str, Any]:
    """Hit /users/me to validate the token. Returns the user object."""
    with httpx.Client(timeout=15) as client:
        resp = client.get(f"{NOTION_API}/users/me", headers=_headers(token))
    if resp.status_code != 200:
        raise NotionError(f"Notion whoami failed: HTTP {resp.status_code}")
    return resp.json()


def create_page(
    token: str,
    *,
    database_id: str,
    title: str,
    properties: dict[str, Any] | None = None,
    body_text: str | None = None,
) -> dict[str, Any]:
    """Create a page in a database. The database must have a Name (or Title)
    column — we set that to `title`. `properties` may contain extra
    database-defined columns (Status, Date, etc.).

    `body_text` is rendered as a single paragraph block under the page."""
    payload: dict[str, Any] = {
        "parent": {"database_id": database_id},
        "properties": {
            **(properties or {}),
            "Name": {"title": [{"text": {"content": title[:2000]}}]},
        },
    }
    if body_text:
        payload["children"] = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": body_text[:2000]}}]
                },
            }
        ]
    with httpx.Client(timeout=20) as client:
        resp = client.post(f"{NOTION_API}/pages", headers=_headers(token), json=payload)
    if resp.status_code >= 300:
        raise NotionError(f"Notion create_page failed: HTTP {resp.status_code} {resp.text[:200]}")
    return resp.json()
