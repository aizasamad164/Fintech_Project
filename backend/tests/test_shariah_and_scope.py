"""Tests for the optional Shariah filter and the sector/global model switch."""
import asyncio
import json
import os
from datetime import date

import numpy as np
import pandas as pd
import pytest

# app.llm builds a Groq client at import time; a dummy key keeps these tests runnable
# in CI / without backend/.env (no network call is made).
os.environ.setdefault("GROQ_API_KEY", "test-key")

from app.compliance import shariah  # noqa: E402
from app.llm import tools  # noqa: E402
from app.optimization import portfolio_service as ps  # noqa: E402
from app.signals import global_signals as gs  # noqa: E402
from app.signals import signal_router as sr  # noqa: E402


# --------------------------------------------------------------------------- Shariah data
def test_shipped_data_is_consistent_with_its_rule():
    data = shariah._load()
    assert data is not None and data["tickers"]
    for ticker, e in data["tickers"].items():
        m, z = e["musaffa"], e["zoya"]
        if m == "halal" and z in (None, "compliant"):
            expected = "compliant"
        elif m == "not_halal" and z in (None, "non_compliant"):
            expected = "non_compliant"
        else:
            expected = "disputed"
        assert e["status"] == expected, ticker


def test_known_statuses():
    assert shariah.is_compliant("AAPL") and shariah.is_compliant("FSLR")
    assert shariah.status("MSFT") == "non_compliant" or shariah.status("MSFT") == "disputed"
    assert not shariah.is_compliant("MSFT")      # Musaffa fails it
    assert not shariah.is_compliant("ORCL")      # screeners disagree -> excluded
    assert not shariah.is_compliant("UNH")
    assert shariah.status("ORCL") == "disputed"
    assert not shariah.is_compliant("NOTASTOCK")  # never screened -> excluded
    assert shariah.is_compliant(" aapl ")         # normalised


def test_every_repo_ticker_has_been_screened():
    from app.ml_config import SECTOR_CONFIGS

    listed = set(shariah._load()["tickers"])
    missing = [t for cfg in SECTOR_CONFIGS.values() for t in cfg["tickers"] if t not in listed]
    assert missing == [], f"add these to shariah_universe.json: {missing}"


def test_filter_sector_map_drops_noncompliant_and_empty_sectors():
    kept, excluded = shariah.filter_sector_map({"Technology": ["AAPL", "MSFT", "ORCL"], "Bad": ["NEE", "RUN"]})
    assert kept == {"Technology": ["AAPL"]}
    assert set(excluded) == {"MSFT", "ORCL", "NEE", "RUN"}


def test_info_counts():
    info = shariah.info()
    assert info["available"] and info["compliant_count"] == 26
    assert info["compliant_by_sector"]["Renewable_Energy"] == 3
    assert "not a fatwa" in info["disclaimer"].lower()


def test_fails_closed_when_data_missing(tmp_path, monkeypatch):
    monkeypatch.setenv(shariah.DATA_PATH_ENV, str(tmp_path / "nope.json"))
    assert shariah.is_compliant("AAPL") is False
    kept, excluded = shariah.filter_sector_map({"Technology": ["AAPL"]})
    assert kept == {} and excluded == ["AAPL"]
    assert shariah.info()["available"] is False


def test_stale_data_warns(tmp_path, monkeypatch):
    path = tmp_path / "s.json"
    path.write_text(json.dumps({"as_of": "2020-01-01", "tickers": {"AAPL": {"status": "compliant"}}}))
    monkeypatch.setenv(shariah.DATA_PATH_ENV, str(path))
    assert "days old" in shariah.info(today=date(2026, 10, 28))["warning"]


# --------------------------------------------------------------------------- router
def test_scope_normalisation():
    assert sr.normalize_scope(None) == "sector"
    assert sr.normalize_scope("Global") == "global"
    assert sr.normalize_scope("mars") is None


def test_router_bad_scope_is_error():
    assert sr.get_signal("AAPL", scope="mars")["status"] == "error"


# --------------------------------------------------------------------------- engine
SECTOR_MAP = {
    "Technology": ["AAPL", "MSFT", "ORCL", "NVDA"],
    "Healthcare": ["UNH", "JNJ", "ABT"],
}
ALL = [t for ts in SECTOR_MAP.values() for t in ts]


def _history(seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(end="2026-10-27", periods=400)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.012, len(idx))))
    return pd.DataFrame({"Close": close}, index=idx)


@pytest.fixture
def engine(tmp_path, monkeypatch):
    monkeypatch.setattr(ps, "get_histories", lambda tickers: {t: _history(i) for i, t in enumerate(tickers)})

    scored = []

    def fake_score(tickers, sector):
        scored.extend(tickers)
        return {t: {"signal": "BUY", "confidence": 0.8, "predicted_return": 0.01 + 0.001 * i,
                    "risk_adjusted_score": 0.5 + 0.01 * i, "predicted_5d_return": "1.0%"}
                for i, t in enumerate(tickers)}

    monkeypatch.setattr(ps, "score_tickers", fake_score)

    as_of = date.today().isoformat()

    def block():
        return {"target_return_5d": 0.015, "clusters": {},
                "signals": {t: {"sector": "x", "cluster": 0, "model": "XGBoost",
                                "bullish_probability": 0.4 - 0.05 * i, "signal": 1, "as_of": as_of}
                            for i, t in enumerate(["AAPL", "ORCL", "ABT", "JNJ", "UNH"])}}

    path = tmp_path / "g.json"
    path.write_text(json.dumps({"schema_version": 1, "as_of": as_of, "horizon_days": 5, "n_tickers": 5,
                                "risk_levels": {k: block() for k in gs.VALID_RISK_LEVELS}}))
    monkeypatch.setenv(gs.SIGNALS_PATH_ENV, str(path))
    return scored


def _run(**kw):
    return ps.rebalance_sync(portfolio_value=5000, sector_map=SECTOR_MAP, **kw)


def test_default_behaviour_unchanged(engine):
    res = _run()
    assert res["status"] == "success"
    assert res["model_scope"] == "sector" and res["shariah_only"] is False
    assert set(engine) == set(ALL)                 # every ticker scored with the sector model
    assert all(a["ml_model"] == "sector" for a in res["allocations"])


def test_shariah_only_removes_noncompliant_before_scoring(engine):
    res = _run(shariah_only=True)
    assert res["status"] == "success" and res["shariah_only"] is True
    assert not ({"MSFT", "ORCL", "UNH"} & set(engine))           # never even scored
    held = {a["ticker"] for a in res["allocations"]}
    assert held <= {"AAPL", "NVDA", "JNJ", "ABT"}
    assert set(res["shariah"]["excluded"]) == {"MSFT", "ORCL", "UNH"}
    assert "fatwa" in res["shariah"]["disclaimer"].lower()


def test_shariah_with_nothing_left_is_a_warning(engine):
    res = ps.rebalance_sync(portfolio_value=5000, sector_map={"X": ["MSFT", "UNH"]}, shariah_only=True)
    assert res["status"] == "warning" and res["allocations"] == []


def test_shariah_fails_closed_without_data(engine, tmp_path, monkeypatch):
    monkeypatch.setenv(shariah.DATA_PATH_ENV, str(tmp_path / "missing.json"))
    res = _run(shariah_only=True)
    assert res["status"] == "warning" and res["allocations"] == []


def test_global_scope_uses_global_model_and_skips_uncovered(engine):
    res = _run(model_scope="global")
    assert res["status"] == "success" and res["model_scope"] == "global"
    assert engine == []                                           # sector models never called
    held = {a["ticker"] for a in res["allocations"]}
    assert held <= {"AAPL", "ORCL", "ABT", "JNJ", "UNH"}          # only tickers the global file covers
    assert all(a["ml_model"] == "global" for a in res["allocations"])
    assert any("Not covered by the global model" in n for n in res["notes"])


def test_global_plus_shariah_combine(engine):
    res = _run(model_scope="global", shariah_only=True)
    held = {a["ticker"] for a in res["allocations"]}
    assert held <= {"AAPL", "ABT", "JNJ"}                         # global-covered AND compliant


def test_global_without_signals_file_warns(engine, tmp_path, monkeypatch):
    monkeypatch.setenv(gs.SIGNALS_PATH_ENV, str(tmp_path / "missing.json"))
    res = _run(model_scope="global")
    assert res["status"] == "warning"


def test_bad_scope_is_a_warning_not_a_crash(engine):
    assert _run(model_scope="mars")["status"] == "warning"


# --------------------------------------------------------------------------- LLM tools
def test_tool_schemas_expose_new_options_as_optional():
    by_name = {t["function"]["name"]: t["function"] for t in tools.AGENT_TOOLS}
    opt = by_name["optimize_portfolio"]["parameters"]
    assert {"model_scope", "shariah_only"} <= set(opt["properties"])
    assert not ({"model_scope", "shariah_only"} & set(opt["required"]))
    pred = by_name["get_ml_prediction"]["parameters"]
    assert {"model_scope", "risk_strategy"} <= set(pred["properties"])


def test_optimize_tool_passes_options_through(monkeypatch):
    seen = {}

    async def fake(**kw):
        seen.update(kw)
        return {"status": "success", "allocations": []}

    monkeypatch.setattr(tools, "run_portfolio_rebalancing", fake)
    asyncio.run(tools.execute_tool_call(
        "optimize_portfolio", {"portfolio_value": 500, "shariah_only": True, "model_scope": "global"}))
    assert seen["shariah_only"] is True and seen["model_scope"] == "global"
    asyncio.run(tools.execute_tool_call("optimize_portfolio", {"portfolio_value": 500}))
    assert seen["shariah_only"] is False and seen["model_scope"] == "sector"


def test_ml_prediction_tool_includes_shariah_status(monkeypatch):
    monkeypatch.setattr(sr, "_sector_signal", lambda t, s: {"ticker": t, "signal": "BUY", "confidence": 0.9, "status": "success"})
    out = asyncio.run(tools.execute_tool_call("get_ml_prediction", {"ticker": "ORCL"}))
    assert out["shariah_status"] == "disputed" and out["model_scope"] == "sector"
    out = asyncio.run(tools.execute_tool_call("get_ml_prediction", {"ticker": "AAPL"}))
    assert out["shariah_status"] == "compliant"
