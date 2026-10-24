# backend/app/data/portfolio_store.py
"""
Saved portfolios (tables: user_portfolios + portfolio_positions, migration 0004).

Uses Supabase when SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are set in
backend/.env. Otherwise falls back to a local JSON file
(backend/.local_portfolios.json, git-ignored) so the app works on localhost
before the database is configured.

Every read is scoped by user_id (report section 7, item 5): a portfolio id on
its own is never enough to read someone else's holdings.
"""
from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)
LOCAL_FILE = Path(__file__).resolve().parents[2] / ".local_portfolios.json"
_lock = threading.Lock()


def _supabase_configured() -> bool:
    url, key = settings.supabase_url, settings.supabase_service_role_key
    return bool(url and key and "your-project" not in url and key != "replace-me")


def storage_mode() -> str:
    return "supabase" if _supabase_configured() else "local-file"


def _db():
    from app.data.supabase_client import get_supabase
    return get_supabase()


# ---------------------------------------------------------------- local file
def _load() -> Dict[str, Any]:
    if LOCAL_FILE.exists():
        try:
            return json.loads(LOCAL_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            logger.warning("Could not read %s; starting empty", LOCAL_FILE)
    return {"portfolios": {}}


def _dump(data: Dict[str, Any]) -> None:
    LOCAL_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------------------------------------------------------------- public API
def save_portfolio(user_id: str, portfolio_name: str, target_sector: str, risk_strategy: str,
                   initial_investment: float, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
    clean_positions = []
    for p in positions:
        shares = round(float(p["shares_held"]), 4)
        buy = round(float(p["buy_price"]), 2)
        clean_positions.append({
            "ticker": str(p["ticker"]).upper()[:10],
            "sector": str(p.get("sector") or "General")[:50],
            "shares_held": shares,
            "buy_price": buy,
            "cost_basis": round(float(p.get("cost_basis") or shares * buy), 2),
        })

    record = {
        "user_id": user_id,
        "portfolio_name": (portfolio_name or "My Advisory Portfolio")[:100],
        "target_sector": (target_sector or "All")[:50],
        "risk_strategy": (risk_strategy or "balanced")[:20],
        "initial_investment": round(float(initial_investment), 2),
    }

    if _supabase_configured():
        db = _db()
        saved = db.table("user_portfolios").insert(record).execute().data[0]
        rows = [{**p, "portfolio_id": saved["id"]} for p in clean_positions]
        if rows:
            db.table("portfolio_positions").insert(rows).execute()
        return {**saved, "positions": clean_positions}

    with _lock:
        data = _load()
        pid = str(uuid.uuid4())
        saved = {**record, "id": pid, "created_at": datetime.now(timezone.utc).isoformat(),
                 "positions": clean_positions}
        data["portfolios"][pid] = saved
        _dump(data)
    return saved


def get_portfolio(portfolio_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    if _supabase_configured():
        db = _db()
        res = db.table("user_portfolios").select("*").eq("id", portfolio_id).eq("user_id", user_id).limit(1).execute()
        if not res.data:
            return None
        pos = db.table("portfolio_positions").select("*").eq("portfolio_id", portfolio_id).execute()
        return {**res.data[0], "positions": pos.data or []}

    p = _load()["portfolios"].get(portfolio_id)
    return p if p and p["user_id"] == user_id else None


def list_portfolios(user_id: str) -> List[Dict[str, Any]]:
    if _supabase_configured():
        db = _db()
        res = db.table("user_portfolios").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        out = []
        for row in res.data or []:
            pos = db.table("portfolio_positions").select("*").eq("portfolio_id", row["id"]).execute()
            out.append({**row, "positions": pos.data or []})
        return out

    items = [p for p in _load()["portfolios"].values() if p["user_id"] == user_id]
    return sorted(items, key=lambda p: p["created_at"], reverse=True)


def delete_portfolio(portfolio_id: str, user_id: str) -> bool:
    if _supabase_configured():
        res = _db().table("user_portfolios").delete().eq("id", portfolio_id).eq("user_id", user_id).execute()
        return bool(res.data)
    with _lock:
        data = _load()
        p = data["portfolios"].get(portfolio_id)
        if not p or p["user_id"] != user_id:
            return False
        del data["portfolios"][portfolio_id]
        _dump(data)
    return True
