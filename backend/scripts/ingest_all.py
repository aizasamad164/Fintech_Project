#!/usr/bin/env python
"""
Batch ingest: fetches OHLCV, computes technical indicators and saves both to
Supabase for every active stock in public.stocks (FR-2.1, FR-2.3).

Run from the backend folder with your virtualenv active:

    python scripts/ingest_all.py                       # every active stock, 15 years
    python scripts/ingest_all.py --sector technology   # one sector
    python scripts/ingest_all.py --tickers AAPL MSFT   # specific tickers
    python scripts/ingest_all.py --years 5 --concurrency 2

Prerequisite: run supabase/migrations/0003_seed_stocks.sql first, otherwise
there is nothing to ingest. Exit code is 0 if every ticker succeeded, else 1.
"""
import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
os.chdir(BACKEND)  # the backend reads backend/.env relative to the working directory
sys.path.insert(0, str(BACKEND))

from app.data.feature_store import save_technical_features  # noqa: E402
from app.data.indicators import compute_indicators  # noqa: E402
from app.data.market_data import fetch_ohlcv  # noqa: E402
from app.data.supabase_client import get_supabase  # noqa: E402
from app.signals.pattern_detection import analyze_patterns, to_pattern_records  # noqa: E402
from app.signals.pattern_store import save_patterns  # noqa: E402

SECTORS = ("technology", "healthcare", "renewable_energy")


def list_tickers(sector: str | None) -> list[str]:
    query = get_supabase().table("stocks").select("ticker").eq("is_active", True)
    if sector:
        query = query.eq("sector", sector)
    return sorted(row["ticker"] for row in query.execute().data)


async def ingest_one(ticker: str, years: int, gate: asyncio.Semaphore) -> tuple[str, bool, str]:
    async with gate:
        start = time.perf_counter()
        try:
            ohlcv = await fetch_ohlcv(ticker, years=years)
            with_indicators = await asyncio.to_thread(compute_indicators, ohlcv.copy())
            rows = await save_technical_features(ticker, with_indicators)
            analysis = await asyncio.to_thread(analyze_patterns, ohlcv)
            patterns = await save_patterns(ticker, to_pattern_records(analysis))
        except Exception as exc:  # noqa: BLE001 — one bad ticker must not stop the batch
            return ticker, False, f"{type(exc).__name__}: {exc}"
        elapsed = time.perf_counter() - start
        return ticker, True, f"{len(ohlcv)} candles, {rows} feature rows, {patterns} patterns, {elapsed:.1f}s"


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--sector", choices=SECTORS, help="only ingest this sector")
    parser.add_argument("--tickers", nargs="+", help="only ingest these tickers")
    parser.add_argument("--years", type=int, default=15, choices=range(1, 16), metavar="1-15")
    parser.add_argument("--concurrency", type=int, default=3, help="parallel tickers (keep low: Yahoo rate-limits)")
    args = parser.parse_args()

    tickers = [t.upper() for t in args.tickers] if args.tickers else list_tickers(args.sector)
    if not tickers:
        print("No tickers found. Run supabase/migrations/0003_seed_stocks.sql first.")
        return 1

    print(f"Ingesting {len(tickers)} ticker(s), {args.years} years each...")
    gate = asyncio.Semaphore(max(1, args.concurrency))
    results = await asyncio.gather(*(ingest_one(t, args.years, gate) for t in tickers))

    failed = []
    for ticker, ok, detail in results:
        print(f"  [{'OK' if ok else 'FAIL'}] {ticker:<6} {detail}")
        if not ok:
            failed.append(ticker)

    print(f"\nDone: {len(tickers) - len(failed)} succeeded, {len(failed)} failed.")
    if failed:
        print("Failed: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
