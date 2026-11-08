import json
import os
from datetime import date

import pytest

from app.signals import global_signals as gs


def _payload(as_of="2026-10-20"):
    def block(target):
        return {
            "target_return_5d": target,
            "clusters": {
                "0": {"model": "Ensemble", "cutoff": 0.11, "val_auc": 0.69, "test_auc_roc": 0.52,
                      "members": ["AAPL", "MSFT"]},
                "1": {"model": "LightGBM", "cutoff": 0.25, "val_auc": 0.63, "test_auc_roc": 0.61,
                      "members": ["ENPH"]},
            },
            "signals": {
                "AAPL": {"sector": "Technology", "cluster": 0, "model": "Ensemble",
                         "bullish_probability": 0.14, "signal": 1, "as_of": as_of},
                "MSFT": {"sector": "Technology", "cluster": 0, "model": "Ensemble",
                         "bullish_probability": 0.09, "signal": 0, "as_of": as_of},
                "ENPH": {"sector": "Renewable_Energy", "cluster": 1, "model": "LightGBM",
                         "bullish_probability": 0.27, "signal": 1, "as_of": as_of},
            },
        }

    return {
        "schema_version": 1,
        "generated_at": "2026-10-21T08:00:00+00:00",
        "as_of": as_of,
        "horizon_days": 5,
        "k_clusters": 2,
        "n_tickers": 3,
        "risk_levels": {
            "conservative": block(0.010),
            "balanced": block(0.015),
            "aggressive": block(0.025),
        },
    }


@pytest.fixture
def signals_file(tmp_path, monkeypatch):
    path = tmp_path / "signals.json"
    path.write_text(json.dumps(_payload()))
    monkeypatch.setenv(gs.SIGNALS_PATH_ENV, str(path))
    return path


TODAY = date(2026, 10, 21)


def test_buy_signal_maps_fields(signals_file):
    r = gs.predict_global_signal("AAPL", "balanced", today=TODAY)
    assert r["status"] == "success"
    assert r["signal"] == "BUY"
    assert r["confidence"] == pytest.approx(0.14)
    assert r["bullish_probability"] == pytest.approx(0.14)
    assert r["sector"] == "Technology"
    assert r["model"] == "Ensemble"
    assert r["cluster"] == 0
    assert r["target_return_5d"] == pytest.approx(0.015)
    assert r["risk_level"] == "balanced"


def test_zero_signal_is_hold(signals_file):
    r = gs.predict_global_signal("MSFT", today=TODAY)
    assert r["signal"] == "HOLD"
    assert r["status"] == "success"
    assert r["confidence"] == pytest.approx(0.09)


def test_ticker_and_risk_are_normalised(signals_file):
    r = gs.predict_global_signal("  aapl ", "AGGRESSIVE", today=TODAY)
    assert r["ticker"] == "AAPL"
    assert r["risk_level"] == "aggressive"
    assert r["target_return_5d"] == pytest.approx(0.025)


def test_unknown_ticker_is_a_warning_hold(signals_file):
    r = gs.predict_global_signal("ZZZZ", today=TODAY)
    assert r["status"] == "warning"
    assert r["signal"] == "HOLD"
    assert "not in the global model" in r["message"]


def test_unknown_risk_level_is_an_error(signals_file):
    r = gs.predict_global_signal("AAPL", "yolo", today=TODAY)
    assert r["status"] == "error"
    assert r["signal"] == "HOLD"


def test_missing_file_does_not_raise(tmp_path, monkeypatch):
    monkeypatch.setenv(gs.SIGNALS_PATH_ENV, str(tmp_path / "nope.json"))
    r = gs.predict_global_signal("AAPL")
    assert r["status"] == "warning"
    assert "train_global_clustering" in r["message"]
    assert gs.list_global_signals() == []


def test_corrupt_file_does_not_raise(tmp_path, monkeypatch):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    monkeypatch.setenv(gs.SIGNALS_PATH_ENV, str(bad))
    assert gs.predict_global_signal("AAPL")["status"] == "warning"


def test_stale_signals_warn_but_still_return_the_signal(signals_file):
    r = gs.predict_global_signal("AAPL", today=date(2026, 11, 20))
    assert r["status"] == "warning"
    assert r["signal"] == "BUY"
    assert "days old" in r["message"]


def test_confidence_is_always_a_float(signals_file):
    # portfolio_service sorts on (signal, confidence) -- None would crash it.
    for ticker in ("AAPL", "MSFT", "ZZZZ"):
        assert isinstance(gs.predict_global_signal(ticker, today=TODAY)["confidence"], float)
    assert isinstance(gs.predict_global_signal("AAPL", "yolo")["confidence"], float)


def test_list_is_sorted_strongest_first(signals_file):
    rows = gs.list_global_signals("balanced", today=TODAY)
    assert [r["ticker"] for r in rows] == ["ENPH", "AAPL", "MSFT"]


def test_list_filters(signals_file):
    assert [r["ticker"] for r in gs.list_global_signals(only_buy=True, today=TODAY)] == ["ENPH", "AAPL"]
    assert [r["ticker"] for r in gs.list_global_signals(sector="technology", today=TODAY)] == ["AAPL", "MSFT"]


def test_cache_reloads_when_file_changes(signals_file):
    assert gs.predict_global_signal("MSFT", today=TODAY)["signal"] == "HOLD"

    updated = _payload()
    updated["risk_levels"]["balanced"]["signals"]["MSFT"]["signal"] = 1
    signals_file.write_text(json.dumps(updated))
    stat = signals_file.stat()
    os.utime(signals_file, (stat.st_atime, stat.st_mtime + 5))  # guarantee a new mtime

    assert gs.predict_global_signal("MSFT", today=TODAY)["signal"] == "BUY"


def test_committed_signals_file_matches_schema():
    """If a real export is committed, make sure it still has the shape this
    module (and anything built on it) relies on."""
    if not os.path.exists(gs.DEFAULT_SIGNALS_PATH):
        pytest.skip("no committed global_clustering_signals.json yet")
    with open(gs.DEFAULT_SIGNALS_PATH, encoding="utf-8") as f:
        data = json.load(f)

    assert data["schema_version"] == 1
    assert set(data["risk_levels"]) == set(gs.VALID_RISK_LEVELS)
    for risk, block in data["risk_levels"].items():
        assert 0 < block["target_return_5d"] < 1
        assert block["clusters"], risk
        for ticker, s in block["signals"].items():
            assert 0.0 <= s["bullish_probability"] <= 1.0, (risk, ticker)
            assert s["signal"] in (0, 1), (risk, ticker)
            assert str(s["cluster"]) in block["clusters"], (risk, ticker)
            date.fromisoformat(s["as_of"])
