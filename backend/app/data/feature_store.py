"""
FR-2.3 (persistence half): write pandas-ta indicator output to
public.technical_features (see supabase/migrations/0001_init.sql).

Kept separate from indicators.py so compute_indicators() stays a pure,
easily-unit-testable function (DataFrame in, DataFrame out) with no DB
side effects — this module is the only place that saves features.
"""
import asyncio
import logging

import pandas as pd

from app.data.supabase_client import get_stock_id, upsert_in_chunks

logger = logging.getLogger(__name__)

# Database column -> pandas-ta column name(s) that can feed it.
# The technical_features table has exactly these indicator columns (see
# migrations 0001 and 0004); anything pandas-ta produces beyond them is not stored.
_COLUMN_CANDIDATES: dict[str, tuple[str, ...]] = {
    "rsi_14": ("RSI_14",),
    "macd": ("MACD_12_26_9",),
    "macd_signal": ("MACDs_12_26_9",),
    "macd_hist": ("MACDh_12_26_9",),
    "ema_50": ("EMA_50",),
    "ema_200": ("EMA_200",),
    "sma_50": ("SMA_50",),
    "sma_200": ("SMA_200",),
    "atr": ("ATRr_14", "ATR_14"),
    "volatility_20": ("VOL_20",),
}


def _to_feature_records(stock_id: str, df: pd.DataFrame) -> list[dict]:
    features = pd.DataFrame(index=df.index)
    for db_col, candidates in _COLUMN_CANDIDATES.items():
        source = next((c for c in candidates if c in df.columns), None)
        if source is not None:
            features[db_col] = df[source]

    if features.columns.empty:
        return []

    # pandas-ta leaves NaN "warm-up" rows at the start (e.g. EMA_200 needs 200 days).
    features = features.dropna(how="all")
    features = features[~features.index.duplicated(keep="last")]
    if features.empty:
        return []

    features.insert(0, "trade_date", pd.DatetimeIndex(features.index).strftime("%Y-%m-%d"))
    features.insert(0, "stock_id", stock_id)

    # NaN is not valid JSON; individual indicators that are still warming up become NULL.
    features = features.astype(object).where(features.notna(), None)
    return features.to_dict("records")


async def save_technical_features(ticker: str, df_with_indicators: pd.DataFrame) -> int:
    """
    Upserts computed indicator rows for `ticker` into technical_features and
    returns the number of rows written (0 if there was nothing to write).

    Raises ValueError if the ticker is not in public.stocks, and lets database
    errors propagate — callers decide how to report them. (Swallowing them here
    would make a missing table or column look like "0 rows written".)
    """
    stock_id = await get_stock_id(ticker)
    if stock_id is None:
        raise ValueError(f"{ticker} is not in public.stocks; add it there first")

    records = _to_feature_records(stock_id, df_with_indicators)
    if not records:
        logger.warning("No indicator values to persist for %s", ticker)
        return 0

    return await asyncio.to_thread(upsert_in_chunks, "technical_features", records)
