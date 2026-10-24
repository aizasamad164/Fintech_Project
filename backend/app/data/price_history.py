# backend/app/data/price_history.py
"""
Daily OHLCV history for many tickers in one yfinance call, cached in memory.

Used by:
  - app.signals.features      (the 23 features the sector models were trained on)
  - app.optimization.*        (real volatility for inverse-volatility weights)
  - 1-year return / trend numbers shown on the dashboard

One network round-trip per batch, then served from cache for `ttl` seconds,
so a dashboard reload does not re-download everything.
"""
from __future__ import annotations

import logging
import time
from typing import Dict, Iterable, List, Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

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
