"""Aggregates all v1 routers under /api/v1."""

from fastapi import APIRouter

from app.api.v1 import (
    actions,
    auth,
    briefings,
    capture,
    commitments,
    dev,
    drafts,
    me,
    meetings,
    notifications,
    sync,
    tasks,
    today,
    waiting,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(sync.router)
api_router.include_router(today.router)
api_router.include_router(commitments.router)
api_router.include_router(drafts.router)
api_router.include_router(actions.router)
api_router.include_router(meetings.router)
api_router.include_router(briefings.router)
api_router.include_router(tasks.router)
api_router.include_router(capture.router)
api_router.include_router(waiting.router)
api_router.include_router(me.router)
api_router.include_router(notifications.router)
api_router.include_router(dev.router)
