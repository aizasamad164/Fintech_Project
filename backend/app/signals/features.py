# backend/app/signals/features.py
"""
Builds the 23 model features at inference time.

This MUST stay in step with ml/ensemble_engin.py::compute_advanced_features,
because the saved scalers/models expect exactly these columns, in this order,
computed the same way. If the training features change, change this too.

News_Sentiment: training used a per-ticker sentiment score from a
`sentiment_engine` module that is not in the repo. We pass a neutral 0.0
(and therefore Sentiment_Momentum = 0.0) until that module is added.
"""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pandas as pd
import ta

FEATURE_COLUMNS = [
    "Daily_Return", "RVOL", "Norm_ATR", "SMA_Ratio",
    "RSI", "MACD_HIST", "PPO", "Stoch_K", "BB_Width",
    "Lag1", "Lag2", "Lag3", "Lag4",
    "SPY_Return", "VIX_Return", "Rel_SPY_Perf",
    "News_Sentiment",
    "VWAP_Distance", "Parkinson_Vol", "ADX",
    "RSI_ZScore", "Price_Vol_Corr", "Sentiment_Momentum",
]


def build_macro_frame(spy: Optional[pd.DataFrame], vix: Optional[pd.DataFrame]) -> pd.DataFrame:
    """SPY / VIX daily returns and SPY's 50-day trend ratio (the macro filter)."""
    if spy is None or spy.empty:
        return pd.DataFrame(columns=["SPY_Return", "VIX_Return", "SPY_SMA50"])
    macro = pd.DataFrame(index=spy.index)
    macro["SPY_Return"] = spy["Close"].pct_change()
    macro["SPY_SMA50"] = spy["Close"] / spy["Close"].rolling(50).mean()
    if vix is not None and not vix.empty:
        macro["VIX_Return"] = vix["Close"].reindex(spy.index).ffill().pct_change()
    else:
        macro["VIX_Return"] = 0.0
    return macro.fillna(1.0)


def compute_feature_frame(ohlcv: pd.DataFrame, macro: pd.DataFrame, news_sentiment: float = 0.0) -> pd.DataFrame:
    """All feature columns for every day of one ticker's history."""
    s = ohlcv.copy().sort_index()
    s = s.join(macro, how="left").fillna(0)

    s["Daily_Return"] = s["Close"].pct_change()
    s["Rel_SPY_Perf"] = s["Daily_Return"] - s["SPY_Return"]

    vol_sma = ta.trend.sma_indicator(s["Volume"], window=20)
    s["RVOL"] = s["Volume"] / (vol_sma + 1e-8)

    atr = ta.volatility.average_true_range(s["High"], s["Low"], s["Close"], window=14)
    s["Norm_ATR"] = atr / s["Close"]

    s["SMA_Ratio"] = s["Close"] / ta.trend.sma_indicator(s["Close"], window=50)
    s["RSI"] = ta.momentum.rsi(s["Close"], window=14)

    macd = ta.trend.MACD(s["Close"], window_fast=12, window_slow=26, window_sign=9)
    s["MACD_HIST"] = macd.macd_diff()
    s["PPO"] = ta.momentum.PercentagePriceOscillator(s["Close"]).ppo()

    stoch = ta.momentum.StochasticOscillator(s["High"], s["Low"], s["Close"], window=14, smooth_window=3)
    s["Stoch_K"] = stoch.stoch()

    bb = ta.volatility.BollingerBands(s["Close"], window=20, window_dev=2)
    s["BB_Width"] = (bb.bollinger_hband() - bb.bollinger_lband()) / bb.bollinger_mavg()

    log_ret = np.log(s["Close"] / s["Close"].shift(1))
    for lag in range(1, 5):
        s[f"Lag{lag}"] = log_ret.shift(lag - 1)

    s["News_Sentiment"] = news_sentiment

    typical = (s["High"] + s["Low"] + s["Close"]) / 3
    s["VWAP"] = (s["Volume"] * typical).cumsum() / (s["Volume"].cumsum() + 1e-8)
    s["VWAP_Distance"] = (s["Close"] - s["VWAP"]) / (s["VWAP"] + 1e-8)

    log_hl = np.log(s["High"] / (s["Low"] + 1e-8))
    s["Parkinson_Vol"] = np.sqrt((1 / (4 * np.log(2))) * (log_hl ** 2)).rolling(14).mean()

    s["ADX"] = ta.trend.adx(s["High"], s["Low"], s["Close"], window=14)

    rsi = s["RSI"]
    s["RSI_ZScore"] = (rsi - rsi.rolling(50).mean()) / (rsi.rolling(50).std() + 1e-8)
    s["Price_Vol_Corr"] = s["Close"].pct_change().rolling(14).corr(s["Volume"].pct_change())

    s["Sentiment_MA3"] = s["News_Sentiment"].rolling(3, min_periods=1).mean()
    s["Sentiment_MA10"] = s["News_Sentiment"].rolling(10, min_periods=1).mean()
    s["Sentiment_Momentum"] = s["Sentiment_MA3"] - s["Sentiment_MA10"]
    return s


def latest_features(ohlcv: pd.DataFrame, macro: pd.DataFrame) -> Optional[Dict[str, float]]:
    """
    The most recent complete feature row for one ticker, plus SPY_SMA50 for the
    macro filter. Returns None if there is not enough history yet.
    """
    if ohlcv is None or len(ohlcv) < 80:
        return None
    frame = compute_feature_frame(ohlcv, macro)
    clean = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=FEATURE_COLUMNS)
    if clean.empty:
        return None
    row = clean.iloc[-1]
    out = {c: float(row[c]) for c in FEATURE_COLUMNS}
    out["SPY_SMA50"] = float(row.get("SPY_SMA50", 1.0) or 1.0)
    return out
