import numpy as np
import pandas as pd

from app.data.feature_store import _to_feature_records
from app.data.indicators import compute_indicators, warm_up


def _candles(days: int = 400) -> pd.DataFrame:
    rng = np.random.default_rng(3)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.014, days)))
    return pd.DataFrame(
        {"open": close, "high": close * 1.01, "low": close * 0.99, "close": close, "volume": 1_000_000},
        index=pd.bdate_range(end="2026-09-18", periods=days),
    )


def test_all_week_one_indicators_are_computed():
    out = compute_indicators(_candles())
    for column in (
        "RSI_14", "MACD_12_26_9", "MACDs_12_26_9", "MACDh_12_26_9",
        "EMA_50", "EMA_200", "SMA_50", "SMA_200", "ATRr_14", "VOL_20",
    ):
        assert column in out.columns, column


def test_indicator_values_are_sensible():
    out = compute_indicators(_candles())
    last = out.iloc[-1]

    assert 0 <= last["RSI_14"] <= 100
    assert last["VOL_20"] > 0
    assert last["ATRr_14"] > 0
    # Warm-up rows are NaN, not zero: EMA-200 needs 200 candles.
    assert out["EMA_200"].iloc[:150].isna().all()


def test_volatility_is_higher_for_a_choppier_series():
    calm, wild = _candles(), _candles()
    wild["close"] = wild["close"] * (1 + 0.05 * np.sin(np.arange(len(wild))))

    assert compute_indicators(wild)["VOL_20"].iloc[-1] > compute_indicators(calm)["VOL_20"].iloc[-1]


def test_feature_records_match_database_columns_and_use_null_for_warmup():
    records = _to_feature_records("stock-1", compute_indicators(_candles()))
    row = records[0]

    assert set(row) == {
        "stock_id", "trade_date", "rsi_14", "macd", "macd_signal", "macd_hist",
        "ema_50", "ema_200", "sma_50", "sma_200", "atr", "volatility_20",
    }
    assert row["ema_200"] is None  # still warming up: NULL, never NaN (NaN is invalid JSON)
    assert all(isinstance(v, (str, float, type(None))) for v in row.values())


def test_warm_up_runs_without_error():
    warm_up()
