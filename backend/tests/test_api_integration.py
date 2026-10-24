"""
Offline end-to-end test of the API. Seeds the price cache with synthetic
history so no internet, Groq key or Supabase is needed.

    cd backend
    python -m pytest tests/test_api_integration.py -q
"""
import uuid

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.data import portfolio_store, price_history
from app.ml_config import SECTOR_CONFIGS


def _fake_ohlcv(seed: int, days: int = 500, drift: float = 0.0004, vol: float = 0.018) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    close = 100 * np.exp(np.cumsum(rng.normal(drift, vol, days)))
    high = close * (1 + rng.uniform(0, 0.02, days))
    low = close * (1 - rng.uniform(0, 0.02, days))
    return pd.DataFrame({"Open": close * (1 + rng.normal(0, 0.003, days)), "High": high, "Low": low,
                         "Close": close, "Volume": rng.integers(1_000_000, 5_000_000, days)}, index=idx)


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    tickers = [t for cfg in SECTOR_CONFIGS.values() for t in cfg["tickers"]] + ["SPY", "^VIX"]
    hist = {t: _fake_ohlcv(i, drift=0.0002 + (i % 7) * 0.0002, vol=0.01 + (i % 5) * 0.006)
            for i, t in enumerate(tickers)}
    price_history.seed_cache(hist)
    price_history.seed_cache({t: df.iloc[-5:] for t, df in hist.items()}, period="5d")
    # keep test saves out of the real local store
    portfolio_store.LOCAL_FILE = tmp_path_factory.mktemp("store") / "portfolios.json"
    from app.main import app
    return TestClient(app)


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["models_found"]["Technology"] is True


@pytest.mark.parametrize("risk", ["conservative", "balanced", "aggressive"])
@pytest.mark.parametrize("sector", ["Technology", "Healthcare", "Pharmaceuticals", "Renewable_Energy", "All"])
def test_rebalance(client, sector, risk):
    r = client.post("/api/portfolio/rebalance", json={
        "portfolio_value": 5000, "target_sector": sector, "risk_strategy": risk, "include_explanation": True})
    assert r.status_code == 200, r.text
    body = r.json()
    allocs = body["allocations"]
    assert 3 <= len(allocs) <= 5
    assert abs(sum(a["weight_pct"] for a in allocs) - 100) < 1.0
    assert body["summary"]["allocated_value"] <= 5000.01
    assert len(body["explanation"]) == 3            # fallback bullets without a Groq key
    assert 1 <= body["summary"]["risk_rating"] <= 5
    assert all(len(a["trend"]) >= 2 for a in allocs)
    if sector == "All":
        assert len({a["sector"] for a in allocs}) >= 2   # multi-sector really spreads out


def test_predictions_differ_between_tickers():
    """Regression: the old loader fed all-zero features, so every ticker got the same output."""
    from app.signals.models.model_loader import score_tickers
    preds = score_tickers(SECTOR_CONFIGS["Technology"]["tickers"], "Technology")
    values = {round(p["predicted_return"], 6) for p in preds.values()}
    assert len(values) > 1


def test_save_list_performance_delete(client):
    uid = str(uuid.uuid4())
    port = client.post("/api/portfolio/rebalance", json={"portfolio_value": 2000, "target_sector": "Technology",
                                                         "include_explanation": False}).json()
    positions = [{"ticker": a["ticker"], "sector": a["sector"], "shares_held": a["shares"], "buy_price": a["price"]}
                 for a in port["allocations"]]
    saved = client.post("/api/portfolio/save", json={"user_id": uid, "initial_investment": 2000,
                                                     "target_sector": "Technology", "positions": positions})
    assert saved.status_code == 200, saved.text
    pid = saved.json()["portfolio"]["id"]

    listed = client.get("/api/portfolio/list", params={"user_id": uid}).json()["portfolios"]
    assert [p["id"] for p in listed] == [pid]

    perf = client.get(f"/api/portfolio/{pid}/performance", params={"user_id": uid}).json()
    assert perf["summary"]["positions_count"] == len(positions)
    assert perf["summary"]["stale_prices"] == 0

    # someone else's id can't read it
    other = client.get(f"/api/portfolio/{pid}/performance", params={"user_id": str(uuid.uuid4())})
    assert other.status_code == 404

    assert client.delete(f"/api/portfolio/{pid}", params={"user_id": uid}).status_code == 200


def test_insights(client):
    rows = client.get("/api/insights").json()["rows"]
    assert len(rows) == 5
    assert rows == sorted(rows, key=lambda r: r["bestReturn"], reverse=True)


def test_chat_without_key_is_graceful(client, monkeypatch):
    from app.llm import chat_routes
    monkeypatch.setattr(chat_routes, "groq_available", lambda: False)
    r = client.post("/api/chat/message", json={"session_id": "t", "message": "What is volatility?"})
    assert r.status_code == 200 and r.json()["status"] == "unavailable"
