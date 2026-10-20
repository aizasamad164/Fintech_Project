"""
Week 2 backend unit tests: discretization (dollar amounts / share counts) and
the portfolio allocator, checked across budgets from $100 to $100,000 so no
budget size can produce negative shares or an allocation that overflows.
"""
import numpy as np
import pandas as pd
import pytest

from app.optimization import allocator
from app.optimization.allocator import RISK_PROFILES, blend_expected_returns, optimize_portfolio
from app.optimization.discretize import discretize_allocation, summarize_allocation
from app.optimization.performance import compute_1yr_performance, trailing_returns_pct

BUDGETS = [100, 250, 500, 1_000, 2_500, 5_000, 10_000, 25_000, 100_000]
PROFILES = list(RISK_PROFILES)


# --------------------------------------------------------------------------
# discretize_allocation
# --------------------------------------------------------------------------
def test_discretize_allocation_whole_shares_basic():
    result = discretize_allocation(
        1000.0, {"AAPL": 0.5, "MSFT": 0.5}, {"AAPL": 150.0, "MSFT": 300.0}, fractional=False
    )
    assert result["AAPL"]["shares"] == 3 + 1  # floor(500/150)=3, +1 from leftover cash
    assert result["MSFT"]["shares"] == 1      # floor(500/300)


def test_discretize_allocation_fractional_is_default():
    result = discretize_allocation(100.0, {"AAPL": 1.0}, {"AAPL": 300.0})
    assert result["AAPL"]["shares"] == pytest.approx(0.3333)
    assert result["AAPL"]["amount"] == pytest.approx(99.99)


def test_small_budget_buys_a_slice_of_an_expensive_stock():
    result = discretize_allocation(100.0, {"BRK": 1.0}, {"BRK": 600_000.0})
    assert result["BRK"]["shares"] >= 0
    assert result["BRK"]["amount"] <= 100.0


def test_whole_shares_can_be_zero_but_never_negative():
    result = discretize_allocation(100.0, {"BRK": 1.0}, {"BRK": 600_000.0}, fractional=False)
    assert result["BRK"] == {"amount": 0.0, "shares": 0}


def test_whole_share_leftover_cash_is_reinvested():
    prices = {"A": 150.0, "B": 300.0}
    result = discretize_allocation(1000.0, {"A": 0.5, "B": 0.5}, prices, fractional=False)
    summary = summarize_allocation(1000.0, result)
    assert summary["cash_left"] < min(prices.values())  # nothing affordable is left unspent


@pytest.mark.parametrize("bad_budget", [0, -5, float("nan"), float("inf")])
def test_invalid_budget_is_rejected(bad_budget):
    with pytest.raises(ValueError):
        discretize_allocation(bad_budget, {"A": 1.0}, {"A": 10.0})


def test_missing_or_bad_price_is_rejected():
    with pytest.raises(ValueError):
        discretize_allocation(100.0, {"A": 0.5, "B": 0.5}, {"A": 10.0})
    with pytest.raises(ValueError):
        discretize_allocation(100.0, {"A": 1.0}, {"A": 0.0})


def test_overallocated_weights_never_overspend():
    result = discretize_allocation(1000.0, {"A": 0.7, "B": 0.7}, {"A": 10.0, "B": 20.0})
    assert summarize_allocation(1000.0, result)["invested"] <= 1000.0


@pytest.mark.parametrize("fractional", [True, False])
@pytest.mark.parametrize("budget", BUDGETS)
def test_budget_sweep_never_negative_or_overflowing(budget, fractional, price_history):
    prices = price_history.iloc[-1].to_dict()
    weights = {t: 1 / len(prices) for t in prices}

    result = discretize_allocation(budget, weights, prices, fractional=fractional)
    summary = summarize_allocation(budget, result)

    assert all(item["shares"] >= 0 and item["amount"] >= 0 for item in result.values())
    assert summary["invested"] <= budget + 1e-9
    assert summary["cash_left"] >= 0


# --------------------------------------------------------------------------
# optimize_portfolio
# --------------------------------------------------------------------------
@pytest.mark.parametrize("profile", PROFILES)
def test_weights_are_valid_for_every_profile(profile, price_history):
    weights = optimize_portfolio(price_history, risk_tolerance=profile)

    assert sum(weights.values()) == pytest.approx(1.0, abs=1e-6)
    assert all(w > 0 for w in weights.values())
    cap = RISK_PROFILES[profile]["max_weight"]
    assert max(weights.values()) <= cap * 1.05  # small drift allowed after dust removal


def test_profiles_are_ordered_by_risk(price_history):
    log_returns = np.log(price_history).diff().dropna()
    covariance = log_returns.cov() * 252

    def volatility(profile):
        w = pd.Series(optimize_portfolio(price_history, risk_tolerance=profile)).reindex(covariance.index).fillna(0)
        return float(np.sqrt(w @ covariance @ w))

    conservative, balanced, aggressive = (volatility(p) for p in PROFILES)
    assert conservative < balanced < aggressive


def test_legacy_risk_names_are_accepted(price_history):
    assert optimize_portfolio(price_history, risk_tolerance="low") == optimize_portfolio(
        price_history, risk_tolerance="conservative"
    )


def test_unknown_risk_profile_is_rejected(price_history):
    with pytest.raises(ValueError):
        optimize_portfolio(price_history, risk_tolerance="yolo")


def test_single_stock_gets_everything(price_history):
    assert optimize_portfolio(price_history[["T00"]], risk_tolerance="aggressive") == {"T00": 1.0}


def test_two_stocks_respect_feasible_cap(price_history):
    weights = optimize_portfolio(price_history[["T00", "T01"]], risk_tolerance="conservative")
    assert sum(weights.values()) == pytest.approx(1.0, abs=1e-6)  # cap 25% is infeasible for 2 stocks; must still solve


def _with_nan(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame.iloc[5, 0] = np.nan
    return frame


@pytest.mark.parametrize(
    "make_bad",
    [
        lambda prices: pd.DataFrame(),                # empty
        lambda prices: prices.iloc[:10],              # too little history
        _with_nan,                                    # missing value
        lambda prices: prices.assign(T00=-1.0),       # non-positive price
    ],
    ids=["empty", "short", "nan", "nonpositive"],
)
def test_invalid_price_history_is_rejected(make_bad, price_history):
    with pytest.raises(ValueError):
        optimize_portfolio(make_bad(price_history))


def test_ml_confidence_tilts_weights_toward_bullish_stock(price_history):
    two = price_history[["T00", "T01"]].copy()
    weights = optimize_portfolio(
        two, confidence_scores={"T00": 0.95, "T01": 0.05}, risk_tolerance="aggressive", alpha=1.0
    )
    assert weights.get("T00", 0) > weights.get("T01", 0)


def test_missing_confidence_scores_are_neutral(price_history):
    assert optimize_portfolio(price_history, None) == optimize_portfolio(
        price_history, {t: 0.5 for t in price_history.columns}
    )


def test_blended_returns_are_clipped(price_history):
    boom = price_history.copy()
    boom["T00"] = np.linspace(1, 5_000, len(boom))  # absurd historical return
    mu = blend_expected_returns(boom, None)
    assert mu.max() <= allocator.EXPECTED_RETURN_CLIP[1]


def test_falls_back_to_min_volatility_then_equal_weight(price_history, monkeypatch):
    def failing_solver(mu, cov, profile, objective):
        if objective != "min_volatility":
            raise RuntimeError("solver failed")
        return {t: 1 / len(mu) for t in mu.index}

    monkeypatch.setattr(allocator, "_solve", failing_solver)
    assert sum(optimize_portfolio(price_history, risk_tolerance="aggressive").values()) == pytest.approx(1.0, abs=1e-6)

    def always_failing(*args, **kwargs):
        raise RuntimeError("solver failed")

    monkeypatch.setattr(allocator, "_solve", always_failing)
    equal = optimize_portfolio(price_history, risk_tolerance="balanced")
    assert len(equal) == price_history.shape[1]
    assert max(equal.values()) - min(equal.values()) < 1e-4


@pytest.mark.parametrize("budget", BUDGETS)
@pytest.mark.parametrize("profile", PROFILES)
def test_full_allocation_across_budgets_and_profiles(budget, profile, price_history):
    weights = optimize_portfolio(price_history, risk_tolerance=profile)
    prices = {t: float(price_history[t].iloc[-1]) for t in weights}

    result = discretize_allocation(budget, weights, prices)
    summary = summarize_allocation(budget, result)

    assert all(item["shares"] >= 0 for item in result.values())
    assert 0 < summary["invested"] <= budget
    assert summary["cash_left"] < budget * 0.01  # fractional shares leave essentially nothing idle


# --------------------------------------------------------------------------
# performance
# --------------------------------------------------------------------------
def test_trailing_returns_and_portfolio_performance():
    prices = pd.DataFrame({"A": np.linspace(100, 200, 300), "B": np.linspace(100, 100, 300)})
    returns = trailing_returns_pct(prices, days=252)

    assert returns["B"] == pytest.approx(0.0)
    assert returns["A"] > 0
    assert compute_1yr_performance({"A": 0.5, "B": 0.5}, returns) == pytest.approx(returns["A"] / 2)


def test_trailing_returns_use_available_history_when_short():
    prices = pd.DataFrame({"A": [100.0, 110.0, 121.0]})
    assert trailing_returns_pct(prices, days=252)["A"] == pytest.approx(21.0)
