"""Waiting-for tracker (PRD 10.1 sections 3-4, journey 5). Derives both directions
of open loops from commitments: who is waiting on the user, and who the user is
waiting on, with the age of each so stale items can be chased."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.enums import CommitmentOwner, CommitmentStatus
from app.db.models import Commitment


@dataclass
class WaitingEntry:
    commitment: Commitment
    age_days: int


@dataclass
class WaitingView:
    waiting_on_you: list[WaitingEntry]  # user owes the counterparty
    you_are_waiting_on: list[WaitingEntry]  # counterparty owes the user


def _age_days(commitment: Commitment, *, now: datetime) -> int:
    created = commitment.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    return max((now - created).days, 0)


def build_waiting(db: Session, user_id: str) -> WaitingView:
    now = datetime.now(UTC)
    open_with_counterparty = list(
        db.scalars(
            select(Commitment).where(
                Commitment.user_id == user_id,
                Commitment.status == CommitmentStatus.open,
                Commitment.counterparty.is_not(None),
            )
        )
    )
    waiting_on_you: list[WaitingEntry] = []
    you_are_waiting_on: list[WaitingEntry] = []
    for c in open_with_counterparty:
        # Automated/marketing/notification senders are not real people expecting a
        # reply, so they never appear in either waiting bucket (the task may still
        # surface in Today's priorities).
        if c.from_automated:
            continue
        entry = WaitingEntry(commitment=c, age_days=_age_days(c, now=now))
        if c.owner == CommitmentOwner.user:
            waiting_on_you.append(entry)
        else:
            you_are_waiting_on.append(entry)

    # Oldest first: stale items are the ones most worth chasing.
    waiting_on_you.sort(key=lambda e: e.age_days, reverse=True)
    you_are_waiting_on.sort(key=lambda e: e.age_days, reverse=True)
    return WaitingView(waiting_on_you=waiting_on_you, you_are_waiting_on=you_are_waiting_on)
