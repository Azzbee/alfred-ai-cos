"""Subscription billing (PRD 24.1).

Two-plan model for now: `free` and `pro`. Real plans + prices live in
Stripe; we identify them by Stripe `price_id` provided via settings.

Surface:
  - get_or_create(user) → Subscription row; new users land on 'free'.
  - create_checkout_session(user, price_id, success_url, cancel_url) →
    a hosted-checkout URL the mobile app opens in a WebView.
  - handle_webhook_event(event) → updates the local Subscription based
    on the Stripe event (checkout.session.completed,
    customer.subscription.updated, customer.subscription.deleted).

Webhook signature verification uses settings.stripe_webhook_secret;
calls fail loudly when the signature doesn't match so we never
accept forged events."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import stripe
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Subscription, User


class BillingError(Exception):
    pass


def _stripe_client() -> Any:
    """Configure the SDK on demand so unconfigured deployments don't crash."""
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise BillingError("Stripe is not configured (set STRIPE_SECRET_KEY).")
    stripe.api_key = settings.stripe_secret_key
    return stripe


# ---------- subscription state ----------


def get_or_create(db: Session, user: User) -> Subscription:
    """Ensure a Subscription row exists for the user. Free-tier default."""
    sub = db.scalar(select(Subscription).where(Subscription.user_id == user.id))
    if sub is not None:
        return sub
    sub = Subscription(user_id=user.id, plan="free", status="inactive")
    db.add(sub)
    db.commit()
    return sub


def has_active_paid_plan(db: Session, user: User) -> bool:
    """True when the user has a non-free plan AND the period hasn't ended."""
    sub = db.scalar(select(Subscription).where(Subscription.user_id == user.id))
    if sub is None:
        return False
    if sub.plan == "free":
        return False
    if sub.status not in {"trialing", "active"}:
        return False
    if sub.current_period_end is None:
        return False
    now = datetime.now(UTC)
    end = sub.current_period_end
    if end.tzinfo is None:
        end = end.replace(tzinfo=UTC)
    return end > now


# ---------- checkout ----------


def create_checkout_session(
    db: Session,
    user: User,
    *,
    price_id: str,
    success_url: str,
    cancel_url: str,
) -> dict[str, Any]:
    """Create a Stripe Checkout Session for `price_id`. Returns
    `{url, id}` so the mobile app can open `url` in a WebView."""
    sdk = _stripe_client()
    sub = get_or_create(db, user)
    # Reuse the customer id when we already have one; Stripe handles
    # creation on first checkout when customer is None.
    session = sdk.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        customer=sub.stripe_customer_id or None,
        customer_email=user.email if not sub.stripe_customer_id else None,
        client_reference_id=user.id,
        metadata={"user_id": user.id},
    )
    return {"url": session.url, "id": session.id}


# ---------- webhooks ----------


def parse_event(payload: bytes, sig_header: str | None) -> dict[str, Any]:
    """Verify the Stripe webhook signature + parse the event. Raises
    BillingError when the signature doesn't match or webhook is not
    configured."""
    settings = get_settings()
    if not settings.stripe_webhook_secret:
        raise BillingError("STRIPE_WEBHOOK_SECRET not configured")
    if not sig_header:
        raise BillingError("Missing Stripe-Signature header")
    try:
        return stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.stripe_webhook_secret,
        )
    except (ValueError, stripe.SignatureVerificationError) as exc:
        raise BillingError(f"Invalid webhook signature: {exc}") from exc


def handle_event(db: Session, event: dict[str, Any]) -> None:
    """Update the local Subscription based on a verified Stripe event.

    Supports:
      - checkout.session.completed → wire up customer_id + subscription_id
      - customer.subscription.updated → status + plan + period_end refresh
      - customer.subscription.deleted → flip to canceled, downgrade plan
    """
    event_type = event.get("type", "")
    data = event.get("data", {}).get("object", {}) or {}

    if event_type == "checkout.session.completed":
        user_id = data.get("client_reference_id") or (data.get("metadata") or {}).get("user_id")
        if not user_id:
            return
        user = db.get(User, user_id)
        if user is None:
            return
        sub = get_or_create(db, user)
        sub.stripe_customer_id = data.get("customer")
        sub.stripe_subscription_id = data.get("subscription")
        db.commit()
        # Subscription details follow in customer.subscription.updated.
        return

    if event_type in {"customer.subscription.updated", "customer.subscription.created"}:
        customer_id = data.get("customer")
        sub = db.scalar(select(Subscription).where(Subscription.stripe_customer_id == customer_id))
        if sub is None:
            return
        sub.stripe_subscription_id = data.get("id") or sub.stripe_subscription_id
        sub.status = data.get("status") or sub.status
        # Resolve plan slug from the price metadata (we ask Stripe pricing
        # admins to set metadata.plan_slug; otherwise fall back to "pro").
        items = (data.get("items") or {}).get("data") or []
        if items:
            price = items[0].get("price") or {}
            meta_slug = (price.get("metadata") or {}).get("plan_slug")
            sub.plan = meta_slug or "pro"
        period_end = data.get("current_period_end")
        if period_end:
            sub.current_period_end = datetime.fromtimestamp(int(period_end), tz=UTC)
        db.commit()
        return

    if event_type == "customer.subscription.deleted":
        customer_id = data.get("customer")
        sub = db.scalar(select(Subscription).where(Subscription.stripe_customer_id == customer_id))
        if sub is None:
            return
        sub.status = "canceled"
        sub.plan = "free"
        sub.current_period_end = None
        db.commit()
        return
