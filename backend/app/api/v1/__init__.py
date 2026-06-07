"""Aggregates all v1 routers under /api/v1."""

from fastapi import APIRouter

from app.api.v1 import (
    actions,
    assistant,
    auth,
    briefings,
    capture,
    commitments,
    dev,
    drafts,
    inbox,
    me,
    meetings,
    messages,
    notifications,
    people,
    plan,
    projects,
    search,
    senders,
    sync,
    tasks,
    today,
    waiting,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(assistant.router)
api_router.include_router(sync.router)
api_router.include_router(today.router)
api_router.include_router(commitments.router)
api_router.include_router(drafts.router)
api_router.include_router(actions.router)
api_router.include_router(meetings.router)
api_router.include_router(messages.router)
api_router.include_router(briefings.router)
api_router.include_router(tasks.router)
api_router.include_router(capture.router)
api_router.include_router(waiting.router)
api_router.include_router(me.router)
api_router.include_router(notifications.router)
api_router.include_router(inbox.router)
api_router.include_router(search.router)
api_router.include_router(senders.router)
api_router.include_router(people.router)
api_router.include_router(projects.router)
api_router.include_router(plan.router)
api_router.include_router(dev.router)
