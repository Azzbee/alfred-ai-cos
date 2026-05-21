"""Background tasks. The API runs sync synchronously for the slice demo; in
production it enqueues sync_user so ingestion + extraction run off the request
path (PRD 13.4 near-real-time ingestion)."""

from __future__ import annotations

from app.db.base import SessionLocal
from app.services import extraction, ingestion
from app.workers.celery_app import celery_app


@celery_app.task(name="albert.sync_user")  # type: ignore[untyped-decorator]
def sync_user(user_id: str, max_results: int = 25) -> dict[str, int]:
    """Ingest recent messages for a user and run extraction over the new ones."""
    db = SessionLocal()
    try:
        messages = ingestion.ingest_recent_messages(db, user_id, max_results=max_results)
        commitments = 0
        for message in messages:
            commitments += len(extraction.process_message(db, message))
        return {"ingested": len(messages), "commitments_found": commitments}
    finally:
        db.close()
