# backend/app/data/market_data.py
import yfinance as yf
from typing import Dict, Any, List

def get_latest_ticker_price(ticker: str) -> Dict[str, Any]:
    """
    Fetches the latest closing or live price for a single stock ticker.
    """
    ticker_clean = ticker.upper().strip()
    try:
        t = yf.Ticker(ticker_clean)
        price = getattr(t.fast_info, 'last_price', None)
        if price is None or price <= 0:
            hist = t.history(period="1d")
            if not hist.empty and "Close" in hist:
                price = float(hist["Close"].iloc[-1])
            else:
                price = 100.0  # Fallback
        return {
            "status": "success",
            "ticker": ticker_clean,
            "price": round(float(price), 2)
        }
    except Exception as e:
        return {
            "status": "error",
            "ticker": ticker_clean,
            "price": 100.0,
            "message": str(e)
        }

def get_multiple_ticker_prices(tickers: List[str]) -> Dict[str, float]:
    """
    Fetches latest prices for multiple tickers in a single batch call.
    Returns a dictionary mapping ticker -> price float.
    """
    cleaned_tickers = list(set([t.upper().strip() for t in tickers if t]))
    prices_dict: Dict[str, float] = {}

    if not cleaned_tickers:
        return prices_dict

    try:
        tickers_str = " ".join(cleaned_tickers)
        data = yf.download(tickers_str, period="1d", progress=False, group_by="ticker")

        for ticker in cleaned_tickers:
            try:
                if len(cleaned_tickers) == 1:
                    close_col = data["Close"] if "Close" in data else None
                else:
                    close_col = data[ticker]["Close"] if ticker in data and "Close" in data[ticker] else None

                if close_col is not None and not close_col.empty:
                    val = close_col.dropna().iloc[-1]
                    prices_dict[ticker] = round(float(val), 2)
                else:
                    prices_dict[ticker] = get_latest_ticker_price(ticker)["price"]
            except Exception:
                prices_dict[ticker] = get_latest_ticker_price(ticker)["price"]
    except Exception:
        for ticker in cleaned_tickers:
            prices_dict[ticker] = get_latest_ticker_price(ticker)["price"]

    return prices_dict