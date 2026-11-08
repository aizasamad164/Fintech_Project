"""
Orchestrates one recommendation:
  sector selection -> candidate stocks -> price history -> optimizer ->
  dollar amounts / share counts -> historical performance.

Signals (FR-3.x) plug in through `confidence_scores`. Without them every stock
is neutral (0.5) and the result is driven by history and risk only.
"""
import asyncio
import logging
import time

from app.compliance import shariah
from app.core.exceptions import InsufficientDataError
from app.data.price_history import get_candidates, load_price_history, resolve_sectors
from app.optimization.allocator import normalize_risk_profile, optimize_portfolio
from app.optimization.discretize import discretize_allocation, summarize_allocation
from app.optimization.performance import (
    compute_1yr_performance,
    project_illustrative_return,
    trailing_returns_pct,
)

logger = logging.getLogger(__name__)

# 5 years is a stable window for covariance; the 15-year history is for the ML features.
OPTIMIZATION_YEARS = 5


async def build_recommendation(
    budget: float,
    risk_profile: str,
    sectors: list[str] | None,
    *,
    fractional_shares: bool = True,
    confidence_scores: dict[str, float] | None = None,
    shariah_only: bool = False,
) -> dict:
    start = time.perf_counter()
    risk_profile = normalize_risk_profile(risk_profile)
    sector_list = resolve_sectors(sectors)

    candidates = await get_candidates(sector_list)
    if not candidates:
        raise InsufficientDataError(
            "No stocks found for the selected sectors. Seed public.stocks (migration 0003) first."
        )
    if shariah_only:
        candidates = [c for c in candidates if shariah.is_compliant(c["ticker"])]
        if not candidates:
            raise InsufficientDataError("No Shariah-compliant stocks are available for the selected sectors.")
    by_ticker = {c["ticker"]: c for c in candidates}

    data = await load_price_history(list(by_ticker), years=OPTIMIZATION_YEARS)
    if data.prices.empty:
        raise InsufficientDataError(
            "No usable price history for the selected sectors. Run scripts/ingest_all.py first."
        )
    prices = data.prices

    # Optimization is CPU-bound; keep it off the event loop (NFR-1.3).
    weights = await asyncio.to_thread(optimize_portfolio, prices, confidence_scores, risk_profile)

    latest = {ticker: float(prices[ticker].iloc[-1]) for ticker in weights}
    allocation = discretize_allocation(budget, weights, latest, fractional=fractional_shares)
    summary = summarize_allocation(budget, allocation)

    one_year = trailing_returns_pct(prices[list(weights)])
    performance_pct = compute_1yr_performance(weights, one_year)

    items = [
        {
            "ticker": ticker,
            "name": by_ticker[ticker]["name"],
            "sector": by_ticker[ticker]["sector"],
            "price": round(latest[ticker], 4),
            "weight": weight,
            "amount": allocation[ticker]["amount"],
            "shares": allocation[ticker]["shares"],
        }
        for ticker, weight in weights.items()
    ]

    return {
        "budget": budget,
        "risk_profile": risk_profile,
        "sectors": sector_list,
        "allocations": items,
        "invested_amount": summary["invested"],
        "cash_left": summary["cash_left"],
        "one_year_performance_pct": round(performance_pct, 2),
        "projected_return": round(project_illustrative_return(summary["invested"], performance_pct), 2),
        "price_data_as_of": str(prices.index[-1].date()),
        "skipped_tickers": data.skipped,
        "shariah_only": shariah_only,
        "generated_in_seconds": round(time.perf_counter() - start, 3),
    }
