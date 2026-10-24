# backend/app/optimization/portfolio_service.py
"""
Builds a focused 3-5 holding portfolio from ML signals + real price history.

Pipeline:
  1. Score every ticker in the chosen sector(s) with its sector model.
  2. Rank candidates for the user's risk strategy (BUY signals first).
  3. Size positions with GlobalAllocationEngine (inverse volatility, real
     daily returns, asset/sector caps). Aggressive tilts toward the model's
     strongest predicted returns instead.
  4. Return both the agent-friendly summary AND the per-holding stats the
     frontend dashboard draws (1-yr return, 12-month trend, volatility...).

Previous version sized positions with random-number "returns"; this one uses
the last year of real daily returns.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from app.data.company_names import company_name
from app.data.price_history import get_histories
from app.ml_config import RISK_PROFILES, SECTOR_CONFIGS
from app.optimization.global_optimizer import GlobalAllocationEngine
from app.signals.models.model_loader import normalise_sector, score_tickers

DEFAULT_SECTOR_MAP = {sector: cfg["tickers"] for sector, cfg in SECTOR_CONFIGS.items()}
TRADING_DAYS = 252

# How each strategy chooses and sizes holdings.
STRATEGY = {
    "conservative": {"top_n": 5, "asset_cap": 0.30, "rank_by": "risk_adj", "rating": 2},
    "balanced":     {"top_n": 5, "asset_cap": 0.35, "rank_by": "risk_adj", "rating": 3},
    "aggressive":   {"top_n": 4, "asset_cap": 0.45, "rank_by": "pred",     "rating": 4},
}


def _risk_key(risk: Optional[str]) -> str:
    r = (risk or "balanced").strip().lower()
    return r if r in STRATEGY else "balanced"


def _resolve_sectors(target_sector: Optional[str], sector_map: Dict[str, List[str]]) -> Dict[str, List[str]]:
    if not target_sector or target_sector.strip().lower() in {"all", "multi-sector", "multi_sector", "combined"}:
        return sector_map
    key = normalise_sector(target_sector)
    return {key: sector_map[key]} if key in sector_map else sector_map


def _vol_label(annual_vol: float) -> str:
    return "Low" if annual_vol < 0.25 else ("Medium" if annual_vol < 0.45 else "High")


def _risk_class(label: str) -> str:
    return {"Low": "Conservative", "Medium": "Balanced", "High": "Aggressive"}[label]


def _monthly_trend(close: pd.Series, points: int = 12) -> tuple[List[float], List[str]]:
    """Last ~12 months of month-end closes, rebased to 100."""
    last_year = close.loc[close.index >= close.index[-1] - pd.Timedelta(days=372)]
    monthly = last_year.resample("ME").last().dropna().iloc[-points:]
    if monthly.empty:
        return [100.0], [close.index[-1].strftime("%b")]
    base = float(monthly.iloc[0]) or 1.0
    return [round(float(v) / base * 100, 2) for v in monthly], [d.strftime("%b") for d in monthly.index]


def _ticker_stats(df: pd.DataFrame) -> Dict[str, Any]:
    close = df["Close"]
    rets = close.pct_change().dropna().iloc[-TRADING_DAYS:]
    ann_vol = float(rets.std() * np.sqrt(TRADING_DAYS)) if len(rets) > 20 else 0.30
    one_year_ago = close.loc[close.index <= close.index[-1] - pd.Timedelta(days=365)]
    start = float(one_year_ago.iloc[-1]) if not one_year_ago.empty else float(close.iloc[0])
    year_return = (float(close.iloc[-1]) / start - 1) * 100 if start else 0.0
    trend, months = _monthly_trend(close)
    return {
        "price": round(float(close.iloc[-1]), 2),
        "annual_vol": ann_vol,
        "year_return_pct": round(year_return, 2),
        "trend": trend,
        "months": months,
        "daily_returns": rets,
        "last_date": close.index[-1].strftime("%Y-%m-%d"),
    }


def _empty_result(portfolio_value: float, target_sector: Optional[str], risk: str, message: str) -> Dict[str, Any]:
    return {
        "status": "warning",
        "message": message,
        "target_sector": target_sector or "All",
        "risk_strategy": risk,
        "allocations": [],
        "summary": {"total_portfolio_value": portfolio_value, "allocated_value": 0.0,
                    "cash_remaining": portfolio_value, "positions_count": 0},
    }


def rebalance_sync(
    portfolio_value: float = 10000.0,
    target_sector: Optional[str] = None,
    sector_map: Optional[Dict[str, List[str]]] = None,
    max_asset_cap: Optional[float] = None,
    max_sector_cap: float = 1.0,
    top_n: Optional[int] = None,
    allow_fractional: bool = True,
    risk_strategy: Optional[str] = "balanced",
) -> Dict[str, Any]:
    risk = _risk_key(risk_strategy)
    strat = STRATEGY[risk]
    top_n = int(top_n or strat["top_n"])
    top_n = max(3, min(5, top_n))
    asset_cap = max_asset_cap or strat["asset_cap"]

    active = _resolve_sectors(target_sector, sector_map or DEFAULT_SECTOR_MAP)
    all_tickers = [t for ts in active.values() for t in ts]
    histories = get_histories(all_tickers)
    if not histories:
        return _empty_result(portfolio_value, target_sector, risk,
                             "Market data is unavailable right now. Check your internet connection and try again.")

    # 1. Score each sector with its own model (ranking is within-sector, as trained)
    preds: Dict[str, Dict[str, Any]] = {}
    for sector, tickers in active.items():
        preds.update(score_tickers(tickers, sector))

    # 2. Build candidate table
    max_daily_vol = RISK_PROFILES[risk]["max_volatility"]
    rows = []
    stats: Dict[str, Dict[str, Any]] = {}
    for sector, tickers in active.items():
        for t in tickers:
            if t not in histories or len(histories[t]) < 60:
                continue
            stats[t] = _ticker_stats(histories[t])
            p = preds.get(t, {})
            daily_vol = float(stats[t]["daily_returns"].iloc[-60:].std())
            rows.append({
                "ticker": t, "sector": sector,
                "signal": p.get("signal", "HOLD"),
                "pred": float(p.get("predicted_return", 0.0)),
                "risk_adj": float(p.get("risk_adjusted_score", 0.0)),
                "confidence": float(p.get("confidence", 0.5)),
                "too_volatile": daily_vol > max_daily_vol,
            })
    if not rows:
        return _empty_result(portfolio_value, target_sector, risk, "Not enough price history to build a portfolio.")

    cand = pd.DataFrame(rows)
    cand["tier"] = cand["signal"].map({"BUY": 0, "HOLD": 1, "SELL": 2}).fillna(1)
    if risk != "aggressive":
        # Conservative/balanced: drop names swinging more than the profile allows,
        # unless that would leave fewer than 3 to choose from.
        calm = cand[~cand["too_volatile"]]
        if len(calm) >= 3:
            cand = calm
    cand = cand.sort_values(["tier", strat["rank_by"]], ascending=[True, False])

    # Multi-sector: take the best from each sector in turn so one sector can't take every slot
    if len(active) > 1:
        picks: List[str] = []
        queues = {s: list(g["ticker"]) for s, g in cand.groupby("sector", sort=False)}
        order = list(dict.fromkeys(cand["sector"]))
        while len(picks) < top_n and any(queues.values()):
            for s in order:
                if queues[s] and len(picks) < top_n:
                    picks.append(queues[s].pop(0))
    else:
        picks = list(cand["ticker"].iloc[:top_n])

    # 3. Size positions
    returns_df = pd.DataFrame({t: stats[t]["daily_returns"] for t in picks}).fillna(0.0)
    prices = pd.Series({t: stats[t]["price"] for t in picks})
    engine = GlobalAllocationEngine(sector_map=active, max_asset_cap=asset_cap, max_sector_cap=max_sector_cap)

    if risk == "aggressive":
        strength = cand.set_index("ticker").loc[picks, "pred"].clip(lower=0) + 0.002
        weights = (strength / strength.sum()).clip(upper=asset_cap)
        weights = weights / weights.sum()
        alloc = pd.DataFrame({
            "Sector": [engine.ticker_to_sector.get(t, "Unknown") for t in picks],
            "Weight": weights.values, "Price": prices.values,
        }, index=picks)
        alloc["USD_Value"] = alloc["Weight"] * portfolio_value
        alloc["Shares"] = np.floor(alloc["USD_Value"] / alloc["Price"] * 1e4) / 1e4 if allow_fractional \
            else (alloc["USD_Value"] / alloc["Price"]).astype(int)
        alloc["Actual_USD_Allocated"] = alloc["Shares"] * alloc["Price"]
        alloc = alloc.sort_values("Weight", ascending=False)
    else:
        alloc = engine.allocate_portfolio(
            signals=pd.Series(1, index=picks), historical_returns=returns_df,
            latest_prices=prices, portfolio_value=portfolio_value, top_n=top_n,
            allow_fractional=allow_fractional, precision=4,
        )

    # 4. Shape the response
    allocations: List[Dict[str, Any]] = []
    total_allocated = 0.0
    for t, row in alloc.iterrows():
        st, p = stats[t], preds.get(t, {})
        usd = round(float(row["Actual_USD_Allocated"]), 2)
        total_allocated += usd
        vol_label = _vol_label(st["annual_vol"])
        allocations.append({
            "ticker": t,
            "name": company_name(t),
            "sector": row["Sector"],
            "weight_pct": round(float(row["Weight"]) * 100, 2),
            "target_usd_value": round(float(row["USD_Value"]), 2),
            "actual_usd_allocated": usd,
            "shares": float(row["Shares"]) if allow_fractional else int(row["Shares"]),
            "price": st["price"],
            "year_return_pct": st["year_return_pct"],
            "annual_volatility_pct": round(st["annual_vol"] * 100, 1),
            "volatility": vol_label,
            "risk_class": _risk_class(vol_label),
            "trend": st["trend"],
            "ml_signal": p.get("signal", "HOLD"),
            "ml_confidence": p.get("confidence", 0.5),
            "predicted_5d_return": p.get("predicted_5d_return", "0.0%"),
        })

    # Portfolio-level history: what this mix would have done over the last 12 months
    w = alloc["Weight"] / alloc["Weight"].sum()
    port_daily = (returns_df[w.index] * w.values).sum(axis=1)
    port_vol = float(port_daily.std() * np.sqrt(TRADING_DAYS)) if len(port_daily) > 20 else 0.25
    weighted_return = float(sum(a["year_return_pct"] * a["weight_pct"] for a in allocations) / 100)
    months = stats[picks[0]]["months"]
    n = min(len(stats[t]["trend"]) for t in w.index)
    historical = [
        {"month": months[-n:][i],
         "value": round(portfolio_value * sum(float(w[t]) * stats[t]["trend"][-n:][i] / stats[t]["trend"][-n:][0]
                                            for t in w.index), 2)}
        for i in range(n)
    ]
    # Blend measured volatility with the strategy the user chose, so a Balanced
    # portfolio never reads as "low risk" just because it had a calm year
    vol_rating = int(1 + np.searchsorted([0.15, 0.22, 0.30, 0.40], port_vol))
    risk_rating = int(np.clip(round((vol_rating + strat["rating"]) / 2 + 0.01), 1, 5))

    return {
        "status": "success",
        "target_sector": target_sector or "All",
        "risk_strategy": risk,
        "allow_fractional": allow_fractional,
        "as_of": max(stats[t]["last_date"] for t in picks),
        "summary": {
            "total_portfolio_value": portfolio_value,
            "allocated_value": round(total_allocated, 2),
            "cash_remaining": round(max(0.0, portfolio_value - total_allocated), 2),
            "positions_count": len(allocations),
            "weighted_1y_return_pct": round(weighted_return, 2),
            "projected_value": round(portfolio_value * (1 + weighted_return / 100), 2),
            "annual_volatility_pct": round(port_vol * 100, 1),
            "risk_rating": risk_rating,
        },
        "historical": historical,
        "allocations": allocations,
    }


async def run_portfolio_rebalancing(**kwargs: Any) -> Dict[str, Any]:
    """Async wrapper used by the API and the agent's optimize_portfolio tool.
    The work (downloads + model inference) is blocking, so it runs in a thread
    to keep the server responsive for other requests."""
    return await asyncio.to_thread(rebalance_sync, **kwargs)
