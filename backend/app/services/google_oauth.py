"""Google OAuth flow for Gmail + Calendar (PRD 12.1, 12.2).

Builds the consent URL, exchanges the code for tokens, and rebuilds credentials
from a stored (decrypted) token payload. Tokens are persisted encrypted by the
caller via app.services.crypto."""

from __future__ import annotations

from typing import Any, cast

import httpx
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from app.core.config import get_settings

settings = get_settings()


def _client_config() -> dict[str, Any]:
    return {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_oauth_redirect_uri],
        }
    }


def build_authorization_url(state: str) -> str:
    """Return the Google consent URL. `state` ties the callback to a pending login."""
    flow = Flow.from_client_config(_client_config(), scopes=settings.google_scopes)
    flow.redirect_uri = settings.google_oauth_redirect_uri
    url, _ = flow.authorization_url(
        access_type="offline",  # request a refresh token
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return cast(str, url)


def exchange_code(code: str) -> dict[str, Any]:
    """Exchange an authorization code for a token payload to encrypt and store.

    Includes the account email, read from the OpenID userinfo endpoint, so the
    caller can upsert the User without a second round trip.
    """
    flow = Flow.from_client_config(_client_config(), scopes=settings.google_scopes)
    flow.redirect_uri = settings.google_oauth_redirect_uri
    flow.fetch_token(code=code)
    creds = flow.credentials
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
        "email": _fetch_email(creds),
    }


def _fetch_email(creds: Credentials) -> str | None:
    """Read the account email from the OpenID userinfo endpoint."""
    resp = httpx.get(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {creds.token}"},
        timeout=10,
    )
    if resp.status_code == 200:
        return cast("str | None", resp.json().get("email"))
    return None


def credentials_from_payload(payload: dict[str, Any]) -> Credentials:
    """Rebuild Google Credentials from a decrypted token payload for API calls."""
    return Credentials(  # type: ignore[no-untyped-call]
        token=payload.get("token"),
        refresh_token=payload.get("refresh_token"),
        token_uri=payload.get("token_uri"),
        client_id=payload.get("client_id"),
        client_secret=payload.get("client_secret"),
        scopes=payload.get("scopes"),
    )
