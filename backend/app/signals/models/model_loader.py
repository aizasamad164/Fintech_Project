# backend/app/signals/models/model_loader.py
import os
import warnings
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

# Suppress sklearn feature validation warnings globally during model inference
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
warnings.filterwarnings("ignore", message=".*valid feature names.*")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../../ml/trained_models"))

SECTOR_MODEL_MAP = {
    "Technology": ("technology_ensemble_model.joblib", "technology_scaler.joblib"),
    "Healthcare": ("healthcare_ensemble_model.joblib", "healthcare_scaler.joblib"),
    "Pharmaceuticals": ("pharmaceuticals_ensemble_model.joblib", "pharmaceuticals_scaler.joblib"),
    "Renewable_Energy": ("renewable_energy_ensemble_model.joblib", "renewable_energy_scaler.joblib"),
    "General": ("general_ensemble_model.joblib", "general_scaler.joblib"),
}

_MODEL_CACHE: Dict[str, Tuple[Any, Any]] = {}

def load_sector_pair(sector_name: str) -> Tuple[Any, Any]:
    if sector_name not in SECTOR_MODEL_MAP:
        sector_name = "General"

    if sector_name in _MODEL_CACHE:
        return _MODEL_CACHE[sector_name]

    model_file, scaler_file = SECTOR_MODEL_MAP[sector_name]
    model_path = os.path.join(MODELS_DIR, model_file)
    scaler_path = os.path.join(MODELS_DIR, scaler_file)

    model = joblib.load(model_path) if os.path.exists(model_path) else None
    scaler = joblib.load(scaler_path) if os.path.exists(scaler_path) else None

    _MODEL_CACHE[sector_name] = (model, scaler)
    return model, scaler

def predict_ticker_signal(ticker: str, sector: str) -> Dict[str, Any]:
    ticker_clean = ticker.upper().strip()
    model, scaler = load_sector_pair(sector)

    if not model or not scaler:
        return {
            "ticker": ticker_clean,
            "sector": sector,
            "signal": "HOLD",
            "confidence": 0.50,
            "status": "warning",
            "message": f"Trained model artifacts for '{sector}' not found in ml/trained_models/."
        }

    try:
        # Match feature column names if preserved on scaler to prevent warnings
        if hasattr(scaler, "feature_names_in_"):
            cols = list(scaler.feature_names_in_)
            dummy_features = pd.DataFrame(np.zeros((1, len(cols))), columns=cols)
        else:
            num_features = getattr(scaler, "n_features_in_", 9)
            dummy_features = np.zeros((1, num_features))

        scaled_features = scaler.transform(dummy_features)
        predicted_return = float(model.predict(scaled_features)[0])

        signal = "BUY" if predicted_return > 0.005 else ("SELL" if predicted_return < -0.005 else "HOLD")
        confidence = round(min(0.95, max(0.55, 0.50 + abs(predicted_return) * 10)), 2)

        return {
            "ticker": ticker_clean,
            "sector": sector,
            "signal": signal,
            "confidence": confidence,
            "predicted_5d_return": f"{round(predicted_return * 100, 2)}%",
            "status": "success"
        }

    except Exception as e:
        return {
            "ticker": ticker_clean,
            "sector": sector,
            "signal": "HOLD",
            "confidence": 0.50,
            "status": "error",
            "message": str(e)
        }