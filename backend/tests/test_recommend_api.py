"""
End-to-end tests of POST /api/v1/recommend with the database and market feed
replaced by an in-memory fake, so they run offline (and in CI).
"""
import pytest
from fastapi.testclient import TestClient

from app.data.price_history import PriceData
from app.main import app
from app.optimization import recommender
from tests.conftest import make_price_history

SECTORS = ["technology", "healthcare", "renewable_energy"]
BUDGETS = [100, 500, 1_000, 5_000, 10_000, 50_000]


@pytest.fixture
def client(monkeypatch):
    prices = make_price_history(n_tickers=12)
    candidates = [
        {"ticker": ticker, "name": f"{ticker} Inc.", "sector": SECTORS[i % 3]}
        for i, ticker in enumerate(prices.columns)
    ]

    async def fake_candidates(sectors):
        return [c for c in candidates if c["sector"] in sectors]

    async def fake_history(tickers, years=5):
        return PriceData(prices=prices[[t for t in tickers if t in prices.columns]], skipped={})

    monkeypatch.setattr(recommender, "get_candidates", fake_candidates)
    monkeypatch.setattr(recommender, "load_price_history", fake_history)
    with TestClient(app) as test_client:
        yield test_client


def _post(client, **overrides):
    body = {"budget": 1000, "risk_profile": "balanced", "sectors": ["technology"], **overrides}
    return client.post("/api/v1/recommend", json=body)


def test_returns_complete_allocation_payload(client):
    response = _post(client)
    assert response.status_code == 200
    data = response.json()

    assert data["risk_profile"] == "balanced"
    assert data["sectors"] == ["technology"]
    assert data["allocations"], "expected at least one position"
    assert sum(a["weight"] for a in data["allocations"]) == pytest.approx(1.0, abs=1e-4)
    assert {"ticker", "name", "sector", "price", "weight", "amount", "shares"} <= set(data["allocations"][0])
    assert all(a["sector"] == "technology" for a in data["allocations"])
    assert data["invested_amount"] + data["cash_left"] == pytest.approx(1000, abs=0.01)
    assert "educational simulation" in data["disclaimer"]
    for key in ("one_year_performance_pct", "projected_return", "price_data_as_of", "generated_in_seconds"):
        assert key in data


@pytest.mark.parametrize("budget", BUDGETS)
@pytest.mark.parametrize("risk", ["conservative", "balanced", "aggressive"])
def test_budget_and_risk_sweep(client, budget, risk):
    data = _post(client, budget=budget, risk_profile=risk, sectors=[]).json()

    assert all(a["shares"] >= 0 and a["amount"] >= 0 for a in data["allocations"])
    assert data["invested_amount"] <= budget
    assert data["cash_left"] >= 0


def test_combined_and_empty_sector_selection_use_every_sector(client):
    for sectors in ([], ["combined"]):
        data = _post(client, sectors=sectors).json()
        assert data["sectors"] == SECTORS


def test_whole_share_mode_returns_integers(client):
    data = _post(client, budget=5000, fractional_shares=False).json()
    assert all(float(a["shares"]).is_integer() for a in data["allocations"])


def test_frontend_route_and_risk_strategy_alias_still_work(client):
    response = client.post(
        "/api/portfolio/generate",
        json={"budget": 1000, "risk_strategy": "aggressive", "sectors": ["healthcare"]},
    )
    assert response.status_code == 200
    assert response.json()["risk_profile"] == "aggressive"


@pytest.mark.parametrize(
    "overrides",
    [
        {"budget": 0},
        {"budget": -100},
        {"budget": 0.5},
        {"risk_profile": "yolo"},
        {"sectors": ["crypto"]},
    ],
)
def test_invalid_requests_are_rejected_with_422(client, overrides):
    assert _post(client, **overrides).status_code == 422


def test_missing_stocks_returns_503(client, monkeypatch):
    async def no_candidates(sectors):
        return []

    monkeypatch.setattr(recommender, "get_candidates", no_candidates)
    response = _post(client)
    assert response.status_code == 503
    assert "Seed" in response.json()["detail"]


def test_no_price_history_returns_503(client, monkeypatch):
    import pandas as pd

    async def empty_history(tickers, years=5):
        return PriceData(prices=pd.DataFrame(), skipped={t: "no market data available" for t in tickers})

    monkeypatch.setattr(recommender, "load_price_history", empty_history)
    assert _post(client).status_code == 503


def test_health_endpoint(client):
    assert client.get("/health").json() == {"status": "ok"}
