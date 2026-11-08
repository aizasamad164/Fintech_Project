"""
Week 1 deliverable: endpoints that ingest market data and compute technical
features.

  POST /api/market/ingest            — fetch + compute + SAVE (write path, slow first time)
  GET  /api/market/features/{ticker} — fetch + compute, NO writes (read path, the "< 1 s" one)
  GET  /api/market/patterns/{ticker} — support/resistance levels + breakouts, NO writes

Deliberately separate from /api/v1/recommend, which additionally needs
optimization on top of this data.
"""
import asyncio
import logging
import math
import time

from fastapi import APIRouter, HTTPException, Path, Query

from app.core.exceptions import MarketDataUnavailableError
from app.data.feature_store import save_technical_features
from app.data.indicators import compute_indicators
from app.data.market_data import fetch_ohlcv
from app.data.supabase_client import get_stock_id
from app.signals.pattern_detection import analyze_patterns, to_pattern_records
from app.signals.pattern_store import save_patterns

logger = logging.getLogger(__name__)
router = APIRouter()

# Letters/digits plus "." or "-" (e.g. BRK-B), 1-10 characters.
_TICKER_PATTERN = r"^[A-Za-z][A-Za-z0-9.\-]{0,9}$"

# Indicator columns returned by GET /features/{ticker}, keyed by response name.
_LATEST_COLUMNS = {
    "rsi_14": "RSI_14",
    "macd": "MACD_12_26_9",
    "macd_signal": "MACDs_12_26_9",
    "macd_hist": "MACDh_12_26_9",
    "ema_50": "EMA_50",
    "ema_200": "EMA_200",
    "sma_50": "SMA_50",
    "sma_200": "SMA_200",
    "atr": "ATRr_14",
    "volatility_20": "VOL_20",
}


@router.post("/ingest")
async def ingest_ticker(
    ticker: str = Query(..., pattern=_TICKER_PATTERN),
    years: int = Query(15, ge=1, le=15),
):
    """
    Fetches OHLCV for `ticker`, computes technical indicators, saves both to
    Supabase (ohlcv_daily and technical_features), and reports elapsed time.
    The ticker must already exist in public.stocks.

    The first call for a ticker is slower since nothing is cached yet;
    later calls hit the in-memory cache.
    """
    ticker = ticker.upper()
    start = time.perf_counter()

    try:
        stock_id = await get_stock_id(ticker)
    except Exception:  # noqa: BLE001
        logger.exception("Stock lookup failed for %s", ticker)
        raise HTTPException(status_code=502, detail="Could not reach the database.")
    if stock_id is None:
        raise HTTPException(
            status_code=404,
            detail=f"{ticker} is not in the stocks table. Add it to public.stocks first.",
        )

    fetch_start = time.perf_counter()
    try:
        ohlcv = await fetch_ohlcv(ticker, years=years)
    except MarketDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    fetch_seconds = time.perf_counter() - fetch_start

    # Indicator math is CPU-bound; keep it off the event loop. Timed on its own
    # because the network steps (Yahoo, Supabase) dominate the total.
    compute_start = time.perf_counter()
    with_indicators = await asyncio.to_thread(compute_indicators, ohlcv.copy())
    compute_seconds = time.perf_counter() - compute_start

    save_start = time.perf_counter()
    try:
        rows_written = await save_technical_features(ticker, with_indicators)
    except Exception:  # noqa: BLE001
        logger.exception("Saving technical_features failed for %s", ticker)
        raise HTTPException(
            status_code=502,
            detail="Market data was fetched but saving the features failed. See server logs.",
        )
    save_seconds = time.perf_counter() - save_start

    # Patterns are a bonus on the write path: a failure here is logged but
    # never fails an ingest whose candles and features were already saved.
    patterns_saved = 0
    try:
        analysis = await asyncio.to_thread(analyze_patterns, ohlcv)
        patterns_saved = await save_patterns(ticker, to_pattern_records(analysis))
    except Exception:  # noqa: BLE001
        logger.exception("Pattern detection/saving failed for %s", ticker)

    elapsed = time.perf_counter() - start
    return {
        "ticker": ticker,
        "candles_fetched": len(ohlcv),
        "features_persisted": rows_written,
        "patterns_persisted": patterns_saved,
        "fetch_seconds": round(fetch_seconds, 3),      # cache / Yahoo / Supabase read
        "compute_seconds": round(compute_seconds, 3),  # indicator math only
        "save_seconds": round(save_seconds, 3),        # Supabase upsert
        "elapsed_seconds": round(elapsed, 3),          # whole request incl. network
    }


@router.get("/features/{ticker}")
async def get_features(
    ticker: str = Path(..., pattern=_TICKER_PATTERN),
    years: int = Query(15, ge=1, le=15),
):
    """
    Computes the technical indicators for `ticker` and returns the latest
    values. Read-only: nothing is written to the database.

    Candles come from the in-memory cache, then from Supabase `ohlcv_daily`
    (if recent), and only then from Yahoo, so a warm call is dominated by the
    ~10 ms indicator computation and comfortably meets the < 1 s target.
    Run POST /ingest (or scripts/ingest_all.py) to refresh stored data.
    """
    ticker = ticker.upper()
    start = time.perf_counter()

    try:
        ohlcv = await fetch_ohlcv(ticker, years=years, prefer_stored=True)
    except MarketDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    compute_start = time.perf_counter()
    with_indicators = await asyncio.to_thread(compute_indicators, ohlcv.copy())
    compute_seconds = time.perf_counter() - compute_start

    last = with_indicators.iloc[-1]
    latest = {}
    for name, column in _LATEST_COLUMNS.items():
        value = last.get(column)
        latest[name] = None if value is None or math.isnan(value) else round(float(value), 6)

    return {
        "ticker": ticker,
        "as_of": str(with_indicators.index[-1].date()),
        "candles_used": len(ohlcv),
        "close": round(float(last["close"]), 4),
        "indicators": latest,
        "compute_seconds": round(compute_seconds, 3),
        "elapsed_seconds": round(time.perf_counter() - start, 3),
    }


@router.get("/patterns/{ticker}")
async def get_patterns(
    ticker: str = Path(..., pattern=_TICKER_PATTERN),
    years: int = Query(2, ge=1, le=15),
):
    """
    Detects support/resistance levels and any fresh upward breakout for
    `ticker`. Read-only: nothing is written (POST /ingest saves patterns).
    """
    ticker = ticker.upper()
    try:
        ohlcv = await fetch_ohlcv(ticker, years=years, prefer_stored=True)
    except MarketDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    analysis = await asyncio.to_thread(analyze_patterns, ohlcv)
    return {"ticker": ticker, **analysis}
