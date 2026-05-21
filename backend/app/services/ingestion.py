"""Ingestion Agent (PRD 14.1, agent 1): pull recent Gmail messages, normalize,
deduplicate, and persist. Stores a snippet rather than the full body to limit
sensitive data at rest; the extraction pipeline uses the body in-process only."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.enums import Provider, SyncStatus
from app.db.models import ConnectedAccount, Message
from app.services import gmail
from app.services.crypto import decrypt_token


def _account(db: Session, user_id: str) -> ConnectedAccount:
    account = db.scalar(
        select(ConnectedAccount).where(
            ConnectedAccount.user_id == user_id,
            ConnectedAccount.provider == Provider.google,
        )
    )
    if account is None:
        raise ValueError("No connected Google account for user")
    return account


def ingest_recent_messages(db: Session, user_id: str, *, max_results: int = 25) -> list[Message]:
    """Fetch recent inbox messages and upsert them. Returns newly created rows.

    Returns the message rows so the caller (or a worker) can hand them to the
    extraction pipeline. Raw bodies are intentionally not persisted.
    """
    account = _account(db, user_id)
    token = decrypt_token(account.token_ciphertext)
    account.sync_status = SyncStatus.syncing
    db.commit()

    new_messages: list[Message] = []
    try:
        for message_id in gmail.list_recent_message_ids(token, max_results=max_results):
            exists = db.scalar(
                select(Message).where(
                    Message.user_id == user_id, Message.external_id == message_id
                )
            )
            if exists:
                continue
            raw = gmail.get_message(token, message_id)
            sent_at = None
            if raw.get("internal_date_ms"):
                sent_at = datetime.fromtimestamp(
                    int(raw["internal_date_ms"]) / 1000, tz=UTC
                )
            message = Message(
                user_id=user_id,
                source="gmail",
                external_id=raw["external_id"],
                thread_id=raw["thread_id"],
                sender=raw["sender"],
                recipients=raw["recipients"],
                subject=raw["subject"],
                snippet=raw["snippet"],
                sent_at=sent_at,
            )
            db.add(message)
            new_messages.append(message)
        account.sync_status = SyncStatus.ok
        account.last_synced_at = datetime.now(UTC)
        account.sync_error = None
        db.commit()
    except Exception as exc:  # surface failures, never silently swallow (PRD 13.3)
        account.sync_status = SyncStatus.error
        account.sync_error = str(exc)
        db.commit()
        raise
    return new_messages
