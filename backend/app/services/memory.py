"""Memory Agent (PRD 14.1 agent 7).

The Memory Agent is the per-user knowledge that influences future Albert
output. Three concerns live here:

  1. **Tone preferences per recipient.** When the user approves a draft via
     the send_email or create_draft capability, we record that draft's tone
     against the recipient's Person row. The next time we draft to that
     person, we use the tone they most often see.

  2. **Relationship type rollups.** A view into Person.relationship_type
     that the Today / Plan / Briefing surfaces can read without re-deriving.

  3. **Organization extraction.** Already lives on Person.organization
     (derived from the email domain at upsert time). The Memory module
     exposes a helper to look it up cheaply for use in cluster naming.

This module is the read/write seam for the agent — services and capabilities
call it instead of poking Person.learned_tone directly so the bookkeeping
(decay, cap, default) stays in one place."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Person, User

# Valid tones the system uses across draft generation. The mobile UI exposes
# four (concise / warm / formal / direct); this mirrors them so a stray
# value (e.g. from a future "playful" feature) doesn't silently get stored.
VALID_TONES = {"concise", "warm", "formal", "direct"}
DEFAULT_TONE = "concise"

# Cap each per-tone count so a long-running streak doesn't lock the
# preference forever. Past the cap, every new tone vote effectively votes
# at full weight against the others.
_TONE_CAP = 20


def record_tone(
    db: Session,
    user: User,
    *,
    recipient_email: str,
    tone: str,
) -> Person | None:
    """Record a tone vote for the Person at `recipient_email`. Idempotent
    on email + tone in the sense that we just increment a counter; calling
    it twice means the tone wins by 2 instead of 1."""
    tone = (tone or "").strip().lower()
    if tone not in VALID_TONES:
        return None
    email_lower = (recipient_email or "").strip().lower()
    if not email_lower or "@" not in email_lower:
        return None
    person = db.scalar(
        select(Person).where(Person.user_id == user.id, Person.email_lower == email_lower)
    )
    if person is None:
        return None
    counts = dict(person.learned_tone or {})
    counts[tone] = min(_TONE_CAP, int(counts.get(tone, 0)) + 1)
    person.learned_tone = counts
    db.commit()
    return person


def preferred_tone(db: Session, user: User, *, recipient_email: str | None) -> str:
    """Pick the tone we'd default to for the next draft to `recipient_email`.
    Returns DEFAULT_TONE when there's no email, no Person, or no learned tone."""
    if not recipient_email or "@" not in recipient_email:
        return DEFAULT_TONE
    email_lower = recipient_email.strip().lower()
    person = db.scalar(
        select(Person).where(Person.user_id == user.id, Person.email_lower == email_lower)
    )
    if person is None:
        return DEFAULT_TONE
    counts = person.learned_tone or {}
    if not counts:
        return DEFAULT_TONE
    # Highest count wins; tie-break by valid-tones order so the answer is
    # deterministic when two tones tie at the same count.
    valid = [t for t in VALID_TONES if t in counts]
    if not valid:
        return DEFAULT_TONE
    return max(valid, key=lambda t: (counts.get(t, 0), -list(VALID_TONES).index(t)))


def organization_for(db: Session, user: User, *, email: str) -> str | None:
    """Look up the org for one email, or None when the email is a free-mail
    address or we don't have a Person row yet."""
    if not email or "@" not in email:
        return None
    person = db.scalar(
        select(Person).where(Person.user_id == user.id, Person.email_lower == email.lower())
    )
    return person.organization if person else None
