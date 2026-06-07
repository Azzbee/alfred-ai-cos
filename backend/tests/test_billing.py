"""Tests for Subscription + billing service (Stripe SDK mocked)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.db.models import Subscription, User
from app.services import billing


@pytest.fixture
def user(db: Session) -> User:
    u = User(email="adam@adam.dev")
    db.add(u)
    db.commit()
    return u


# --- get_or_create ---


def test_get_or_create_seeds_free_plan(db: Session, user: User) -> None:
    sub = billing.get_or_create(db, user)
    assert sub.plan == "free"
    assert sub.status == "inactive"
    assert sub.user_id == user.id


def test_get_or_create_idempotent(db: Session, user: User) -> None:
    a = billing.get_or_create(db, user)
    b = billing.get_or_create(db, user)
    assert a.id == b.id
    assert db.query(Subscription).count() == 1


# --- has_active_paid_plan ---


def test_free_plan_is_not_paid(db: Session, user: User) -> None:
    billing.get_or_create(db, user)
    assert billing.has_active_paid_plan(db, user) is False


def test_active_pro_plan_is_paid(db: Session, user: User) -> None:
    sub = billing.get_or_create(db, user)
    sub.plan = "pro"
    sub.status = "active"
    sub.current_period_end = datetime.now(UTC) + timedelta(days=15)
    db.commit()
    assert billing.has_active_paid_plan(db, user) is True


def test_expired_period_is_not_paid(db: Session, user: User) -> None:
    sub = billing.get_or_create(db, user)
    sub.plan = "pro"
    sub.status = "active"
    sub.current_period_end = datetime.now(UTC) - timedelta(days=1)
    db.commit()
    assert billing.has_active_paid_plan(db, user) is False


def test_past_due_is_not_paid(db: Session, user: User) -> None:
    sub = billing.get_or_create(db, user)
    sub.plan = "pro"
    sub.status = "past_due"
    sub.current_period_end = datetime.now(UTC) + timedelta(days=10)
    db.commit()
    assert billing.has_active_paid_plan(db, user) is False


# --- handle_event ---


def test_checkout_completed_links_customer_and_subscription(db: Session, user: User) -> None:
    billing.get_or_create(db, user)
    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": user.id,
                "customer": "cus_123",
                "subscription": "sub_abc",
            }
        },
    }
    billing.handle_event(db, event)
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).one()
    assert sub.stripe_customer_id == "cus_123"
    assert sub.stripe_subscription_id == "sub_abc"


def test_subscription_updated_sets_plan_and_period(db: Session, user: User) -> None:
    sub = billing.get_or_create(db, user)
    sub.stripe_customer_id = "cus_123"
    db.commit()
    future_ts = int((datetime.now(UTC) + timedelta(days=30)).timestamp())
    event = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_abc",
                "customer": "cus_123",
                "status": "active",
                "current_period_end": future_ts,
                "items": {
                    "data": [
                        {
                            "price": {
                                "id": "price_pro_monthly",
                                "metadata": {"plan_slug": "pro"},
                            }
                        }
                    ]
                },
            }
        },
    }
    billing.handle_event(db, event)
    db.refresh(sub)
    assert sub.status == "active"
    assert sub.plan == "pro"
    assert sub.current_period_end is not None


def test_subscription_deleted_flips_to_free(db: Session, user: User) -> None:
    sub = billing.get_or_create(db, user)
    sub.stripe_customer_id = "cus_123"
    sub.plan = "pro"
    sub.status = "active"
    sub.current_period_end = datetime.now(UTC) + timedelta(days=30)
    db.commit()
    event = {
        "type": "customer.subscription.deleted",
        "data": {"object": {"customer": "cus_123"}},
    }
    billing.handle_event(db, event)
    db.refresh(sub)
    assert sub.status == "canceled"
    assert sub.plan == "free"
    assert sub.current_period_end is None


def test_event_for_unknown_customer_is_noop(db: Session, user: User) -> None:
    """An event for a customer we don't know about shouldn't create rows."""
    event = {
        "type": "customer.subscription.updated",
        "data": {"object": {"id": "sub_x", "customer": "cus_unknown"}},
    }
    billing.handle_event(db, event)
    assert db.query(Subscription).count() == 0


def test_create_checkout_session_requires_stripe_key(
    db: Session, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("STRIPE_SECRET_KEY", "")
    # Clear the cached settings so the env var change takes effect.
    from app.core.config import get_settings

    get_settings.cache_clear()
    with pytest.raises(billing.BillingError, match="Stripe is not configured"):
        billing.create_checkout_session(
            db,
            user,
            price_id="price_x",
            success_url="https://x.io/ok",
            cancel_url="https://x.io/cancel",
        )
    get_settings.cache_clear()


def test_parse_event_refuses_without_webhook_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "")
    from app.core.config import get_settings

    get_settings.cache_clear()
    with pytest.raises(billing.BillingError, match="not configured"):
        billing.parse_event(b"{}", "sig")
    get_settings.cache_clear()
