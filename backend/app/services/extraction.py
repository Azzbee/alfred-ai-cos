"""Extraction Agent (PRD 14.1, agent 2) + classification (agent for PRD 12.2).

For each message it classifies the email and extracts commitments via the LLM,
then persists a Message classification and Commitment rows with evidence and
confidence. The full body is fetched from Gmail in-process and never stored,
keeping the DB free of raw email content."""

from __future__ import annotations

import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.enums import CommitmentStatus, Provider, SourceType
from app.db.models import Commitment, ConnectedAccount, Message, User
from app.llm import get_llm
from app.services import gmail
from app.services.crypto import decrypt_token

# Common filler words that carry no identity for a commitment. Two phrasings of the
# same task ("retain Premium" vs "maintain Premium") differ only in filler/synonyms,
# so keying on the distinctive content words collapses them.
_STOPWORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "to",
        "for",
        "of",
        "and",
        "or",
        "in",
        "on",
        "at",
        "by",
        "your",
        "you",
        "with",
        "before",
        "after",
        "is",
        "are",
        "be",
        "this",
        "that",
        "it",
        "as",
        "retain",
        "maintain",
        "keep",
        "extend",
        "access",
        "please",
        "send",
        "make",
        "sure",
    }
)


def _dedup_key(owner: str, counterparty: str | None, description: str) -> str:
    """A normalized key for collapsing near-duplicate commitments. Keys on owner +
    counterparty + the sorted set of distinctive content words (4+ chars, not filler),
    so reworded variants of the same task ('Upload notes to Studocu to retain Premium'
    vs '...to maintain Premium') produce the same key regardless of order/synonyms."""
    words = re.findall(r"[a-z0-9]+", description.lower())
    content = sorted({w for w in words if len(w) >= 4 and w not in _STOPWORDS})
    cp = (counterparty or "").lower().strip()
    return f"{owner}|{cp}|{' '.join(content)}"


def process_message(db: Session, message: Message, *, body: str | None = None) -> list[Commitment]:
    """Classify one message and extract its commitments. Persists results.

    The body is fetched from Gmail in-process when not supplied, so it is never
    stored. Callers that already hold the body (e.g. the dev seed path) pass it
    in to avoid a Gmail round trip.
    """
    llm = get_llm()
    user = db.get(User, message.user_id)
    if user is None:
        raise ValueError("Missing user for extraction")

    if body is None:
        account = (
            db.query(ConnectedAccount)
            .filter(
                ConnectedAccount.user_id == message.user_id,
                ConnectedAccount.provider == Provider.google,
            )
            .first()
        )
        if account is None:
            raise ValueError("Missing connected account for extraction")
        token = decrypt_token(account.token_ciphertext)
        body = gmail.get_message(token, message.external_id)["body"]

    classification = llm.classify_message(subject=message.subject, body=body, sender=message.sender)
    message.classification = classification.classification
    message.priority = classification.priority
    message.action_required = classification.action_required
    # Persist the one-line reason as the body_summary surrogate for the slice.
    message.body_summary = classification.reason

    # Anchor relative deadlines to when the email was sent, falling back to today.
    reference_date = message.sent_at.date() if message.sent_at else datetime.now(UTC).date()
    extracted = llm.extract_commitments(
        subject=message.subject,
        body=body,
        sender=message.sender,
        user_email=user.email,
        reference_date=reference_date,
    )
    # Dedup against existing open commitments (and within this batch) so separate
    # emails about the same thing do not pile up multiple near-identical entries.
    existing_open = db.scalars(
        select(Commitment).where(
            Commitment.user_id == message.user_id,
            Commitment.status == CommitmentStatus.open,
        )
    )
    seen = {_dedup_key(c.owner, c.counterparty, c.description) for c in existing_open}

    commitments: list[Commitment] = []
    for item in extracted:
        key = _dedup_key(item.owner, item.counterparty, item.description)
        if key in seen:
            continue
        seen.add(key)
        commitment = Commitment(
            user_id=message.user_id,
            description=item.description,
            owner=item.owner,
            counterparty=item.counterparty,
            due_date=item.due_date,
            priority=item.priority,
            source_type=SourceType.gmail,
            source_id=message.id,
            evidence=item.evidence,
            confidence=item.confidence,
            from_automated=item.from_automated,
        )
        db.add(commitment)
        commitments.append(commitment)

    db.commit()
    return commitments
