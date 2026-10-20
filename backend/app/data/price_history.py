"""
Builds the inputs the optimizer needs for a sector selection:
  * candidate stocks from public.stocks
  * one aligned DataFrame of daily closes (columns = tickers)

Stocks that cannot be loaded, or that have too little history, are skipped
and reported rather than failing the whole request (NFR-3.2).
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

import pandas as pd

from app.data.market_data import fetch_ohlcv
from app.data.supabase_client import get_supabase

logger = logging.getLogger(__name__)

VALID_SECTORS = ("technology", "healthcare", "renewable_energy")
# ~1 trading year plus margin, so a true 1-year return can be computed.
MIN_HISTORY_ROWS = 260
# Yahoo/Supabase are hit in parallel; cap it so a big sector doesn't stampede them.
MAX_PARALLEL_FETCHES = 8


@dataclass
class PriceData:
    prices: pd.DataFrame                              # aligned closes, no gaps
    skipped: dict[str, str] = field(default_factory=dict)  # ticker -> reason


def resolve_sectors(sectors: list[str] | None) -> list[str]:
    """Normalises a sector selection. Empty or ["combined"] means every sector."""
    cleaned = [s.strip().lower() for s in (sectors or []) if s and s.strip()]
    if not cleaned or "combined" in cleaned:
        return list(VALID_SECTORS)
    unknown = [s for s in cleaned if s not in VALID_SECTORS]
    if unknown:
        raise ValueError(f"Unknown sector(s): {', '.join(unknown)}. Use: {', '.join(VALID_SECTORS)}, or 'combined'.")
    return list(dict.fromkeys(cleaned))


def _query_candidates(sectors: list[str]) -> list[dict]:
    return (
        get_supabase()
        .table("stocks")
        .select("ticker,name,sector")
        .eq("is_active", True)
        .in_("sector", sectors)
        .order("ticker")
        .execute()
        .data
    ) or []


async def get_candidates(sectors: list[str] | None) -> list[dict]:
    """Active stocks in the selected sectors: [{"ticker", "name", "sector"}]."""
    return await asyncio.to_thread(_query_candidates, resolve_sectors(sectors))


async def load_price_history(tickers: list[str], years: int = 5) -> PriceData:
    """
    Loads daily closes for `tickers` (stored candles first, live feed as
    backup) and aligns them on their common trading days.
    """
    gate = asyncio.Semaphore(MAX_PARALLEL_FETCHES)

    async def _one(ticker: str):
        async with gate:
            return await fetch_ohlcv(ticker, years=years, prefer_stored=True)

    results = await asyncio.gather(*(_one(t) for t in tickers), return_exceptions=True)

    closes: dict[str, pd.Series] = {}
    skipped: dict[str, str] = {}
    for ticker, result in zip(tickers, results):
        if isinstance(result, Exception):
            logger.warning("Skipping %s: %s", ticker, result)
            skipped[ticker] = "no market data available"
        elif len(result) < MIN_HISTORY_ROWS:
            skipped[ticker] = f"only {len(result)} days of history"
        else:
            closes[ticker] = result["close"].astype(float)

    if not closes:
        return PriceData(prices=pd.DataFrame(), skipped=skipped)

    prices = pd.concat(closes, axis=1).sort_index()
    prices = prices.ffill(limit=5).dropna()   # bridge tiny gaps, then keep only common days
    if len(prices) < MIN_HISTORY_ROWS:
        skipped.update({t: "history does not overlap the other stocks" for t in prices.columns})
        return PriceData(prices=pd.DataFrame(), skipped=skipped)
    return PriceData(prices=prices, skipped=skipped)
