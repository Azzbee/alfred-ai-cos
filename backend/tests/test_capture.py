"""Capture service tests against SQLite + a fake LLM."""

from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.db.enums import Priority, SourceType
from app.db.models import Task, User
from app.schemas.llm import ParsedTask
from app.services import capture as capture_service
from tests.fakes import FakeLLM

TODAY = date(2026, 5, 21)
TOMORROW = date(2026, 5, 22)


@pytest.fixture
def user(db: Session) -> User:
    u = User(email="capture@example.com")
    db.add(u)
    db.commit()
    return u


def _patch(monkeypatch: pytest.MonkeyPatch, fake: FakeLLM) -> None:
    monkeypatch.setattr(capture_service, "get_llm", lambda: fake)


def test_capture_creates_each_parsed_task(
    db: Session, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeLLM(
        capture_tasks=[
            ParsedTask(title="Call the broker", due_date=TOMORROW, priority=Priority.high),
            ParsedTask(title="Review the CBRE valuation"),
            ParsedTask(title="Draft the pellet line offer in French"),
        ],
        detected_project="Factory Sale",
    )
    _patch(monkeypatch, fake)

    tasks, project = capture_service.capture_text(
        db, user.id, text="messy note", reference_date=TODAY, source_type=SourceType.voice
    )
    assert len(tasks) == 3
    assert project == "Factory Sale"
    assert db.query(Task).count() == 3
    broker = next(t for t in tasks if "broker" in t.title)
    assert broker.due_date == TOMORROW
    assert broker.priority == Priority.high
    assert broker.source_type == SourceType.voice


def test_capture_empty_creates_nothing(
    db: Session, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch(monkeypatch, FakeLLM(capture_tasks=[]))
    tasks, project = capture_service.capture_text(
        db, user.id, text="thanks!", reference_date=TODAY
    )
    assert tasks == []
    assert project is None
    assert db.query(Task).count() == 0
