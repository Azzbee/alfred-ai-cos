"""Extraction Agent (PRD 14.1, agent 2) + classification (agent for PRD 12.2).

For each message it classifies the email and extracts commitments via the LLM,
then persists a Message classification and Commitment rows with evidence and
confidence. The full body is fetched from Gmail in-process and never stored,
keeping the DB free of raw email content."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.enums import Provider, SourceType
from app.db.models import Commitment, ConnectedAccount, Message, User
from app.llm import get_llm
from app.services import gmail
from app.services.crypto import decrypt_token


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
    commitments: list[Commitment] = []
    for item in extracted:
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
        )
        db.add(commitment)
        commitments.append(commitment)

    db.commit()
    return commitments
