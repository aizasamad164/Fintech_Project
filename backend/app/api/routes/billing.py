"""
StockSense Pro ($9/month) through Stripe.

  GET  /api/billing/config      is Stripe set up, and the price to show
  GET  /api/billing/status      does the signed-in user have Pro
  POST /api/billing/subscribe   start a subscription -> client_secret for the card form
  POST /api/billing/confirm     after the card form succeeds: re-check with Stripe, record Pro
  POST /api/billing/cancel      cancel at the end of the current period
  POST /api/billing/webhook     Stripe -> us (renewals, failed payments, cancellations)
  POST /api/billing/demo-upgrade  ONLY when Stripe is not configured: simulated upgrade for local demos

Pro is always decided here from Stripe's answer, never from what the browser says.
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.api.deps import CurrentUser, auth_mode, get_current_user
from app.billing import gateway, store
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def _status_payload(row) -> dict:
    return {
        "is_pro": store.is_pro(row),
        "status": (row or {}).get("status", "none"),
        "current_period_end": (row or {}).get("current_period_end"),
        "cancel_at_period_end": bool((row or {}).get("cancel_at_period_end")),
        "simulated": bool((row or {}).get("simulated")),
    }


@router.get("/config")
async def billing_config():
    return {
        "configured": gateway.configured(),
        "auth_mode": auth_mode(),
        "price": {"amount_cents": settings.pro_price_cents, "currency": settings.pro_currency, "interval": "month"},
    }


@router.get("/status")
async def billing_status(user: CurrentUser = Depends(get_current_user)):
    return _status_payload(await asyncio.to_thread(store.get, user.id))


@router.post("/subscribe")
async def subscribe(user: CurrentUser = Depends(get_current_user)):
    if not gateway.configured():
        raise HTTPException(status_code=503, detail="Payments aren't set up: add STRIPE_SECRET_KEY to backend/.env.")
    row = await asyncio.to_thread(store.get, user.id)
    if store.is_pro(row):
        raise HTTPException(status_code=409, detail="You already have Pro.")
    try:
        customer_id = await asyncio.to_thread(gateway.ensure_customer, (row or {}).get("stripe_customer_id"), user.id, user.email)
        await asyncio.to_thread(store.upsert, user.id, stripe_customer_id=customer_id, status=(row or {}).get("status", "none"))
        out = await asyncio.to_thread(gateway.create_subscription, customer_id, user.id)
    except Exception as exc:  # noqa: BLE001 - Stripe errors -> readable message
        logger.exception("Stripe subscribe failed")
        raise HTTPException(status_code=502, detail=f"Payment provider error: {getattr(exc, 'user_message', None) or exc}")
    if not out.get("client_secret"):
        raise HTTPException(status_code=502, detail="Stripe did not return a payment form for this subscription.")
    return out


class ConfirmRequest(BaseModel):
    subscription_id: str


@router.post("/confirm")
async def confirm(req: ConfirmRequest, user: CurrentUser = Depends(get_current_user)):
    if not gateway.configured():
        raise HTTPException(status_code=503, detail="Payments aren't set up.")
    row = await asyncio.to_thread(store.get, user.id)
    try:
        sub = await asyncio.to_thread(gateway.retrieve_subscription, req.subscription_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Payment provider error: {exc}")
    summary = gateway.summarize(sub)
    # The subscription must belong to this user's Stripe customer
    if not row or summary["stripe_customer_id"] != row.get("stripe_customer_id"):
        raise HTTPException(status_code=403, detail="That subscription doesn't belong to this account.")
    row = await asyncio.to_thread(store.upsert, user.id, **summary, simulated=False)
    return _status_payload(row)


@router.post("/cancel")
async def cancel(user: CurrentUser = Depends(get_current_user)):
    row = await asyncio.to_thread(store.get, user.id)
    if not store.is_pro(row):
        raise HTTPException(status_code=400, detail="There's no active subscription to cancel.")
    if row.get("simulated"):
        row = await asyncio.to_thread(store.upsert, user.id, status="canceled")
        return _status_payload(row)
    try:
        sub = await asyncio.to_thread(gateway.cancel_at_period_end, row["stripe_subscription_id"])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Payment provider error: {exc}")
    row = await asyncio.to_thread(store.upsert, user.id, **gateway.summarize(sub))
    return _status_payload(row)


@router.post("/webhook")
async def webhook(request: Request):
    """Keeps Pro in sync when Stripe renews, fails or cancels a subscription."""
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="STRIPE_WEBHOOK_SECRET is not set.")
    payload = await request.body()
    try:
        event = gateway.construct_event(payload, request.headers.get("stripe-signature", ""))
    except Exception:  # noqa: BLE001 - bad signature or payload
        raise HTTPException(status_code=400, detail="Invalid Stripe signature.")

    etype = event["type"]
    obj = event["data"]["object"]
    if etype.startswith("customer.subscription."):
        summary = gateway.summarize(obj)
        meta = gateway._get(obj, "metadata") or {}
        user_id = gateway._get(meta, "user_id")
        if not user_id:
            row = await asyncio.to_thread(store.find_by_customer, summary["stripe_customer_id"])
            user_id = row["user_id"] if row else None
        if user_id:
            await asyncio.to_thread(store.upsert, user_id, **summary, simulated=False)
    return {"received": True}


@router.post("/demo-upgrade")
async def demo_upgrade(user: CurrentUser = Depends(get_current_user)):
    """Local demos without Stripe keys. Refused whenever Stripe IS configured,
    so it can never be used to skip a real payment."""
    if gateway.configured() or settings.app_env.lower() == "production":
        raise HTTPException(status_code=403, detail="Simulated upgrades are only available when payments aren't set up.")
    row = await asyncio.to_thread(store.upsert, user.id, status="active", simulated=True, cancel_at_period_end=False)
    return _status_payload(row)
