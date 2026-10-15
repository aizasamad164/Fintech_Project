import numpy as np
import pandas as pd


class GlobalAllocationEngine:
    """
    Global Allocation Engine managing portfolio risk via Inverse Volatility 
    sizing, asset-level caps, and top-down sector-level limits.
    """
    def __init__(
        self,
        sector_map: dict,
        max_asset_cap: float = 0.15,
        max_sector_cap: float = 0.35,
        trading_days: int = 252
    ):
        self.sector_map = sector_map
        self.max_asset_cap = max_asset_cap
        self.max_sector_cap = max_sector_cap
        self.trading_days = trading_days

        # Invert mapping: Ticker -> Sector
        self.ticker_to_sector = {}
        for sector_name, tickers in sector_map.items():
            if isinstance(tickers, dict) and "tickers" in tickers:
                tickers = tickers["tickers"]
            for ticker in tickers:
                self.ticker_to_sector[ticker] = sector_name

    def calculate_weights(
        self,
        signals: pd.Series,
        historical_returns: pd.DataFrame
    ) -> pd.Series:
        """
        Computes inverse-volatility weights subject to asset and sector caps.
        """
        active_tickers = signals[signals == 1].index.tolist()
        if not active_tickers:
            return pd.Series(dtype=float)

        # 1. Compute Annualized Volatility (std * sqrt(252))
        sub_returns = historical_returns[active_tickers]
        vols = sub_returns.std() * np.sqrt(self.trading_days)
        
        # Handle zero or NaN volatility gracefully
        vols = vols.replace(0, np.nan).fillna(vols.mean() if not np.isnan(vols.mean()) else 0.20)

        # 2. Inverse Volatility Weighting: w_i = (1 / sigma_i) / sum(1 / sigma_j)
        inv_vols = 1.0 / vols
        weights = inv_vols / inv_vols.sum()

        # 3. Enforce Asset-Level Cap (e.g., max 15% per stock)
        weights = weights.clip(upper=self.max_asset_cap)
        weights = weights / weights.sum()

        # 4. Enforce Top-Down Sector-Level Caps (e.g., max 35% per sector)
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

        final_weights = df_weights["Weight"]
        return final_weights

    def allocate_portfolio(
        self,
        signals: pd.Series,
        historical_returns: pd.DataFrame,
        latest_prices: pd.Series,
        portfolio_value: float = 100000.0
    ) -> pd.DataFrame:
        """
        Translates weights into exact USD capital amounts and discrete share counts.
        """
        weights = self.calculate_weights(signals, historical_returns)
        if weights.empty:
            return pd.DataFrame(columns=["Sector", "Weight", "USD_Value", "Shares", "Price"])

        active_tickers = weights.index.tolist()
        
        df = pd.DataFrame({
            "Ticker": active_tickers,
            "Sector": [self.ticker_to_sector.get(t, "Unknown") for t in active_tickers],
            "Weight": weights.values,
            "Price": [latest_prices.get(t, np.nan) for t in active_tickers]
        }).set_index("Ticker")

        df["USD_Value"] = df["Weight"] * portfolio_value
        df["Shares"] = (df["USD_Value"] / df["Price"]).fillna(0).astype(int)

        return df.sort_values(by="Weight", ascending=False)