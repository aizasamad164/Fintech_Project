# backend/app/optimization/portfolio_service.py
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

from app.signals.models.model_loader import predict_ticker_signal
from app.optimization.global_optimizer import GlobalAllocationEngine
from app.data.market_data import get_latest_ticker_price

DEFAULT_SECTOR_MAP = {
    "technology": ["AAPL", "NVDA", "MSFT", "AMD"],
    "healthcare": ["JNJ", "PFE", "UNH"],
    "pharmaceuticals": ["LLY", "MRK", "ABBV"],
    "renewable_energy": ["ENPH", "SEDG", "FSLR"]
}

async def run_portfolio_rebalancing(
    portfolio_value: float = 10000.0,
    sector_map: Optional[Dict[str, List[str]]] = None,
    max_asset_cap: float = 0.15,
    max_sector_cap: float = 0.35,
    allow_fractional: bool = True
) -> Dict[str, Any]:
    """
    Live portfolio rebalancing engine connecting model signals, live prices,
    and GlobalAllocationEngine (with fractional share support).
    Called by FastAPI (/api/portfolio/rebalance) and the AI Agent.
    """
    sector_map = sector_map or DEFAULT_SECTOR_MAP

    signals_dict = {}
    prices_dict = {}
    returns_data = {}

    # 1. Fetch ML predictions & live prices across configured tickers
    for sector, tickers in sector_map.items():
        for ticker in tickers:
            pred = predict_ticker_signal(ticker, sector)
            signal_val = 1 if pred.get("signal") == "BUY" else 0
            signals_dict[ticker] = signal_val

            price_info = get_latest_ticker_price(ticker)
            prices_dict[ticker] = price_info.get("price", 100.0)

            # Generate synthetic 30d returns proxy for volatility sizing
            np.random.seed(hash(ticker) % 10000)
            returns_data[ticker] = np.random.normal(0.001, 0.02, 30)

    signals_series = pd.Series(signals_dict)
    prices_series = pd.Series(prices_dict)
    historical_returns_df = pd.DataFrame(returns_data)

    # 2. Instantiate Inverse-Volatility Allocation Engine
    engine = GlobalAllocationEngine(
        sector_map=sector_map,
        max_asset_cap=max_asset_cap,
        max_sector_cap=max_sector_cap
    )

    # 3. Calculate portfolio allocations (Fractional vs Whole shares)
    allocation_df = engine.allocate_portfolio(
        signals=signals_series,
        historical_returns=historical_returns_df,
        latest_prices=prices_series,
        portfolio_value=portfolio_value,
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

    # 4. Format structured output for Frontend and Agent
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
        "allow_fractional": allow_fractional,
        "summary": {
            "total_portfolio_value": portfolio_value,
            "allocated_value": round(total_allocated, 2),
            "cash_remaining": round(max(0.0, portfolio_value - total_allocated), 2),
            "positions_count": len(allocation_list)
        },
        "allocations": allocation_list
    }