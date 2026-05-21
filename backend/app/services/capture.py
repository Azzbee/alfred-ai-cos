"""Capture service (PRD 10.3, journey 6). Parse a messy note into structured tasks
and persist them. Used by both text capture (A6) and voice capture (A7, after
transcription)."""

from __future__ import annotations

from datetime import date as date_type

from sqlalchemy.orm import Session

from app.db.enums import SourceType
from app.db.models import Task
from app.llm import get_llm
from app.services import tasks as task_service


def capture_text(
    db: Session,
    user_id: str,
    *,
    text: str,
    reference_date: date_type,
    source_type: SourceType = SourceType.manual,
) -> tuple[list[Task], str | None]:
    """Parse `text` into tasks, persist them, and return (tasks, detected_project)."""
    result = get_llm().parse_capture(text=text, reference_date=reference_date)
    created: list[Task] = []
    for parsed in result.tasks:
        created.append(
            task_service.create_task(
                db,
                user_id,
                title=parsed.title,
                due_date=parsed.due_date,
                priority=parsed.priority,
                source_type=source_type,
            )
        )
    return created, result.detected_project
