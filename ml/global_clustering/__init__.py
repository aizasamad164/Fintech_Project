"""Cross-sector clustering + auto model selection (LightGBM / RandomForest /
XGBoost / LSTM / weighted ensemble per cluster).

    pipeline.py        data -> indicators -> clusters -> per-cluster models -> per-stock scores
    tuning.py          one-off walk-forward hyperparameter search (writes tuned_params.json)
    export_signals.py  turns the trained pipeline's CURRENT scores into the JSON the backend serves

Entry point: ml/train_global_clustering.py
"""
