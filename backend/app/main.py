"""FastAPI application entrypoint. Run: uv run uvicorn app.main:app --reload"""

from fastapi import FastAPI

from app.api.v1 import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Albert",
    version="0.1.0",
    description="AI chief of staff. First slice: Gmail -> commitments -> Today -> draft reply.",
)
app.include_router(api_router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}
