"""Test bootstrap. Sets the minimal env the Settings model requires before any
app module imports it, so unit tests run without a real .env or live services."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://albert:albert@localhost:5432/albert")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "test-secret")
# A valid Fernet key (urlsafe base64, 32 bytes) so crypto imports succeed in tests.
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", "ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=")
