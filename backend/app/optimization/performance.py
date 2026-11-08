"""
FR-4.3: Compute historical 1-year performance % for the generated portfolio
and project an illustrative monetary return based on the user's budget.
"""
import pandas as pd

TRADING_DAYS_PER_YEAR = 252


def trailing_returns_pct(price_history: pd.DataFrame, days: int = TRADING_DAYS_PER_YEAR) -> dict[str, float]:
    """
    Per-ticker return over the last `days` trading days, in percent.
    If the history is shorter than `days`, the whole available span is used.
    """
    if len(price_history) < 2:
        raise ValueError("Need at least two price rows to compute a return.")
    window = min(days, len(price_history) - 1)
    start = price_history.iloc[-(window + 1)]
    end = price_history.iloc[-1]
    return {ticker: float((end[ticker] / start[ticker] - 1) * 100) for ticker in price_history.columns}


def compute_1yr_performance(weights: dict, one_year_returns: dict) -> float:
    """Weighted sum of each ticker's 1-year return, in percent."""
    return sum(weights[t] * one_year_returns[t] for t in weights)


def project_illustrative_return(budget: float, performance_pct: float) -> float:
    """Purely illustrative — not a guarantee (see FR-5.3 disclaimer)."""
    return budget * (performance_pct / 100)
