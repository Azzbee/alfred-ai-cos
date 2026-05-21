"""Aggregates all v1 routers under /api/v1."""

from fastapi import APIRouter

from app.api.v1 import actions, auth, commitments, drafts, sync, today

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(sync.router)
api_router.include_router(today.router)
api_router.include_router(commitments.router)
api_router.include_router(drafts.router)
api_router.include_router(actions.router)
