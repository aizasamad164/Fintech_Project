"""
FR-4.2: Translate portfolio weights into dollar amounts and discrete share counts.

Amount_i = B * w_i
Shares_i = floor(Amount_i / Price_i)
"""
import math


def discretize_allocation(budget: float, weights: dict, prices: dict) -> dict:
    """
    weights: {ticker: weight}
    prices: {ticker: current_price}
    Returns: {ticker: {"amount": float, "shares": int}}
    """
    allocation = {}
    for ticker, weight in weights.items():
        amount = budget * weight
        price = prices[ticker]
        shares = math.floor(amount / price)
        allocation[ticker] = {"amount": amount, "shares": shares}
    return allocation
