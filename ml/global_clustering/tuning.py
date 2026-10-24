"""
Run this ONCE (offline, ideally before serving/demoing), not per cluster.

Tuning on a few hundred rows per tiny cluster mostly finds noise, not
signal. Instead, this uses TimeSeriesSplit (walk-forward, chronological
folds -- never trains on a fold's future to predict its past) on the FULL
pooled cross-sector dataset, which has ~30x more rows than any single
cluster. The result generalizes far better and only needs to be computed
once; pipeline.py's model fitters load it automatically.

max_depth is deliberately NOT tuned here -- it's a risk-profile knob
(conservative gets shallower/safer trees, aggressive gets deeper ones) by
design in backend/app/ml_config.py, not a pure accuracy target.

Usage:
    python -m ml.global_clustering.tuning      (from the repo root)

Writes ml/global_clustering/tuned_params.json. Delete it (or re-run this script) to
force a re-tune -- e.g. after the ticker universe changes meaningfully.
"""

import itertools
import json
import os
import random
import time

import numpy as np
import lightgbm as lgb
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import TimeSeriesSplit

from .pipeline import (
    FEATURE_COLS,
    SequenceLSTMClassifier,
    add_target_column,
    compute_common_indicators,
    fetch_all_sectors_data,
)

TUNED_PARAMS_PATH = os.path.join(os.path.dirname(__file__), "tuned_params.json")
N_SPLITS = 4
SEARCH_SAMPLE_SIZE = 10
SEED = 42


def _cv_auc(model_builder, X, y, n_splits=N_SPLITS):
    tscv = TimeSeriesSplit(n_splits=n_splits)
    scores = []
    for train_idx, val_idx in tscv.split(X):
        y_va = y.iloc[val_idx]
        if y_va.nunique() < 2:
            continue
        model = model_builder()
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        probs = model.predict_proba(X.iloc[val_idx])[:, 1]
        scores.append(roc_auc_score(y_va, probs))
    return float(np.mean(scores)) if scores else 0.5


def tune_lightgbm(X, y):
    grid = list(itertools.product([7, 15, 31], [0.7, 0.9], [0.7, 0.9], [0.02, 0.05]))
    sampled = random.Random(SEED).sample(grid, min(SEARCH_SAMPLE_SIZE, len(grid)))
    best_params, best_score = None, -1.0
    for num_leaves, ff, bf, lr in sampled:
        params = dict(num_leaves=num_leaves, feature_fraction=ff, bagging_fraction=bf, learning_rate=lr)
        builder = lambda p=params: lgb.LGBMClassifier(
            n_estimators=300, is_unbalance=True, random_state=42, verbose=-1, **p
        )
        score = _cv_auc(builder, X, y)
        if score > best_score:
            best_params, best_score = params, score
    print(f"[tune] LightGBM: CV AUC={best_score:.4f} params={best_params}")
    return best_params, best_score


def tune_random_forest(X, y):
    grid = list(itertools.product([200, 300], [5, 10, 20], ["sqrt", "log2"]))
    sampled = random.Random(SEED).sample(grid, min(SEARCH_SAMPLE_SIZE, len(grid)))
    best_params, best_score = None, -1.0
    for n_est, min_leaf, max_feat in sampled:
        params = dict(n_estimators=n_est, min_samples_leaf=min_leaf, max_features=max_feat)
        builder = lambda p=params: RandomForestClassifier(
            class_weight="balanced", random_state=42, n_jobs=-1, **p
        )
        score = _cv_auc(builder, X, y)
        if score > best_score:
            best_params, best_score = params, score
    print(f"[tune] RandomForest: CV AUC={best_score:.4f} params={best_params}")
    return best_params, best_score


def tune_xgboost(X, y):
    grid = list(itertools.product([0.02, 0.05], [0.7, 0.9], [0.7, 0.9], [0.0, 0.1], [1.0, 2.0]))
    sampled = random.Random(SEED).sample(grid, min(SEARCH_SAMPLE_SIZE, len(grid)))
    best_params, best_score = None, -1.0
    for lr, ss, cs, alpha, lam in sampled:
        params = dict(learning_rate=lr, subsample=ss, colsample_bytree=cs, reg_alpha=alpha, reg_lambda=lam)
        builder = lambda p=params: xgb.XGBClassifier(
            n_estimators=300, eval_metric="auc", random_state=42, verbosity=0, **p
        )
        score = _cv_auc(builder, X, y)
        if score > best_score:
            best_params, best_score = params, score
    print(f"[tune] XGBoost: CV AUC={best_score:.4f} params={best_params}")
    return best_params, best_score


def tune_lstm_seq_len(X, y, candidates=(5, 10, 15)):
    """Only a 2-fold check -- NN training is far more expensive than the
    tree models above, so this deliberately searches a narrower space."""
    tscv = TimeSeriesSplit(n_splits=2)
    best_len, best_score = 10, -1.0
    for seq_len in candidates:
        scores = []
        for train_idx, val_idx in tscv.split(X):
            X_tr, X_va = X.iloc[train_idx], X.iloc[val_idx]
            y_tr, y_va = y.iloc[train_idx], y.iloc[val_idx]
            if y_va.nunique() < 2 or len(X_tr) < seq_len * 3:
                continue
            model = SequenceLSTMClassifier(input_dim=X.shape[1], seq_len=seq_len, epochs=15)
            model.fit(X_tr, y_tr, X_va, y_va)
            probs = model.predict_proba(X_va)[:, 1]
            scores.append(roc_auc_score(y_va, probs))
        if scores:
            avg = float(np.mean(scores))
            if avg > best_score:
                best_len, best_score = seq_len, avg
    print(f"[tune] LSTM: best seq_len={best_len} CV AUC={best_score:.4f}")
    return {"seq_len": best_len}, best_score


def tune_all_models():
    print("Fetching pooled cross-sector data for global hyperparameter tuning...")
    raw = fetch_all_sectors_data()
    indicators = compute_common_indicators(raw)
    indicators = add_target_column(indicators, risk_level="balanced")  # tune once, reuse for every risk level
    indicators = indicators.sort_index()
    X, y = indicators[FEATURE_COLS], indicators["Target"]
    print(f"Pooled dataset: {len(X)} rows across {indicators['Ticker'].nunique()} tickers.\n")

    t0 = time.time()
    lgb_params, lgb_score = tune_lightgbm(X, y)
    rf_params, rf_score = tune_random_forest(X, y)
    xgb_params, xgb_score = tune_xgboost(X, y)
    lstm_params, lstm_score = tune_lstm_seq_len(X, y)

    results = {
        "LightGBM": {"params": lgb_params, "cv_auc": lgb_score},
        "RandomForest": {"params": rf_params, "cv_auc": rf_score},
        "XGBoost": {"params": xgb_params, "cv_auc": xgb_score},
        "LSTM": {"params": lstm_params, "cv_auc": lstm_score},
    }
    with open(TUNED_PARAMS_PATH, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDone in {time.time() - t0:.1f}s. Saved to {TUNED_PARAMS_PATH}")
    return results


if __name__ == "__main__":
    tune_all_models()
