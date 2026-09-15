"""
FreightIQ Baseline Forecasting Models
=====================================
Statistically grounded baseline models for dry bulk freight rate benchmarking:
1. Naive Historical Baseline: predicts the most recent observed rate (persistence model)
2. Moving Average Baseline: predicts the 4-week moving average of historical rates
"""
from __future__ import annotations
from typing import Dict, Optional
import numpy as np
import pandas as pd


class NaiveHistoricalBaseline:
    """
    Persistence / Naive Baseline:
    Predicts the last observed rate for each route/vessel combination.
    """

    def __init__(self):
        self.last_known_rates: Dict[tuple[str, str, str], float] = {}
        self.global_mean: float = 15.0

    def fit(self, meta_df: pd.DataFrame, y: np.ndarray) -> "NaiveHistoricalBaseline":
        """Record the latest rate observed in the training set per route."""
        df = meta_df.copy()
        df["target"] = y
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        self.global_mean = float(np.mean(y)) if len(y) > 0 else 15.0

        for key, grp in df.groupby(["origin", "destination", "vessel_class"]):
            origin, dest, vc = key
            self.last_known_rates[(origin, dest, vc)] = float(grp["target"].iloc[-1])

        return self

    def predict(self, meta_df: pd.DataFrame, X: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Predict for test meta_df. If lag_1_rate is present in meta_df, uses actual immediate lag.
        Otherwise falls back to the route's last known training rate.
        """
        preds = []
        for idx, row in meta_df.iterrows():
            if "lag_1_rate" in row and pd.notnull(row["lag_1_rate"]):
                preds.append(float(row["lag_1_rate"]))
            else:
                key = (row["origin"], row["destination"], row["vessel_class"])
                preds.append(self.last_known_rates.get(key, self.global_mean))
        return np.array(preds, dtype=np.float32)


class MovingAverageBaseline:
    """
    Rolling Moving Average Baseline:
    Predicts the k-period rolling average of prior rates.
    """

    def __init__(self, window: int = 4):
        self.window = window
        self.route_means: Dict[tuple[str, str, str], float] = {}
        self.global_mean: float = 15.0

    def fit(self, meta_df: pd.DataFrame, y: np.ndarray) -> "MovingAverageBaseline":
        """Compute training rolling mean and route-level historical averages."""
        df = meta_df.copy()
        df["target"] = y
        self.global_mean = float(np.mean(y)) if len(y) > 0 else 15.0

        for key, grp in df.groupby(["origin", "destination", "vessel_class"]):
            origin, dest, vc = key
            tail = grp["target"].tail(self.window).values
            self.route_means[(origin, dest, vc)] = float(np.mean(tail)) if len(tail) > 0 else self.global_mean

        return self

    def predict(self, meta_df: pd.DataFrame, X: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Predict rolling average. If roll_4_rate is present in meta_df, uses it.
        Otherwise falls back to route-level tail mean.
        """
        preds = []
        for idx, row in meta_df.iterrows():
            if "roll_4_rate" in row and pd.notnull(row["roll_4_rate"]):
                preds.append(float(row["roll_4_rate"]))
            else:
                key = (row["origin"], row["destination"], row["vessel_class"])
                preds.append(self.route_means.get(key, self.global_mean))
        return np.array(preds, dtype=np.float32)
