#!/usr/bin/env python
"""
Measures the Week 1 "features in under 1 second" target.

    python scripts/benchmark_features.py                  # offline: synthetic 15-year series
    python scripts/benchmark_features.py --ticker AAPL    # real data path (needs .env + network)

Offline mode times only the indicator computation (what your code controls).
--ticker mode times the request path as GET /api/market/features/{ticker}
runs it: a cold call (nothing cached) and a warm call (in-memory cache).
"""
import argparse
import asyncio
import os
import statistics
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

BACKEND = Path(__file__).resolve().parents[1]
os.chdir(BACKEND)
sys.path.insert(0, str(BACKEND))

from app.data.indicators import compute_indicators  # noqa: E402

TARGET_SECONDS = 1.0


def synthetic_ohlcv(days: int = 3900) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.015, days)))
    return pd.DataFrame(
        {"open": close, "high": close * 1.01, "low": close * 0.99, "close": close, "volume": 1_000_000},
        index=pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days),
    )


def verdict(seconds: float) -> str:
    return "PASS" if seconds < TARGET_SECONDS else "FAIL"


def bench_offline(runs: int = 20) -> None:
    base = synthetic_ohlcv()

    # The very first call after process start pays a one-time warm-up cost.
    # The app runs indicators.warm_up() at startup, so it is reported separately.
    start = time.perf_counter()
    compute_indicators(base.copy())
    first_call = time.perf_counter() - start

    times = []
    for _ in range(runs):
        start = time.perf_counter()
        compute_indicators(base.copy())
        times.append(time.perf_counter() - start)
    median, worst = statistics.median(times), max(times)
    print(f"Offline compute, {len(base)} candles")
    print(f"  first call (one-time warm-up): {first_call * 1000:.0f} ms")
    print(f"  steady state x {runs}: median {median * 1000:.1f} ms | worst {worst * 1000:.1f} ms "
          f"| target < {TARGET_SECONDS * 1000:.0f} ms -> {verdict(worst)}")


async def bench_ticker(ticker: str) -> None:
    from app.data.market_data import fetch_ohlcv  # imports settings, so only when needed

    for label in ("cold", "warm"):
        start = time.perf_counter()
        ohlcv = await fetch_ohlcv(ticker, years=15, prefer_stored=True)
        fetched = time.perf_counter()
        await asyncio.to_thread(compute_indicators, ohlcv.copy())
        done = time.perf_counter()
        print(
            f"{ticker} {label:<4}: fetch {fetched - start:.3f}s + compute {done - fetched:.3f}s "
            f"= {done - start:.3f}s -> {verdict(done - start)}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", help="benchmark the real fetch + compute path for this ticker")
    args = parser.parse_args()
    bench_offline()
    if args.ticker:
        asyncio.run(bench_ticker(args.ticker.upper()))
