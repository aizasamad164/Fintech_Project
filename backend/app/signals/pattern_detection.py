"""
FR-3.1: Detect price support/resistance and breakout formations
using scipy.signal.find_peaks.

Pipeline:
  1. find_peaks on highs (resistance) and on inverted lows (support), keeping
     only *prominent* swings so day-to-day noise is ignored.
  2. Cluster swings at nearly the same price into one horizontal level; the
     more touches a level has, the stronger it is.
  3. Flag an upward breakout when price recently closed above a resistance
     level that it was below a few sessions ago.

Everything here is pure (arrays / DataFrames in, dicts out) so it is easy to
unit-test. Saving to the database lives in app/signals/pattern_store.py.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

# Only the most recent year of candles is used to find levels: a level from
# eight years ago says little about where price reacts today.
DEFAULT_LOOKBACK_DAYS = 252
# A swing must stand out by at least this fraction of the window's average price.
DEFAULT_PROMINENCE_PCT = 0.03
# Swings closer together than this many candles count as the same swing.
DEFAULT_MIN_DISTANCE = 5
# Swings within this fraction of each other are merged into one level.
DEFAULT_CLUSTER_TOLERANCE_PCT = 0.015
# Price must close this far above a resistance level to call it a breakout.
DEFAULT_BREAKOUT_BUFFER_PCT = 0.005
# ...having been at or below the level this many sessions ago.
DEFAULT_RECENT_DAYS = 5
# Volume above this multiple of its 20-day average marks a breakout as confirmed.
VOLUME_CONFIRMATION_MULTIPLE = 1.5
VOLUME_AVERAGE_WINDOW = 20


def _cluster_levels(
    idx: np.ndarray, prices: np.ndarray, tolerance_pct: float
) -> list[dict]:
    """Merges swing points at nearly the same price into horizontal levels."""
    if len(idx) == 0:
        return []

    order = np.argsort(prices)
    clusters: list[list[int]] = [[order[0]]]
    for pos in order[1:]:
        cluster_mean = float(np.mean(prices[clusters[-1]]))
        if abs(prices[pos] - cluster_mean) <= tolerance_pct * cluster_mean:
            clusters[-1].append(pos)
        else:
            clusters.append([pos])

    levels = [
        {
            "price": round(float(np.mean(prices[members])), 4),
            "touches": len(members),
            "last_idx": int(np.max(idx[members])),
        }
        for members in clusters
    ]
    # Strongest first; among equals, the most recently touched first.
    levels.sort(key=lambda lv: (-lv["touches"], -lv["last_idx"]))
    return levels


def detect_support_resistance(
    close_prices: np.ndarray,
    high_prices: np.ndarray | None = None,
    low_prices: np.ndarray | None = None,
    *,
    lookback: int = DEFAULT_LOOKBACK_DAYS,
    prominence_pct: float = DEFAULT_PROMINENCE_PCT,
    distance: int = DEFAULT_MIN_DISTANCE,
    cluster_tolerance_pct: float = DEFAULT_CLUSTER_TOLERANCE_PCT,
) -> dict:
    """
    Returns:
      resistance_idx / support_idx        — indices (into the full input arrays)
                                            of prominent swing highs / lows
      resistance_levels / support_levels  — clustered horizontal levels, each
                                            {"price", "touches", "last_idx"},
                                            strongest first
    High/low arrays are optional; the close series is used when they are omitted.
    """
    close = np.asarray(close_prices, dtype=float)
    high = close if high_prices is None else np.asarray(high_prices, dtype=float)
    low = close if low_prices is None else np.asarray(low_prices, dtype=float)

    empty = {
        "resistance_idx": np.array([], dtype=int),
        "support_idx": np.array([], dtype=int),
        "resistance_levels": [],
        "support_levels": [],
    }
    if len(close) < 2 * distance + 1:
        return empty

    offset = max(0, len(close) - lookback)
    close_w, high_w, low_w = close[offset:], high[offset:], low[offset:]

    prominence = prominence_pct * float(np.nanmean(close_w))
    peaks, _ = find_peaks(high_w, prominence=prominence, distance=distance)
    troughs, _ = find_peaks(-low_w, prominence=prominence, distance=distance)

    peaks_full = peaks + offset
    troughs_full = troughs + offset
    return {
        "resistance_idx": peaks_full,
        "support_idx": troughs_full,
        "resistance_levels": _cluster_levels(peaks_full, high[peaks_full], cluster_tolerance_pct),
        "support_levels": _cluster_levels(troughs_full, low[troughs_full], cluster_tolerance_pct),
    }


def detect_breakouts(
    close_prices: np.ndarray,
    resistance_levels: list[dict],
    volume: np.ndarray | None = None,
    *,
    buffer_pct: float = DEFAULT_BREAKOUT_BUFFER_PCT,
    recent_days: int = DEFAULT_RECENT_DAYS,
) -> list[dict]:
    """
    An upward breakout is a resistance level that price was at or below
    `recent_days` sessions ago and has now closed clearly above (by `buffer_pct`).
    Returns [{"price_level", "close", "volume_confirmed"}], strongest level first.
    """
    close = np.asarray(close_prices, dtype=float)
    if len(close) <= recent_days:
        return []

    before = close[-(recent_days + 1)]
    latest = close[-1]

    volume_confirmed = False
    if volume is not None:
        vol = np.asarray(volume, dtype=float)
        if len(vol) > VOLUME_AVERAGE_WINDOW:
            average = float(np.mean(vol[-(VOLUME_AVERAGE_WINDOW + 1):-1]))
            volume_confirmed = bool(average > 0 and vol[-1] > VOLUME_CONFIRMATION_MULTIPLE * average)

    breakouts = []
    for level in resistance_levels:
        price = level["price"]
        if before <= price and latest > price * (1 + buffer_pct):
            breakouts.append(
                {
                    "price_level": price,
                    "close": round(float(latest), 4),
                    "volume_confirmed": volume_confirmed,
                }
            )
    return breakouts


def analyze_patterns(
    ohlcv: pd.DataFrame,
    *,
    recent_days: int = DEFAULT_RECENT_DAYS,
    **kwargs,
) -> dict:
    """
    Runs the full FR-3.1 analysis on a candle DataFrame (columns: open, high,
    low, close, volume; DatetimeIndex). Levels are learned from candles BEFORE
    the last `recent_days` so a fresh breakout candle can't become its own
    resistance. Extra kwargs go to detect_support_resistance.
    """
    if len(ohlcv) <= recent_days:
        return {"as_of": None, "support": [], "resistance": [], "breakouts": []}

    close = ohlcv["close"].to_numpy(dtype=float)
    high = ohlcv["high"].to_numpy(dtype=float)
    low = ohlcv["low"].to_numpy(dtype=float)
    volume = ohlcv["volume"].to_numpy(dtype=float) if "volume" in ohlcv else None

    cut = len(ohlcv) - recent_days
    levels = detect_support_resistance(close[:cut], high[:cut], low[:cut], **kwargs)

    return {
        "as_of": str(pd.Timestamp(ohlcv.index[-1]).date()),
        "support": levels["support_levels"],
        "resistance": levels["resistance_levels"],
        "breakouts": detect_breakouts(close, levels["resistance_levels"], volume, recent_days=recent_days),
    }


def to_pattern_records(analysis: dict, max_levels_per_type: int = 3) -> list[dict]:
    """
    Flattens analyze_patterns() output into rows for public.chart_patterns:
    {"trade_date", "pattern_type", "price_level"}. Only the strongest
    `max_levels_per_type` support and resistance levels are kept.
    """
    if analysis.get("as_of") is None:
        return []

    trade_date = analysis["as_of"]
    records = [
        {"trade_date": trade_date, "pattern_type": "support", "price_level": lv["price"]}
        for lv in analysis["support"][:max_levels_per_type]
    ]
    records += [
        {"trade_date": trade_date, "pattern_type": "resistance", "price_level": lv["price"]}
        for lv in analysis["resistance"][:max_levels_per_type]
    ]
    records += [
        {"trade_date": trade_date, "pattern_type": "breakout", "price_level": b["price_level"]}
        for b in analysis["breakouts"]
    ]
    return records
