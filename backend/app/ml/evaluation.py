"""
FreightIQ ML Evaluation Engine
==============================
Metrics and benchmarking routines for chronological time-series evaluation:
- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- MAPE (Mean Absolute Percentage Error)
- R² Score
Compares Naive Baseline, Moving Average Baseline, Random Forest, Gradient Boosting, and Ensemble.
"""
from __future__ import annotations
from typing import Any, Dict, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def compute_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Error."""
    return float(mean_absolute_error(y_true, y_pred))


def compute_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root Mean Squared Error."""
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def compute_mape(y_true: np.ndarray, y_pred: np.ndarray, epsilon: float = 1e-5) -> float:
    """
    Mean Absolute Percentage Error (returned as percentage, e.g. 5.25 for 5.25%).
    Clamps denom to prevent division by near-zero.
    """
    y_true_arr = np.asarray(y_true, dtype=np.float64)
    y_pred_arr = np.asarray(y_pred, dtype=np.float64)
    denom = np.maximum(np.abs(y_true_arr), epsilon)
    mape = np.mean(np.abs((y_true_arr - y_pred_arr) / denom)) * 100.0
    return float(round(mape, 2))


def compute_all_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute standard metrics bundle."""
    mae = compute_mae(y_true, y_pred)
    rmse = compute_rmse(y_true, y_pred)
    mape = compute_mape(y_true, y_pred)
    r2 = float(r2_score(y_true, y_pred))
    return {
        "mae": round(mae, 3),
        "rmse": round(rmse, 3),
        "mape_pct": round(mape, 2),
        "r2": round(r2, 4),
    }


def format_benchmark_table(results: Dict[str, Dict[str, float]]) -> str:
    """Format benchmark results dictionary into a clean markdown table."""
    headers = ["Model", "MAE ($/MT)", "RMSE ($/MT)", "MAPE (%)", "R² Score"]
    rows = []
    for model_name, metrics in results.items():
        rows.append(
            f"| {model_name:<26} | {metrics['mae']:>10.3f} | {metrics['rmse']:>11.3f} | {metrics['mape_pct']:>8.2f}% | {metrics['r2']:>8.4f} |"
        )

    divider = "|:---------------------------|-----------:|------------:|---------:|---------:|"
    table = [
        f"| {' | '.join(headers)} |",
        divider,
        *rows,
    ]
    return "\n".join(table)
