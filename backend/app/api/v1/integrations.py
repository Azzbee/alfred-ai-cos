"""Paste-token integration endpoints (PRD Phase 2 ergonomic shortcut).

Real OAuth flows for Notion / Todoist / Slack are documented in
`docs/integrations/<provider>.md`. As a pragmatic intermediate, this
router accepts a paste-token payload so the user can connect from the
mobile Settings screen by copying an integration token from the
provider's dashboard.

  - POST /api/v1/integrations/{provider}/connect → save the token
  - DELETE /api/v1/integrations/{provider}        → revoke + delete

Provider-specific shape:
  - notion:  {"access_token": str, "database_id": str}
  - todoist: {"access_token": str}
  - slack:   {"access_token": str (bot xoxb-…)}"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.db.enums import Provider, SyncStatus
from app.db.models import ConnectedAccount, User
from app.services.crypto import encrypt_token

router = APIRouter(prefix="/integrations", tags=["integrations"])

# Providers this endpoint can manage. Google is handled by the OAuth flow.
ManagedProvider = Literal["notion", "todoist", "slack"]


class ConnectRequest(BaseModel):
    access_token: str
    database_id: str | None = None  # Notion only


class ConnectionOut(BaseModel):
    provider: Provider
    connected: bool
    connected_at: datetime | None
    has_database_id: bool


def _provider_enum(name: str) -> Provider:
    try:
        return Provider(name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown provider {name}") from exc


@router.post("/{provider}/connect", response_model=ConnectionOut)
def connect(
    provider: ManagedProvider,
    payload: ConnectRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConnectionOut:
    """Store an integration token. Idempotent: re-posting updates the token."""
    if not payload.access_token.strip():
        raise HTTPException(status_code=400, detail="access_token required")
    if provider == "notion" and not payload.database_id:
        raise HTTPException(status_code=400, detail="Notion connection requires database_id")
    prov = _provider_enum(provider)
    blob = {"access_token": payload.access_token.strip()}
    if payload.database_id:
        blob["database_id"] = payload.database_id.strip()
    existing = db.scalar(
        select(ConnectedAccount).where(
            ConnectedAccount.user_id == user.id, ConnectedAccount.provider == prov
        )
    )
    if existing is not None:
        existing.token_ciphertext = encrypt_token(blob)
        existing.last_synced_at = datetime.now(UTC)
        existing.sync_status = SyncStatus.ok
        existing.sync_error = None
    else:
        existing = ConnectedAccount(
            user_id=user.id,
            provider=prov,
            provider_account_email=user.email,  # placeholder; provider-specific later
            scopes=[],
            token_ciphertext=encrypt_token(blob),
            sync_status=SyncStatus.ok,
            last_synced_at=datetime.now(UTC),
        )
        db.add(existing)
    db.commit()
    return ConnectionOut(
        provider=prov,
        connected=True,
        connected_at=existing.last_synced_at,
        has_database_id=bool(payload.database_id),
    )


@router.delete("/{provider}", status_code=204)
def disconnect(
    provider: ManagedProvider,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete the stored connection. (Provider-side token revocation is
    documented per-provider; we don't call it here because the user can
    revoke from the provider's own dashboard.)"""
    prov = _provider_enum(provider)
    account = db.scalar(
        select(ConnectedAccount).where(
            ConnectedAccount.user_id == user.id, ConnectedAccount.provider == prov
        )
    )
    if account is None:
        raise HTTPException(status_code=404, detail="Not connected")
    db.delete(account)
    db.commit()


@router.get("", response_model=list[ConnectionOut])
def list_connections(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ConnectionOut]:
    """List the user's currently-connected integrations (excluding Google,
    which has its own flow)."""
    rows = list(
        db.scalars(
            select(ConnectedAccount).where(
                ConnectedAccount.user_id == user.id,
                ConnectedAccount.provider.in_([Provider.notion, Provider.todoist, Provider.slack]),
            )
        )
    )
    out: list[ConnectionOut] = []
    for r in rows:
        # We can't safely tell whether the stored blob has a database_id
        # without decrypting; surface a best-effort flag instead.
        out.append(
            ConnectionOut(
                provider=r.provider,
                connected=True,
                connected_at=r.last_synced_at,
                has_database_id=r.provider == Provider.notion,
            )
        )
    return out
