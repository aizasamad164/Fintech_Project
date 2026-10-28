# backend/app/compliance/shariah.py
"""
Optional Shariah-compliance filter for the stock universe.

Shariah screening is a rule about WHICH stocks may be considered, not a
prediction, so the ML models are untouched: we remove non-compliant tickers
from the universe first, then score / allocate the rest exactly as usual.

Data lives in `backend/app/data/shariah_universe.json` (override the path with
the SHARIAH_DATA_PATH env var). It records, per ticker, what each third-party
screener said, plus a derived `status`:

    compliant      passes Musaffa and Zoya does not contradict it  -> allowed
    disputed       the screeners disagree                          -> excluded
    non_compliant  fails                                           -> excluded
    (not listed)   never screened                                  -> excluded

The filter FAILS CLOSED: if the data file is missing or unreadable, nothing is
treated as compliant, so a "Shariah only" request never silently includes
unscreened stocks.

Screening results change when companies report earnings; refresh the JSON
(and its `as_of` date) about once a quarter.
"""
import json
import os
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DATA_PATH = os.path.join(BASE_DIR, "data", "shariah_universe.json")
DATA_PATH_ENV = "SHARIAH_DATA_PATH"
STALE_AFTER_DAYS = 120  # about a quarter plus a grace period

_cache: Dict[str, Any] = {"path": None, "mtime": None, "data": None}


def _data_path() -> str:
    return os.environ.get(DATA_PATH_ENV) or DEFAULT_DATA_PATH


def _load() -> Optional[Dict[str, Any]]:
    path = _data_path()
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
    if not isinstance(data, dict) or not isinstance(data.get("tickers"), dict):
        return None
    _cache.update(path=path, mtime=mtime, data=data)
    return data


def status(ticker: str) -> Optional[str]:
    """'compliant' | 'disputed' | 'non_compliant', or None when unscreened / data missing."""
    data = _load()
    if data is None:
        return None
    entry = data["tickers"].get((ticker or "").upper().strip())
    return entry.get("status") if entry else None


def is_compliant(ticker: str) -> bool:
    return status(ticker) == "compliant"


def filter_sector_map(sector_map: Dict[str, List[str]]) -> Tuple[Dict[str, List[str]], List[str]]:
    """Keep only compliant tickers. Returns (filtered_map, excluded_tickers).
    Sectors left with no tickers are dropped."""
    kept: Dict[str, List[str]] = {}
    excluded: List[str] = []
    for sector, tickers in sector_map.items():
        ok = [t for t in tickers if is_compliant(t)]
        excluded.extend(t for t in tickers if t not in ok)
        if ok:
            kept[sector] = ok
    return kept, excluded


def info(today: Optional[date] = None) -> Dict[str, Any]:
    """Summary for the API / UI: how the filter works, when it was screened, how big it is."""
    data = _load()
    if data is None:
        return {"available": False,
                "message": "Shariah screening data not found (backend/app/data/shariah_universe.json)."}
    tickers = data["tickers"]
    compliant = sorted(t for t, e in tickers.items() if e.get("status") == "compliant")
    by_sector: Dict[str, int] = {}
    for t in compliant:
        s = tickers[t].get("sector", "Unknown")
        by_sector[s] = by_sector.get(s, 0) + 1

    out: Dict[str, Any] = {
        "available": True,
        "as_of": data.get("as_of"),
        "rule": data.get("rule"),
        "sources": data.get("sources", []),
        "disclaimer": data.get("disclaimer"),
        "compliant_count": len(compliant),
        "compliant_by_sector": by_sector,
        "compliant_tickers": compliant,
    }
    try:
        age = ((today or date.today()) - date.fromisoformat(str(data.get("as_of")))).days
        out["age_days"] = age
        if age > STALE_AFTER_DAYS:
            out["warning"] = (f"Screening results are {age} days old; statuses may have changed. "
                              "Refresh app/data/shariah_universe.json.")
    except ValueError:
        pass
    return out
