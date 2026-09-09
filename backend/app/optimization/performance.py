"""
FR-4.3: Compute historical 1-year performance % for the generated portfolio
and project an illustrative monetary return based on the user's budget.
"""


def compute_1yr_performance(weights: dict, one_year_returns: dict) -> float:
    """Weighted sum of each ticker's 1-year return, in percent."""
    return sum(weights[t] * one_year_returns[t] for t in weights)


def project_illustrative_return(budget: float, performance_pct: float) -> float:
    """Purely illustrative — not a guarantee (see FR-5.3 disclaimer)."""
    return budget * (performance_pct / 100)
