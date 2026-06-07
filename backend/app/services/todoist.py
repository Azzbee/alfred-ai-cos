"""Todoist REST v2 client (PRD Phase 2 integration).

Two operations: create a task, list tasks (for the bidirectional sync
follow-up). The capability provider in
`app/capabilities/providers/todoist_task.py` wraps these."""

from __future__ import annotations

from typing import Any

import httpx

TODOIST_API = "https://api.todoist.com/rest/v2"


class TodoistError(Exception):
    pass


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def create_task(
    token: str,
    *,
    content: str,
    description: str | None = None,
    project_id: str | None = None,
    due_string: str | None = None,
    priority: int | None = None,
) -> dict[str, Any]:
    """Create a Todoist task. `content` is the title; `due_string` accepts
    Todoist's natural-language ("tomorrow at 5pm"); priority is 1-4 with
    4 = highest."""
    payload: dict[str, Any] = {"content": content[:500]}
    if description:
        payload["description"] = description[:16000]
    if project_id:
        payload["project_id"] = project_id
    if due_string:
        payload["due_string"] = due_string
    if priority is not None and 1 <= priority <= 4:
        payload["priority"] = priority
    with httpx.Client(timeout=15) as client:
        resp = client.post(f"{TODOIST_API}/tasks", headers=_headers(token), json=payload)
    if resp.status_code >= 300:
        raise TodoistError(f"Todoist create_task failed: HTTP {resp.status_code} {resp.text[:200]}")
    return resp.json()
