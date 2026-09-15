"""
FreightIQ ML Evaluation Script
==============================
Evaluates the persisted champion model and baselines on out-of-time chronological data.
Computes:
- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- MAPE (Mean Absolute Percentage Error)
- R² Score

Usage:
    python -m app.ml.evaluate
    python -m app.ml.evaluate --benchmark-all
"""
from __future__ import annotations
import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from app.ml.baselines import MovingAverageBaseline, NaiveHistoricalBaseline
from app.ml.dataset_generator import generate_full_synthetic_dataset
from app.ml.evaluation import compute_all_metrics, format_benchmark_table
from app.ml.model import (
    FreightForecastingEnsemble,
    GradientBoostingFreightModel,
    RandomForestFreightModel,
    XGBoostFreightModel,
    get_model,
)
from app.ml.preprocessing import process_tabular_dataset, train_test_chronological_split
from app.ml.registry import get_model_registry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FreightIQ.ML.Evaluate")


def run_evaluation(test_ratio: float = 0.20, benchmark_all: bool = False) -> Dict[str, Any]:
    logger.info("Generating evaluation dataset...")
    df = generate_full_synthetic_dataset(weeks=156, seed=42)
    feat_df, X, y = process_tabular_dataset(df)

    logger.info(f"Chronological split at test_ratio={test_ratio:.2f}...")
    X_train, y_train, X_test, y_test, train_meta, test_meta = train_test_chronological_split(
        feat_df, X, y, test_ratio=test_ratio
    )

    results: Dict[str, Dict[str, float]] = {}

    # 1. Naive Historical Baseline (Lag-1)
    naive = NaiveHistoricalBaseline().fit(train_meta, y_train)
    results["Naive Historical (Lag-1)"] = compute_all_metrics(y_test, naive.predict(test_meta, X_test))

    # 2. Moving Average Baseline (4-Week)
    ma = MovingAverageBaseline(window=4).fit(train_meta, y_train)
    results["Moving Average (4-Week)"] = compute_all_metrics(y_test, ma.predict(test_meta, X_test))

    if benchmark_all:
        logger.info("Refitting individual ML models (RF, GBM) for benchmark...")
        rf = RandomForestFreightModel().fit(X_train, y_train)
        results["Random Forest"] = compute_all_metrics(y_test, rf.predict(X_test))

        gbm = GradientBoostingFreightModel().fit(X_train, y_train)
        results["Gradient Boosting"] = compute_all_metrics(y_test, gbm.predict(X_test))

        xgb = XGBoostFreightModel()
        if xgb.is_available:
            xgb.fit(X_train, y_train)
            results["XGBoost"] = compute_all_metrics(y_test, xgb.predict(X_test))

    # 3. Evaluated Champion Model from Disk
    logger.info("Loading trained champion ensemble from disk...")
    champion = get_model()
    if champion.is_trained:
        pred_champ = champion.predict_point(X_test)
        results["FreightIQ Champion Ensemble"] = compute_all_metrics(y_test, pred_champ)
    else:
        logger.warning("Champion model not trained on disk. Refitting...")
        champion.fit(X_train, y_train)
        pred_champ = champion.predict_point(X_test)
        results["FreightIQ Champion Ensemble"] = compute_all_metrics(y_test, pred_champ)

    print("\n" + "=" * 80)
    print("        FREIGHT FORECASTING EVALUATION REPORT (CHRONOLOGICAL SPLIT)")
    print("=" * 80)
    print(format_benchmark_table(results))
    print("=" * 80 + "\n")

    return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate FreightIQ Forecasting Models")
    parser.add_argument("--test-ratio", type=float, default=0.20, help="Fraction for out-of-time test")
    parser.add_argument("--benchmark-all", action="store_true", help="Re-fit RF and GBM during evaluation")
    args = parser.parse_args()
    run_evaluation(test_ratio=args.test_ratio, benchmark_all=args.benchmark_all)


if __name__ == "__main__":
    main()
