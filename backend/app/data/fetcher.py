import pandas as pd
import yfinance as yf
from datetime import datetime
from config import SECTOR_CONFIGS

def fetch_sector_data(sector_name: str) -> pd.DataFrame:
    sector_info = SECTOR_CONFIGS[sector_name]
    tickers = sector_info["tickers"] if isinstance(sector_info, dict) else sector_info

    end_date = datetime.now()
    start_date = end_date - pd.Timedelta(days=1100)

    dfs = []
    for ticker in tickers:
        try:
            ticker_obj = yf.Ticker(ticker)
            
            # 1. Fetch history with an explicit timeout to prevent terminal hangs
            df = ticker_obj.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                timeout=10
            )

            if df.empty:
                continue

            # 2. Strip timezone info (Fixes tz-naive with tz-aware join error)
            if hasattr(df.index, "tz") and df.index.tz is not None:
                df.index = df.index.tz_localize(None)

            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
            df['Ticker'] = ticker
            df['Sector'] = sector_name

            dfs.append(df.iloc[-750:])
        except Exception as e:
            print(f"Skipping {ticker}: {e}")
            continue

    if not dfs:
        raise ValueError(f"No valid price data downloaded for sector {sector_name}")

    return pd.concat(dfs, axis=0)