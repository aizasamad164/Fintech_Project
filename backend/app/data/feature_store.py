"""
FR-2.3 (persistence half): write pandas-ta indicator output to
public.technical_features (see supabase/migrations/0002_add_cache_tables.sql).

Kept separate from indicators.py so compute_indicators() stays a pure,
easily-unit-testable function (DataFrame in, DataFrame out) with no DB
side effects — this module is the only place that talks to Supabase.
"""
import logging

import pandas as pd

from app.data.supabase_client import get_supabase

logger = logging.getLogger(__name__)

# Maps the columns pandas-ta appends -> our DB column names.
_COLUMN_MAP = {
    "RSI_14": "rsi_14",
    "MACD_12_26_9": "macd",
    "MACDs_12_26_9": "macd_signal",
    "MACDh_12_26_9": "macd_hist",
    "EMA_50": "ema_50",
    "EMA_200": "ema_200",
    "ATRr_14": "atr",
}


async def save_technical_features(ticker: str, df_with_indicators: pd.DataFrame) -> int:
    """
    Upserts computed indicator rows for `ticker` into technical_features.
    Returns the number of rows written. Best-effort: logs and returns 0 on
    failure rather than breaking the caller's request (same pattern as the
    market_cache write-through in market_data.py).
    """
    present_cols = [c for c in _COLUMN_MAP if c in df_with_indicators.columns]
    if not present_cols:
        logger.warning("No known indicator columns found for %s; nothing to persist", ticker)
        return 0

    feature_df = df_with_indicators[present_cols].rename(columns=_COLUMN_MAP)
    feature_df = feature_df.dropna(how="all")  # pandas-ta leaves NaN warm-up rows at the start

    if feature_df.empty:
        return 0

    rows = []
    for idx, row in feature_df.iterrows():
        record = {"ticker": ticker, "trade_date": idx.strftime("%Y-%m-%d")}
        record.update({col: (None if pd.isna(val) else float(val)) for col, val in row.items()})
        rows.append(record)

    try:
        supabase = get_supabase()
        for i in range(0, len(rows), 500):
            supabase.table("technical_features").upsert(rows[i : i + 500]).execute()
        return len(rows)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to persist technical_features for %s: %s", ticker, exc)
        return 0
