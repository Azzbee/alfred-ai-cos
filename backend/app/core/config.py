"""Typed application settings, loaded from environment. See ../../.env.example."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    environment: Literal["development", "staging", "production"] = "development"
    app_base_url: str = "http://localhost:8000"
    log_level: str = "INFO"

    # Postgres / Redis
    database_url: str
    redis_url: str

    # Auth / encryption
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 43_200
    token_encryption_key: str

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_oauth_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    # LLM
    llm_provider: Literal["anthropic"] = "anthropic"
    anthropic_api_key: str = ""
    llm_classify_model: str = "claude-haiku-4-5"
    llm_extract_model: str = "claude-sonnet-4-6"
    llm_draft_model: str = "claude-sonnet-4-6"

    # Gmail OAuth scopes for the first slice: read inbox, create drafts. No send scope yet.
    google_scopes: list[str] = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/calendar.readonly",
        "openid",
        "email",
        "profile",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
