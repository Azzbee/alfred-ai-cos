"""Tests for the paste-token integration endpoints."""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.v1 import integrations as integrations_api
from app.db.enums import Provider
from app.db.models import ConnectedAccount, User
from app.services.crypto import decrypt_token


@pytest.fixture
def user(db: Session) -> User:
    u = User(email="adam@adam.dev")
    db.add(u)
    db.commit()
    return u


def test_connect_notion_requires_database_id(db: Session, user: User) -> None:
    with pytest.raises(HTTPException) as exc:
        integrations_api.connect(
            provider="notion",
            payload=integrations_api.ConnectRequest(access_token="ntn_xyz"),
            user=user,
            db=db,
        )
    assert exc.value.status_code == 400


def test_connect_todoist_stores_token(db: Session, user: User) -> None:
    integrations_api.connect(
        provider="todoist",
        payload=integrations_api.ConnectRequest(access_token="td-xyz"),
        user=user,
        db=db,
    )
    account = (
        db.query(ConnectedAccount)
        .filter(
            ConnectedAccount.user_id == user.id,
            ConnectedAccount.provider == Provider.todoist,
        )
        .one()
    )
    creds = decrypt_token(account.token_ciphertext)
    assert creds["access_token"] == "td-xyz"


def test_connect_slack_stores_token(db: Session, user: User) -> None:
    integrations_api.connect(
        provider="slack",
        payload=integrations_api.ConnectRequest(access_token="xoxb-test"),
        user=user,
        db=db,
    )
    account = (
        db.query(ConnectedAccount)
        .filter(
            ConnectedAccount.user_id == user.id,
            ConnectedAccount.provider == Provider.slack,
        )
        .one()
    )
    creds = decrypt_token(account.token_ciphertext)
    assert creds["access_token"] == "xoxb-test"


def test_connect_notion_stores_database_id(db: Session, user: User) -> None:
    integrations_api.connect(
        provider="notion",
        payload=integrations_api.ConnectRequest(access_token="ntn_xyz", database_id="db_abc"),
        user=user,
        db=db,
    )
    account = (
        db.query(ConnectedAccount)
        .filter(
            ConnectedAccount.user_id == user.id,
            ConnectedAccount.provider == Provider.notion,
        )
        .one()
    )
    creds = decrypt_token(account.token_ciphertext)
    assert creds["access_token"] == "ntn_xyz"
    assert creds["database_id"] == "db_abc"


def test_reconnect_updates_existing(db: Session, user: User) -> None:
    integrations_api.connect(
        provider="todoist",
        payload=integrations_api.ConnectRequest(access_token="first"),
        user=user,
        db=db,
    )
    integrations_api.connect(
        provider="todoist",
        payload=integrations_api.ConnectRequest(access_token="second"),
        user=user,
        db=db,
    )
    rows = (
        db.query(ConnectedAccount)
        .filter(
            ConnectedAccount.user_id == user.id,
            ConnectedAccount.provider == Provider.todoist,
        )
        .all()
    )
    assert len(rows) == 1
    creds = decrypt_token(rows[0].token_ciphertext)
    assert creds["access_token"] == "second"


def test_disconnect_removes_row(db: Session, user: User) -> None:
    integrations_api.connect(
        provider="slack",
        payload=integrations_api.ConnectRequest(access_token="xoxb-test"),
        user=user,
        db=db,
    )
    integrations_api.disconnect(provider="slack", user=user, db=db)
    assert (
        db.query(ConnectedAccount)
        .filter(
            ConnectedAccount.user_id == user.id,
            ConnectedAccount.provider == Provider.slack,
        )
        .count()
        == 0
    )


def test_disconnect_404_when_not_connected(db: Session, user: User) -> None:
    with pytest.raises(HTTPException) as exc:
        integrations_api.disconnect(provider="slack", user=user, db=db)
    assert exc.value.status_code == 404


def test_list_returns_connected_only(db: Session, user: User) -> None:
    integrations_api.connect(
        provider="slack",
        payload=integrations_api.ConnectRequest(access_token="xoxb-test"),
        user=user,
        db=db,
    )
    rows = integrations_api.list_connections(user=user, db=db)
    assert len(rows) == 1
    assert rows[0].provider == Provider.slack
