# backend/app/signals/models/model_loader.py
"""
Loads the sector ensemble models from ml/trained_models/ and scores tickers.

Previous version fed the models an all-zeros feature row, so every ticker in
a sector got the identical prediction. This version computes the real 23
features from recent price history (app.signals.features) and applies the
same scoring rules used in training (ml/ensemble_engin.py):

  Risk_Adj_Score      = predicted 5-day return / normalised ATR
  Bullish_Probability = logistic(1.2 * cross-sectional z-score of that score)
  BUY  if  rank in top 20% of the sector AND predicted return > 0.5%
           AND SPY is above ~its 50-day trend (macro filter)
"""
from __future__ import annotations

import logging
import os
import time
import warnings
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from app.data.price_history import get_histories
from app.ml_config import SECTOR_CONFIGS
from app.signals.features import FEATURE_COLUMNS, build_macro_frame, latest_features

warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
warnings.filterwarnings("ignore", message=".*valid feature names.*")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../../ml/trained_models"))

SECTOR_MODEL_MAP = {
    "Technology": ("technology_ensemble_model.joblib", "technology_scaler.joblib"),
    "Healthcare": ("healthcare_ensemble_model.joblib", "healthcare_scaler.joblib"),
    "Pharmaceuticals": ("pharmaceuticals_ensemble_model.joblib", "pharmaceuticals_scaler.joblib"),
    "Renewable_Energy": ("renewable_energy_ensemble_model.joblib", "renewable_energy_scaler.joblib"),
    "General": ("general_ensemble_model.joblib", "general_scaler.joblib"),
}

NEUTRAL_THRESHOLD = 0.005
TOP_RANK_PCT = 0.20
MACRO_MIN = 0.98

_MODEL_CACHE: Dict[str, Tuple[Any, Any]] = {}
# Predictions only change when new daily prices arrive; reuse them for 10 minutes
_SCORE_TTL = 10 * 60
_SCORE_CACHE: Dict[Tuple[Tuple[str, ...], str], Tuple[float, Dict[str, Dict[str, Any]]]] = {}


def normalise_sector(name: Optional[str]) -> str:
    """'renewable energy' / 'Renewable_Energy' / 'tech' -> canonical key."""
    if not name:
        return "General"
    key = name.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "technology": "Technology", "tech": "Technology",
        "healthcare": "Healthcare", "health_care": "Healthcare",
        "pharmaceuticals": "Pharmaceuticals", "pharma": "Pharmaceuticals",
        "renewable_energy": "Renewable_Energy", "renewable": "Renewable_Energy",
        "renewables": "Renewable_Energy", "general": "General",
    }
    return aliases.get(key, "General")


def sector_of(ticker: str) -> Optional[str]:
    t = ticker.upper().strip()
    for sector, cfg in SECTOR_CONFIGS.items():
        if t in cfg["tickers"]:
            return sector
    return None


def load_sector_pair(sector_name: str) -> Tuple[Any, Any]:
    sector_name = sector_name if sector_name in SECTOR_MODEL_MAP else "General"
    if sector_name in _MODEL_CACHE:
        return _MODEL_CACHE[sector_name]
    model_file, scaler_file = SECTOR_MODEL_MAP[sector_name]
    model_path = os.path.join(MODELS_DIR, model_file)
    scaler_path = os.path.join(MODELS_DIR, scaler_file)
    model = joblib.load(model_path) if os.path.exists(model_path) else None
    scaler = joblib.load(scaler_path) if os.path.exists(scaler_path) else None
    _MODEL_CACHE[sector_name] = (model, scaler)
    return model, scaler


def _resolve_model_sector(ticker: str, sector: Optional[str]) -> str:
    """Use the requested sector's model; if that model doesn't exist (e.g. General),
    fall back to the model of the sector the ticker belongs to."""
    s = normalise_sector(sector)
    model, scaler = load_sector_pair(s)
    if model is not None and scaler is not None:
        return s
    return sector_of(ticker) or s


def score_tickers(tickers: List[str], sector: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Scores several tickers at once with cross-sectional ranking (as in training).
    Returns {ticker: prediction dict}. Missing data -> HOLD with status 'warning'.
    """
    tickers = [t.upper().strip() for t in tickers if t]
    cache_key = (tuple(sorted(tickers)), normalise_sector(sector))
    hit = _SCORE_CACHE.get(cache_key)
    if hit and time.time() - hit[0] < _SCORE_TTL:
        return {k: dict(v) for k, v in hit[1].items()}
    histories = get_histories(tickers + ["SPY", "^VIX"])
    macro = build_macro_frame(histories.get("SPY"), histories.get("^VIX"))

    rows: Dict[str, Dict[str, Any]] = {}
    results: Dict[str, Dict[str, Any]] = {}

    for t in tickers:
        model_sector = _resolve_model_sector(t, sector)
        model, scaler = load_sector_pair(model_sector)
        base = {"ticker": t, "sector": model_sector}
        if model is None or scaler is None:
            results[t] = {**base, "signal": "HOLD", "confidence": 0.5, "predicted_return": 0.0,
                          "predicted_5d_return": "0.0%", "status": "warning",
                          "message": f"No trained model for '{model_sector}' in ml/trained_models/."}
            continue
        feats = latest_features(histories.get(t), macro)
        if feats is None:
            results[t] = {**base, "signal": "HOLD", "confidence": 0.5, "predicted_return": 0.0,
                          "predicted_5d_return": "0.0%", "status": "warning",
                          "message": "Not enough recent price history to score this ticker."}
            continue
        try:
            X = pd.DataFrame([[feats[c] for c in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)
            pred = float(model.predict(scaler.transform(X))[0])
            rows[t] = {**base, "pred": pred, "norm_atr": feats["Norm_ATR"], "spy_sma50": feats["SPY_SMA50"]}
        except Exception as exc:  # noqa: BLE001
            results[t] = {**base, "signal": "HOLD", "confidence": 0.5, "predicted_return": 0.0,
                          "predicted_5d_return": "0.0%", "status": "error", "message": str(exc)}

    if rows:
        df = pd.DataFrame.from_dict(rows, orient="index")
        df["risk_adj"] = df["pred"] / (df["norm_atr"] + 1e-8)
        std = df["risk_adj"].std() if len(df) > 1 else 0.0
        z = (df["risk_adj"] - df["risk_adj"].mean()) / (std + 1e-8) if len(df) > 1 else df["pred"] * 100
        df["prob"] = 1 / (1 + np.exp(-1.2 * z))
        df["rank"] = df["risk_adj"].rank(ascending=False, pct=True) if len(df) > 1 else 0.0

        for t, r in df.iterrows():
            macro_ok = r["spy_sma50"] >= MACRO_MIN
            if r["pred"] > NEUTRAL_THRESHOLD and r["rank"] <= TOP_RANK_PCT and macro_ok:
                signal = "BUY"
            elif r["pred"] < -NEUTRAL_THRESHOLD:
                signal = "SELL"
            else:
                signal = "HOLD"
            results[t] = {
                "ticker": t,
                "sector": r["sector"],
                "signal": signal,
                "confidence": round(float(r["prob"] if signal != "SELL" else 1 - r["prob"]), 2),
                "bullish_probability": round(float(r["prob"]), 3),
                "predicted_return": round(float(r["pred"]), 5),
                "predicted_5d_return": f"{round(float(r['pred']) * 100, 2)}%",
                "risk_adjusted_score": round(float(r["risk_adj"]), 4),
                "macro_filter_passed": bool(macro_ok),
                "status": "success",
            }
    if rows:  # only cache when we actually had data
        _SCORE_CACHE[cache_key] = (time.time(), results)
    return results


def predict_ticker_signal(ticker: str, sector: str = "General") -> Dict[str, Any]:
    """
    Single-ticker prediction used by the chat agent. The ticker is ranked against
    its own sector's universe so 'top 20%' means the same thing as in training.
    """
    t = ticker.upper().strip()
    model_sector = _resolve_model_sector(t, sector)
    peers = SECTOR_CONFIGS.get(model_sector, {}).get("tickers", [])
    universe = list(dict.fromkeys([t] + list(peers)))
    return score_tickers(universe, model_sector)[t]
