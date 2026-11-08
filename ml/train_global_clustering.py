"""Train the global (cross-sector) clustering models for all three risk levels
and export the CURRENT per-stock signals for the backend to serve.

Run from the repo root:

    python ml/train_global_clustering.py                # normal run
    python ml/train_global_clustering.py --retune       # force a fresh hyperparameter search first
    python ml/train_global_clustering.py --benchmark    # also time the no-clustering baseline (slow)

Needs internet (yfinance). Writes:
    backend/app/signals/models/global_clustering_signals.json   <- what the API reads (commit this)
    ml/global_clustering/last_run_results.csv                   <- per-cluster metrics (git-ignored)
    ml/global_clustering/tuned_params.json                      <- only when tuning runs (commit this)
"""

import argparse
import os
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd  # noqa: E402

from ml.global_clustering import pipeline  # noqa: E402
from ml.global_clustering.export_signals import build_payload, build_risk_block, write_payload  # noqa: E402
from ml.global_clustering.tuning import TUNED_PARAMS_PATH, tune_all_models  # noqa: E402

RISK_LEVELS = ["conservative", "balanced", "aggressive"]
DEFAULT_OUTPUT = REPO_ROOT / "backend" / "app" / "signals" / "models" / "global_clustering_signals.json"
DEFAULT_RESULTS_CSV = REPO_ROOT / "ml" / "global_clustering" / "last_run_results.csv"


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--retune", action="store_true", help="re-run hyperparameter tuning even if tuned_params.json exists")
    p.add_argument("--benchmark", action="store_true", help="also time the per-ticker no-clustering baseline (slow)")
    p.add_argument("--output", default=str(DEFAULT_OUTPUT), help="where to write the signals JSON")
    p.add_argument("--results-csv", default=str(DEFAULT_RESULTS_CSV), help="where to write per-cluster metrics")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    print("=" * 90)
    print("GLOBAL (CROSS-SECTOR) CLUSTERING -- 4-MODEL AUTO SELECTION + ENSEMBLE -> SIGNALS EXPORT")
    print("=" * 90)

    if args.retune or not os.path.exists(TUNED_PARAMS_PATH):
        print("\nRunning hyperparameter tuning (walk-forward CV on the pooled dataset). "
              "This takes a few minutes; the result is cached in tuned_params.json.\n")
        tune_all_models()
        pipeline.reload_tuned_params()  # make THIS run use the fresh params
        print()

    # Fetch + indicators + clustering happen ONCE -- none of it depends on risk level.
    indicators, cluster_map, k, latest = pipeline.prepare_global_clusters(return_latest=True)
    print(f"\nTicker -> Cluster assignment (same for every risk level, k={k}):")
    print(cluster_map.to_string())

    summaries, blocks = [], {}
    for risk in RISK_LEVELS:
        summary, _per_stock_history, models, cutoffs = pipeline.run_global_clustering_pipeline(
            indicators, cluster_map, k, risk_level=risk, run_benchmark=args.benchmark
        )
        summaries.append(summary)
        blocks[risk] = build_risk_block(
            summary, latest, cluster_map, models, cutoffs, pipeline.RISK_PROFILES[risk]
        )

    full_summary = pd.concat(summaries, ignore_index=True)

    print("\n" + "=" * 90)
    print("PER-CLUSTER RESULTS (winning model/ensemble auto-selected on validation AUC)")
    print("=" * 90)
    print(full_summary.to_string(index=False))

    os.makedirs(os.path.dirname(args.results_csv), exist_ok=True)
    full_summary.to_csv(args.results_csv, index=False)

    payload = build_payload(blocks, k=k, n_tickers=len(cluster_map))
    out_path = write_payload(payload, args.output)

    print("\n" + "=" * 90)
    print(f"CURRENT SIGNALS (balanced), newest price date scored: {payload['as_of']}")
    print("=" * 90)
    rows = [
        {"Ticker": t, **{key: s[key] for key in ("sector", "cluster", "model", "bullish_probability", "signal", "as_of")}}
        for t, s in blocks["balanced"]["signals"].items()
    ]
    print(pd.DataFrame(rows).sort_values("bullish_probability", ascending=False).to_string(index=False))

    print(f"\nSignals JSON  -> {out_path}")
    print(f"Metrics CSV   -> {args.results_csv}")
    return payload


if __name__ == "__main__":
    main()
