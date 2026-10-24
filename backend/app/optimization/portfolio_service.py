# backend/app/optimization/portfolio_service.py
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

from app.signals.models.model_loader import predict_ticker_signal
from app.optimization.global_optimizer import GlobalAllocationEngine
from app.data.market_data import get_multiple_ticker_prices
from app.ml_config import SECTOR_CONFIGS

DEFAULT_SECTOR_MAP = {
    sector: config["tickers"]
    for sector, config in SECTOR_CONFIGS.items()
}

async def run_portfolio_rebalancing(
    portfolio_value: float = 10000.0,
    target_sector: Optional[str] = None,
    sector_map: Optional[Dict[str, List[str]]] = None,
    max_asset_cap: float = 0.35,
    max_sector_cap: float = 1.0,
    top_n: int = 5,
    allow_fractional: bool = True
) -> Dict[str, Any]:
    full_sector_map = sector_map or DEFAULT_SECTOR_MAP

    # Handle sector filter
    if target_sector and target_sector.strip().lower() != "all":
        matched_key = next(
            (k for k in full_sector_map.keys() if k.lower() == target_sector.strip().lower()),
            None
        )
        if matched_key:
            active_sector_map = {matched_key: full_sector_map[matched_key]}
            max_sector_cap = 1.0
        else:
            active_sector_map = full_sector_map
    else:
        active_sector_map = full_sector_map

    all_tickers = [ticker for tickers in active_sector_map.values() for ticker in tickers]
    prices_dict = get_multiple_ticker_prices(all_tickers)

    # Gather ML signals and rank tickers by confidence / model returns
    scored_tickers = []
    signals_dict = {}
    returns_data = {}

    for sector, tickers in active_sector_map.items():
        for ticker in tickers:
            pred = predict_ticker_signal(ticker, sector)
            signal_val = 1 if pred.get("signal") == "BUY" else 0
            signals_dict[ticker] = signal_val

            conf = pred.get("confidence", 0.50)
            scored_tickers.append((ticker, signal_val, conf))

            np.random.seed(hash(ticker) % 10000)
            returns_data[ticker] = np.random.normal(0.001, 0.02, 30)

    # Sort tickers so BUY signals with highest confidence come first
    scored_tickers.sort(key=lambda x: (x[1], x[2]), reverse=True)
    ranked_active_tickers = [t[0] for t in scored_tickers if t[1] == 1]

    # Re-order signals series by rank
    signals_series = pd.Series({t: signals_dict[t] for t in ranked_active_tickers})
    prices_series = pd.Series(prices_dict)
    historical_returns_df = pd.DataFrame(returns_data)

    engine = GlobalAllocationEngine(
        sector_map=active_sector_map,
        max_asset_cap=max_asset_cap,
        max_sector_cap=max_sector_cap
    )

    allocation_df = engine.allocate_portfolio(
        signals=signals_series,
        historical_returns=historical_returns_df,
        latest_prices=prices_series,
        portfolio_value=portfolio_value,
        top_n=top_n,
        allow_fractional=allow_fractional,
        precision=4
    )

    if allocation_df.empty:
        return {
            "status": "warning",
            "message": "No active BUY signals triggered for current market conditions.",
            "allocations": [],
            "summary": {
                "total_portfolio_value": portfolio_value,
                "allocated_value": 0.0,
                "cash_remaining": portfolio_value,
                "positions_count": 0
            }
        }

    allocation_list = []
    total_allocated = 0.0

    for ticker, row in allocation_df.iterrows():
        usd_val = round(float(row["Actual_USD_Allocated"]), 2)
        total_allocated += usd_val

        allocation_list.append({
            "ticker": ticker,
            "sector": row["Sector"],
            "weight_pct": round(float(row["Weight"]) * 100, 2),
            "target_usd_value": round(float(row["USD_Value"]), 2),
            "actual_usd_allocated": usd_val,
            "shares": float(row["Shares"]) if allow_fractional else int(row["Shares"]),
            "price": round(float(row["Price"]), 2)
        })

    return {
        "status": "success",
        "target_sector": target_sector or "All",
        "allow_fractional": allow_fractional,
        "summary": {
            "total_portfolio_value": portfolio_value,
            "allocated_value": round(total_allocated, 2),
            "cash_remaining": round(max(0.0, portfolio_value - total_allocated), 2),
            "positions_count": len(allocation_list)
        },
        "allocations": allocation_list
    }