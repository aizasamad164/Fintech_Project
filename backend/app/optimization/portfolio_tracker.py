# backend/app/optimization/portfolio_tracker.py
"""
Live performance (P&L) for a saved portfolio. Report Appendix B, plus:
  - review note 7: a holding whose live price couldn't be fetched is flagged
    `price_is_live: False` (and counted in `stale_prices`) instead of silently
    showing a 0% change as if it were real.
  - biggest mover per portfolio, so the chat agent knows which stock to explain.
"""
from typing import Any, Dict, List

from app.data.company_names import company_name
from app.data.price_history import get_histories


def _live_prices(tickers: List[str]) -> Dict[str, float]:
    """Latest close per ticker from the cached history batch (one network call)."""
    out: Dict[str, float] = {}
    for t, df in get_histories(tickers, period="5d").items():
        if not df.empty:
            out[t] = float(df["Close"].iloc[-1])
    return out


def calculate_portfolio_performance(positions: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not positions:
        return {
            "summary": {"total_invested": 0.0, "current_value": 0.0, "total_gain_loss_usd": 0.0,
                        "total_gain_loss_pct": 0.0, "positions_count": 0, "stale_prices": 0},
            "holdings": [],
        }

    tickers = [str(p["ticker"]).upper() for p in positions]
    live = _live_prices(tickers)

    total_invested = 0.0
    current_value = 0.0
    holdings = []
    stale = 0

    for pos in positions:
        ticker = str(pos["ticker"]).upper()
        shares = float(pos["shares_held"])
        buy_price = float(pos["buy_price"])
        cost_basis = float(pos.get("cost_basis") or shares * buy_price)

        is_live = ticker in live
        current_price = live.get(ticker, buy_price)
        stale += 0 if is_live else 1

        value = shares * current_price
        gain = value - cost_basis
        gain_pct = (current_price - buy_price) / buy_price * 100 if buy_price > 0 else 0.0

        total_invested += cost_basis
        current_value += value
        holdings.append({
            "ticker": ticker,
            "name": company_name(ticker),
            "sector": pos.get("sector", "General"),
            "shares": round(shares, 4),
            "buy_price": round(buy_price, 2),
            "current_price": round(current_price, 2),
            "cost_basis": round(cost_basis, 2),
            "current_value": round(value, 2),
            "gain_loss_usd": round(gain, 2),
            "gain_loss_pct": round(gain_pct, 2),
            "price_is_live": is_live,
        })

    total_gain = current_value - total_invested
    total_pct = total_gain / total_invested * 100 if total_invested > 0 else 0.0
    mover = max(holdings, key=lambda h: abs(h["gain_loss_usd"])) if holdings else None

    return {
        "summary": {
            "total_invested": round(total_invested, 2),
            "current_value": round(current_value, 2),
            "total_gain_loss_usd": round(total_gain, 2),
            "total_gain_loss_pct": round(total_pct, 2),
            "positions_count": len(holdings),
            "stale_prices": stale,
            "biggest_mover": mover["ticker"] if mover else None,
        },
        "holdings": sorted(holdings, key=lambda h: h["current_value"], reverse=True),
    }
