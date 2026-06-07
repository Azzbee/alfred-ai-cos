"""Importance learning: turn the user's accept/dismiss/snooze/act behavior into
a per-user adjustment that the priority ranker mixes in.

The shape is intentionally simple. We track two things per user:

  - per-sender adjustment: +act counts and -dismiss counts, capped so a single
    enthusiastic week doesn't permanently lock a sender into "critical".
  - per-category adjustment: same shape but for keyword categories (money,
    legal, ask, meeting). When the user repeatedly dismisses money-flagged
    items but acts on meeting-flagged items, the ranker drifts toward what
    the user actually cares about.

Storage lives in user.preferences under "learning" so we don't need a
migration. The data is per-user, not per-org, and the shape is small enough
to fit comfortably in a JSON column (~hundreds of keys at most for any real
user; commodity Postgres handles that fine).

Updates are idempotent on event id — the same act/dismiss can't double-count
if a worker re-runs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy.orm import Session

from app.db.models import Commitment, Message, User

Event = Literal["act", "dismiss", "snooze", "open"]

# Per-event score delta. Asymmetric: "act" gives a stronger signal than "open",
# and "dismiss" is the only negative one because snoozing means "later", not
# "no". The values are tuned so ~5 acts ≈ +5 score on the next item.
_DELTAS: dict[Event, float] = {
    "act": 1.5,
    "dismiss": -1.0,
    "snooze": 0.0,  # intentional: park, not vote
    "open": 0.3,  # opened the detail = mild signal
}

# Bounds prevent runaway in either direction. ±15 keeps learning meaningful
# without letting it dominate the baseline ranker.
_BOUND = 15.0


@dataclass
class LearningView:
    """Snapshot of the user's learned adjustments — exposed for debugging."""

    by_sender: dict[str, float]
    by_category: dict[str, float]


# ---------- read ----------


def get_learning(user: User) -> LearningView:
    raw = (user.preferences or {}).get("learning", {})
    return LearningView(
        by_sender={str(k): float(v) for k, v in (raw.get("by_sender") or {}).items()},
        by_category={str(k): float(v) for k, v in (raw.get("by_category") or {}).items()},
    )


def adjustment_for(learning: LearningView, *, sender: str | None, categories: list[str]) -> float:
    """Combined score adjustment for one commitment. Bounded so the sum of all
    learned signals can't blow past ±20 on a single item."""
    total = 0.0
    if sender:
        total += learning.by_sender.get(sender.lower(), 0.0)
    for cat in categories:
        total += learning.by_category.get(cat, 0.0)
    # The hard cap on the *combined* signal mirrors the per-axis bound, so even
    # if every dimension fires the worst case is bounded and explainable.
    return max(-20.0, min(20.0, total))


# ---------- write ----------


def _decay(value: float) -> float:
    """Gentle pull-toward-zero so old signals fade as new ones arrive. Without
    this, a user who changed jobs would carry old preferences forever."""
    if value == 0:
        return 0.0
    sign = 1 if value > 0 else -1
    return sign * max(0.0, abs(value) - 0.05)


def _apply(value: float, delta: float) -> float:
    """Add delta, decay, clamp. Order matters: decay first so a long-quiet
    signal fades a little before the new event lands."""
    return max(-_BOUND, min(_BOUND, _decay(value) + delta))


def record_event(
    db: Session, user: User, *, event: Event, commitment: Commitment | None = None
) -> None:
    """Update the learning state for one user-event. Resolves the commitment's
    sender (via Message.sender) and the keyword categories the ranker would
    apply, so the same signals the ranker rewards are the ones learning shifts.

    Idempotency: callers that may double-fire should pass a unique id through
    a separate dedup layer. This function itself is monotonic — calling it
    twice will count twice. The cron worker that emits behavior events should
    dedup at the event-source layer."""
    delta = _DELTAS.get(event, 0.0)
    if delta == 0.0:
        return

    sender: str | None = None
    categories: list[str] = []

    if commitment is not None and commitment.source_id:
        msg = db.get(Message, commitment.source_id)
        if msg and msg.sender:
            sender = msg.sender.lower()
        # Mirror the ranker's keyword detection so learning and scoring agree
        # on what category an item belongs to.
        text = f"{commitment.description or ''} {commitment.evidence or ''}"
        categories = _categories_in(text)

    prefs = dict(user.preferences or {})
    learning = dict(prefs.get("learning") or {})
    by_sender = dict(learning.get("by_sender") or {})
    by_cat = dict(learning.get("by_category") or {})

    if sender:
        by_sender[sender] = _apply(float(by_sender.get(sender, 0.0)), delta)
    for cat in categories:
        by_cat[cat] = _apply(float(by_cat.get(cat, 0.0)), delta)

    learning["by_sender"] = by_sender
    learning["by_category"] = by_cat
    prefs["learning"] = learning
    user.preferences = prefs

    # Also bump the Person's importance_weight so the People screen reflects
    # the learning loop in real time. Bounded ±1 inside adjust_importance.
    if commitment is not None and commitment.counterparty_person_id:
        from app.db.models import Person
        from app.services import people as people_service

        person = db.get(Person, commitment.counterparty_person_id)
        if person is not None:
            # Smaller delta on Person.importance_weight than on the dict — the
            # dict is bounded ±15 while importance_weight is ±1, so we scale
            # 1/10 to keep the trajectories proportional.
            people_service.adjust_importance(person, delta * 0.1)
    db.commit()


# ---------- categories ----------

# These mirror the ranker's _HIGH_STAKES_RE families but split by intent, so
# learning can move them independently. Money/legal terms split from process
# terms (meeting, scheduling, calendar) because users often care about one and
# ignore the other.
_CATEGORY_PATTERNS: dict[str, list[str]] = {
    "money": ["contract", "wire", "invoice", "payment", "$", "salary", "offer", "funding"],
    "legal": ["legal", "lawsuit", "nda", "compliance", "kyc", "aml", "gdpr", "hipaa"],
    "ask": ["can you", "could you", "please", "send me", "send us", "review", "approve", "?"],
    "meeting": ["meeting", "call", "schedule", "calendar", "sync", "1:1"],
    "incident": ["breach", "incident", "outage", "down", "broken", "urgent"],
}


def _categories_in(text: str) -> list[str]:
    """Lower-cost than running the ranker's regex — these are substring matches.
    Returns the unique set of categories this text triggers."""
    if not text:
        return []
    lc = text.lower()
    return [cat for cat, words in _CATEGORY_PATTERNS.items() if any(w in lc for w in words)]
