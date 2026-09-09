"""
FR-2.3: Compute technical indicators using pandas-ta:
RSI (14-day), MACD, EMA (50/200-day), ATR.
"""
import pandas as pd
import pandas_ta as ta


def compute_indicators(ohlcv: pd.DataFrame) -> pd.DataFrame:
    """
    Expects a DataFrame with columns: open, high, low, close, volume.
    Returns the same DataFrame with indicator columns appended.
    """
    ohlcv.ta.rsi(length=14, append=True)
    ohlcv.ta.macd(append=True)
    ohlcv.ta.ema(length=50, append=True)
    ohlcv.ta.ema(length=200, append=True)
    ohlcv.ta.atr(append=True)
    return ohlcv
