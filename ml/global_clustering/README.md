# Global (cross-sector) clustering model

Groups the screened stocks from **all sectors** into clusters by behaviour, then for each cluster
trains four candidates (LightGBM, RandomForest, XGBoost, LSTM) plus a weighted ensemble of those that
beat chance, and keeps whichever scores best on **validation** AUC. Probabilities are Platt-calibrated.
Runs for all three risk levels (they differ in the return a stock must reach in 5 trading days to count
as "bullish", and in how selective the cutoff is).

## Run it

From the repo root, in a venv with `pip install -r ml/requirements.txt`:

```bash
python ml/train_global_clustering.py             # tunes once if needed, trains, exports signals
python ml/train_global_clustering.py --retune    # force a fresh hyperparameter search first
python ml/train_global_clustering.py --benchmark # also time the no-clustering baseline (slow)
```

Needs internet (yfinance). Re-run **after changing the ticker universe or risk profiles** in
`backend/app/ml_config.py`, and refresh periodically -- the exported signals are only as fresh as the run.

## What it writes

| File | What | Commit it? |
|---|---|---|
| `backend/app/signals/models/global_clustering_signals.json` | Newest signal per ticker, for each risk level. **This is what the API reads.** | yes |
| `ml/global_clustering/tuned_params.json` | Cached hyperparameter-search result | yes (saves teammates ~5 min) |
| `ml/global_clustering/last_run_results.csv` | Per-cluster metrics from the last run | no (git-ignored) |

## How the backend uses it

`backend/app/signals/global_signals.py` reads the JSON (no torch/lightgbm needed at request time):

```python
from app.signals.global_signals import predict_global_signal, list_global_signals

predict_global_signal("AAPL", risk_level="balanced")
# {"ticker": "AAPL", "signal": "BUY" | "HOLD", "confidence": 0.14, "status": "success", ...}

list_global_signals("balanced", sector="Technology", only_buy=True)   # strongest first
```

Set `GLOBAL_SIGNALS_PATH` to read the file from somewhere else (e.g. a mounted volume).

## Things to know

- `confidence` is a calibrated **probability** of reaching the risk level's 5-day target return, so it is
  usually well below 0.5. It is not on the same scale as `model_loader.predict_ticker_signal`'s heuristic
  confidence (0.55-0.95): rank within one model, don't mix them.
- The model only has BUY / HOLD (no SELL), and only covers tickers that pass the fundamentals screen
  (`max_pe`, `min_profit_margin` per sector in `ml_config.py`). Skipped tickers are printed with the reason.
- The fundamentals screen lives in `pipeline.fetch_screened_sector_data`; the shared
  `backend/app/data/fetcher.py` is untouched.
