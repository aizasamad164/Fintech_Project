# backend/app/signals/signal_router.py
"""
One entry point for "give me this ticker's ML signal", for either model family:

  scope="sector"  the existing per-sector models (model_loader.predict_ticker_signal)
  scope="global"  the cross-sector clustering model (global_signals.predict_global_signal)

The allocation engine, the LLM tools and the API all go through `get_signal`,
so adding a scope later means touching one file. "sector" is the default
everywhere, so nothing changes for callers that don't ask for "global".
"""
from typing import Any, Dict, Optional

from app.signals.global_signals import VALID_RISK_LEVELS, predict_global_signal

VALID_SCOPES = ("sector", "global")
DEFAULT_SCOPE = "sector"
DEFAULT_RISK_LEVEL = "balanced"

# Spellings people (and LLMs) are likely to use.
_SCOPE_ALIASES = {
    "sector": "sector",
    "sector_specific": "sector",
    "local": "sector",
    "global": "global",
    "all": "global",
    "cross_sector": "global",
}


def normalize_scope(scope: Optional[str]) -> Optional[str]:
    """'sector' | 'global', or None when the value isn't recognised.
    An empty/missing value means the default ('sector')."""
    if scope is None or not str(scope).strip():
        return DEFAULT_SCOPE
    return _SCOPE_ALIASES.get(str(scope).strip().lower().replace("-", "_").replace(" ", "_"))


def normalize_risk_level(risk_level: Optional[str]) -> Optional[str]:
    """One of VALID_RISK_LEVELS, or None when the value isn't recognised."""
    if risk_level is None or not str(risk_level).strip():
        return DEFAULT_RISK_LEVEL
    value = str(risk_level).strip().lower()
    return value if value in VALID_RISK_LEVELS else None


def _sector_signal(ticker: str, sector: str) -> Dict[str, Any]:
    # Imported lazily: model_loader pulls in joblib/sklearn artefacts, which the
    # global path (a plain JSON read) doesn't need.
    from app.signals.models.model_loader import predict_ticker_signal

    return predict_ticker_signal(ticker=ticker, sector=sector)


def get_signal(ticker: str, sector: Optional[str] = None, scope: Optional[str] = DEFAULT_SCOPE,
               risk_level: Optional[str] = DEFAULT_RISK_LEVEL) -> Dict[str, Any]:
    """Signal dict ({"signal": "BUY"|"HOLD"|..., "confidence": float, "status": ...})
    from the requested model family. Adds "model_scope" to the result.

    `sector` is only used by the sector models; `risk_level` only by the global one.
    A bad scope/risk level returns status "error" (HOLD, confidence 0.0) instead of raising.
    """
    scope_clean = normalize_scope(scope)
    if scope_clean is None:
        return {
            "ticker": (ticker or "").upper().strip(), "signal": "HOLD", "confidence": 0.0,
            "status": "error", "model_scope": scope,
            "message": f"Unknown model scope '{scope}'. Use one of: {', '.join(VALID_SCOPES)}.",
        }

    if scope_clean == "global":
        risk_clean = normalize_risk_level(risk_level)
        if risk_clean is None:
            return {
                "ticker": (ticker or "").upper().strip(), "signal": "HOLD", "confidence": 0.0,
                "status": "error", "model_scope": "global",
                "message": f"Unknown risk level '{risk_level}'. Use one of: {', '.join(VALID_RISK_LEVELS)}.",
            }
        result = predict_global_signal(ticker, risk_level=risk_clean)
    else:
        result = _sector_signal(ticker, sector or "General")

    result["model_scope"] = scope_clean
    return result
