"""
FreightIQ ML Training Pipeline
==============================
CLI and module to run the complete training & chronological evaluation pipeline:
1. Ingest raw data (from synthetic generator, DB, or CSV)
2. Clean and engineer features with strict time-series integrity
3. Split chronologically (earlier train dates vs later test dates)
4. Train baseline models (Naive, Moving Average)
5. Train ML models (Random Forest, Gradient Boosting, XGBoost if available)
6. Train Champion FreightForecastingEnsemble
7. Evaluate all models on out-of-time test set (MAE, RMSE, MAPE)
8. Persist champion model and update Model Registry

Usage:
    python -m app.ml.train
"""
from __future__ import annotations
import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
import pandas as pd

from app.ml.baselines import MovingAverageBaseline, NaiveHistoricalBaseline
from app.ml.dataset_generator import generate_full_synthetic_dataset
from app.ml.evaluation import compute_all_metrics, format_benchmark_table
from app.ml.model import (
    FreightForecastingEnsemble,
    GradientBoostingFreightModel,
    RandomForestFreightModel,
    XGBoostFreightModel,
)
from app.ml.preprocessing import FEATURE_NAMES, process_tabular_dataset, train_test_chronological_split
from app.ml.registry import get_model_registry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("FreightIQ.ML.Train")


def run_training_pipeline(
    raw_df: Optional[pd.DataFrame] = None,
    test_ratio: float = 0.20,
    save_artifacts: bool = True,
) -> Dict[str, Any]:
    """Execute the full end-to-end training and evaluation pipeline."""
    logger.info("Step 1/7: Acquiring raw time-series dataset...")
    if raw_df is None or raw_df.empty:
        logger.info("Generating full deterministic synthetic dataset...")
        raw_df = generate_full_synthetic_dataset(weeks=156, seed=42)

    logger.info(f"Loaded {len(raw_df)} raw records across routes.")

    logger.info("Step 2/7: Cleaning and engineering features...")
    feat_df, X, y = process_tabular_dataset(raw_df)
    logger.info(f"Engineered feature matrix: X shape {X.shape}, y shape {y.shape}")

    logger.info("Step 3/7: Splitting data strictly chronologically (no future leakage)...")
    X_train, y_train, X_test, y_test, train_meta, test_meta = train_test_chronological_split(
        feat_df, X, y, test_ratio=test_ratio
    )
    train_dates = pd.to_datetime(train_meta["date"])
    test_dates = pd.to_datetime(test_meta["date"])
    logger.info(
        f"Train window: {train_dates.min().strftime('%Y-%m-%d')} to {train_dates.max().strftime('%Y-%m-%d')} ({len(X_train)} samples)"
    )
    logger.info(
        f"Test window:  {test_dates.min().strftime('%Y-%m-%d')} to {test_dates.max().strftime('%Y-%m-%d')} ({len(X_test)} samples)"
    )

    benchmarks: Dict[str, Dict[str, float]] = {}

    # 4. Train Baselines
    logger.info("Step 4/7: Training and evaluating baseline models...")
    # Naive Baseline
    naive = NaiveHistoricalBaseline().fit(train_meta, y_train)
    pred_naive = naive.predict(test_meta, X_test)
    benchmarks["Naive Historical (Lag-1)"] = compute_all_metrics(y_test, pred_naive)

    # Moving Average Baseline
    ma = MovingAverageBaseline(window=4).fit(train_meta, y_train)
    pred_ma = ma.predict(test_meta, X_test)
    benchmarks["Moving Average (4-Week)"] = compute_all_metrics(y_test, pred_ma)

    # 5. Train Individual ML Models
    logger.info("Step 5/7: Training individual ML models...")
    # Random Forest
    rf = RandomForestFreightModel().fit(X_train, y_train)
    pred_rf = rf.predict(X_test)
    benchmarks["Random Forest"] = compute_all_metrics(y_test, pred_rf)

    # Gradient Boosting
    gbm = GradientBoostingFreightModel().fit(X_train, y_train)
    pred_gbm = gbm.predict(X_test)
    benchmarks["Gradient Boosting"] = compute_all_metrics(y_test, pred_gbm)

    # XGBoost if available
    xgb_model = XGBoostFreightModel()
    if xgb_model.is_available:
        xgb_model.fit(X_train, y_train)
        pred_xgb = xgb_model.predict(X_test)
        benchmarks["XGBoost"] = compute_all_metrics(y_test, pred_xgb)
    else:
        logger.info("XGBoost library not installed; skipped.")

    # 6. Train Champion Blended Ensemble
    logger.info("Step 6/7: Training Champion Blended Ensemble...")
    ensemble = FreightForecastingEnsemble()
    ensemble.fit(X_train, y_train)
    pred_ensemble = ensemble.predict_point(X_test)
    champion_metrics = compute_all_metrics(y_test, pred_ensemble)
    benchmarks["FreightIQ Champion Ensemble"] = champion_metrics

    # Retrain champion on full dataset for maximum deployment accuracy
    logger.info("Refitting Champion Ensemble on full available dataset for deployment...")
    champion_deploy = FreightForecastingEnsemble()
    champion_deploy.fit(X, y)
    champion_deploy.metrics = champion_metrics

    # 7. Print Comparative Table and Persist
    logger.info("Step 7/7: Model Benchmarking & Persistence...")
    table_str = format_benchmark_table(benchmarks)
    print("\n" + "=" * 80)
    print("      FREIGHTIQ TIME-SERIES FORECASTING BENCHMARK (CHRONOLOGICAL SPLIT)")
    print("=" * 80)
    print(table_str)
    print("=" * 80)
    print(f"[*] Champion Ensemble Out-of-Time MAE: ${champion_metrics['mae']:.3f}/MT")
    print(f"[*] Champion Ensemble Out-of-Time RMSE: ${champion_metrics['rmse']:.3f}/MT")
    print(f"[*] Champion Ensemble Out-of-Time MAPE: {champion_metrics['mape_pct']:.2f}%")
    print(f"[*] Champion Ensemble Out-of-Time R²:   {champion_metrics['r2']:.4f}")
    print("=" * 80 + "\n")

    if save_artifacts:
        champion_deploy.save()
        registry = get_model_registry()
        registry.register_training_run(
            active_model_name="FreightForecastingEnsemble",
            champion_metrics=champion_metrics,
            benchmarks=benchmarks,
            training_samples=len(X),
            features=FEATURE_NAMES,
        )
        logger.info("Champion model and Model Registry successfully persisted.")

    return {
        "benchmarks": benchmarks,
        "champion_metrics": champion_metrics,
        "training_samples": len(X),
        "test_samples": len(X_test),
        "model": champion_deploy,
    }


def main():
    parser = argparse.ArgumentParser(description="FreightIQ ML Forecasting Engine Trainer")
    parser.add_argument("--test-ratio", type=float, default=0.20, help="Out-of-time test ratio")
    parser.add_argument("--no-save", action="store_true", help="Do not persist model artifacts")
    args = parser.parse_args()

    run_training_pipeline(
        test_ratio=args.test_ratio,
        save_artifacts=not args.no_save,
    )


if __name__ == "__main__":
    main()
