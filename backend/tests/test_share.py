"""Tests for the /share endpoint."""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.v1 import share as share_api
from app.db.models import Task, User


@pytest.fixture
def user(db: Session) -> User:
    u = User(email="adam@adam.dev")
    db.add(u)
    db.commit()
    return u


def test_share_requires_url_or_text(db: Session, user: User) -> None:
    with pytest.raises(HTTPException) as exc:
        share_api.receive_share(
            payload=share_api.ShareRequest(),
            user=user,
            db=db,
        )
    assert exc.value.status_code == 400


def test_share_creates_task_from_url(db: Session, user: User) -> None:
    out = share_api.receive_share(
        payload=share_api.ShareRequest(url="https://example.com/article"),
        user=user,
        db=db,
    )
    assert out.task_id
    task = db.query(Task).one()
    assert task.title == "example.com"
    assert "https://example.com/article" in (task.description or "")


def test_share_creates_task_from_text(db: Session, user: User) -> None:
    out = share_api.receive_share(
        payload=share_api.ShareRequest(text="Read this thing.\n\nIt's important."),
        user=user,
        db=db,
    )
    assert out.task_id
    task = db.query(Task).one()
    assert task.title == "Read this thing."


def test_explicit_title_wins(db: Session, user: User) -> None:
    out = share_api.receive_share(
        payload=share_api.ShareRequest(
            title="Custom title",
            url="https://example.com",
            text="line one",
        ),
        user=user,
        db=db,
    )
    task = db.query(Task).one()
    assert task.title == "Custom title"
    assert out.title == "Custom title"


def test_url_and_text_both_persisted(db: Session, user: User) -> None:
    share_api.receive_share(
        payload=share_api.ShareRequest(
            url="https://example.com",
            text="quote from the article",
        ),
        user=user,
        db=db,
    )
    task = db.query(Task).one()
    assert "https://example.com" in (task.description or "")
    assert "quote from the article" in (task.description or "")


def test_long_text_truncated_in_description(db: Session, user: User) -> None:
    big = "x" * 10_000
    share_api.receive_share(
        payload=share_api.ShareRequest(text=big),
        user=user,
        db=db,
    )
    task = db.query(Task).one()
    assert len(task.description or "") <= 4000
