"""Billing endpoints (PRD 24 monetization).

- GET  /api/v1/billing                    → current subscription view
- POST /api/v1/billing/checkout           → create a Stripe Checkout Session
- POST /api/v1/billing/webhook            → Stripe event receiver
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_current_user
from app.db.base import get_db
from app.db.models import User
from app.services import billing

router = APIRouter(prefix="/billing", tags=["billing"])


class SubscriptionOut(BaseModel):
    plan: str
    status: str
    current_period_end: datetime | None
    has_active_paid_plan: bool


class CheckoutRequest(BaseModel):
    price_id: str | None = None  # optional — falls back to STRIPE_PRO_PRICE_ID
    success_url: str
    cancel_url: str


class CheckoutOut(BaseModel):
    url: str
    id: str


@router.get("", response_model=SubscriptionOut)
def get_subscription(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubscriptionOut:
    sub = billing.get_or_create(db, user)
    return SubscriptionOut(
        plan=sub.plan,
        status=sub.status,
        current_period_end=sub.current_period_end,
        has_active_paid_plan=billing.has_active_paid_plan(db, user),
    )


@router.post("/checkout", response_model=CheckoutOut)
def checkout(
    payload: CheckoutRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CheckoutOut:
    settings = get_settings()
    price_id = payload.price_id or settings.stripe_pro_price_id
    if not price_id:
        raise HTTPException(
            status_code=400,
            detail="No price_id provided and STRIPE_PRO_PRICE_ID not set",
        )
    try:
        session = billing.create_checkout_session(
            db,
            user,
            price_id=price_id,
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
        )
    except billing.BillingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return CheckoutOut(url=session["url"], id=session["id"])


@router.post("/webhook", status_code=204)
async def webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> None:
    """Stripe webhook endpoint. The signature header proves the body came
    from Stripe; an invalid signature returns 400 and the event is NOT
    applied to the local subscription."""
    settings = get_settings()
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook not configured")
    body = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        event = billing.parse_event(body, sig)
    except billing.BillingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    billing.handle_event(db, event)
