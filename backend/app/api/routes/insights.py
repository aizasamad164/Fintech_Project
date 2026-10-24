# backend/app/api/routes/insights.py
"""
GET /api/insights -> cross-industry board: for every sector (plus all sectors
combined), which risk strategy's portfolio had the best past-12-month return.

Builds 15 portfolios (5 scopes x 3 strategies) without LLM calls, so the first
request takes a few seconds; results are cached for 30 minutes.
"""
import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter

from app.optimization.portfolio_service import rebalance_sync

router = APIRouter()

SCOPES = {  # frontend label -> backend sector key
    "Technology": "Technology",
    "Healthcare": "Healthcare",
    "Pharmaceuticals": "Pharmaceuticals",
    "Renewable Energy": "Renewable_Energy",
    "Multi-Sector": "All",
}
RISKS = ["conservative", "balanced", "aggressive"]
_TTL = 30 * 60
_cache: Optional[Tuple[float, Dict[str, Any]]] = None


def _build() -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for label, key in SCOPES.items():
        best = None
        for risk in RISKS:
            r = rebalance_sync(portfolio_value=10000.0, target_sector=key, risk_strategy=risk)
            if r.get("status") != "success":
                continue
            ret = r["summary"]["weighted_1y_return_pct"]
            if best is None or ret > best[0]:
                best = (ret, risk, r)
        if best:
            ret, risk, r = best
            base = r["historical"][0]["value"] or 1.0
            rows.append({
                "sector": label,
                "bestRisk": risk.capitalize(),
                "bestReturn": round(ret, 1),
                "trend": [round(h["value"] / base * 100, 2) for h in r["historical"]],
                "tickers": [a["ticker"] for a in r["allocations"]],
            })
    rows.sort(key=lambda x: x["bestReturn"], reverse=True)
    return {"status": "success", "generated_at": time.time(), "rows": rows}


@router.get("")
async def insights():
    global _cache
    if _cache and time.time() - _cache[0] < _TTL:
        return _cache[1]
    data = await asyncio.to_thread(_build)
    if data["rows"]:
        _cache = (time.time(), data)
    return data
