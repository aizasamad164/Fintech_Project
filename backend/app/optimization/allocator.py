"""
FR-4.1: Mean-variance optimization using PyPortfolioOpt, combining
ML confidence scores with historical covariance matrices.

Risk profiles (FR-1.3) differ in BOTH the objective and how concentrated the
portfolio may be, so Conservative / Balanced / Aggressive give visibly
different results:

  conservative — minimise volatility, no stock above 25 %
  balanced     — maximise return minus a moderate risk penalty, cap 35 %
  aggressive   — chase return with a light risk penalty, cap 50 %

If the chosen objective cannot be solved (e.g. no asset has a usable expected
return) the optimizer degrades gracefully: minimum volatility, then equal
weights. It never raises for numerical reasons, only for invalid input.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from pypfopt import EfficientFrontier, expected_returns, risk_models

logger = logging.getLogger(__name__)

RISK_PROFILES: dict[str, dict] = {
    "conservative": {"objective": "min_volatility", "max_weight": 0.25},
    "balanced": {"objective": "utility", "risk_aversion": 4.0, "max_weight": 0.35},
    "aggressive": {"objective": "utility", "risk_aversion": 0.5, "max_weight": 0.50},
}

# Older names used before the API settled on conservative/balanced/aggressive.
RISK_ALIASES = {"low": "conservative", "moderate": "balanced", "high": "aggressive"}

MIN_HISTORY_ROWS = 60           # need at least ~3 months of prices for a covariance estimate
MIN_POSITION_WEIGHT = 0.02      # weights below 2 % are dust and are dropped
ML_RETURN_SPREAD = 0.20         # confidence 0 -> -20 %/yr, 1 -> +20 %/yr
EXPECTED_RETURN_CLIP = (-0.50, 1.00)  # keep a 15-year moonshot from dominating the optimizer


def normalize_risk_profile(risk: str) -> str:
    key = str(risk).strip().lower()
    key = RISK_ALIASES.get(key, key)
    if key not in RISK_PROFILES:
        valid = ", ".join(RISK_PROFILES)
        raise ValueError(f"Unknown risk profile '{risk}'. Use one of: {valid}.")
    return key


def blend_expected_returns(
    price_history: pd.DataFrame,
    confidence_scores: dict[str, float] | None,
    alpha: float = 0.5,
) -> pd.Series:
    """
    Blends historical mean returns with ML confidence scores.

    :param price_history: DataFrame where columns are ticker symbols and rows are daily prices.
    :param confidence_scores: Dict mapping ticker symbol to P(Bullish) in [0.0, 1.0].
        Missing tickers (or None) are treated as neutral (0.5), so the ML model
        is optional.
    :param alpha: Weight given to ML predictions versus historical returns (default: 0.5).
    :return: Series of blended expected annual returns for each asset.
    """
    confidence_scores = confidence_scores or {}
    mu_historical = expected_returns.mean_historical_return(price_history)

    # 0.5 -> 0 adjustment, 1.0 -> +0.20, 0.0 -> -0.20
    signal = pd.Series(
        {
            ticker: (float(np.clip(confidence_scores.get(ticker, 0.5), 0.0, 1.0)) - 0.5) * 2 * ML_RETURN_SPREAD
            for ticker in price_history.columns
        }
    )

    blended = (1 - alpha) * mu_historical + alpha * signal
    return blended.clip(*EXPECTED_RETURN_CLIP)


def _covariance(price_history: pd.DataFrame) -> pd.DataFrame:
    """Ledoit-Wolf shrinkage is far more stable than the raw sample covariance
    when there are many assets and comparatively few observations."""
    try:
        return risk_models.CovarianceShrinkage(price_history).ledoit_wolf()
    except Exception:  # noqa: BLE001
        logger.warning("Ledoit-Wolf covariance failed; using sample covariance", exc_info=True)
        return risk_models.sample_cov(price_history)


def _solve(mu: pd.Series, cov: pd.DataFrame, profile: dict, objective: str) -> dict[str, float]:
    n = len(mu)
    # The cap must leave room for weights to sum to 1 (n * cap >= 1).
    cap = min(1.0, max(profile["max_weight"], 1.0 / n * 1.0001))
    ef = EfficientFrontier(mu, cov, weight_bounds=(0, cap))

    if objective == "min_volatility":
        ef.min_volatility()
    else:
        ef.max_quadratic_utility(risk_aversion=profile.get("risk_aversion", 4.0))
    return dict(ef.clean_weights(cutoff=MIN_POSITION_WEIGHT))


def _finalize(weights: dict[str, float]) -> dict[str, float]:
    """Drops zero weights, renormalises to exactly 1.0, sorts largest first."""
    positive = {t: float(w) for t, w in weights.items() if w and w > 0}
    total = sum(positive.values())
    if total <= 0:
        raise ValueError("Optimizer produced no positive weights.")

    normalized = {t: round(w / total, 6) for t, w in positive.items()}
    largest = max(normalized, key=normalized.get)
    normalized[largest] = round(normalized[largest] + (1.0 - sum(normalized.values())), 6)
    return dict(sorted(normalized.items(), key=lambda kv: kv[1], reverse=True))


def optimize_portfolio(
    price_history: pd.DataFrame,
    confidence_scores: dict[str, float] | None = None,
    risk_tolerance: str = "balanced",
    alpha: float = 0.5,
) -> dict[str, float]:
    """
    Computes portfolio weights using PyPortfolioOpt with ML-blended returns.

    :param price_history: DataFrame of historical prices (columns = tickers), no gaps.
    :param confidence_scores: Optional {ticker: P(bullish)}; omitted = neutral.
    :param risk_tolerance: 'conservative' | 'balanced' | 'aggressive'
        (legacy 'low' | 'moderate' | 'high' are accepted).
    :param alpha: Weight for blending ML confidence score with historical mean return.
    :return: {ticker: weight}; long-only, weights sum to 1.0, largest first.
    """
    if price_history is None or price_history.empty:
        raise ValueError("Price history DataFrame cannot be empty.")
    if len(price_history) < MIN_HISTORY_ROWS:
        raise ValueError(f"Need at least {MIN_HISTORY_ROWS} days of prices, got {len(price_history)}.")
    if price_history.isna().any().any():
        raise ValueError("Price history contains missing values; align and clean it first.")
    if (price_history <= 0).any().any():
        raise ValueError("Price history contains non-positive prices.")

    profile_name = normalize_risk_profile(risk_tolerance)
    profile = RISK_PROFILES[profile_name]
    tickers = list(price_history.columns)

    if len(tickers) == 1:
        return {tickers[0]: 1.0}

    try:
        mu = blend_expected_returns(price_history, confidence_scores, alpha=alpha)
        cov = _covariance(price_history)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not estimate returns/covariance (%s); using equal weights", exc)
        return _finalize({t: 1.0 / len(tickers) for t in tickers})

    for objective in dict.fromkeys([profile["objective"], "min_volatility"]):
        try:
            return _finalize(_solve(mu, cov, profile, objective))
        except Exception as exc:  # noqa: BLE001 — solver/feasibility errors -> next fallback
            logger.warning("%s objective failed for '%s' profile: %s", objective, profile_name, exc)

    logger.warning("All optimizers failed for '%s'; using equal weights", profile_name)
    return _finalize({t: 1.0 / len(tickers) for t in tickers})
