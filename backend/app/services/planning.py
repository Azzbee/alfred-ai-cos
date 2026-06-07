"""Planning Agent (PRD 14.1 agent 4).

Turns Today's signal — open commitments + calendar events + meetings to
prepare — into an actual time-blocked daily plan. Deterministic (no LLM):
the algorithm is small, debuggable, and the resulting blocks carry their
reasoning in a `why` string so the user can see why a block is where it is.

The plan is built around the calendar (events are fixed) and then fills
the gaps with blocks chosen from open commitments + tasks. Block types:

  - calendar:      an existing event the user is locked into
  - meeting_prep:  scheduled 25-30 min before a meeting needing prep
  - focus:         a chunk of uninterrupted time on a high-priority item
  - comms:         a batch of reply-drafting / email actions
  - quick_wins:    a sweep of low-effort items (typically 15-30 min)
  - break:         a buffer inserted between back-to-backs

The user's preferred working hours come from `User.preferences.working_hours`
(default 09:00–18:00 local). The user's timezone drives "local" — the same
field the per-user briefing scheduler already reads."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as date_type
from datetime import datetime, time, timedelta
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.enums import CommitmentOwner, CommitmentStatus, Priority
from app.db.models import CalendarEvent, Commitment, User
from app.services.priority import build_context, score_commitment

BlockKind = Literal[
    "calendar",
    "meeting_prep",
    "focus",
    "comms",
    "quick_wins",
    "break",
]

# Defaults (override via User.preferences.working_hours).
_DEFAULT_DAY_START = time(9, 0)
_DEFAULT_DAY_END = time(18, 0)

# Block durations.
_MEETING_PREP_DURATION = timedelta(minutes=15)
_FOCUS_MIN_DURATION = timedelta(minutes=45)
_FOCUS_MAX_DURATION = timedelta(minutes=90)
_COMMS_DURATION = timedelta(minutes=45)
_QUICK_WINS_DURATION = timedelta(minutes=25)
_BREAK_DURATION = timedelta(minutes=15)

# Gap policy.
_MIN_USABLE_GAP = timedelta(minutes=20)


@dataclass
class PlanBlock:
    """One block on the daily plan."""

    start: datetime
    end: datetime
    kind: BlockKind
    title: str
    why: str
    # Up to a handful of associated items (commitment_ids, event_id, etc.).
    item_ids: list[str] = field(default_factory=list)


@dataclass
class DailyPlan:
    """The plan as the API surfaces it."""

    plan_date: date_type
    timezone: str
    blocks: list[PlanBlock] = field(default_factory=list)
    summary: str = ""


# ---------- inputs ----------


def _user_timezone(user: User) -> ZoneInfo:
    try:
        return ZoneInfo(user.timezone or "UTC")
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _working_hours(user: User) -> tuple[time, time]:
    """Read working_hours from prefs, fall back to 09-18. Format: 'HH-HH'."""
    raw = (user.preferences or {}).get("working_hours")
    if not raw or not isinstance(raw, str) or "-" not in raw:
        return (_DEFAULT_DAY_START, _DEFAULT_DAY_END)
    try:
        a, b = raw.split("-", 1)
        return (_parse_hhmm(a), _parse_hhmm(b))
    except ValueError:
        return (_DEFAULT_DAY_START, _DEFAULT_DAY_END)


def _parse_hhmm(s: str) -> time:
    s = s.strip()
    if ":" in s:
        h, m = s.split(":", 1)
        return time(int(h), int(m))
    return time(int(s))


# ---------- core ----------


def build_plan(db: Session, user: User, *, plan_date: date_type) -> DailyPlan:
    """The entry point. Returns a DailyPlan built around the user's
    calendar for plan_date, with focus/comms/quick-wins blocks filling
    the gaps and meeting-prep blocks slotted before meetings that need it."""
    tz = _user_timezone(user)
    day_start_local, day_end_local = _working_hours(user)
    day_start = datetime.combine(plan_date, day_start_local, tzinfo=tz)
    day_end = datetime.combine(plan_date, day_end_local, tzinfo=tz)

    # Pull events that fall (partially) inside the working window.
    events = _events_for_day(db, user.id, plan_date=plan_date, tz=tz)
    # Sort by start so the gap calculation is monotonic.
    events.sort(key=lambda e: e.start_time or day_start)

    blocks: list[PlanBlock] = []

    # 1. Lay down calendar blocks.
    for ev in events:
        s = _to_tz(ev.start_time, tz)
        e = _to_tz(ev.end_time, tz)
        if s is None or e is None:
            continue
        # Clip into the working window so a 7am call doesn't push the plan early.
        s = max(s, day_start)
        e = min(e, day_end)
        if e <= s:
            continue
        blocks.append(
            PlanBlock(
                start=s,
                end=e,
                kind="calendar",
                title=ev.title or "Meeting",
                why="On your calendar",
                item_ids=[ev.id],
            )
        )

    # 2. Pre-meeting prep blocks for events that need prep AND have room.
    prep_blocks = _meeting_prep_blocks(events, blocks, day_start, day_end, tz)
    blocks.extend(prep_blocks)
    blocks.sort(key=lambda b: b.start)

    # 3. Score commitments + decide focus / comms / quick-win allocation.
    scored = _rank_commitments(db, user, plan_date)
    focus_items = [s for s in scored if _is_focus_item(s)]
    comms_items = [s for s in scored if _is_comms_item(s)]
    quick_items = [s for s in scored if _is_quick_win(s)]

    # 4. Fill gaps. Priority order inside each gap: focus → comms → quick wins.
    gaps = _gaps(blocks, day_start, day_end)
    for gap_start, gap_end in gaps:
        cursor = gap_start
        gap_duration = gap_end - cursor

        # Insert a focus block if the gap is big enough.
        if focus_items and gap_duration >= _FOCUS_MIN_DURATION:
            top = focus_items.pop(0)
            block_len = min(_FOCUS_MAX_DURATION, gap_end - cursor)
            blocks.append(
                PlanBlock(
                    start=cursor,
                    end=cursor + block_len,
                    kind="focus",
                    title=top["title"],
                    why=top["reason"],
                    item_ids=[top["id"]],
                )
            )
            cursor += block_len
            if gap_end - cursor >= _BREAK_DURATION:
                blocks.append(
                    PlanBlock(
                        start=cursor,
                        end=cursor + _BREAK_DURATION,
                        kind="break",
                        title="Break",
                        why="Buffer between focus and the next thing",
                    )
                )
                cursor += _BREAK_DURATION

        # Insert a comms block if there are reply drafts to batch.
        if comms_items and gap_end - cursor >= _COMMS_DURATION:
            batch = [comms_items.pop(0) for _ in range(min(4, len(comms_items)))]
            blocks.append(
                PlanBlock(
                    start=cursor,
                    end=cursor + _COMMS_DURATION,
                    kind="comms",
                    title=f"Reply batch ({len(batch)})",
                    why="Group reply drafting to keep the inbox shallow",
                    item_ids=[b["id"] for b in batch],
                )
            )
            cursor += _COMMS_DURATION

        # Quick wins fill any remaining gap.
        if quick_items and gap_end - cursor >= _QUICK_WINS_DURATION:
            take = []
            while quick_items and len(take) < 5:
                take.append(quick_items.pop(0))
            blocks.append(
                PlanBlock(
                    start=cursor,
                    end=cursor + _QUICK_WINS_DURATION,
                    kind="quick_wins",
                    title=f"Quick wins ({len(take)})",
                    why="Small items you can clear in 5 minutes each",
                    item_ids=[t["id"] for t in take],
                )
            )
            cursor += _QUICK_WINS_DURATION

    blocks.sort(key=lambda b: b.start)
    summary = _summary(blocks)
    return DailyPlan(plan_date=plan_date, timezone=str(tz), blocks=blocks, summary=summary)


def _events_for_day(
    db: Session, user_id: str, *, plan_date: date_type, tz: ZoneInfo
) -> list[CalendarEvent]:
    day_start_local = datetime.combine(plan_date, time(0, 0), tzinfo=tz)
    day_end_local = day_start_local + timedelta(days=1)
    rows = list(
        db.scalars(
            select(CalendarEvent).where(
                CalendarEvent.user_id == user_id,
                CalendarEvent.start_time.is_not(None),
                CalendarEvent.start_time >= day_start_local.astimezone(ZoneInfo("UTC")),
                CalendarEvent.start_time < day_end_local.astimezone(ZoneInfo("UTC")),
            )
        )
    )
    return rows


def _to_tz(value: datetime | None, tz: ZoneInfo) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        # SQLite roundtrip — treat as UTC.
        value = value.replace(tzinfo=ZoneInfo("UTC"))
    return value.astimezone(tz)


def _meeting_prep_blocks(
    events: list[CalendarEvent],
    existing: list[PlanBlock],
    day_start: datetime,
    day_end: datetime,
    tz: ZoneInfo,
) -> list[PlanBlock]:
    """Schedule a 15-min prep block before any event that needs prep, when
    there's free space immediately before it."""
    prep_blocks: list[PlanBlock] = []
    occupied = [(b.start, b.end) for b in existing if b.kind == "calendar"]
    for ev in events:
        if not getattr(ev, "prep_required", False):
            continue
        ev_start = _to_tz(ev.start_time, tz)
        if ev_start is None or ev_start < day_start:
            continue
        candidate_end = ev_start
        candidate_start = ev_start - _MEETING_PREP_DURATION
        if candidate_start < day_start:
            continue
        # Check overlap with calendar blocks.
        clash = any(not (candidate_end <= s or candidate_start >= e) for s, e in occupied)
        if clash:
            continue
        prep_blocks.append(
            PlanBlock(
                start=candidate_start,
                end=candidate_end,
                kind="meeting_prep",
                title=f"Prep for {ev.title or 'meeting'}",
                why="15-min prep slot before the meeting",
                item_ids=[ev.id],
            )
        )
        # Mark the prep block occupied so a second event doesn't claim the
        # same slot.
        occupied.append((candidate_start, candidate_end))
    return prep_blocks


def _gaps(
    blocks: list[PlanBlock], day_start: datetime, day_end: datetime
) -> list[tuple[datetime, datetime]]:
    """Return free intervals inside the working window."""
    if not blocks:
        return [(day_start, day_end)] if day_end > day_start else []
    occupied = sorted([(b.start, b.end) for b in blocks if b.kind in {"calendar", "meeting_prep"}])
    if not occupied:
        return [(day_start, day_end)]
    gaps: list[tuple[datetime, datetime]] = []
    cursor = day_start
    for s, e in occupied:
        if s > cursor + _MIN_USABLE_GAP:
            gaps.append((cursor, min(s, day_end)))
        cursor = max(cursor, e)
    if cursor < day_end and day_end - cursor >= _MIN_USABLE_GAP:
        gaps.append((cursor, day_end))
    return gaps


def _rank_commitments(db: Session, user: User, plan_date: date_type) -> list[dict]:
    """Score open commitments using the priority engine and return them
    sorted by score descending, with metadata the planner uses for
    bucketing."""
    open_rows = list(
        db.scalars(
            select(Commitment).where(
                Commitment.user_id == user.id,
                Commitment.status == CommitmentStatus.open,
            )
        )
    )
    if not open_rows:
        return []
    ctx = build_context(db, user)
    out: list[dict] = []
    for c in open_rows:
        scored = score_commitment(c, today=plan_date, context=ctx)
        out.append(
            {
                "id": c.id,
                "title": c.description[:120],
                "reason": scored.reason,
                "priority": scored.priority,
                "score": scored.score,
                "owner": c.owner,
                "has_email_source": bool(c.source_id),
                "due_date": c.due_date,
            }
        )
    out.sort(key=lambda x: -x["score"])
    return out


def _is_focus_item(item: dict) -> bool:
    """Focus-block-worthy: high/critical priority, AND the commitment is the
    user's own work (owner=user). A 'you are waiting on Mary' item isn't a
    focus block — there's nothing to focus on."""
    if item["owner"] != CommitmentOwner.user:
        return False
    return item["priority"] in (Priority.critical, Priority.high)


def _is_comms_item(item: dict) -> bool:
    """Comms-block-worthy: medium-or-higher, email-sourced (a draft to write),
    user owes the counterparty. Excludes the focus items already claimed."""
    if _is_focus_item(item):
        return False
    if item["owner"] != CommitmentOwner.user:
        return False
    if not item["has_email_source"]:
        return False
    return item["priority"] in (Priority.medium, Priority.high)


def _is_quick_win(item: dict) -> bool:
    """Anything low-priority or owner!=user that didn't slot into focus or
    comms gets swept into quick wins."""
    if _is_focus_item(item) or _is_comms_item(item):
        return False
    return item["priority"] in (Priority.low, Priority.medium, Priority.high)


def _summary(blocks: list[PlanBlock]) -> str:
    if not blocks:
        return "Your day is clear."
    counts: dict[BlockKind, int] = {}
    for b in blocks:
        counts[b.kind] = counts.get(b.kind, 0) + 1
    parts: list[str] = []
    if counts.get("calendar"):
        parts.append(f"{counts['calendar']} meeting(s)")
    if counts.get("meeting_prep"):
        parts.append(f"{counts['meeting_prep']} prep slot(s)")
    if counts.get("focus"):
        parts.append(f"{counts['focus']} focus block(s)")
    if counts.get("comms"):
        parts.append("a reply batch")
    if counts.get("quick_wins"):
        parts.append("a quick-wins sweep")
    return "Your day: " + ", ".join(parts) + "."
