"""
FR-2.1: Fetch historical daily OHLCV candle data (up to 15 years) for candidate stocks.
Uses yfinance. Respects rate limits via app.data.cache (FR-2.4).
Falls back to previously saved candles if the live feed is unresponsive (NFR-3.2).

Database tables used (see supabase/migrations/0001_init.sql):
  stocks       — ticker -> stock_id. The ticker must already exist here.
  ohlcv_daily  — one row per (stock_id, trade_date); the durable fallback store.
"""
import asyncio
import logging
from datetime import date, timedelta
from typing import Any, Dict, List

import pandas as pd
import yfinance as yf

from app.core.exceptions import MarketDataUnavailableError
from app.data.cache import get_cached, set_cached
from app.data.supabase_client import (
    CHUNK_SIZE,
    get_stock_id,
    get_supabase,
    upsert_in_chunks,
)

logger = logging.getLogger(__name__)

# Columns every OHLCV frame is normalized down to before it leaves this module.
_OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]


# A stored series counts as "fresh" if its last candle is at most this many
# calendar days old (covers weekends and market holidays).
_FRESH_WITHIN_DAYS = 5


def _is_fresh(df: pd.DataFrame) -> bool:
    last = pd.Timestamp(df.index.max()).date()
    return (date.today() - last).days <= _FRESH_WITHIN_DAYS


async def fetch_ohlcv(ticker: str, years: int = 15, prefer_stored: bool = False) -> pd.DataFrame:
    """
    Returns a DataFrame (indexed by date, columns: open/high/low/close/volume)
    of daily candles for `ticker` going back `years` years.

    Order of lookup:
      1. In-memory cache (app.data.cache) — fastest, per-process, short TTL.
      2. (only if prefer_stored) Supabase `ohlcv_daily`, when its newest candle
         is recent. Much faster and cheaper than Yahoo, so request-time code
         (recommendations, features) should pass prefer_stored=True and leave
         live refreshes to the ingest endpoint / scripts/ingest_all.py.
      3. Live feed (yfinance) — source of truth; on success the candles are
         also saved to Supabase `ohlcv_daily`.
      4. Supabase `ohlcv_daily` — durable fallback (NFR-3.2), used when the
         live feed is down or rate-limited.

    Raises MarketDataUnavailableError only if every source fails.
    """
    ticker = ticker.upper().strip()
    cache_key = f"ohlcv:{ticker}:{years}y"

    cached = get_cached(cache_key)
    if cached is not None:
        return cached

    if prefer_stored:
        stored = await _read_from_supabase(ticker, years)
        if stored is not None and not stored.empty and _is_fresh(stored):
            set_cached(cache_key, stored)
            return stored

    try:
        # yfinance is a blocking call; run it off the event loop (NFR-1.3).
        df = await asyncio.to_thread(_download_from_yfinance, ticker, years)
    except Exception as exc:  # noqa: BLE001 — any live-feed failure falls back
        logger.warning("Live fetch failed for %s (%s); trying Supabase ohlcv_daily", ticker, exc)
        df = await _read_from_supabase(ticker, years)
        if df is None or df.empty:
            raise MarketDataUnavailableError(
                f"No live or saved OHLCV data available for {ticker}"
            ) from exc
        set_cached(cache_key, df)
        return df

    set_cached(cache_key, df)
    await _write_to_supabase(ticker, df)
    return df


# ---------------------------------------------------------------------------
# Live feed
# ---------------------------------------------------------------------------
def _download_from_yfinance(ticker: str, years: int) -> pd.DataFrame:
    start = (date.today() - timedelta(days=365 * years)).isoformat()

    raw = yf.download(ticker, start=start, progress=False, auto_adjust=True)

    if raw is None or raw.empty:
        raise MarketDataUnavailableError(f"yfinance returned no data for {ticker}")

    # Newer yfinance versions return two-level columns like ("Close", "AAPL")
    # even for one ticker; older ones return flat columns. Handle both.
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    df = raw.rename(columns=str.lower)[_OHLCV_COLUMNS].copy()
    df.index.name = "date"
    return df.dropna(subset=["close"])


# ---------------------------------------------------------------------------
# Supabase: write (after a successful live fetch)
# ---------------------------------------------------------------------------
def _to_ohlcv_records(stock_id: str, df: pd.DataFrame) -> list[dict]:
    """Turns the candle frame into rows for public.ohlcv_daily."""
    # open/high/low/close/volume are all NOT NULL in the table, so drop
    # any incomplete candle rather than letting one bad row fail the batch.
    clean = df[_OHLCV_COLUMNS].dropna()
    # One row per date, or Postgres rejects the batch ("cannot affect row a second time").
    clean = clean[~clean.index.duplicated(keep="last")].copy()

    clean["volume"] = clean["volume"].round().astype("int64")
    clean["trade_date"] = pd.DatetimeIndex(clean.index).strftime("%Y-%m-%d")
    clean["stock_id"] = stock_id
    return clean[["stock_id", "trade_date", *_OHLCV_COLUMNS]].to_dict("records")


async def _write_to_supabase(ticker: str, df: pd.DataFrame) -> None:
    """
    Best-effort durable copy. A failure here must never break the request —
    it only means the fallback is a little staler — but it is logged with a
    full traceback so it can't fail silently.
    """
    try:
        stock_id = await get_stock_id(ticker)
        if stock_id is None:
            logger.warning(
                "%s is not in public.stocks; candles were NOT saved. "
                "Add the ticker to the stocks table first.",
                ticker,
            )
            return
        records = _to_ohlcv_records(stock_id, df)
        await asyncio.to_thread(upsert_in_chunks, "ohlcv_daily", records)
    except Exception:  # noqa: BLE001
        logger.exception("Saving candles to Supabase failed for %s", ticker)


# ---------------------------------------------------------------------------
# Supabase: read (fallback)
# ---------------------------------------------------------------------------
def _read_ohlcv_rows(stock_id: str, years: int) -> list[dict]:
    """
    Reads saved candles page by page. Supabase returns at most 1000 rows per
    request, and 15 years of daily candles is ~3,900 rows, so a single query
    would silently return only the oldest ~4 years.
    """
    cutoff = (date.today() - timedelta(days=365 * years)).isoformat()
    client = get_supabase()

    rows: list[dict] = []
    offset = 0
    while True:
        page = (
            client.table("ohlcv_daily")
            .select("trade_date,open,high,low,close,volume")
            .eq("stock_id", stock_id)
            .gte("trade_date", cutoff)
            .order("trade_date")
            .range(offset, offset + CHUNK_SIZE - 1)
            .execute()
            .data
        ) or []
        rows.extend(page)
        if len(page) < CHUNK_SIZE:
            return rows
        offset += CHUNK_SIZE


async def _read_from_supabase(ticker: str, years: int) -> pd.DataFrame | None:
    """Read-path fallback: last saved candles from ohlcv_daily (NFR-3.2)."""
    try:
        stock_id = await get_stock_id(ticker)
        if stock_id is None:
            return None
        rows = await asyncio.to_thread(_read_ohlcv_rows, stock_id, years)
    except Exception:  # noqa: BLE001
        logger.exception("Supabase fallback read failed for %s", ticker)
        return None

    if not rows:
        return None

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["trade_date"])
    df = df.drop(columns="trade_date").set_index("date")
    return df[_OHLCV_COLUMNS].astype(float)



def get_latest_ticker_price(ticker: str) -> Dict[str, Any]:
    """
    Fetches the latest closing or live price for a single stock ticker.
    """
    ticker_clean = ticker.upper().strip()
    try:
        t = yf.Ticker(ticker_clean)
        price = getattr(t.fast_info, 'last_price', None)
        if price is None or price <= 0:
            hist = t.history(period="1d")
            if not hist.empty and "Close" in hist:
                price = float(hist["Close"].iloc[-1])
            else:
                price = 100.0  # Fallback
        return {"status": "success", "ticker": ticker_clean, "price": round(float(price), 2)}
    except Exception as e:
        return {"status": "error", "ticker": ticker_clean, "price": 100.0, "message": str(e)}


def get_multiple_ticker_prices(tickers: List[str]) -> Dict[str, float]:
    """
    Fetches latest prices for multiple tickers in a single batch call.
    Returns a dictionary mapping ticker -> price float.
    """
    cleaned_tickers = list(set([t.upper().strip() for t in tickers if t]))
    prices_dict: Dict[str, float] = {}

    if not cleaned_tickers:
        return prices_dict

    try:
        data = yf.download(" ".join(cleaned_tickers), period="1d", progress=False, group_by="ticker")
        for ticker in cleaned_tickers:
            try:
                if len(cleaned_tickers) == 1:
                    close_col = data["Close"] if "Close" in data else None
                else:
                    close_col = data[ticker]["Close"] if ticker in data and "Close" in data[ticker] else None

                if close_col is not None and not close_col.empty:
                    prices_dict[ticker] = round(float(close_col.dropna().iloc[-1]), 2)
                else:
                    prices_dict[ticker] = get_latest_ticker_price(ticker)["price"]
            except Exception:
                prices_dict[ticker] = get_latest_ticker_price(ticker)["price"]
    except Exception:
        for ticker in cleaned_tickers:
            prices_dict[ticker] = get_latest_ticker_price(ticker)["price"]

    return prices_dict