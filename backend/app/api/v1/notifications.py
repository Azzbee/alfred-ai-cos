"""Notification routes (PRD 12.8): device registration, list, feedback, and quiet-hours
preference. Notification scanning + sending runs in the Celery beat task."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.db.models import Device, Notification, User
from app.schemas.api import (
    DeviceRegisterRequest,
    NotificationFeedbackRequest,
    NotificationOut,
    NotificationPrefs,
)

router = APIRouter(tags=["notifications"])


@router.post("/devices", status_code=204)
def register_device(
    payload: DeviceRegisterRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Register or refresh a push token. Idempotent on the token."""
    existing = db.scalar(select(Device).where(Device.push_token == payload.push_token))
    if existing is None:
        db.add(
            Device(user_id=user.id, push_token=payload.push_token, platform=payload.platform)
        )
    else:
        existing.user_id = user.id
        existing.platform = payload.platform
    db.commit()


@router.get("/notifications", response_model=list[NotificationOut])
def list_notifications(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Notification]:
    return list(
        db.scalars(
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc())
        )
    )


@router.post("/notifications/{notification_id}/feedback", response_model=NotificationOut)
def notification_feedback(
    notification_id: str,
    payload: NotificationFeedbackRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Notification:
    row = db.get(Notification, notification_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    row.useful = payload.useful
    db.commit()
    return row


@router.post("/notifications/prefs", status_code=204)
def set_notification_prefs(
    prefs: NotificationPrefs,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    merged = dict(user.preferences)
    if prefs.quiet_hours is not None:
        merged["quiet_hours"] = prefs.quiet_hours
    user.preferences = merged
    db.commit()
