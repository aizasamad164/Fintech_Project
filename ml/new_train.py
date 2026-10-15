# ml/train.py
import os
import sys
import pandas as pd
import yfinance as yf
import joblib

# Ensure config and ML dependencies are in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from backend.app.config import SECTOR_CONFIGS
except ImportError:
    SECTOR_CONFIGS = {
        "technology": ["AAPL", "NVDA", "MSFT", "AMD"],
        "healthcare": ["JNJ", "PFE", "UNH"],
        "pharmaceuticals": ["LLY", "MRK", "ABBV"],
        "renewable_energy": ["ENPH", "SEDG", "FSLR"]
    }

from ml.ensemble_engin import (
    compute_advanced_features,
    train_sector_ensemble_regressor,
)
from backend.app.optimization.allocator import GlobalAllocationEngine

# Target directory for exported binaries
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "trained_models"))
os.makedirs(MODELS_DIR, exist_ok=True)


def extract_tickers_and_sectors(sector_map: dict) -> tuple[list, dict]:
    all_tickers = []
    ticker_to_sector = {}

    for sector_name, content in sector_map.items():
        tickers = content if isinstance(content, list) else content.get("tickers", [])
        for ticker in tickers:
            if isinstance(ticker, str) and ticker.isupper() and len(ticker) <= 5:
                all_tickers.append(ticker)
                ticker_to_sector[ticker] = sector_name

    return list(set(all_tickers)), ticker_to_sector


def load_market_data(sector_map: dict, start_date="2021-01-01", end_date="2026-09-18") -> pd.DataFrame:
    all_tickers, ticker_to_sector = extract_tickers_and_sectors(sector_map)
    if not all_tickers:
        raise ValueError("No valid tickers found in configuration.")

    print(f"[+] Downloading market data for {len(all_tickers)} tickers...")
    data = yf.download(all_tickers, start=start_date, end=end_date, group_by="ticker", progress=False)

    records = []
    for ticker in all_tickers:
        try:
            df_t = data[ticker].dropna().copy() if len(all_tickers) > 1 else data.dropna().copy()
            if not df_t.empty:
                df_t["Ticker"] = ticker
                df_t["Sector"] = ticker_to_sector[ticker]
                records.append(df_t)
        except KeyError:
            print(f"[!] Warning: Failed data download for '{ticker}'")

    if not records:
        raise ValueError("No stock data downloaded.")

    full_df = pd.concat(records, axis=0)
    if hasattr(full_df.index, "tz") and full_df.index.tz is not None:
        full_df.index = full_df.index.tz_localize(None)

    return full_df


def main():
    print("==================================================================")
    print("STARTING BATCH TRAINING PIPELINE & ARTIFACT EXPORT")
    print("==================================================================")

    raw_df = load_market_data(SECTOR_CONFIGS)
    clean_df, feature_cols = compute_advanced_features(raw_df)

    all_metrics = []
    all_scored_dfs = []

    for sector_name in clean_df["Sector"].unique():
        print(f"\n>>> TRAINING SECTOR MODEL: [{sector_name.upper()}] <<<")
        sector_df = clean_df[clean_df["Sector"] == sector_name].copy()
        if sector_df.empty:
            continue

        model, scaler, metrics, scored_df = train_sector_ensemble_regressor(
            sector_df, feature_cols, sector_name, risk_level="balanced"
        )

        model_filename = f"{sector_name.lower().replace(' ', '_')}_ensemble_model.joblib"
        scaler_filename = f"{sector_name.lower().replace(' ', '_')}_scaler.joblib"

        joblib.dump(model, os.path.join(MODELS_DIR, model_filename))
        joblib.dump(scaler, os.path.join(MODELS_DIR, scaler_filename))
        print(f"[+] Saved artifacts to 'ml/trained_models/{model_filename}'")

        all_metrics.append(metrics)
        all_scored_dfs.append(scored_df)

    metrics_df = pd.DataFrame(all_metrics)
    print("\nPER-SECTOR EVALUATION SUMMARY:\n", metrics_df.to_string(index=False))


if __name__ == "__main__":
    main()