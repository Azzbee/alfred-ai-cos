"""Extraction quality tests: cross-message dedup and automated-sender handling.
Run against SQLite with a fake LLM (no Gmail, no Anthropic)."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from app.db.enums import CommitmentOwner, Priority
from app.db.models import Commitment, Message, User
from app.services import extraction
from app.services.extraction import _dedup_key
from tests.fakes import FakeLLM, fake_commitment


@pytest.fixture
def user(db: Session) -> User:
    u = User(email="extract@example.com")
    db.add(u)
    db.commit()
    return u


def _message(user_id: str, ext: str) -> Message:
    m = Message(
        user_id=user_id,
        external_id=ext,
        sender="x@example.com",
        recipients=[],
        sent_at=datetime.now(UTC),
    )
    return m


def _patch(monkeypatch: pytest.MonkeyPatch, fake: FakeLLM) -> None:
    monkeypatch.setattr(extraction, "get_llm", lambda: fake)


# --- dedup key (pure) ---


def test_dedup_key_collapses_near_duplicates() -> None:
    a = _dedup_key("user", "Studocu", "Upload notes to Studocu to retain Premium access")
    b = _dedup_key("user", "Studocu", "Upload notes to Studocu to maintain Premium access!")
    assert a == b


def test_dedup_key_distinguishes_real_differences() -> None:
    a = _dedup_key("user", "Dana", "Send the Q3 report")
    b = _dedup_key("user", "Marc", "Call the broker back")
    assert a != b


# --- cross-message dedup in the pipeline ---


def test_duplicate_commitments_across_messages_are_deduped(
    db: Session, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    dup = fake_commitment(
        description="Upload notes to Studocu to retain Premium", counterparty="Studocu"
    )
    _patch(monkeypatch, FakeLLM(commitments=[dup]))

    m1 = _message(user.id, "msg-1")
    db.add(m1)
    db.flush()
    extraction.process_message(db, m1, body="upload notes to keep premium")

    # A second email about the same thing (slightly reworded) should not add a row.
    dup2 = fake_commitment(
        description="Upload notes to Studocu to maintain Premium!", counterparty="Studocu"
    )
    _patch(monkeypatch, FakeLLM(commitments=[dup2]))
    m2 = _message(user.id, "msg-2")
    db.add(m2)
    db.flush()
    created = extraction.process_message(db, m2, body="upload to maintain premium")

    assert created == []  # deduped
    assert db.query(Commitment).filter(Commitment.user_id == user.id).count() == 1


def test_from_automated_is_persisted(
    db: Session, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    auto = fake_commitment(
        description="Verify your login", counterparty="Crunchyroll", from_automated=True
    )
    _patch(monkeypatch, FakeLLM(commitments=[auto]))
    m = _message(user.id, "msg-auto")
    db.add(m)
    db.flush()
    created = extraction.process_message(db, m, body="suspicious login detected")
    assert len(created) == 1
    assert created[0].from_automated is True


def test_automated_excluded_from_waiting(db: Session, user: User) -> None:
    from app.services.waiting import build_waiting

    db.add(
        Commitment(
            user_id=user.id,
            description="Real person reply",
            owner=CommitmentOwner.user,
            counterparty="Camille",
            source_type="gmail",
            confidence=0.9,
            from_automated=False,
        )
    )
    db.add(
        Commitment(
            user_id=user.id,
            description="Upload notes to Studocu",
            owner=CommitmentOwner.user,
            counterparty="Studocu",
            source_type="gmail",
            confidence=0.9,
            from_automated=True,
        )
    )
    db.commit()
    view = build_waiting(db, user.id)
    people = [e.commitment.counterparty for e in view.waiting_on_you]
    assert people == ["Camille"]  # Studocu (automated) excluded


def test_automated_priority_uses_neutral_phrasing() -> None:
    from datetime import date

    from app.services.priority import score_commitment

    c = Commitment(
        user_id="u",
        description="Upload notes before Premium expires",
        owner=CommitmentOwner.user,
        counterparty="Studocu",
        due_date=date(2026, 5, 21),
        priority=Priority.medium,
        source_type="gmail",
        confidence=0.9,
        from_automated=True,
    )
    scored = score_commitment(c, today=date(2026, 5, 21))
    assert "Studocu is waiting on you" not in scored.reason  # no false "person waiting"
