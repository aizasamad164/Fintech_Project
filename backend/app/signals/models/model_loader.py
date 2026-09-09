"""
FR-3.2 / FR-3.3: Load sector-specialized LightGBM/XGBoost classifiers.
Falls back to the combined general model for multi-sector requests.
"""
import joblib
from pathlib import Path

MODELS_DIR = Path(__file__).parent
_model_cache: dict = {}


def load_model(sector: str):
    """
    sector: e.g. 'technology', 'healthcare', or 'combined' for multi-sector.
    Caches loaded models in memory to avoid repeated disk reads.
    """
    if sector in _model_cache:
        return _model_cache[sector]

    model_path = MODELS_DIR / f"{sector}_model.pkl"
    if not model_path.exists():
        model_path = MODELS_DIR / "general_model.pkl"  # fallback (FR-3.3)

    model = joblib.load(model_path)
    _model_cache[sector] = model
    return model


def predict_bullish_probability(sector: str, feature_matrix) -> float:
    """Returns P(Bullish) for a given stock's technical indicator matrix."""
    model = load_model(sector)
    return model.predict_proba(feature_matrix)[:, 1]
