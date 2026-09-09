"""
Offline training script for sector-specialized classifiers (FR-3.2).
NOT run at request time — run manually / via a scheduled job to (re)generate
the .pkl files in app/signals/models/.

Reminder: use Purged Group TimeSeries Split for cross-validation to avoid
lookahead bias (see Advances in Financial Machine Learning, Lopez de Prado).
"""

if __name__ == "__main__":
    # TODO: load training dataset (from external storage, not committed to git),
    # engineer features via app.data.indicators, train LightGBM/XGBoost per sector,
    # save artifacts to app/signals/models/<sector>_model.pkl
    raise NotImplementedError
