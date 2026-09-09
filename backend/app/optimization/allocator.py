"""
FR-4.1: Mean-variance optimization using PyPortfolioOpt, combining
ML confidence scores with historical covariance matrices.
"""
from pypfopt import EfficientFrontier, risk_models, expected_returns


def optimize_weights(price_history, confidence_scores: dict) -> dict:
    """
    price_history: DataFrame of historical close prices, columns = tickers.
    confidence_scores: {ticker: P(Bullish)} from app.signals.models.
    Returns: {ticker: weight} summing to 1.0.
    """
    mu = expected_returns.mean_historical_return(price_history)
    # TODO: blend `mu` with confidence_scores to tilt toward ML-favored stocks
    S = risk_models.sample_cov(price_history)

    ef = EfficientFrontier(mu, S)
    ef.max_sharpe()
    return ef.clean_weights()
