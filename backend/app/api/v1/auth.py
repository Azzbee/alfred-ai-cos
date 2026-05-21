"""Google OAuth login + connection routes (PRD 9.1, 12.1, 12.2).

The same Google consent grants Gmail + Calendar and serves as Albert's login.
On callback Albert upserts the User, stores encrypted tokens, and returns its own
session JWT. State is signed into a short-lived JWT to bind the callback safely.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_session_token
from app.db.base import get_db
from app.db.enums import Provider, SyncStatus
from app.db.models import ConnectedAccount, User
from app.schemas.api import AuthStartResponse, SessionToken
from app.services import google_oauth
from app.services.crypto import encrypt_token

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.get("/google/start", response_model=AuthStartResponse)
def google_start() -> AuthStartResponse:
    """Begin the Google OAuth flow. The mobile app opens authorization_url."""
    nonce = secrets.token_urlsafe(16)
    state = jwt.encode(
        {"nonce": nonce, "exp": datetime.now(UTC) + timedelta(minutes=10)},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return AuthStartResponse(
        authorization_url=google_oauth.build_authorization_url(state), state=state
    )


@router.get("/google/callback")
def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Google redirects here. Exchange code, upsert user, store tokens, mint session."""
    try:
        jwt.decode(state, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from exc

    token_payload = google_oauth.exchange_code(code)
    profile_email = _require_email(token_payload)

    user = db.scalar(select(User).where(User.email == profile_email))
    if user is None:
        user = User(email=profile_email)
        db.add(user)
        db.flush()

    account = db.scalar(
        select(ConnectedAccount).where(
            ConnectedAccount.user_id == user.id, ConnectedAccount.provider == Provider.google
        )
    )
    ciphertext = encrypt_token(token_payload)
    if account is None:
        account = ConnectedAccount(
            user_id=user.id,
            provider=Provider.google,
            provider_account_email=profile_email,
            scopes=token_payload.get("scopes", []),
            token_ciphertext=ciphertext,
            sync_status=SyncStatus.never,
        )
        db.add(account)
    else:
        account.token_ciphertext = ciphertext
        account.scopes = token_payload.get("scopes", [])
    db.commit()

    session = create_session_token(user.id)
    # Hand the session back to the app via deep link. The app reads the token param.
    return RedirectResponse(url=f"albert://auth?token={session}")


@router.post("/dev-session", response_model=SessionToken)
def dev_session(email: str, db: Session = Depends(get_db)) -> SessionToken:
    """Development-only: mint a session for a user by email without Google.
    Disabled outside development."""
    if settings.environment != "development":
        raise HTTPException(status_code=404, detail="Not found")
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email)
        db.add(user)
        db.commit()
    return SessionToken(access_token=create_session_token(user.id))


def _require_email(token_payload: dict[str, Any]) -> str:
    """Account email, read from Google's userinfo during exchange_code."""
    email = token_payload.get("email")
    if not email or not isinstance(email, str):
        raise HTTPException(status_code=502, detail="Google did not return an account email")
    return email
