"""
Cross-sector clustering pipeline -- v3, maximum-effort pass.

Fixed vs. the previous round:
  - Single clustering fit, not once-per-risk-level. Fetching data and
    forming clusters doesn't depend on risk level; only the Target
    threshold does. prepare_global_clusters() runs this ONCE.
  - Fair efficiency benchmark: baseline now fits the SAME 4-candidate pool
    per ticker that the clustered path fits per cluster, so the reported
    speedup reflects grouping strategy, not "1 model vs 4 models".
  - XGBoost now actually early-stops (it silently trained all 300 trees
    regardless of overfitting before).

Added:
  - Hyperparameters for LightGBM/RandomForest/XGBoost are loaded from
    clustering/tuned_params.json if present -- produced ONCE by
    hyperparameter_tuning.py via walk-forward (TimeSeriesSplit) cross-
    validation on the full pooled dataset. Tuning per-tiny-cluster would
    mostly fit noise; tuning once on ~3 years x 30 tickers and reusing the
    result everywhere is the statistically sound version of the same idea.
    Falls back to sane regularized defaults if the cache doesn't exist yet.
  - Platt-scaling probability calibration on the winning model (see
    _calibrate/_CalibratedWrapper below). Predicted probabilities feed both
    the risk-level quantile cutoff AND the downstream portfolio allocator
    (score_individual_stocks) -- both need probabilities that mean the
    same thing across model families, and a raw LSTM sigmoid output isn't
    calibrated the same way a tree ensemble's leaf-average is. Isotonic
    regression was tried first and dropped: with only a per-cluster
    validation slice to fit on, its step function collapsed many distinct
    stocks onto identical probabilities in practice.
  - A weighted-average ensemble of every candidate that beat 0.5 val AUC
    competes against the 4 individual models. Small-data settings are
    exactly where ensembling tends to reduce variance -- if it wins on
    validation, it's used; if not, the single best model is kept.
  - Gradient clipping in the LSTM training loop (financial return series
    are noisy; unclipped gradients are a common source of instability).
  - Per-candidate try/except: one model failing to fit on a very small
    cluster no longer takes down the whole pipeline run.

In the StockSense repo (ml/global_clustering/pipeline.py):
  - Config comes from backend/app/ml_config.py (shared with the backend).
  - The fundamentals-screened fetch lives in this module
    (fetch_screened_sector_data) instead of overwriting the shared
    backend/app/data/fetcher.py, which has no PE/margin screening.
  - compute_common_indicators(require_label=False) keeps the most recent
    rows (whose 5-day forward return isn't known yet) so the CURRENT signal
    can be scored; training paths still use labeled rows only.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import ta
import yfinance as yf
import lightgbm as lgb
import xgboost as xgb
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, roc_auc_score, silhouette_score
from sklearn.preprocessing import MinMaxScaler, StandardScaler

# Config is shared with the backend (backend/app/ml_config.py). Put the repo
# root on sys.path so this package works however it's launched
# (`python ml/train_global_clustering.py`, `python -m ml.global_clustering...`).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.app.ml_config import RISK_PROFILES, SECTOR_CONFIGS  # noqa: E402

# ---------------------------------------------------------------------------
# Fixed, sector-agnostic indicator windows -- required so clustering compares
# stocks on the same yardstick regardless of which sector they came from.
# ---------------------------------------------------------------------------
COMMON_RSI_WINDOW = 14
COMMON_TREND_SMA = 50
COMMON_VOL_SMA = 20

FEATURE_COLS = [
    "Daily_Return", "RVOL", "Norm_ATR", "SMA_Ratio",
    "RSI", "MACD_HIST", "PPO", "Stoch_K", "BB_Width",
    "Lag1", "Lag2", "Lag3", "Lag4",
]

CLUSTER_TRAIN_FRAC = 0.60   # matches _time_split's train proportion
LSTM_SEQ_LEN_DEFAULT = 10   # overridden by tuned_params.json if present


# ---------------------------------------------------------------------------
# Tuned hyperparameters -- see hyperparameter_tuning.py. Loaded once at
# import time; safe empty-dict fallback if tuning hasn't been run yet.
# ---------------------------------------------------------------------------
_TUNED_PARAMS_PATH = os.path.join(os.path.dirname(__file__), "tuned_params.json")


def _load_tuned_params() -> dict:
    if os.path.exists(_TUNED_PARAMS_PATH):
        try:
            with open(_TUNED_PARAMS_PATH) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            print(f"Warning: could not read {_TUNED_PARAMS_PATH}, using defaults.")
    return {}


_TUNED = _load_tuned_params()


def reload_tuned_params() -> dict:
    """Re-read tuned_params.json into _TUNED IN PLACE. The model fitters read
    _TUNED at call time, so call this right after tuning to make the SAME
    process use the fresh params (otherwise a first run that tunes would
    still train on the defaults it loaded at import)."""
    _TUNED.clear()
    _TUNED.update(_load_tuned_params())
    return _TUNED


# ---------------------------------------------------------------------------
# 1. Data
# ---------------------------------------------------------------------------
# Minimum trading days of history before a ticker is usable -- below this the
# rolling windows (up to the 50-day SMA) plus dropna would gut it anyway, so
# skip it up front with a clear reason instead of letting it vanish silently.
MIN_HISTORY_DAYS = 120


def fetch_screened_sector_data(sector_name: str) -> pd.DataFrame:
    """Pull + fundamentally screen (max_pe / min_profit_margin from
    ml_config) every configured ticker for one sector.

    Every skip (screened out, fetch failed, too little history) is printed
    with its reason, and one flaky ticker can't take the whole sector down.
    Timezones are stripped so the index matches the rest of the repo's data
    code (backend/app/data/fetcher.py does the same).
    """
    config = SECTOR_CONFIGS[sector_name]
    end_date = datetime.now()
    start_date = end_date - pd.Timedelta(days=1100)

    combined_dfs = []
    skipped = []

    for ticker in config["tickers"]:
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
        except Exception as e:
            skipped.append((ticker, f"fundamentals fetch failed: {e}"))
            continue

        pe = info.get("trailingPE", 999)
        margin = info.get("profitMargins", -1)

        if pe > config["max_pe"] or margin < config["min_profit_margin"]:
            skipped.append((ticker, f"failed fundamentals screen (PE={pe}, margin={margin})"))
            continue

        try:
            df = ticker_obj.history(
                start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"), timeout=10
            )
        except Exception as e:
            skipped.append((ticker, f"price history fetch failed: {e}"))
            continue

        if df.empty:
            skipped.append((ticker, "no price history returned"))
            continue

        if getattr(df.index, "tz", None) is not None:
            df.index = df.index.tz_localize(None)

        df = df[["Open", "High", "Low", "Close", "Volume"]].dropna().copy()
        if len(df) < MIN_HISTORY_DAYS:
            skipped.append((ticker, f"only {len(df)} trading days of history (need {MIN_HISTORY_DAYS}+)"))
            continue

        df["Ticker"] = ticker
        df["Sector"] = sector_name
        combined_dfs.append(df.iloc[-750:])

    if skipped:
        print(f"[{sector_name}] Skipped {len(skipped)}/{len(config['tickers'])} tickers:")
        for ticker, reason in skipped:
            print(f"    {ticker}: {reason}")

    if not combined_dfs:
        raise ValueError(f"No tickers passed fundamental screening for sector {sector_name}")

    return pd.concat(combined_dfs, axis=0)


def fetch_all_sectors_data() -> pd.DataFrame:
    """Pool every fundamentally-screened ticker, across all sectors."""
    frames = []
    for sector in SECTOR_CONFIGS:
        try:
            frames.append(fetch_screened_sector_data(sector))
        except ValueError as e:
            print(f"Skipping {sector}: {e}")
    if not frames:
        raise RuntimeError("No sector data available for global clustering.")
    return pd.concat(frames, axis=0)


# ---------------------------------------------------------------------------
# 2. Feature engineering -- uniform windows, paper's 6 indicators + 4 lags,
#    plus RVOL for volume signal. No risk_level here: indicators don't
#    depend on it, only the eventual Target threshold does (see
#    add_target_column below) -- computing indicators once instead of once
#    per risk level avoids 3x redundant fetch + indicator math.
# ---------------------------------------------------------------------------
def compute_common_indicators(df: pd.DataFrame, require_label: bool = True) -> pd.DataFrame:
    """require_label=True (default, used for ALL training): drop rows whose
    5-day forward return isn't known yet. require_label=False keeps those
    newest rows (Future_5D_Return is NaN there) so the current signal can
    be scored -- never feed those rows to training."""
    out = []

    for ticker, sub in df.groupby("Ticker"):
        s = sub.copy()
        s["Future_5D_Return"] = s["Close"].shift(-5) / s["Close"] - 1.0
        s["Daily_Return"] = s["Close"].pct_change()

        vol_sma = ta.trend.sma_indicator(s["Volume"], window=COMMON_VOL_SMA)
        s["RVOL"] = s["Volume"] / (vol_sma + 1e-8)

        atr = ta.volatility.average_true_range(s["High"], s["Low"], s["Close"], window=14)
        s["Norm_ATR"] = atr / s["Close"]

        s["SMA_Ratio"] = s["Close"] / ta.trend.sma_indicator(s["Close"], window=COMMON_TREND_SMA)
        s["RSI"] = ta.momentum.rsi(s["Close"], window=COMMON_RSI_WINDOW)

        macd_obj = ta.trend.MACD(s["Close"], window_fast=12, window_slow=26, window_sign=9)
        s["MACD_HIST"] = macd_obj.macd_diff()

        s["PPO"] = ta.momentum.PercentagePriceOscillator(s["Close"]).ppo()

        stoch_obj = ta.momentum.StochasticOscillator(s["High"], s["Low"], s["Close"], window=14, smooth_window=3)
        s["Stoch_K"] = stoch_obj.stoch()

        bb_obj = ta.volatility.BollingerBands(s["Close"], window=20, window_dev=2)
        s["BB_Width"] = (bb_obj.bollinger_hband() - bb_obj.bollinger_lband()) / bb_obj.bollinger_mavg()

        log_ret = np.log(s["Close"] / s["Close"].shift(1))
        for lag in range(1, 5):
            s[f"Lag{lag}"] = log_ret.shift(lag - 1)

        out.append(s)

    full = pd.concat(out, axis=0)
    required = FEATURE_COLS + (["Future_5D_Return"] if require_label else [])
    clean = full.dropna(subset=required).copy()
    return clean[["Ticker", "Sector"] + FEATURE_COLS + ["Future_5D_Return"]]


def add_target_column(indicator_df: pd.DataFrame, risk_level: str) -> pd.DataFrame:
    """Cheap, risk-specific labeling -- run per risk level; indicators
    themselves (the expensive part) are computed only once."""
    risk_cfg = RISK_PROFILES[risk_level]
    out = indicator_df.copy()
    out["Target"] = (out["Future_5D_Return"] >= risk_cfg["target_return"]).astype(int)
    return out


# ---------------------------------------------------------------------------
# 3. Clustering -- K-Means fit ONLY on the chronological training period
#    (a single global date cutoff, so every ticker's clustering input comes
#    from the same calendar window). Never refit on validation/test data.
# ---------------------------------------------------------------------------
def build_cluster_input_features(indicator_df: pd.DataFrame) -> pd.DataFrame:
    agg = indicator_df.groupby("Ticker")[FEATURE_COLS].agg(["mean", "std"])
    agg.columns = [f"{c}_{stat}" for c, stat in agg.columns]
    return agg.fillna(0.0)


def choose_k_and_cluster(cluster_features: pd.DataFrame, k_min: int = 2, k_max: int | None = None):
    """cluster_features must already contain ONLY training-period data --
    see prepare_global_clusters. There's no separate "transform val/test"
    step because cluster membership is a per-ticker label decided once,
    not recomputed per row/date."""
    n = len(cluster_features)
    if k_max is None:
        k_max = max(k_min, n - 1)

    scaler = MinMaxScaler()
    X = scaler.fit_transform(cluster_features.values)

    best_k, best_score, best_labels = None, -1.0, None
    for k in range(k_min, min(k_max, n - 1) + 1):
        labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(X)
        score = silhouette_score(X, labels)
        if score > best_score:
            best_k, best_score, best_labels = k, score, labels

    result = cluster_features.copy()
    result["Cluster"] = best_labels
    print(f"Chosen k={best_k} (silhouette={best_score:.3f}) across {n} tickers, all sectors pooled")
    return result[["Cluster"]], best_k


# ---------------------------------------------------------------------------
# 4. Representative data -- date-aligned averaging: intersect each member's
#    dates first, then average, instead of a plain groupby-mean that could
#    silently mix mismatched calendars.
# ---------------------------------------------------------------------------
def build_cluster_representative_data(indicator_df: pd.DataFrame, cluster_map: pd.DataFrame,
                                       risk_level: str = "balanced") -> dict:
    risk_cfg = RISK_PROFILES[risk_level]
    df = indicator_df.merge(cluster_map, left_on="Ticker", right_index=True)

    rep_by_cluster = {}
    for cid, sub in df.groupby("Cluster"):
        members = sub["Ticker"].unique()
        member_frames = [sub[sub["Ticker"] == t][FEATURE_COLS + ["Future_5D_Return"]] for t in members]

        common_idx = member_frames[0].index
        for m in member_frames[1:]:
            common_idx = common_idx.intersection(m.index)
        aligned = [m.loc[common_idx] for m in member_frames]

        avg_df = (sum(aligned) / len(aligned)).sort_index()
        avg_df["Target"] = (avg_df["Future_5D_Return"] >= risk_cfg["target_return"]).astype(int)
        rep_by_cluster[cid] = avg_df

    return rep_by_cluster


# ---------------------------------------------------------------------------
# 5. Model candidates
# ---------------------------------------------------------------------------
def _time_split(X, y, returns):
    n = len(X)
    train_end = int(n * 0.60)
    val_end = int(n * 0.80)
    return (
        X.iloc[:train_end], y.iloc[:train_end],
        X.iloc[train_end:val_end], y.iloc[train_end:val_end],
        X.iloc[val_end:], y.iloc[val_end:], returns.iloc[val_end:],
    )


def _fit_lightgbm(X_tr, y_tr, X_val, y_val, risk_cfg):
    tuned = _TUNED.get("LightGBM", {}).get("params", {})
    params = dict(num_leaves=15, feature_fraction=0.8, bagging_fraction=0.8, learning_rate=0.02)
    params.update(tuned)  # tuned values win when present
    model = lgb.LGBMClassifier(
        n_estimators=300, max_depth=risk_cfg["max_depth"],   # max_depth stays risk-specific by design
        is_unbalance=True, random_state=42, verbose=-1, **params,
    )
    model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)],
              callbacks=[lgb.early_stopping(stopping_rounds=20, verbose=False)])
    return model


def _fit_random_forest(X_tr, y_tr, X_val, y_val, risk_cfg):
    tuned = _TUNED.get("RandomForest", {}).get("params", {})
    params = dict(n_estimators=300, min_samples_leaf=10, max_features="sqrt")
    params.update(tuned)
    model = RandomForestClassifier(
        max_depth=risk_cfg["max_depth"], class_weight="balanced", random_state=42, n_jobs=-1, **params,
    )
    model.fit(X_tr, y_tr)
    return model


def _fit_xgboost(X_tr, y_tr, X_val, y_val, risk_cfg):
    tuned = _TUNED.get("XGBoost", {}).get("params", {})
    params = dict(learning_rate=0.02, subsample=0.8, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=1.0)
    params.update(tuned)
    model = xgb.XGBClassifier(
        n_estimators=300, max_depth=min(risk_cfg["max_depth"], 10),
        eval_metric="auc", random_state=42, verbosity=0,
        early_stopping_rounds=20,   # <-- fixed: this was missing, so XGBoost never actually stopped early
        **params,
    )
    model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
    return model


class _LSTMNet(nn.Module):
    def __init__(self, input_dim, hidden_dim=32, num_layers=1, dropout=0.2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim, hidden_size=hidden_dim,
            num_layers=num_layers, batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.fc1 = nn.Linear(hidden_dim, 16)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(16, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.relu(self.fc1(out[:, -1, :]))
        return self.sigmoid(self.fc2(out))


class _WindowDataset(Dataset):
    """Turns chronologically-ordered rows into overlapping (seq_len, n_features)
    windows, each labelled with the target at the window's last day."""

    def __init__(self, X, y, seq_len):
        self.x, self.y = [], []
        for i in range(len(X) - seq_len):
            self.x.append(X[i: i + seq_len])
            self.y.append(y[i + seq_len])
        self.x = torch.tensor(np.array(self.x), dtype=torch.float32)
        self.y = torch.tensor(np.array(self.y), dtype=torch.float32).unsqueeze(1)

    def __len__(self):
        return len(self.x)

    def __getitem__(self, idx):
        return self.x[idx], self.y[idx]


class SequenceLSTMClassifier:
    """sklearn-style (.fit / .predict_proba) wrapper around _LSTMNet, so it
    sits in CANDIDATE_FITTERS next to LightGBM/RandomForest/XGBoost and is
    scored/selected/calibrated/ensembled the same way as the others.

    Rows handed to fit/predict_proba are plain (n_samples, n_features)
    tables in chronological order (per cluster, or per ticker in
    score_individual_stocks) -- reshaped into sliding windows internally.
    Rows before the first full window get a neutral 0.5 probability rather
    than being dropped, so output length always matches input length.
    """

    def __init__(self, input_dim, seq_len=LSTM_SEQ_LEN_DEFAULT, hidden_dim=32,
                 epochs=30, batch_size=16, lr=1e-3, patience=5, seed=42):
        self.seq_len = seq_len
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.patience = patience
        self.scaler = StandardScaler()
        # Every other candidate (LightGBM/RandomForest/XGBoost) is seeded
        # with random_state=42; this was the one unseeded source of
        # run-to-run variation -- weight init here previously drew from
        # whatever state the global torch RNG happened to be in, so which
        # candidates cleared 0.5 val AUC (and therefore which subset the
        # ensemble/best-model selection used) could shift between two runs
        # on the exact same data. Seeding here makes LSTM results
        # reproducible the same way the tree models already are.
        torch.manual_seed(seed)
        self.model = _LSTMNet(input_dim, hidden_dim=hidden_dim)

    def fit(self, X_tr, y_tr, X_val=None, y_val=None):
        X_tr = np.asarray(X_tr, dtype=np.float32)
        y_tr = np.asarray(y_tr, dtype=np.float32)
        self.seq_len_ = max(2, min(self.seq_len, len(X_tr) // 3 or 2))

        X_tr_s = self.scaler.fit_transform(X_tr)
        train_ds = _WindowDataset(X_tr_s, y_tr, self.seq_len_)
        if len(train_ds) == 0:
            raise ValueError("Not enough rows to build a single LSTM training window.")
        train_loader = DataLoader(train_ds, batch_size=self.batch_size, shuffle=False)

        has_val = X_val is not None and len(X_val) > self.seq_len_
        if has_val:
            X_val_s = self.scaler.transform(np.asarray(X_val, dtype=np.float32))
            val_ds = _WindowDataset(X_val_s, np.asarray(y_val, dtype=np.float32), self.seq_len_)
            val_loader = DataLoader(val_ds, batch_size=self.batch_size, shuffle=False) if len(val_ds) else None
        else:
            val_loader = None

        criterion = nn.BCELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr, weight_decay=1e-4)

        best_val_loss, best_state, bad_epochs = float("inf"), None, 0
        for _ in range(self.epochs):
            self.model.train()
            for xb, yb in train_loader:
                optimizer.zero_grad()
                loss = criterion(self.model(xb), yb)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)  # stability on noisy series
                optimizer.step()

            if val_loader is not None:
                self.model.eval()
                v_loss, n_seen = 0.0, 0
                with torch.no_grad():
                    for xb, yb in val_loader:
                        v_loss += criterion(self.model(xb), yb).item() * xb.size(0)
                        n_seen += xb.size(0)
                v_loss /= max(n_seen, 1)
                if v_loss < best_val_loss:
                    best_val_loss = v_loss
                    best_state = {k: v.clone() for k, v in self.model.state_dict().items()}
                    bad_epochs = 0
                else:
                    bad_epochs += 1
                    if bad_epochs >= self.patience:
                        break

        if best_state is not None:
            self.model.load_state_dict(best_state)
        return self

    def predict_proba(self, X):
        X = np.asarray(X, dtype=np.float32)
        n = len(X)
        probs = np.full(n, 0.5, dtype=np.float32)
        seq_len = getattr(self, "seq_len_", self.seq_len)

        if n > seq_len:
            X_s = self.scaler.transform(X)
            windows = np.stack([X_s[i - seq_len:i] for i in range(seq_len, n)])
            self.model.eval()
            with torch.no_grad():
                batch = torch.tensor(windows, dtype=torch.float32)
                preds = self.model(batch).squeeze(-1).numpy()
            probs[seq_len:] = preds

        return np.column_stack([1.0 - probs, probs])


def _fit_lstm(X_tr, y_tr, X_val, y_val, risk_cfg):
    tuned_seq_len = _TUNED.get("LSTM", {}).get("params", {}).get("seq_len", LSTM_SEQ_LEN_DEFAULT)
    model = SequenceLSTMClassifier(input_dim=X_tr.shape[1], seq_len=tuned_seq_len)
    model.fit(X_tr, y_tr, X_val, y_val)
    return model


CANDIDATE_FITTERS = {
    "LightGBM": _fit_lightgbm,
    "RandomForest": _fit_random_forest,
    "XGBoost": _fit_xgboost,
    "LSTM": _fit_lstm,
}


# ---------------------------------------------------------------------------
# Calibration + ensembling
# ---------------------------------------------------------------------------
class _CalibratedWrapper:
    """Platt scaling (a 1-feature logistic regression fit on raw score ->
    label), fit on the validation set. Implemented by hand (rather than
    sklearn's CalibratedClassifierCV) so it works identically across all 4
    candidate types -- including the hand-rolled LSTM wrapper, which isn't
    a full sklearn estimator -- without depending on sklearn version-
    specific 'prefit' API changes.

    Was isotonic regression -- switched to Platt scaling because isotonic
    fits a step function, and with only a couple hundred validation rows
    per cluster (this app's actual data scale) that staircase ends up with
    just a handful of distinct steps. In production that showed up as a
    dozen genuinely different stocks all getting the EXACT same calibrated
    probability (e.g. 0.1764706, repeatedly) -- collapsing the ranking the
    allocation engine needs. Platt scaling is smooth and strictly
    monotonic, so it reshapes probabilities without ever tying two
    different raw scores to the same output. Isotonic's extra flexibility
    only pays off with much more calibration data than a per-cluster
    validation slice provides here."""
    def __init__(self, base_model, calibrator):
        self.base_model = base_model
        self.calibrator = calibrator

    def predict_proba(self, X):
        raw = self.base_model.predict_proba(X)[:, 1]
        calibrated = np.clip(self.calibrator.predict_proba(raw.reshape(-1, 1))[:, 1], 1e-6, 1 - 1e-6)
        return np.column_stack([1 - calibrated, calibrated])


def _calibrate(model, X_val, y_val):
    if len(y_val) < 10 or y_val.nunique() < 2:
        return model  # not enough validation data to calibrate reliably -- skip
    raw_val_probs = model.predict_proba(X_val)[:, 1]
    platt = LogisticRegression()
    platt.fit(raw_val_probs.reshape(-1, 1), y_val)
    return _CalibratedWrapper(model, platt)


class _EnsembleProbaWrapper:
    """Weighted average of every candidate that beat random-guessing (val
    AUC > 0.5) on this cluster, weighted by how far above 0.5 it scored."""
    def __init__(self, models_and_weights):
        self.models_and_weights = models_and_weights

    def predict_proba(self, X):
        total_w = sum(w for _, w in self.models_and_weights)
        agg = np.zeros(len(X))
        for model, w in self.models_and_weights:
            agg += w * model.predict_proba(X)[:, 1]
        agg /= total_w
        return np.column_stack([1 - agg, agg])


def train_best_model_for_cluster(X, y, returns, cluster_id, risk_level: str):
    """Fits all 4 candidates (skipping any that fail on too-small data),
    calibrates each, builds an ensemble if 2+ candidates are usable, and
    picks whichever -- individual model or ensemble -- has the best
    VALIDATION auc-roc. Selection never looks at the test set."""
    risk_cfg = RISK_PROFILES[risk_level]
    X_tr, y_tr, X_val, y_val, X_test, y_test, ret_test = _time_split(X, y, returns)

    fitted = {}
    timings = {}
    for name, fitter in CANDIDATE_FITTERS.items():
        t0 = time.time()
        try:
            model = fitter(X_tr, y_tr, X_val, y_val, risk_cfg)
        except Exception as e:
            print(f"  [Cluster {cluster_id}, {risk_level}] {name} failed to fit, skipping: {e}")
            continue
        timings[name] = time.time() - t0

        calibrated = _calibrate(model, X_val, y_val)
        val_probs = calibrated.predict_proba(X_val)[:, 1]
        val_auc = roc_auc_score(y_val, val_probs) if y_val.nunique() > 1 else 0.5
        fitted[name] = {"model": calibrated, "val_auc": val_auc}

    if not fitted:
        raise RuntimeError(f"All 4 candidates failed to fit for cluster {cluster_id} ({risk_level}).")

    contributing = {n: f for n, f in fitted.items() if f["val_auc"] > 0.5}
    if len(contributing) >= 2:
        weighted = [(f["model"], max(f["val_auc"] - 0.5, 0.01)) for f in contributing.values()]
        ensemble = _EnsembleProbaWrapper(weighted)
        ens_val_probs = ensemble.predict_proba(X_val)[:, 1]
        ens_val_auc = roc_auc_score(y_val, ens_val_probs) if y_val.nunique() > 1 else 0.5
        fitted["Ensemble"] = {"model": ensemble, "val_auc": ens_val_auc}

    best_name = max(fitted, key=lambda n: fitted[n]["val_auc"])
    best_model = fitted[best_name]["model"]
    best_val_auc = fitted[best_name]["val_auc"]

    # Per-candidate val AUCs, so "Ensemble won" is checkable rather than a
    # black box -- previously only the winner's score was visible, so
    # there was no way to tell e.g. whether LSTM ever actually cleared 0.5
    # or was dead weight every run.
    individual_aucs = ", ".join(
        f"{n}={fitted[n]['val_auc']:.3f}" for n in CANDIDATE_FITTERS if n in fitted
    )
    ensemble_members = ", ".join(sorted(contributing)) if "Ensemble" in fitted else ""

    test_probs = best_model.predict_proba(X_test)[:, 1]
    val_probs = best_model.predict_proba(X_val)[:, 1]
    dynamic_cutoff = float(np.quantile(val_probs, risk_cfg["quantile_threshold"]))
    preds_binary = (test_probs >= dynamic_cutoff).astype(int)

    strategy_returns = ret_test * preds_binary
    total_strat_return = np.prod(1 + strategy_returns) - 1
    sharpe_ratio = (strategy_returns.mean() / (strategy_returns.std() + 1e-8)) * np.sqrt(252)

    metrics = {
        "Cluster": f"GlobalCluster_{cluster_id}",
        "Risk Profile": risk_level.capitalize(),
        "Model Chosen": best_name,
        "Candidates Fit": ", ".join(n for n in fitted if n != "Ensemble"),
        "Candidate Val AUCs": individual_aucs,
        "Ensemble Members (val AUC > 0.5)": ensemble_members,
        "Val AUC (selection basis)": round(best_val_auc, 4),
        "AUC-ROC": round(roc_auc_score(y_test, test_probs), 4) if y_test.nunique() > 1 else float("nan"),
        "Precision": round(precision_score(y_test, preds_binary, zero_division=0), 4),
        "Accuracy": round(accuracy_score(y_test, preds_binary), 4),
        "Cumulative Return": f"{round(total_strat_return * 100, 2)}%",
        "Sharpe Ratio": round(sharpe_ratio, 2),
        "Train Time (s, all candidates)": round(sum(timings.values()), 2),
    }
    return best_model, metrics, dynamic_cutoff


# ---------------------------------------------------------------------------
# 6. Per-stock scoring -- what the portfolio allocation engine actually needs
# ---------------------------------------------------------------------------
def score_individual_stocks(indicator_df: pd.DataFrame, cluster_map: pd.DataFrame,
                             cluster_models: dict, cluster_cutoffs: dict) -> pd.DataFrame:
    """Applies each cluster's winning model back onto its members' own
    (non-averaged) rows, one ticker's chronological slice at a time --
    important for the LSTM/ensemble candidates, which read row order as a
    sliding window; interleaving multiple tickers' rows would silently
    build windows that jump between stocks."""
    df = indicator_df.merge(cluster_map, left_on="Ticker", right_index=True)
    scored = []

    for cid, sub in df.groupby("Cluster"):
        if cid not in cluster_models:
            continue
        model = cluster_models[cid]
        cutoff = cluster_cutoffs[cid]

        for ticker, tsub in sub.groupby("Ticker"):
            tsub = tsub.sort_index()
            probs = model.predict_proba(tsub[FEATURE_COLS])[:, 1]

            result = tsub[["Ticker", "Sector"]].copy()
            result["Cluster"] = cid
            result["Bullish_Probability"] = probs
            result["Signal"] = (probs >= cutoff).astype(int)
            scored.append(result)

    return pd.concat(scored, axis=0).reset_index(names="Date")


# ---------------------------------------------------------------------------
# 7. Efficiency benchmark -- SAME 4-candidate pool per ticker as the
#    clustered path uses per cluster, so "speedup" reflects grouping
#    strategy alone, not an unequal amount of modeling work.
# ---------------------------------------------------------------------------
def benchmark_no_clustering_baseline(indicators_with_target: pd.DataFrame, risk_level: str) -> float:
    risk_cfg = RISK_PROFILES[risk_level]
    total_time = 0.0
    for ticker, sub in indicators_with_target.groupby("Ticker"):
        sub = sub.sort_index()
        X, y, returns = sub[FEATURE_COLS], sub["Target"], sub["Future_5D_Return"]
        X_tr, y_tr, X_val, y_val, X_test, y_test, ret_test = _time_split(X, y, returns)
        for fitter in CANDIDATE_FITTERS.values():
            t0 = time.time()
            try:
                fitter(X_tr, y_tr, X_val, y_val, risk_cfg)
            except Exception:
                pass
            total_time += time.time() - t0
    return total_time


# ---------------------------------------------------------------------------
# 8. End-to-end pipeline -- one-time PREPARE (fetch, indicators, clustering)
#    plus a cheap per-risk-level step (labeling, training, scoring).
# ---------------------------------------------------------------------------
def prepare_global_clusters(train_frac: float = CLUSTER_TRAIN_FRAC, return_latest: bool = False):
    """Run this ONCE. Clustering is fit only on the chronological training
    slice (a single date cutoff shared by every ticker), so cluster
    membership never sees validation/test-period data."""
    raw = fetch_all_sectors_data()
    indicators = compute_common_indicators(raw).sort_index()

    unique_dates = pd.Index(indicators.index.unique()).sort_values()
    if len(unique_dates) < 3:
        raise ValueError("Not enough historical dates for chronological clustering split.")
    train_end_pos = max(1, int(len(unique_dates) * train_frac) - 1)
    train_end_date = unique_dates[train_end_pos]
    train_indicators = indicators.loc[indicators.index <= train_end_date]

    cluster_input = build_cluster_input_features(train_indicators)
    cluster_map, k = choose_k_and_cluster(cluster_input)

    if return_latest:
        # Same features, but INCLUDING the newest rows whose forward return
        # isn't known yet -- used only for scoring the current signal.
        latest = compute_common_indicators(raw, require_label=False).sort_index()
        return indicators, cluster_map, k, latest
    return indicators, cluster_map, k


def run_global_clustering_pipeline(indicators: pd.DataFrame, cluster_map: pd.DataFrame, k: int,
                                    risk_level: str = "balanced", run_benchmark: bool = True):
    """run_benchmark=False skips the per-ticker no-clustering comparison
    (it trains 4 models x every ticker and dominates runtime) -- the
    signal-export script turns it off; the default keeps old behavior."""
    indicators_with_target = add_target_column(indicators, risk_level)
    rep_by_cluster = build_cluster_representative_data(indicators, cluster_map, risk_level=risk_level)

    metrics_rows = []
    cluster_models, cluster_cutoffs = {}, {}
    clustering_train_time = 0.0

    for cid, rep_df in rep_by_cluster.items():
        X, y, returns = rep_df[FEATURE_COLS], rep_df["Target"], rep_df["Future_5D_Return"]
        model, metrics, cutoff = train_best_model_for_cluster(X, y, returns, cid, risk_level)
        clustering_train_time += metrics["Train Time (s, all candidates)"]
        metrics_rows.append(metrics)
        cluster_models[cid] = model
        cluster_cutoffs[cid] = cutoff

    summary = pd.DataFrame(metrics_rows)
    summary.insert(0, "k_clusters", k)

    per_stock_scores = score_individual_stocks(indicators, cluster_map, cluster_models, cluster_cutoffs)

    if run_benchmark:
        baseline_time = benchmark_no_clustering_baseline(indicators_with_target, risk_level)
        n_tickers = indicators["Ticker"].nunique()
        print(f"\n[{risk_level.upper()}] Training time -- clustering-based: {clustering_train_time:.1f}s "
              f"(4 candidates x {k} clusters) | no-clustering baseline: {baseline_time:.1f}s "
              f"(4 candidates x {n_tickers} tickers) | speedup: {baseline_time / clustering_train_time:.2f}x")
    else:
        print(f"[{risk_level.upper()}] Trained {k} clusters in {clustering_train_time:.1f}s "
              f"(4 candidates per cluster)")

    return summary, per_stock_scores, cluster_models, cluster_cutoffs
