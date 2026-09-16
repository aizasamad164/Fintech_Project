"""
Week 1 deliverable: an endpoint that ingests market data and computes
technical features. Deliberately separate from /api/portfolio/generate,
which additionally needs ML signals (Week 3) and optimization (Week 4) —
wiring those in before they exist would just be another stub.
"""
import time

from fastapi import APIRouter, HTTPException

from app.core.exceptions import MarketDataUnavailableError
from app.data.feature_store import save_technical_features
from app.data.indicators import compute_indicators
from app.data.market_data import fetch_ohlcv

router = APIRouter()


@router.post("/ingest")
async def ingest_ticker(ticker: str, years: int = 15):
    """
    Fetches OHLCV for `ticker`, computes technical indicators, persists both
    to Supabase, and reports elapsed time (target: <1s per NFR-1.1's spirit
    for this stage — note the first call for a ticker will be slower since
    nothing is cached yet; subsequent calls hit the in-memory cache).
    """
    start = time.perf_counter()

    try:
        ohlcv = await fetch_ohlcv(ticker, years=years)
    except MarketDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    with_indicators = compute_indicators(ohlcv.copy())
    rows_written = await save_technical_features(ticker, with_indicators)

    elapsed = time.perf_counter() - start
    return {
        "ticker": ticker,
        "candles_fetched": len(ohlcv),
        "features_persisted": rows_written,
        "elapsed_seconds": round(elapsed, 3),
    }
