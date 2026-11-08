# backend/app/signals/global_signals.py
"""
Serves the global (cross-sector) clustering model's precomputed signals.

The model itself (LightGBM / RandomForest / XGBoost / LSTM / ensemble per
cluster) is trained OFFLINE by `ml/train_global_clustering.py`, which writes
one small JSON file. This module only reads that file, so the backend needs no
torch / lightgbm at request time (NFR-1.1: 3 s end to end, NFR-1.2: CPU only).

It returns the same shape as `model_loader.predict_ticker_signal`
({"signal": "BUY"|"HOLD", "confidence": float, "status": ...}), so call sites
can switch over with a one-line change.

Differences from model_loader worth knowing:
  * `confidence` is the model's CALIBRATED PROBABILITY that the stock gains at
    least `target_return_5d` within 5 trading days (that target depends on the
    risk level). It is usually well below 0.5 -- the base rate of hitting the
    target is low -- so it is NOT on the same scale as model_loader's heuristic
    0.55-0.95 confidence. Rank within one model's output; don't mix the two.
  * The model has no "sell" notion: a ticker is either BUY or HOLD.
  * Results are per risk level ("conservative" | "balanced" | "aggressive").
  * It only knows the tickers it was trained on (the screened universe).
"""
import json
import os
from datetime import date, datetime
from typing import Any, Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SIGNALS_PATH = os.path.join(BASE_DIR, "models", "global_clustering_signals.json")
SIGNALS_PATH_ENV = "GLOBAL_SIGNALS_PATH"  # optional override (e.g. a mounted volume in production)

VALID_RISK_LEVELS = ("conservative", "balanced", "aggressive")
STALE_AFTER_DAYS = 7  # warn when the newest scored price date is older than this

_cache: Dict[str, Any] = {"path": None, "mtime": None, "data": None}


def _signals_path() -> str:
    return os.environ.get(SIGNALS_PATH_ENV) or DEFAULT_SIGNALS_PATH


def _load_signals() -> Optional[Dict[str, Any]]:
    """Read the JSON, cached until the file changes on disk (so a retrain is
    picked up without restarting the server). None if missing/unreadable."""
    path = _signals_path()
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return None

    if _cache["path"] == path and _cache["mtime"] == mtime and _cache["data"] is not None:
        return _cache["data"]

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or "risk_levels" not in data:
        return None

    _cache.update(path=path, mtime=mtime, data=data)
    return data


def _age_days(as_of: Optional[str], today: Optional[date]) -> Optional[int]:
    if not as_of:
        return None
    try:
        return ((today or datetime.now().date()) - date.fromisoformat(as_of)).days
    except ValueError:
        return None


def _result(ticker: str, risk_level: str, status: str, message: Optional[str] = None,
            **fields: Any) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "ticker": ticker,
        "sector": None,
        "signal": "HOLD",
        "confidence": 0.0,  # always a float: callers sort on it
        "risk_level": risk_level,
        "status": status,
    }
    out.update(fields)
    if message:
        out["message"] = message
    return out


def _shape(ticker: str, risk_level: str, entry: Dict[str, Any], block: Dict[str, Any],
           data: Dict[str, Any], today: Optional[date]) -> Dict[str, Any]:
    probability = float(entry["bullish_probability"])
    result = _result(
        ticker, risk_level, "success",
        sector=entry.get("sector"),
        signal="BUY" if int(entry["signal"]) == 1 else "HOLD",
        confidence=round(probability, 4),
        bullish_probability=round(probability, 4),
        model=entry.get("model"),
        cluster=entry.get("cluster"),
        as_of=entry.get("as_of"),
        target_return_5d=block.get("target_return_5d"),
        horizon_days=data.get("horizon_days", 5),
    )
    age = _age_days(entry.get("as_of") or data.get("as_of"), today)
    if age is not None and age > STALE_AFTER_DAYS:
        result["status"] = "warning"
        result["message"] = (
            f"Signals are {age} days old (as of {entry.get('as_of')}); "
            "retrain with ml/train_global_clustering.py to refresh."
        )
    return result


def predict_global_signal(ticker: str, risk_level: str = "balanced",
                          today: Optional[date] = None) -> Dict[str, Any]:
    """Current signal for one ticker from the global clustering model."""
    ticker_clean = (ticker or "").upper().strip()
    risk = (risk_level or "balanced").lower().strip()

    data = _load_signals()
    if data is None:
        return _result(
            ticker_clean, risk, "warning",
            "Global clustering signals not found. Generate them with "
            "`python ml/train_global_clustering.py`.",
        )

    block = data["risk_levels"].get(risk)
    if block is None:
        return _result(
            ticker_clean, risk, "error",
            f"Unknown risk level '{risk_level}'. Use one of: {', '.join(VALID_RISK_LEVELS)}.",
        )

    entry = block.get("signals", {}).get(ticker_clean)
    if entry is None:
        return _result(
            ticker_clean, risk, "warning",
            f"'{ticker_clean}' is not in the global model's universe "
            f"({data.get('n_tickers', '?')} screened tickers).",
        )

    return _shape(ticker_clean, risk, entry, block, data, today)


def list_global_signals(risk_level: str = "balanced", sector: Optional[str] = None,
                        only_buy: bool = False, today: Optional[date] = None) -> List[Dict[str, Any]]:
    """Every covered ticker's current signal, strongest first (optionally one
    sector and/or BUY only). Empty list if the signals file is unavailable or
    the risk level is unknown -- use predict_global_signal for the reason."""
    risk = (risk_level or "balanced").lower().strip()
    data = _load_signals()
    if data is None or risk not in data["risk_levels"]:
        return []

    block = data["risk_levels"][risk]
    sector_filter = sector.strip().lower() if sector else None
    out = []
    for ticker, entry in block.get("signals", {}).items():
        if sector_filter and str(entry.get("sector", "")).lower() != sector_filter:
            continue
        item = _shape(ticker, risk, entry, block, data, today)
        if only_buy and item["signal"] != "BUY":
            continue
        out.append(item)

    out.sort(key=lambda r: r["confidence"], reverse=True)
    return out
