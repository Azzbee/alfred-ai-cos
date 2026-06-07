"""People service (PRD 14.1 agent 7, PRD 15.1 Person).

Maintains the user's Person memory:

  - `upsert_from_message(...)`: called by ingestion. Resolves the message's
    sender to a Person row, creating one if it's the first time we've seen
    them. Updates name (best-effort, latest header wins), organization
    (from domain, skipping free-mail), interaction stats, and last_interaction_at.
  - `upsert_from_recipient(...)`: called by ingestion for outbound messages.
    Counts replies the user has sent.
  - `link_commitment(...)`: called by extraction. Parses `counterparty` for
    an email and sets `Commitment.counterparty_person_id` when it matches.
  - `infer_relationship(...)`: heuristic that runs after the stats update —
    same domain → colleague, automated sender → automated, very-high inbound
    no replies → vendor, balanced inbound + outbound → client. Skipped if
    `relationship_locked` is set (user override wins).
  - `update_importance(...)`: bumped from the learning loop on act/dismiss
    events so the importance_weight stays in lockstep with sender bias.

The service is intentionally idempotent and re-entrant: every entry point
either finds an existing Person and updates fields, or creates a new one
keyed on (user_id, email_lower). No write happens without a lookup first."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.enums import RelationshipType
from app.db.models import Commitment, Message, Person, User

# Domains we treat as "personal" — no organization is inferred from these.
_FREE_MAIL_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "yahoo.co.uk",
    "yahoo.fr",
    "hotmail.com",
    "outlook.com",
    "live.com",
    "icloud.com",
    "me.com",
    "mac.com",
    "protonmail.com",
    "proton.me",
    "fastmail.com",
    "gmx.com",
    "aol.com",
    "qq.com",
    "163.com",
    "126.com",
    "yandex.com",
    "tutanota.com",
    "mail.ru",
    "yandex.ru",
}


# Inbound thresholds for relationship inference. Picked conservatively so a
# brand-new contact stays `unknown` until enough signal is accumulated.
_VENDOR_INBOUND_THRESHOLD = 5
_CLIENT_BALANCED_THRESHOLD = 3  # minimum each direction


def _parse_email(raw: str) -> tuple[str, str]:
    """Split 'Mary Smith <mary@x.co>' into (display_name, email_lower).
    Either side can be empty when the input is malformed."""
    if not raw:
        return ("", "")
    raw = raw.strip()
    if "<" in raw and ">" in raw:
        name = raw.split("<", 1)[0].strip().strip('"').strip()
        email = raw.split("<", 1)[1].split(">", 1)[0].strip().lower()
        return (name, email)
    if "@" in raw:
        return ("", raw.lower())
    return (raw, "")


def _domain_of(email: str) -> str:
    if "@" not in email:
        return ""
    return email.split("@", 1)[1].lower()


def _organization_from(email: str) -> str | None:
    """Return the second-level domain as the organization, unless the domain
    is on the free-mail list. 'mary@buyer.co' -> 'buyer.co';
    'mary@gmail.com' -> None."""
    dom = _domain_of(email)
    if not dom:
        return None
    # Reduce e.g. 'email.notifications.stripe.com' to 'stripe.com'.
    parts = dom.split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in {
        "co.uk",
        "gov.uk",
        "ac.uk",
        "com.au",
        "co.jp",
        "com.br",
    }:
        root = ".".join(parts[-3:])
    elif len(parts) >= 2:
        root = ".".join(parts[-2:])
    else:
        root = dom
    if root in _FREE_MAIL_DOMAINS:
        return None
    return root


# ---------- lookup / upsert ----------


def get_or_create(
    db: Session,
    user_id: str,
    *,
    email: str,
    name: str | None = None,
) -> Person | None:
    """Find or create the Person for an email under this user. Returns None
    when the input doesn't parse to a real email."""
    _name, email_lower = _parse_email(email) if "<" in email else ("", email.lower())
    if not email_lower or "@" not in email_lower:
        return None
    name = name or _name or None
    existing = db.scalar(
        select(Person).where(Person.user_id == user_id, Person.email_lower == email_lower)
    )
    if existing is not None:
        # Lazily improve the display name when we now have a better one.
        if name and (not existing.name or existing.name == existing.email_lower):
            existing.name = name
        # Backfill organization if missing.
        if existing.organization is None:
            existing.organization = _organization_from(email_lower)
        return existing
    person = Person(
        user_id=user_id,
        email_lower=email_lower,
        name=name,
        organization=_organization_from(email_lower),
    )
    db.add(person)
    db.flush()
    return person


# ---------- ingestion entry points ----------


def _bump_inbound(person: Person, sent_at: datetime | None) -> None:
    person.inbound_count = (person.inbound_count or 0) + 1
    _bump_last_interaction(person, sent_at)


def _bump_outbound(person: Person, sent_at: datetime | None) -> None:
    person.outbound_count = (person.outbound_count or 0) + 1
    _bump_last_interaction(person, sent_at)


def _bump_last_interaction(person: Person, sent_at: datetime | None) -> None:
    ts = sent_at or datetime.now(UTC)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    prev = person.last_interaction_at
    if prev is None or (prev.replace(tzinfo=UTC) if prev.tzinfo is None else prev) < ts:
        person.last_interaction_at = ts


def upsert_from_message(db: Session, user: User, message: Message) -> Person | None:
    """Called by ingestion for every new Message. Resolves the sender to a
    Person and links it back via `Message.sender_person_id`. Also processes
    every recipient as outbound for the user's own outbound copy (when the
    sender IS the user). Returns the sender's Person, or None when the sender
    string didn't parse."""
    user_email_lower = (user.email or "").lower()
    sender_name, sender_email = _parse_email(message.sender or "")
    sender = get_or_create(db, user.id, email=sender_email, name=sender_name)
    if sender is None:
        return None

    # If the sender is the user themselves, this is an outbound copy — bump
    # the recipients instead, and mark the user-self person accordingly.
    if sender_email == user_email_lower:
        sender.relationship_type = RelationshipType.self_
        sender.relationship_locked = True
        for r in message.recipients or []:
            r_name, r_email = _parse_email(str(r))
            recipient = get_or_create(db, user.id, email=r_email, name=r_name)
            if recipient is not None:
                _bump_outbound(recipient, message.sent_at)
                _maybe_infer_relationship(recipient, user_email_lower)
        # Don't double-count the outbound on the sender (the user).
        return sender

    _bump_inbound(sender, message.sent_at)
    # Carry the classifier's verdict into the relationship when it's a clean
    # signal — it'd be weird for the People screen to show Mailchimp as
    # `unknown` when sender_class already calls it `automated`.
    if message.sender_classification in {"automated", "bulk"}:
        if not sender.relationship_locked:
            sender.relationship_type = RelationshipType.automated
    elif message.sender_classification == "suspicious":
        if not sender.relationship_locked:
            sender.relationship_type = RelationshipType.suspicious
    else:
        _maybe_infer_relationship(sender, user_email_lower)

    # Link the message back to the person for cheap retrieval later.
    message.sender_person_id = sender.id
    return sender


def link_commitment(db: Session, user: User, commitment: Commitment) -> Person | None:
    """Called by extraction after a Commitment is created. If the counterparty
    parses to an email, link the Person via `counterparty_person_id`. Returns
    the Person or None when no link was made."""
    if not commitment.counterparty:
        return None
    name, email = _parse_email(commitment.counterparty)
    if not email:
        return None
    person = get_or_create(db, user.id, email=email, name=name)
    if person is None:
        return None
    commitment.counterparty_person_id = person.id
    return person


# ---------- relationship inference ----------


def _maybe_infer_relationship(person: Person, user_email_lower: str) -> None:
    """Update relationship_type based on accumulated interaction stats.
    Skips if the user has locked the override. Deliberately conservative:
    leaves `unknown` set until we have at least a few data points so the
    People screen doesn't oscillate on first contact."""
    if person.relationship_locked:
        return
    if person.relationship_type in {
        RelationshipType.self_,
        RelationshipType.automated,
        RelationshipType.suspicious,
        RelationshipType.investor,
        RelationshipType.family,
        RelationshipType.friend,
    }:
        # These are either user-set or terminal — don't overwrite from stats.
        return

    user_domain = user_email_lower.split("@", 1)[1] if "@" in user_email_lower else ""
    sender_domain = person.email_lower.split("@", 1)[1] if "@" in person.email_lower else ""

    # Same corporate domain → colleague. Skip free-mail to avoid labeling
    # every gmail.com contact as a colleague of a gmail.com user.
    if (
        sender_domain
        and user_domain
        and sender_domain == user_domain
        and sender_domain not in _FREE_MAIL_DOMAINS
    ):
        person.relationship_type = RelationshipType.colleague
        return

    inbound = person.inbound_count or 0
    outbound = person.outbound_count or 0

    # Balanced two-way conversation at a non-free domain → client.
    if (
        inbound >= _CLIENT_BALANCED_THRESHOLD
        and outbound >= _CLIENT_BALANCED_THRESHOLD
        and person.organization is not None
    ):
        person.relationship_type = RelationshipType.client
        return

    # Many inbounds, no outbounds, at an org domain → vendor.
    if inbound >= _VENDOR_INBOUND_THRESHOLD and outbound == 0 and person.organization is not None:
        person.relationship_type = RelationshipType.vendor
        return


# ---------- importance ----------


def adjust_importance(person: Person, delta: float) -> None:
    """Bounded ±1 update used by the learning loop. The priority ranker reads
    Person.importance_weight (when set) instead of the per-sender bias dict —
    same signal, surfaced as a real field on the People screen."""
    current = person.importance_weight or 0.0
    person.importance_weight = max(-1.0, min(1.0, current + delta))


# ---------- user overrides ----------


def set_relationship(db: Session, person: Person, *, relationship: RelationshipType) -> Person:
    """Lock a relationship_type as user-set. Heuristic updates stop."""
    person.relationship_type = relationship
    person.relationship_locked = True
    db.commit()
    return person


def set_notes(db: Session, person: Person, *, notes: str | None) -> Person:
    person.notes = notes
    db.commit()
    return person
