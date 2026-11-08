"""
Who has Pro. One row per user (table `subscriptions`, migration 0009).

Uses Supabase when configured, otherwise a local JSON file
(backend/.local_billing.json, git-ignored), same pattern as portfolio_store.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from app.data import portfolio_store

LOCAL_FILE = Path(__file__).resolve().parents[2] / ".local_billing.json"
_lock = threading.Lock()

# Stripe subscription statuses that count as "has Pro"
ACTIVE_STATUSES = {"active", "trialing"}


def _supabase():
    from app.data.supabase_client import get_supabase
    return get_supabase()


def _load() -> Dict[str, Any]:
    if LOCAL_FILE.exists():
        try:
            return json.loads(LOCAL_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
    return {}


def get(user_id: str) -> Optional[Dict[str, Any]]:
    if portfolio_store.storage_mode() == "supabase":
        res = _supabase().table("subscriptions").select("*").eq("user_id", user_id).limit(1).execute()
        return res.data[0] if res.data else None
    return _load().get(user_id)


def find_by_customer(customer_id: str) -> Optional[Dict[str, Any]]:
    if portfolio_store.storage_mode() == "supabase":
        res = _supabase().table("subscriptions").select("*").eq("stripe_customer_id", customer_id).limit(1).execute()
        return res.data[0] if res.data else None
    return next((r for r in _load().values() if r.get("stripe_customer_id") == customer_id), None)


def upsert(user_id: str, **fields: Any) -> Dict[str, Any]:
    row = {**(get(user_id) or {}), **fields, "user_id": user_id,
           "updated_at": datetime.now(timezone.utc).isoformat()}
    if portfolio_store.storage_mode() == "supabase":
        _supabase().table("subscriptions").upsert(row, on_conflict="user_id").execute()
        return row
    with _lock:
        data = _load()
        data[user_id] = row
        LOCAL_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return row


def is_pro(row: Optional[Dict[str, Any]]) -> bool:
    return bool(row) and row.get("status") in ACTIVE_STATUSES
