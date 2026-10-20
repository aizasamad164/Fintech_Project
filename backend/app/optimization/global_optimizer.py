# backend/app/optimization/global_optimizer.py
import numpy as np
import pandas as pd
from typing import Optional


class GlobalAllocationEngine:
    """
    Global Allocation Engine managing portfolio risk via Inverse Volatility 
    sizing, asset-level caps, and top-down sector-level limits.
    Supports Top-N position filtering for focused real-world portfolios.
    """
    def __init__(
        self,
        sector_map: dict,
        max_asset_cap: float = 0.35,
        max_sector_cap: float = 1.0,
        trading_days: int = 252
    ):
        self.sector_map = sector_map
        self.max_asset_cap = max_asset_cap
        self.max_sector_cap = max_sector_cap
        self.trading_days = trading_days

        self.ticker_to_sector = {}
        for sector_name, tickers in sector_map.items():
            if isinstance(tickers, dict) and "tickers" in tickers:
                tickers = tickers["tickers"]
            for ticker in tickers:
                self.ticker_to_sector[ticker] = sector_name

    def calculate_weights(
        self,
        signals: pd.Series,
        historical_returns: pd.DataFrame,
        top_n: Optional[int] = 5
    ) -> pd.Series:
        """
        Computes inverse-volatility weights for the Top-N active tickers.
        """
        active_tickers = signals[signals == 1].index.tolist()
        if not active_tickers:
            return pd.Series(dtype=float)

        # 1. Limit to Top-N tickers if specified
        if top_n and len(active_tickers) > top_n:
            active_tickers = active_tickers[:top_n]

        # 2. Compute Annualized Volatility
        sub_returns = historical_returns[active_tickers]
        vols = sub_returns.std() * np.sqrt(self.trading_days)
        vols = vols.replace(0, np.nan).fillna(vols.mean() if not np.isnan(vols.mean()) else 0.20)

        # 3. Inverse Volatility Weighting
        inv_vols = 1.0 / vols
        weights = inv_vols / inv_vols.sum()

        # 4. Enforce Asset Caps (Dynamically relaxed for top-N focused portfolios)
        effective_asset_cap = max(self.max_asset_cap, 1.0 / len(active_tickers) + 0.10)
        weights = weights.clip(upper=effective_asset_cap)
        weights = weights / weights.sum()

        # 5. Enforce Sector Caps
        df_weights = pd.DataFrame({
            "Ticker": active_tickers,
            "Sector": [self.ticker_to_sector.get(t, "Unknown") for t in active_tickers],
            "Weight": weights.values
        }).set_index("Ticker")

        for sector_name, group in df_weights.groupby("Sector"):
            sector_sum = group["Weight"].sum()
            if sector_sum > self.max_sector_cap:
                scale_factor = self.max_sector_cap / sector_sum
                df_weights.loc[df_weights["Sector"] == sector_name, "Weight"] *= scale_factor

        return df_weights["Weight"]

    def allocate_portfolio(
        self,
        signals: pd.Series,
        historical_returns: pd.DataFrame,
        latest_prices: pd.Series,
        portfolio_value: float = 10000.0,
        top_n: Optional[int] = 5,
        allow_fractional: bool = True,
        precision: int = 4
    ) -> pd.DataFrame:
        """
        Translates weights into capital amounts and share counts for Top-N holdings.
        """
        weights = self.calculate_weights(signals, historical_returns, top_n=top_n)
        if weights.empty:
            return pd.DataFrame(columns=["Sector", "Weight", "USD_Value", "Actual_USD_Allocated", "Shares", "Price"])

        active_tickers = weights.index.tolist()
        
        df = pd.DataFrame({
            "Ticker": active_tickers,
            "Sector": [self.ticker_to_sector.get(t, "Unknown") for t in active_tickers],
            "Weight": weights.values,
            "Price": [latest_prices.get(t, np.nan) for t in active_tickers]
        }).set_index("Ticker")

        df["USD_Value"] = df["Weight"] * portfolio_value
        
        if allow_fractional:
            df["Shares"] = (df["USD_Value"] / df["Price"]).fillna(0).round(precision)
        else:
            df["Shares"] = (df["USD_Value"] / df["Price"]).fillna(0).astype(int)

        df["Actual_USD_Allocated"] = df["Shares"] * df["Price"]

        return df.sort_values(by="Weight", ascending=False)