"""
Shared test setup. Fake credentials are set BEFORE any `app` module is
imported, so tests never read backend/.env and can never touch a real
Supabase project. CI has no .env at all, so this is also what lets
`app.main` import there.
"""
import os

os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["SUPABASE_URL"] = "http://localhost:54321"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-service-role-key"
os.environ["SUPABASE_ANON_KEY"] = "test-anon-key"
os.environ["GROQ_API_KEY"] = "test-groq-key"

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402


def make_price_history(n_tickers: int = 12, days: int = 756, seed: int = 0) -> pd.DataFrame:
    """Synthetic daily closes with different drifts, volatilities and price levels."""
    rng = np.random.default_rng(seed)
    drifts = rng.uniform(0.02, 0.30, n_tickers) / 252
    vols = rng.uniform(0.18, 0.55, n_tickers) / np.sqrt(252)
    market = rng.normal(0, 1, (days, 1))  # shared factor so the stocks are correlated
    returns = drifts + 0.5 * vols * market + 0.85 * vols * rng.normal(0, 1, (days, n_tickers))
    start_prices = rng.choice([12, 45, 130, 310, 780], n_tickers)
    prices = start_prices * np.exp(np.cumsum(returns, axis=0))
    return pd.DataFrame(
        prices,
        columns=[f"T{i:02d}" for i in range(n_tickers)],
        index=pd.bdate_range(end="2026-09-18", periods=days),
    )


@pytest.fixture
def price_history() -> pd.DataFrame:
    return make_price_history()
