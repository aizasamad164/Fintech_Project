"""Turn the trained pipeline's CURRENT per-stock scores into the JSON file the
backend serves (backend/app/signals/global_signals.py reads it).

Why a file instead of live inference: the signals are 5-day-horizon, so a
refresh per training run is plenty, and serving a small JSON keeps torch /
LightGBM / XGBoost out of the backend image and the request path (NFR-1.1:
3 s end to end, NFR-1.2: CPU only).

File shape (schema_version 1):

    {
      "schema_version": 1,
      "generated_at": "2026-10-21T08:00:00+00:00",
      "as_of": "2026-10-20",            # newest price date that was scored
      "horizon_days": 5,
      "k_clusters": 2,
      "n_tickers": 33,
      "risk_levels": {
        "balanced": {
          "target_return_5d": 0.015,    # what "bullish" means at this risk level
          "clusters": {"0": {"model": "Ensemble", "cutoff": 0.11, "val_auc": 0.69,
                              "test_auc_roc": 0.52, "members": ["AAPL", ...]}, ...},
          "signals":  {"AAPL": {"sector": "Technology", "cluster": 0,
                                 "model": "Ensemble", "bullish_probability": 0.098,
                                 "signal": 0, "as_of": "2026-10-20"}, ...}
        }, "conservative": {...}, "aggressive": {...}
      }
    }
"""

import json
import os
import tempfile
from datetime import datetime, timezone

import pandas as pd

from .pipeline import score_individual_stocks

SCHEMA_VERSION = 1
HORIZON_DAYS = 5
DISCLAIMER = "Educational simulation output, not regulated financial advice."


def _cluster_id(label) -> int:
    """'GlobalCluster_0' -> 0"""
    return int(str(label).rsplit("_", 1)[-1])


def build_risk_block(summary: pd.DataFrame, latest_features: pd.DataFrame,
                     cluster_map: pd.DataFrame, cluster_models: dict,
                     cluster_cutoffs: dict, risk_cfg: dict) -> dict:
    """One risk level's worth of output: per-cluster model info + each
    ticker's NEWEST score.

    Each ticker is scored over its whole history and then the last row is
    taken -- the LSTM reads a window of past rows, so scoring a lone row
    would just return its neutral 0.5 placeholder."""
    scored = score_individual_stocks(latest_features, cluster_map, cluster_models, cluster_cutoffs)
    newest = scored.sort_values("Date").groupby("Ticker").tail(1)

    members = {}
    for ticker, row in cluster_map.iterrows():
        members.setdefault(int(row["Cluster"]), []).append(str(ticker))

    clusters = {}
    for _, row in summary.iterrows():
        cid = _cluster_id(row["Cluster"])
        clusters[str(cid)] = {
            "model": str(row["Model Chosen"]),
            "cutoff": round(float(cluster_cutoffs[cid]), 6),
            "val_auc": round(float(row["Val AUC (selection basis)"]), 4),
            "test_auc_roc": round(float(row["AUC-ROC"]), 4),
            "members": sorted(members.get(cid, [])),
        }

    signals = {}
    for _, r in newest.sort_values("Ticker").iterrows():
        cid = int(r["Cluster"])
        signals[str(r["Ticker"])] = {
            "sector": str(r["Sector"]),
            "cluster": cid,
            "model": clusters[str(cid)]["model"],
            "bullish_probability": round(float(r["Bullish_Probability"]), 6),
            "signal": int(r["Signal"]),
            "as_of": pd.Timestamp(r["Date"]).strftime("%Y-%m-%d"),
        }

    return {
        "target_return_5d": float(risk_cfg["target_return"]),
        "clusters": clusters,
        "signals": signals,
    }


def build_payload(blocks_by_risk: dict, k: int, n_tickers: int) -> dict:
    dates = [s["as_of"] for block in blocks_by_risk.values() for s in block["signals"].values()]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "as_of": max(dates) if dates else None,
        "horizon_days": HORIZON_DAYS,
        "k_clusters": int(k),
        "n_tickers": int(n_tickers),
        "disclaimer": DISCLAIMER,
        "risk_levels": blocks_by_risk,
    }


def write_payload(payload: dict, path) -> str:
    """Atomic write (temp file + rename) so the backend never reads a
    half-written file while a retrain is saving."""
    path = os.fspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    return path
