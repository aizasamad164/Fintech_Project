import time
import numpy as np
import pandas as pd
import ta
import yfinance as yf

from sklearn.ensemble import RandomForestRegressor, VotingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor

from config import RISK_PROFILES
from sentiment_engine import get_ticker_sentiment

BASE_FEATURES = [
    "Daily_Return", "RVOL", "Norm_ATR", "SMA_Ratio",
    "RSI", "MACD_HIST", "PPO", "Stoch_K", "BB_Width",
    "Lag1", "Lag2", "Lag3", "Lag4",
    "SPY_Return", "VIX_Return", "Rel_SPY_Perf",
    "News_Sentiment"
]


def fetch_macro_data(start_date: str, end_date: str) -> pd.DataFrame:
    macro = yf.download(["SPY", "^VIX"], start=start_date, end=end_date, progress=False, timeout=10)["Close"]
    if hasattr(macro.index, "tz") and macro.index.tz is not None:
        macro.index = macro.index.tz_localize(None)

    macro_df = pd.DataFrame(index=macro.index)
    macro_df["SPY_Return"] = macro["SPY"].pct_change()
    macro_df["VIX_Return"] = macro["^VIX"].pct_change()
    macro_df["SPY_SMA50"] = macro["SPY"] / macro["SPY"].rolling(50).mean()
    return macro_df.fillna(1.0)


def compute_advanced_features(df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    start_str = df.index.min().strftime("%Y-%m-%d")
    end_str = df.index.max().strftime("%Y-%m-%d")
    macro_df = fetch_macro_data(start_str, end_str)

    out = []
    for ticker, sub in df.groupby("Ticker"):
        s = sub.copy().sort_index()
        if hasattr(s.index, "tz") and s.index.tz is not None:
            s.index = s.index.tz_localize(None)

        s = s.join(macro_df, how="left").fillna(0)
        if isinstance(s.columns, pd.MultiIndex):
            s.columns = [col[0] if isinstance(col, tuple) else col for col in s.columns]

        s["Future_5D_Return"] = s["Close"].shift(-5) / s["Close"] - 1.0
        s["Daily_Return"] = s["Close"].pct_change()
        s["Rel_SPY_Perf"] = s["Daily_Return"] - s["SPY_Return"]

        vol_sma = ta.trend.sma_indicator(s["Volume"], window=20)
        s["RVOL"] = s["Volume"] / (vol_sma + 1e-8)

        atr = ta.volatility.average_true_range(s["High"], s["Low"], s["Close"], window=14)
        s["Norm_ATR"] = atr / s["Close"]

        s["SMA_Ratio"] = s["Close"] / ta.trend.sma_indicator(s["Close"], window=50)
        s["RSI"] = ta.momentum.rsi(s["Close"], window=14)

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

        s["News_Sentiment"] = get_ticker_sentiment(ticker)

        s["VWAP"] = (s["Volume"] * (s["High"] + s["Low"] + s["Close"]) / 3).cumsum() / (s["Volume"].cumsum() + 1e-8)
        s["VWAP_Distance"] = (s["Close"] - s["VWAP"]) / (s["VWAP"] + 1e-8)

        log_hl = np.log(s["High"] / (s["Low"] + 1e-8))
        s["Parkinson_Vol"] = np.sqrt((1 / (4 * np.log(2))) * (log_hl ** 2)).rolling(14).mean()

        s["ADX"] = ta.trend.adx(s["High"], s["Low"], s["Close"], window=14)

        rsi = s["RSI"]
        s["RSI_ZScore"] = (rsi - rsi.rolling(50).mean()) / (rsi.rolling(50).std() + 1e-8)
        s["Price_Vol_Corr"] = s["Close"].pct_change().rolling(14).corr(s["Volume"].pct_change())

        s["Sentiment_MA3"] = s["News_Sentiment"].rolling(3, min_periods=1).mean()
        s["Sentiment_MA10"] = s["News_Sentiment"].rolling(10, min_periods=1).mean()
        s["Sentiment_Momentum"] = s["Sentiment_MA3"] - s["Sentiment_MA10"]

        out.append(s)

    full = pd.concat(out, axis=0)
    all_features = BASE_FEATURES + [
        "VWAP_Distance", "Parkinson_Vol", "ADX",
        "RSI_ZScore", "Price_Vol_Corr", "Sentiment_Momentum"
    ]

    clean = full.dropna(subset=all_features + ["Future_5D_Return"]).copy()
    return clean, all_features


def calibrate_cross_sectional_probabilities(df_predictions: pd.DataFrame) -> pd.DataFrame:
    df = df_predictions.copy()
    df["Pred_ZScore"] = df.groupby(df.index)["Risk_Adj_Score"].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-8)
    )
    df["Bullish_Probability"] = 1 / (1 + np.exp(-1.2 * df["Pred_ZScore"]))
    return df


def apply_stop_loss_and_holding_rules(df: pd.DataFrame, max_holding_days=20, stop_loss_pct=0.08) -> pd.DataFrame:
    """Applies a trailing stop-loss (-8%) and hard 20-day holding window exit filter."""
    df = df.copy().sort_index()

    out_dfs = []
    for ticker, sub in df.groupby("Ticker"):
        s = sub.copy()
        signals = s["Raw_Signal"].values
        returns = s["Future_5D_Return"].values
        final_signals = np.zeros(len(s), dtype=int)

        in_position = False
        holding_counter = 0
        peak_return = 0.0
        cum_return = 0.0

        for i in range(len(s)):
            raw_sig = signals[i]

            if not in_position:
                if raw_sig == 1:
                    in_position = True
                    holding_counter = 1
                    cum_return = returns[i]
                    peak_return = cum_return
                    final_signals[i] = 1
            else:
                holding_counter += 1
                cum_return = (1 + cum_return) * (1 + returns[i]) - 1
                peak_return = max(peak_return, cum_return)
                drawdown = cum_return - peak_return

                if drawdown <= -stop_loss_pct or holding_counter >= max_holding_days or raw_sig == 0:
                    in_position = False
                    final_signals[i] = 0
                    holding_counter = 0
                else:
                    final_signals[i] = 1

        s["Signal"] = final_signals
        out_dfs.append(s)

    return pd.concat(out_dfs, axis=0)


def train_sector_ensemble_regressor(df_sector: pd.DataFrame, feature_cols: list, sector_name: str, risk_level: str):
    unique_dates = np.array(sorted(df_sector.index.unique()))
    n_dates = len(unique_dates)

    train_end_idx = int(n_dates * 0.60)
    val_end_idx = int(n_dates * 0.80)

    X_train = df_sector.loc[df_sector.index.isin(unique_dates[:train_end_idx]), feature_cols]
    y_train = df_sector.loc[df_sector.index.isin(unique_dates[:train_end_idx]), "Future_5D_Return"]

    X_val = df_sector.loc[df_sector.index.isin(unique_dates[train_end_idx:val_end_idx]), feature_cols]
    y_val = df_sector.loc[df_sector.index.isin(unique_dates[train_end_idx:val_end_idx]), "Future_5D_Return"]

    X_test = df_sector.loc[df_sector.index.isin(unique_dates[val_end_idx:]), feature_cols]
    y_test = df_sector.loc[df_sector.index.isin(unique_dates[val_end_idx:]), "Future_5D_Return"]
    test_df = df_sector.loc[df_sector.index.isin(unique_dates[val_end_idx:])].copy()

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    lgb = LGBMRegressor(n_estimators=100, learning_rate=0.03, max_depth=5, random_state=42, verbose=-1)
    xgb = XGBRegressor(n_estimators=100, learning_rate=0.03, max_depth=5, random_state=42, verbosity=0)
    rf = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)

    ensemble = VotingRegressor(estimators=[("lgb", lgb), ("xgb", xgb), ("rf", rf)])

    t0 = time.time()
    ensemble.fit(X_train_scaled, y_train)
    train_time = time.time() - t0

    val_preds = ensemble.predict(X_val_scaled)
    test_preds = ensemble.predict(X_test_scaled)

    test_df["Predicted_Return"] = test_preds
    
    # Risk-Adjusted Prediction Score
    test_df["Risk_Adj_Score"] = test_df["Predicted_Return"] / (test_df["Norm_ATR"] + 1e-8)
    
    # Probability Calibration & Ranking
    test_df = calibrate_cross_sectional_probabilities(test_df)
    test_df["Rank"] = test_df.groupby(test_df.index)["Risk_Adj_Score"].rank(ascending=False, pct=True)

    NEUTRAL_THRESHOLD = 0.005
    macro_filter = (test_df["SPY_SMA50"] >= 0.98)
    test_df["Raw_Signal"] = ((test_df["Rank"] <= 0.20) & (test_df["Predicted_Return"] > NEUTRAL_THRESHOLD) & macro_filter).astype(int)

    test_df = apply_stop_loss_and_holding_rules(test_df)

    test_returns = test_df["Future_5D_Return"] * test_df["Signal"]
    total_test_return = np.prod(1 + test_returns) - 1
    sharpe_ratio = (test_returns.mean() / (test_returns.std() + 1e-8)) * np.sqrt(252 / 5)

    metrics = {
        "Sector": sector_name,
        "Risk Profile": risk_level.capitalize(),
        "Model": "Ensemble_RiskAdj",
        "Val R2": round(r2_score(y_val, val_preds), 4),
        "Test R2": round(r2_score(y_test, test_preds), 4),
        "Test MAE": round(mean_absolute_error(y_test, test_preds), 4),
        "Test MSE": round(mean_squared_error(y_test, test_preds), 4),
        "Test Return": f"{round(total_test_return * 100, 2)}%",
        "Sharpe Ratio": round(sharpe_ratio, 2),
        "Trade Rate": f"{round((test_df['Signal'].sum() / len(test_df)) * 100, 2)}%",
        "Train Time (s)": round(train_time, 2),
    }

    # Full Dataset Scoring Output
    X_full_scaled = scaler.transform(df_sector[feature_cols])
    scored_df = df_sector[["Ticker", "Norm_ATR", "Future_5D_Return"]].copy()
    scored_df["Sector"] = sector_name
    scored_df["Predicted_Return"] = ensemble.predict(X_full_scaled)
    scored_df["Risk_Adj_Score"] = scored_df["Predicted_Return"] / (scored_df["Norm_ATR"] + 1e-8)
    scored_df = calibrate_cross_sectional_probabilities(scored_df)
    scored_df["Rank"] = scored_df.groupby(scored_df.index)["Risk_Adj_Score"].rank(ascending=False, pct=True)

    full_macro_filter = (df_sector["SPY_SMA50"] >= 0.98)
    scored_df["Raw_Signal"] = ((scored_df["Rank"] <= 0.20) & (scored_df["Predicted_Return"] > NEUTRAL_THRESHOLD) & full_macro_filter).astype(int)
    scored_df = apply_stop_loss_and_holding_rules(scored_df)

    return ensemble, scaler, metrics, scored_df.reset_index(names="Date")