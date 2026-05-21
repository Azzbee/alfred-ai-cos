"""LLM factory. Returns the configured provider as an LLMClient. Services should
call get_llm() and depend on the LLMClient Protocol, never on a provider directly."""

from functools import lru_cache

from app.core.config import get_settings
from app.llm.base import LLMClient


@lru_cache
def get_llm() -> LLMClient:
    settings = get_settings()
    if settings.llm_provider == "anthropic":
        from app.llm.providers.anthropic_client import AnthropicLLMClient

        return AnthropicLLMClient()
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
