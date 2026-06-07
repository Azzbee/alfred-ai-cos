"""Auto-approve policies (PRD Phase 3 "delegated workflows").

The execution spine (services/execution.py) calls `find_matching` for
every ActionProposal it's about to require user approval on. When a
policy matches, the proposal is flipped to approved + executed in the
same request — no notification, no waiting.

Safety rails baked in:

  - Wildcard policies refused at create time (must specify at least
    counterparty_email or counterparty_domain).
  - Financial actions (make_payment / place_order) require max_cents
    and never match when the proposal value exceeds it.
  - active_window restricts matching to a time-of-day range so a
    misconfigured policy can't fire at 3am.
  - fire_count tracked per policy so the UI can show how aggressive
    a rule is in practice.

Risk taxonomy lock: policies for risk_level >= 4 (financial / sensitive)
also require a max_cents AND a non-wildcard counterparty. Anything more
permissive than that is explicitly refused — delegation has to remain
narrow at the dangerous tiers."""

from __future__ import annotations

from datetime import datetime, time
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.enums import ActionType, RiskLevel
from app.db.models import ActionProposal, AutoApprovePolicy, User


def _user_tz(user: User) -> ZoneInfo:
    try:
        return ZoneInfo(user.timezone or "UTC")
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _parse_window(raw: str | None) -> tuple[time, time] | None:
    """Parse 'HH-HH' or 'HH:MM-HH:MM' into (start, end). None = always
    active."""
    if not raw or "-" not in raw:
        return None
    a, b = raw.split("-", 1)

    def _t(s: str) -> time | None:
        s = s.strip()
        try:
            if ":" in s:
                h, m = s.split(":", 1)
                return time(int(h), int(m))
            return time(int(s))
        except ValueError:
            return None

    start, end = _t(a), _t(b)
    if start is None or end is None:
        return None
    return start, end


def _in_window(now: time, window: tuple[time, time] | None) -> bool:
    if window is None:
        return True
    start, end = window
    if start <= end:
        return start <= now < end
    return now >= start or now < end


# ---------- match ----------


def _proposal_value_cents(proposal: ActionProposal) -> int | None:
    """For financial actions, extract the proposed amount in cents from
    the target dict. None when the field isn't present."""
    amount = (proposal.target or {}).get("amount_cents")
    if isinstance(amount, int):
        return amount
    if isinstance(amount, (float, str)):
        try:
            return int(amount)
        except (TypeError, ValueError):
            return None
    return None


def _proposal_counterparty(proposal: ActionProposal) -> tuple[str | None, str | None]:
    """Best-effort counterparty (email, domain) from the proposal target."""
    raw = (proposal.target or {}).get("to") or (proposal.target or {}).get(
        "recipient"
    )
    if not raw or "@" not in raw:
        return (None, None)
    email = raw.split("<")[-1].rstrip(">").strip().lower()
    if "@" not in email:
        return (None, None)
    return (email, email.split("@", 1)[1])


def find_matching(
    db: Session, user: User, proposal: ActionProposal, *, now: datetime | None = None
) -> AutoApprovePolicy | None:
    """Return the first enabled policy that matches this proposal, or
    None when manual approval is required."""
    now = now or datetime.now(_user_tz(user))
    if now.tzinfo is None:
        now = now.replace(tzinfo=_user_tz(user))
    local_time = now.astimezone(_user_tz(user)).time()

    candidates = list(
        db.scalars(
            select(AutoApprovePolicy).where(
                AutoApprovePolicy.user_id == user.id,
                AutoApprovePolicy.enabled.is_(True),
                AutoApprovePolicy.action_type == proposal.action_type,
            )
        )
    )
    if not candidates:
        return None

    email, domain = _proposal_counterparty(proposal)
    cents = _proposal_value_cents(proposal)
    risk_is_financial = proposal.risk_level >= RiskLevel.financial_legal.value

    for policy in candidates:
        if policy.counterparty_email and policy.counterparty_email != email:
            continue
        if policy.counterparty_domain and policy.counterparty_domain != domain:
            continue
        if not _in_window(local_time, _parse_window(policy.active_window)):
            continue
        if risk_is_financial:
            if policy.max_cents is None:
                continue
            if cents is None or cents > policy.max_cents:
                continue
        if policy.content_substring:
            content = (proposal.proposed_content or "").lower()
            if policy.content_substring.lower() not in content:
                continue
        return policy
    return None


def record_fire(db: Session, policy: AutoApprovePolicy) -> None:
    policy.fire_count = (policy.fire_count or 0) + 1
    db.commit()


# ---------- CRUD ----------


def create_policy(
    db: Session,
    user: User,
    *,
    action_type: ActionType,
    counterparty_email: str | None = None,
    counterparty_domain: str | None = None,
    max_cents: int | None = None,
    content_substring: str | None = None,
    note: str | None = None,
    active_window: str | None = None,
    enabled: bool = True,
    meta: dict[str, Any] | None = None,
) -> AutoApprovePolicy:
    """Refuses wildcard-everything policies and refuses risk>=4 policies
    that don't carry both max_cents AND a counterparty constraint."""
    counterparty_email = (
        counterparty_email.strip().lower() if counterparty_email else None
    )
    counterparty_domain = (
        counterparty_domain.strip().lower() if counterparty_domain else None
    )
    if not counterparty_email and not counterparty_domain:
        raise ValueError(
            "Auto-approve policies must specify counterparty_email or counterparty_domain"
        )
    # Financial actions: require max_cents AND a specific counterparty.
    if action_type in {ActionType.make_payment, ActionType.place_order}:
        if max_cents is None or max_cents <= 0:
            raise ValueError("Financial auto-approve policies must set max_cents > 0")
        if not counterparty_email:
            raise ValueError(
                "Financial auto-approve policies must target a specific email"
            )
    # Validate active_window when provided.
    if active_window is not None and _parse_window(active_window) is None:
        raise ValueError("active_window must be 'HH-HH' or 'HH:MM-HH:MM'")
    policy = AutoApprovePolicy(
        user_id=user.id,
        action_type=action_type,
        counterparty_email=counterparty_email,
        counterparty_domain=counterparty_domain,
        max_cents=max_cents,
        content_substring=content_substring,
        note=note,
        active_window=active_window,
        enabled=enabled,
        meta=meta or {},
    )
    db.add(policy)
    db.commit()
    return policy


def set_enabled(db: Session, policy: AutoApprovePolicy, *, enabled: bool) -> AutoApprovePolicy:
    policy.enabled = enabled
    db.commit()
    return policy


def delete_policy(db: Session, policy: AutoApprovePolicy) -> None:
    db.delete(policy)
    db.commit()
