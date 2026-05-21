"""Smart notifications (PRD 12.8). Calm, not noisy: importance thresholds, quiet
hours, batching, and dedup. The decision logic is pure and tested; delivery goes
through a NotificationProvider so the transport (Expo Push now) is swappable."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time
from datetime import date as date_type
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.enums import (
    CommitmentOwner,
    CommitmentStatus,
    NotificationImportance,
    NotificationStatus,
    NotificationType,
)
from app.db.models import Commitment, Device, Notification, User

# Importance of each notification type. Below the user's threshold => batched.
_IMPORTANCE: dict[NotificationType, NotificationImportance] = {
    NotificationType.approval_needed: NotificationImportance.high,
    NotificationType.deadline_risk: NotificationImportance.high,
    NotificationType.schedule_conflict: NotificationImportance.high,
    NotificationType.meeting_prep: NotificationImportance.normal,
    NotificationType.follow_up_due: NotificationImportance.normal,
    NotificationType.unanswered_email: NotificationImportance.normal,
    NotificationType.reminder: NotificationImportance.normal,
    NotificationType.daily_briefing: NotificationImportance.low,
}

# Proactiveness preference -> minimum importance that sends immediately.
_THRESHOLD: dict[str, NotificationImportance] = {
    "quiet": NotificationImportance.high,
    "balanced": NotificationImportance.normal,
    "very_proactive": NotificationImportance.low,
}


@dataclass
class DeliveryDecision:
    send_now: bool
    reason: str


def importance_of(ntype: NotificationType) -> NotificationImportance:
    return _IMPORTANCE.get(ntype, NotificationImportance.normal)


def _parse_quiet_hours(raw: object) -> tuple[time, time] | None:
    """Parse a 'HH-HH' or 'HH:MM-HH:MM' quiet-hours string into (start, end)."""
    if not isinstance(raw, str) or "-" not in raw:
        return None
    start_s, end_s = raw.split("-", 1)

    def _t(s: str) -> time | None:
        s = s.strip()
        try:
            if ":" in s:
                h, m = s.split(":")
                return time(int(h), int(m))
            return time(int(s))
        except (ValueError, TypeError):
            return None

    start, end = _t(start_s), _t(end_s)
    if start is None or end is None:
        return None
    return start, end


def in_quiet_hours(now: time, quiet: tuple[time, time] | None) -> bool:
    """True if `now` falls in the quiet window. Handles windows that cross midnight."""
    if quiet is None:
        return False
    start, end = quiet
    if start <= end:
        return start <= now < end
    # Crosses midnight, e.g. 22:00-07:00.
    return now >= start or now < end


def decide_delivery(
    *,
    ntype: NotificationType,
    now: time,
    proactiveness: str | None,
    quiet_hours_raw: object,
) -> DeliveryDecision:
    """Decide whether to send immediately or hold/batch a notification."""
    threshold = _THRESHOLD.get(proactiveness or "balanced", NotificationImportance.normal)
    if importance_of(ntype) < threshold:
        return DeliveryDecision(False, "below importance threshold; batched")
    if in_quiet_hours(now, _parse_quiet_hours(quiet_hours_raw)):
        # High-importance items still send during quiet hours (escalation).
        if importance_of(ntype) >= NotificationImportance.high:
            return DeliveryDecision(True, "high importance overrides quiet hours")
        return DeliveryDecision(False, "held by quiet hours")
    return DeliveryDecision(True, "sent")


class NotificationProvider(Protocol):
    """Sends a push notification to a device token."""

    def send(self, *, push_token: str, title: str, body: str, data: dict[str, Any]) -> None: ...


def enqueue(
    db: Session,
    user_id: str,
    *,
    ntype: NotificationType,
    title: str,
    body: str,
    payload: dict[str, Any] | None = None,
    dedup_key: str | None = None,
) -> Notification | None:
    """Create a notification unless one with the same dedup_key already exists.
    Returns None when deduplicated (PRD 12.8 do not notify twice for the same thing)."""
    if dedup_key is not None:
        existing = db.scalar(
            select(Notification).where(
                Notification.user_id == user_id, Notification.dedup_key == dedup_key
            )
        )
        if existing is not None:
            return None
    notification = Notification(
        user_id=user_id,
        type=ntype,
        title=title,
        body=body,
        payload=payload or {},
        dedup_key=dedup_key,
        status=NotificationStatus.pending,
    )
    db.add(notification)
    db.commit()
    return notification


def devices_for(db: Session, user_id: str) -> list[Device]:
    return list(db.scalars(select(Device).where(Device.user_id == user_id)))


def quiet_hours_pref(user: User) -> object:
    return user.preferences.get("quiet_hours")


def proactiveness_pref(user: User) -> str | None:
    value = user.preferences.get("proactiveness")
    return value if isinstance(value, str) else None


def dispatch_pending(
    db: Session, user: User, *, now: time, provider: NotificationProvider
) -> dict[str, int]:
    """Send pending notifications that clear the user's threshold and quiet hours;
    leave the rest pending. Returns counts. Idempotent: only touches pending rows."""
    pending = list(
        db.scalars(
            select(Notification).where(
                Notification.user_id == user.id,
                Notification.status == NotificationStatus.pending,
            )
        )
    )
    if not pending:
        return {"sent": 0, "held": 0}

    targets = devices_for(db, user.id)
    sent = held = 0
    for n in pending:
        decision = decide_delivery(
            ntype=n.type,
            now=now,
            proactiveness=proactiveness_pref(user),
            quiet_hours_raw=quiet_hours_pref(user),
        )
        if not decision.send_now:
            held += 1
            continue
        for device in targets:
            provider.send(
                push_token=device.push_token,
                title=n.title,
                body=n.body,
                data={"type": str(n.type), **n.payload},
            )
        n.status = NotificationStatus.sent
        n.sent_at = datetime.now(UTC)
        sent += 1
    db.commit()
    return {"sent": sent, "held": held}


def scan_for_risks(db: Session, user_id: str, *, today: date_type) -> int:
    """Enqueue notifications for at-risk open loops (PRD 12.8). Deduped per
    commitment+type so a rescan does not re-notify. Returns the count enqueued."""
    open_commitments = list(
        db.scalars(
            select(Commitment).where(
                Commitment.user_id == user_id,
                Commitment.status == CommitmentStatus.open,
                Commitment.due_date.is_not(None),
            )
        )
    )
    enqueued = 0
    for c in open_commitments:
        assert c.due_date is not None
        days = (c.due_date - today).days
        # Deadline risk: the user owes something due within a day or overdue.
        if c.owner == CommitmentOwner.user and days <= 1:
            label = "overdue" if days < 0 else ("due today" if days == 0 else "due tomorrow")
            created = enqueue(
                db,
                user_id,
                ntype=NotificationType.deadline_risk,
                title=f"{label.capitalize()}: {c.description[:60]}",
                body=c.reason or f"This is {label} and {c.counterparty or 'someone'} is waiting.",
                payload={"commitment_id": c.id},
                dedup_key=f"deadline:{c.id}",
            )
            if created is not None:
                enqueued += 1
    return enqueued
