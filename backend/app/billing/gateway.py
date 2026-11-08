"""
Every call to Stripe lives here, so the rest of the app (and the tests) never
touch the Stripe SDK directly.

Card numbers never reach our server: the browser sends them straight to Stripe
through Stripe's Payment Element, and we only ever see ids and statuses.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import stripe

from app.config import settings

logger = logging.getLogger(__name__)
PRICE_LOOKUP_KEY = "stocksense_pro_monthly"
_price_id_cache: Optional[str] = None


def configured() -> bool:
    key = settings.stripe_secret_key
    return bool(key) and key.startswith(("sk_test_", "sk_live_", "rk_test_", "rk_live_"))


def _client() -> None:
    stripe.api_key = settings.stripe_secret_key


def price_id() -> str:
    """STRIPE_PRICE_ID if set; otherwise find (or create once) a $9/month price by lookup key."""
    global _price_id_cache
    if settings.stripe_price_id:
        return settings.stripe_price_id
    if _price_id_cache:
        return _price_id_cache
    _client()
    found = stripe.Price.list(lookup_keys=[PRICE_LOOKUP_KEY], active=True, limit=1)
    if found.data:
        _price_id_cache = found.data[0].id
        return _price_id_cache
    product = stripe.Product.create(name="StockSense Pro", description="All sectors, full Insights ranking")
    price = stripe.Price.create(
        product=product.id, unit_amount=settings.pro_price_cents, currency=settings.pro_currency,
        recurring={"interval": "month"}, lookup_key=PRICE_LOOKUP_KEY,
    )
    _price_id_cache = price.id
    return price.id


def ensure_customer(existing_id: Optional[str], user_id: str, email: Optional[str]) -> str:
    _client()
    if existing_id:
        return existing_id
    customer = stripe.Customer.create(email=email or None, metadata={"user_id": user_id})
    return customer.id


def create_subscription(customer_id: str, user_id: str) -> Dict[str, Any]:
    """An incomplete subscription whose first invoice the browser pays with the card form."""
    _client()
    sub = stripe.Subscription.create(
        customer=customer_id,
        items=[{"price": price_id()}],
        payment_behavior="default_incomplete",
        payment_settings={"save_default_payment_method": "on_subscription", "payment_method_types": ["card"]},
        metadata={"user_id": user_id},
        expand=["latest_invoice.confirmation_secret"],   # payment_intent no longer exists on invoices in current API versions
    )
    return {"subscription_id": sub.id, "client_secret": _client_secret(sub), "status": sub.status}


def _client_secret(sub: Any) -> Optional[str]:
    inv = _get(sub, "latest_invoice")
    secret = _get(_get(inv, "confirmation_secret"), "client_secret")   # Stripe API 2025-03-31 and newer
    if not secret:
        secret = _get(_get(inv, "payment_intent"), "client_secret")    # older API versions
    return secret


def retrieve_subscription(subscription_id: str) -> Any:
    _client()
    return stripe.Subscription.retrieve(subscription_id)


def cancel_at_period_end(subscription_id: str, cancel: bool = True) -> Any:
    _client()
    return stripe.Subscription.modify(subscription_id, cancel_at_period_end=cancel)


def construct_event(payload: bytes, signature: str) -> Any:
    return stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)


def summarize(sub: Any) -> Dict[str, Any]:
    """The fields we store, read from a Stripe subscription (object or dict)."""
    end = _get(sub, "current_period_end")
    if end is None:  # newer API versions keep the period on each item
        items = _get(_get(sub, "items"), "data") or []
        end = _get(items[0], "current_period_end") if items else None
    return {
        "stripe_subscription_id": _get(sub, "id"),
        "stripe_customer_id": _get(sub, "customer") if isinstance(_get(sub, "customer"), str) else _get(_get(sub, "customer"), "id"),
        "status": _get(sub, "status"),
        "cancel_at_period_end": bool(_get(sub, "cancel_at_period_end")),
        "current_period_end": datetime.fromtimestamp(end, tz=timezone.utc).isoformat() if end else None,
    }


def _get(obj: Any, key: str) -> Any:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(key)
    try:
        return obj[key]
    except (KeyError, TypeError, IndexError):
        return getattr(obj, key, None)
