"""
FR-2.3: Compute technical indicators using pandas-ta:
RSI (14-day), MACD (line, signal, histogram), EMA (50/200-day),
SMA (50/200-day), ATR (14-day) and 20-day annualised volatility.
"""
import numpy as np
import pandas as pd
import pandas_ta as ta  # noqa: F401  (registers the DataFrame.ta accessor)

TRADING_DAYS_PER_YEAR = 252
VOLATILITY_WINDOW = 20


def compute_indicators(ohlcv: pd.DataFrame) -> pd.DataFrame:
    """
    Expects a DataFrame with columns: open, high, low, close, volume.
    Returns the same DataFrame with indicator columns appended:
    RSI_14, MACD_12_26_9 / MACDh_12_26_9 / MACDs_12_26_9, EMA_50, EMA_200,
    SMA_50, SMA_200, ATRr_14 and VOL_20.
    """
    ohlcv.ta.rsi(length=14, append=True)
    ohlcv.ta.macd(append=True)
    ohlcv.ta.ema(length=50, append=True)
    ohlcv.ta.ema(length=200, append=True)
    ohlcv.ta.sma(length=50, append=True)
    ohlcv.ta.sma(length=200, append=True)
    ohlcv.ta.atr(append=True)

    # Volatility: rolling std of daily returns over ~1 trading month, annualised.
    ohlcv["VOL_20"] = (
        ohlcv["close"].pct_change().rolling(VOLATILITY_WINDOW).std()
        * np.sqrt(TRADING_DAYS_PER_YEAR)
    )
    return ohlcv


def warm_up() -> None:
    """
    Runs the indicator pipeline once on a small synthetic series. The first
    call after process start is slow (library imports / JIT compilation, up to
    a few seconds), so the app calls this at startup and the first real request
    stays inside the 1-second budget.
    """
    rng = np.random.default_rng(0)
    close = 100 + np.cumsum(rng.normal(0, 1, 300))
    frame = pd.DataFrame(
        {"open": close, "high": close + 1, "low": close - 1, "close": close, "volume": 1_000},
        index=pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=300),
    )
    compute_indicators(frame)
