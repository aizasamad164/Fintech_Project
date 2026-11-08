"""
FR-4.2: Translate portfolio weights into dollar amounts and share counts.

Fractional mode (default, matches modern brokers):
    Shares_i = floor(B * w_i / Price_i, to `decimals` places)
Whole-share mode (fractional=False):
    Shares_i = floor(B * w_i / Price_i), then any leftover cash is spent on
    extra whole shares of the positions furthest below their target.

Guarantees, for any valid input:
  * shares and amounts are never negative
  * sum(amount) never exceeds the budget (every value is rounded DOWN)
"""
from __future__ import annotations

import math

CENTS = 100


def _floor_to(value: float, factor: int) -> float:
    # The tiny epsilon stops float noise (e.g. 2.9999999999) from losing a unit.
    return math.floor(value * factor + 1e-9) / factor


def _validate(budget: float, weights: dict, prices: dict) -> dict[str, float]:
    if not isinstance(budget, (int, float)) or not math.isfinite(budget) or budget <= 0:
        raise ValueError("Budget must be a positive number.")

    active = {t: float(w) for t, w in weights.items() if w and w > 0}
    if not active:
        raise ValueError("Weights must contain at least one positive value.")
    if any(w < 0 for w in weights.values()):
        raise ValueError("Weights cannot be negative.")

    for ticker in active:
        price = prices.get(ticker)
        if price is None or not math.isfinite(price) or price <= 0:
            raise ValueError(f"Missing or invalid price for {ticker}.")

    total = sum(active.values())
    if total > 1.0:  # rescale so an over-allocated input can never overspend the budget
        active = {t: w / total for t, w in active.items()}
    return active


def discretize_allocation(
    budget: float,
    weights: dict,
    prices: dict,
    *,
    fractional: bool = True,
    decimals: int = 4,
) -> dict:
    """
    weights: {ticker: weight}
    prices: {ticker: current_price}
    Returns: {ticker: {"amount": float, "shares": float | int}}
    """
    active = _validate(budget, weights, prices)

    if fractional:
        factor = 10 ** decimals
        shares = {t: _floor_to(budget * w / prices[t], factor) for t, w in active.items()}
    else:
        shares = {t: math.floor(budget * w / prices[t] + 1e-9) for t, w in active.items()}
        cash = budget - sum(shares[t] * prices[t] for t in shares)
        while True:
            affordable = [t for t in shares if prices[t] <= cash + 1e-9]
            if not affordable:
                break
            # Buy one more share of whichever affordable position is furthest below target.
            pick = max(affordable, key=lambda t: budget * active[t] - shares[t] * prices[t])
            shares[pick] += 1
            cash -= prices[pick]

    allocation = {}
    for ticker in weights:
        n = shares.get(ticker, 0)
        amount = _floor_to(n * prices[ticker], CENTS) if n else 0.0
        allocation[ticker] = {"amount": amount, "shares": n if fractional else int(n)}
    return allocation


def summarize_allocation(budget: float, allocation: dict) -> dict:
    """Total invested and cash left over (never negative)."""
    invested = round(sum(item["amount"] for item in allocation.values()), 2)
    return {"invested": invested, "cash_left": round(max(budget - invested, 0.0), 2)}
