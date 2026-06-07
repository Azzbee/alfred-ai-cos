"""Google Drive context retrieval (PRD Phase 3).

Read-only access to the user's Drive so the Meeting Prep + Draft
agents can pull the latest doc on a project, find "the spec Marc
shared on Monday," and surface file metadata in commitments.

Scopes (added in app.core.config):
  - drive.readonly        — read file contents
  - drive.metadata.readonly — file listings without contents

This is a thin wrapper around the existing google-api-python-client
machinery — auth comes from the same ConnectedAccount(provider=google)
the rest of the Google features use. NOTE: adding the Drive scopes
invalidates existing tokens; users re-consent on next sign-in."""

from __future__ import annotations

from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core.config import get_settings


def _service(token_payload: dict[str, Any]) -> Any:
    settings = get_settings()
    creds = Credentials(
        token=token_payload.get("token"),
        refresh_token=token_payload.get("refresh_token"),
        token_uri=token_payload.get("token_uri"),
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=token_payload.get("scopes") or settings.google_scopes,
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def search_files(
    token_payload: dict[str, Any],
    *,
    query: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search Drive by fulltext + name. Returns a list of file metadata
    dicts (id, name, mimeType, modifiedTime, webViewLink)."""
    svc = _service(token_payload)
    # `fullText contains` searches indexed content; `name contains` covers
    # filename hits. Combine with OR for recall.
    esc = _escape(query)
    q = f"(fullText contains '{esc}' or name contains '{esc}') and trashed = false"
    fields = (
        "files(id, name, mimeType, modifiedTime, webViewLink, owners(displayName, emailAddress))"
    )
    resp = (
        svc.files()
        .list(
            q=q,
            pageSize=max(1, min(limit, 50)),
            fields=fields,
            orderBy="modifiedTime desc",
        )
        .execute()
    )
    return resp.get("files", [])


def get_file_text(token_payload: dict[str, Any], *, file_id: str) -> str:
    """Read a Drive file as plain text. Google Docs → exported text;
    other types fall back to the raw bytes when text-shaped. Returns
    the decoded body (capped at 100KB to keep LLM context bounded)."""
    svc = _service(token_payload)
    # Get metadata first so we know whether to use export_media (Google
    # native types) vs get_media (uploaded files).
    meta = svc.files().get(fileId=file_id, fields="id, mimeType, name").execute()
    mime = meta.get("mimeType", "")

    if mime == "application/vnd.google-apps.document":
        data = svc.files().export(fileId=file_id, mimeType="text/plain").execute()
    elif mime == "application/vnd.google-apps.spreadsheet":
        data = svc.files().export(fileId=file_id, mimeType="text/csv").execute()
    elif mime in {"text/plain", "text/csv", "text/markdown", "application/json"}:
        data = svc.files().get_media(fileId=file_id).execute()
    else:
        return f"(binary file — {mime}; download via webViewLink)"

    if isinstance(data, bytes):
        text = data.decode("utf-8", errors="replace")
    else:
        text = str(data)
    return text[:100_000]


def _escape(s: str) -> str:
    """Single-quote-escape for Drive's query syntax."""
    return s.replace("\\", "\\\\").replace("'", "\\'")
