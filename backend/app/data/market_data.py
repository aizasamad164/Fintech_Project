"""
FR-2.1: Fetch historical daily OHLCV candle data (up to 15 years) for candidate stocks.
Uses yfinance. Respects rate limits via app.data.cache (FR-2.4).
Falls back to cached close prices if the live feed is unresponsive (NFR-3.2).
"""
import logging
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from app.core.exceptions import MarketDataUnavailableError
from app.data.cache import get_cached, set_cached
from app.data.supabase_client import get_supabase

logger = logging.getLogger(__name__)

# Columns we normalize every OHLCV frame down to before it leaves this module.
_OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]


async def fetch_ohlcv(ticker: str, years: int = 15) -> pd.DataFrame:
    """
    Returns a DataFrame (indexed by date, columns: open/high/low/close/volume)
    of daily candles for `ticker` going back `years` years.

    Order of lookup:
      1. In-memory cache (app.data.cache) — fastest, per-process, short TTL.
      2. Live feed (yfinance) — source of truth, also refreshes both caches.
      3. Supabase `market_cache` table — durable fallback (NFR-3.2), used when
         the live feed is down or rate-limited.

    Raises MarketDataUnavailableError only if all three fail.
    """
    cache_key = f"ohlcv:{ticker}:{years}y"

    cached = get_cached(cache_key)
    if cached is not None:
        return cached

    try:
        df = await _fetch_from_yfinance(ticker, years)
        set_cached(cache_key, df)
        await _write_through_to_supabase(ticker, df)
        return df
    except Exception as exc:  # noqa: BLE001 — deliberately broad: any live-feed failure falls back
        logger.warning("Live fetch failed for %s (%s); falling back to Supabase cache", ticker, exc)
        df = await _fetch_from_supabase_cache(ticker, years)
        if df is not None and not df.empty:
            set_cached(cache_key, df)
            return df
        raise MarketDataUnavailableError(
            f"No live or cached OHLCV data available for {ticker}"
        ) from exc


async def _fetch_from_yfinance(ticker: str, years: int) -> pd.DataFrame:
    """Blocking yfinance call — fine for now at MVP scale; move to a thread
    executor (asyncio.to_thread) if this ever becomes a bottleneck under
    concurrent load (NFR-1.3)."""
    start = (datetime.utcnow() - timedelta(days=365 * years)).strftime("%Y-%m-%d")

    raw = yf.download(
        ticker,
        start=start,
        progress=False,
        auto_adjust=True,
        multi_level_index=False,
    )

    if raw is None or raw.empty:
        raise MarketDataUnavailableError(f"yfinance returned no data for {ticker}")

    df = raw.rename(columns=str.lower)[_OHLCV_COLUMNS].copy()
    df.index.name = "date"
    df = df.dropna(subset=["close"])
    return df


async def _write_through_to_supabase(ticker: str, df: pd.DataFrame) -> None:
    """
    Best-effort durable backstop (see 0001_init.sql: market_cache). Failure
    to write here should never break the request — it's a cache refresh,
    not the primary read path.
    """
    try:
        supabase = get_supabase()
        rows = [
            {
                "ticker": ticker,
                "trade_date": idx.strftime("%Y-%m-%d"),
                "open": None if pd.isna(row.open) else float(row.open),
                "high": None if pd.isna(row.high) else float(row.high),
                "low": None if pd.isna(row.low) else float(row.low),
                "close": float(row.close),
                "volume": None if pd.isna(row.volume) else int(row.volume),
            }
            for idx, row in df.iterrows()
        ]
        # upsert on (ticker, trade_date) primary key, chunked to stay well
        # under Supabase's request size limits for 15yrs of daily candles.
        for i in range(0, len(rows), 500):
            supabase.table("market_cache").upsert(rows[i : i + 500]).execute()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Supabase write-through failed for %s: %s", ticker, exc)


async def _fetch_from_supabase_cache(ticker: str, years: int) -> pd.DataFrame | None:
    """Read-path fallback: last known candles from market_cache (NFR-3.2)."""
    try:
        supabase = get_supabase()
        cutoff = (datetime.utcnow() - timedelta(days=365 * years)).strftime("%Y-%m-%d")
        resp = (
            supabase.table("market_cache")
            .select("trade_date,open,high,low,close,volume")
            .eq("ticker", ticker)
            .gte("trade_date", cutoff)
            .order("trade_date")
            .execute()
        )
        if not resp.data:
            return None
        df = pd.DataFrame(resp.data).rename(columns={"trade_date": "date"})
        df["date"] = pd.to_datetime(df["date"])
        return df.set_index("date")
    except Exception as exc:  # noqa: BLE001
        logger.error("Supabase fallback read failed for %s: %s", ticker, exc)
        return None