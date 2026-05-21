"""Symmetric encryption for third-party OAuth tokens at rest (PRD 13.1, 13.2).

Tokens are encrypted with Fernet before they touch Postgres. The key comes from
TOKEN_ENCRYPTION_KEY and must be managed as a secret (rotated via re-encryption)."""

import json
from typing import Any, cast

from cryptography.fernet import Fernet

from app.core.config import get_settings

_fernet = Fernet(get_settings().token_encryption_key.encode())


def encrypt_token(token_payload: dict[str, Any]) -> str:
    """Encrypt an OAuth token dict (access_token, refresh_token, expiry, ...)."""
    return _fernet.encrypt(json.dumps(token_payload).encode()).decode()


def decrypt_token(ciphertext: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(_fernet.decrypt(ciphertext.encode()).decode()))
