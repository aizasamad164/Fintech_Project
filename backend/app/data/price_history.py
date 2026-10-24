"""
Stock candidates, daily price history for the optimizer, and a cached
yfinance history loader for the feature code.

Merged from aiza (candidate loading for the optimizer) and hafsa
(yfinance history cache used by app.signals.features and the dashboard).
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

import pandas as pd
import yfinance as yf

from app.data.market_data import fetch_ohlcv
from app.data.supabase_client import get_supabase

logger = logging.getLogger(__name__)

VALID_SECTORS = ("technology", "healthcare", "renewable_energy", "pharmaceuticals")
# ~1 trading year plus margin, so a true 1-year return can be computed.
MIN_HISTORY_ROWS = 260
# Yahoo/Supabase are hit in parallel; cap it so a big sector doesn't stampede them.
MAX_PARALLEL_FETCHES = 8


# ===========================================================================
# Optimizer inputs (aiza)
# ===========================================================================
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


# ===========================================================================
# Cached yfinance histories for features and the dashboard (hafsa)
# ===========================================================================
# ~400 trading days: enough for 1-yr returns plus the 50-day / 200-day warm-up
# windows the features need.
DEFAULT_PERIOD = "2y"
_TTL_SECONDS = 60 * 30

_CACHE: Dict[str, tuple[float, pd.DataFrame]] = {}


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    if hasattr(df.index, "tz") and df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    keep = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    return df[keep].dropna(subset=["Close"])


def get_histories(tickers: Iterable[str], period: str = DEFAULT_PERIOD) -> Dict[str, pd.DataFrame]:
    """
    Returns {ticker: OHLCV DataFrame}. Tickers that fail to download are
    simply missing from the result; callers must handle that.
    """
    wanted = sorted({t.upper().strip() for t in tickers if t})
    now = time.time()
    out: Dict[str, pd.DataFrame] = {}
    missing: List[str] = []

    for t in wanted:
        hit = _CACHE.get(f"{t}:{period}")
        if hit and now - hit[0] < _TTL_SECONDS:
            out[t] = hit[1]
        else:
            missing.append(t)

    if missing:
        try:
            data = yf.download(
                missing, period=period, interval="1d", group_by="ticker",
                auto_adjust=True, progress=False, threads=True, timeout=20,
            )
            for t in missing:
                try:
                    sub = data[t] if len(missing) > 1 else data
                    df = _clean(sub.copy())
                    if not df.empty:
                        _CACHE[f"{t}:{period}"] = (now, df)
                        out[t] = df
                except Exception:  # noqa: BLE001 - one bad ticker must not sink the batch
                    logger.warning("No history for %s", t)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Batch history download failed: %s", exc)

    return out


def get_history(ticker: str, period: str = DEFAULT_PERIOD) -> Optional[pd.DataFrame]:
    return get_histories([ticker], period).get(ticker.upper().strip())


def seed_cache(histories: Dict[str, pd.DataFrame], period: str = DEFAULT_PERIOD) -> None:
    """Test helper: preload histories so no network is needed."""
    now = time.time()
    for t, df in histories.items():
        _CACHE[f"{t.upper()}:{period}"] = (now, _clean(df.copy()))