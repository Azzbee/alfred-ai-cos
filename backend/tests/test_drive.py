"""Tests for the /drive endpoints."""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.v1 import drive as drive_api
from app.db.enums import Provider, SyncStatus
from app.db.models import ConnectedAccount, User
from app.services import gdrive
from app.services.crypto import encrypt_token


@pytest.fixture
def user(db: Session) -> User:
    u = User(email="adam@adam.dev")
    db.add(u)
    db.commit()
    return u


def _connect_google(db: Session, user: User) -> None:
    db.add(
        ConnectedAccount(
            user_id=user.id,
            provider=Provider.google,
            provider_account_email=user.email,
            scopes=["drive.readonly"],
            token_ciphertext=encrypt_token({"token": "fake", "scopes": ["drive.readonly"]}),
            sync_status=SyncStatus.ok,
        )
    )
    db.commit()


def test_search_400_without_google_connection(db: Session, user: User) -> None:
    with pytest.raises(HTTPException) as exc:
        drive_api.search(q="hello", limit=5, user=user, db=db)
    assert exc.value.status_code == 400


def test_search_returns_files(db: Session, user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    _connect_google(db, user)

    def fake_search(token, *, query, limit):
        assert query == "barnes"
        return [
            {
                "id": "f1",
                "name": "Barnes financials.docx",
                "mimeType": "application/vnd.google-apps.document",
                "modifiedTime": "2026-06-01T12:00:00Z",
                "webViewLink": "https://docs.google.com/document/d/f1",
                "owners": [{"displayName": "Mary", "emailAddress": "mary@buyer.co"}],
            }
        ]

    monkeypatch.setattr(gdrive, "search_files", fake_search)
    rows = drive_api.search(q="barnes", limit=10, user=user, db=db)
    assert len(rows) == 1
    assert rows[0].name == "Barnes financials.docx"
    assert rows[0].owner_email == "mary@buyer.co"


def test_search_propagates_drive_errors_as_502(
    db: Session, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _connect_google(db, user)

    def boom(*a, **kw):
        raise RuntimeError("upstream 401")

    monkeypatch.setattr(gdrive, "search_files", boom)
    with pytest.raises(HTTPException) as exc:
        drive_api.search(q="x", limit=1, user=user, db=db)
    assert exc.value.status_code == 502


def test_file_text_truncation_flag(
    db: Session, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _connect_google(db, user)
    big = "x" * 100_000

    def fake_text(token, *, file_id):
        return big

    monkeypatch.setattr(gdrive, "get_file_text", fake_text)
    out = drive_api.file_text(file_id="f1", user=user, db=db)
    assert out.id == "f1"
    assert len(out.text) == 100_000
    assert out.truncated is True


def test_file_text_normal_size(db: Session, user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    _connect_google(db, user)
    monkeypatch.setattr(gdrive, "get_file_text", lambda token, *, file_id: "hello")
    out = drive_api.file_text(file_id="f1", user=user, db=db)
    assert out.text == "hello"
    assert out.truncated is False
