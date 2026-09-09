"""
FR-2.1: Fetch historical daily OHLCV candle data (up to 15 years) for candidate stocks.
Uses yfinance / Finnhub. Respects rate limits via app.data.cache (FR-2.4).
Falls back to cached close prices if the live feed is unresponsive (NFR-3.2).
"""
from app.config import settings


async def fetch_ohlcv(ticker: str, years: int = 15):
    """
    Returns a DataFrame of Open/High/Low/Close/Volume for the given ticker.
    TODO: implement via yfinance.download() or Finnhub REST client,
    check app.data.cache before hitting the external API.
    """
    raise NotImplementedError
