"""Priority Agent (PRD 14.1 agent 3, 16.1): transparent weighted scoring.

The first version is a rules-based, explainable scorer (PRD 16.1 says start
transparent, refine with user behavior later). Every score carries a
human-readable reason (PRD principle 3). The LLM is not used here so priority is
deterministic and debuggable; learning from feedback is deferred (see TODO)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.db.enums import CommitmentOwner, Priority
from app.db.models import Commitment


@dataclass
class ScoredCommitment:
    commitment: Commitment
    score: float
    priority: Priority
    reason: str


def _days_until(due: date | None, today: date) -> int | None:
    if due is None:
        return None
    return (due - today).days


def score_commitment(commitment: Commitment, *, today: date) -> ScoredCommitment:
    """Return a 0-100 score, a derived priority label, and a reason string."""
    score = 0.0
    reasons: list[str] = []

    days = _days_until(commitment.due_date, today)
    if days is not None:
        if days < 0:
            score += 50
            reasons.append(f"overdue by {abs(days)} day(s)")
        elif days == 0:
            score += 45
            reasons.append("due today")
        elif days == 1:
            score += 35
            reasons.append("due tomorrow")
        elif days <= 3:
            score += 20
            reasons.append(f"due in {days} days")
        else:
            score += 5

    # The user owing someone is more actionable than someone owing the user.
    if commitment.owner == CommitmentOwner.user:
        score += 20
        if commitment.counterparty:
            reasons.append(f"{commitment.counterparty} is waiting on you")
    else:
        score += 5
        if commitment.counterparty:
            reasons.append(f"you are waiting on {commitment.counterparty}")

    # Extraction confidence dampens the score so shaky items rank lower.
    score *= 0.5 + 0.5 * commitment.confidence
    if commitment.confidence < 0.6:
        reasons.append("low confidence, shown as a suggestion")

    priority = _label(score)
    reason = "High priority because " if priority in (Priority.critical, Priority.high) else ""
    reason += ", and ".join(reasons) + "." if reasons else "No strong urgency signals."
    return ScoredCommitment(commitment=commitment, score=score, priority=priority, reason=reason)


def _label(score: float) -> Priority:
    if score >= 60:
        return Priority.critical
    if score >= 40:
        return Priority.high
    if score >= 20:
        return Priority.medium
    if score >= 5:
        return Priority.low
    return Priority.noise
