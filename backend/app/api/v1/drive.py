"""Google Drive context endpoint (PRD Phase 3).

Read-only Drive search. Returns file metadata only; body retrieval is
a separate fetch so the mobile client can preview before committing
to a (potentially large) text load.

  - GET /api/v1/drive/search?q=…&limit=…
  - GET /api/v1/drive/files/{file_id}/text → plain text content
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.db.enums import Provider
from app.db.models import ConnectedAccount, User
from app.services import gdrive
from app.services.crypto import decrypt_token

router = APIRouter(prefix="/drive", tags=["drive"])


class DriveFileOut(BaseModel):
    id: str
    name: str
    mime_type: str
    modified_at: datetime | None
    web_view_link: str | None
    owner_name: str | None
    owner_email: str | None


class FileTextOut(BaseModel):
    id: str
    text: str
    truncated: bool


def _google_token(db: Session, user: User) -> dict[str, Any]:
    account = db.scalar(
        select(ConnectedAccount).where(
            ConnectedAccount.user_id == user.id,
            ConnectedAccount.provider == Provider.google,
        )
    )
    if account is None:
        raise HTTPException(
            status_code=400,
            detail="Google account not connected. Reconnect with Drive scopes.",
        )
    return decrypt_token(account.token_ciphertext)


def _to_out(raw: dict[str, Any]) -> DriveFileOut:
    owners = raw.get("owners") or []
    first_owner = owners[0] if owners else {}
    return DriveFileOut(
        id=raw["id"],
        name=raw.get("name", "(no name)"),
        mime_type=raw.get("mimeType", ""),
        modified_at=_parse_dt(raw.get("modifiedTime")),
        web_view_link=raw.get("webViewLink"),
        owner_name=first_owner.get("displayName"),
        owner_email=first_owner.get("emailAddress"),
    )


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


@router.get("/search", response_model=list[DriveFileOut])
def search(
    q: str = Query(min_length=2, max_length=200),
    limit: int = Query(default=10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DriveFileOut]:
    token = _google_token(db, user)
    try:
        rows = gdrive.search_files(token, query=q, limit=limit)
    except Exception as exc:  # noqa: BLE001 — propagate as 502; the user sees the cause
        raise HTTPException(status_code=502, detail=f"Drive search failed: {exc}") from exc
    return [_to_out(r) for r in rows]


@router.get("/files/{file_id}/text", response_model=FileTextOut)
def file_text(
    file_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileTextOut:
    token = _google_token(db, user)
    try:
        text = gdrive.get_file_text(token, file_id=file_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Drive read failed: {exc}") from exc
    return FileTextOut(id=file_id, text=text, truncated=len(text) >= 100_000)
