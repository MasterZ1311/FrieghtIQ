"""
FreightIQ ML Models
===================
Production-grade forecasting models for dry bulk shipping:
- RandomForestFreightModel: Random Forest regressor with leaf constraints
- GradientBoostingFreightModel: Gradient boosted regression trees
- XGBoostFreightModel: XGBoost regressor (gracefully falls back if not installed)
- QuantileUncertaintyModel: Dual quantile regressors (10th and 90th percentiles)
- FreightForecastingEnsemble: Blended champion ensemble combining GBM, RF, and Ridge
"""
from __future__ import annotations
import importlib.util
import logging
import math
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from app.ml.preprocessing import FEATURE_NAMES, build_single_feature_vector, process_tabular_dataset

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent
MODEL_PATH = MODEL_DIR / "trained_model.pkl"
REGISTRY_PATH = MODEL_DIR / "model_registry.json"


# ─── 1. Random Forest Model ───────────────────────────────────────────────────

class RandomForestFreightModel:
    """Random Forest regressor with depth and leaf regularization."""

    def __init__(self, n_estimators: int = 150, max_depth: int = 10, random_state: int = 42):
        self.rf = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=random_state,
            n_jobs=-1,
        )
        self.is_trained = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RandomForestFreightModel":
        self.rf.fit(X, y)
        self.is_trained = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_trained:
            raise RuntimeError("Model is not trained.")
        return self.rf.predict(X)

    def feature_importances(self) -> np.ndarray:
        if not self.is_trained:
            return np.ones(len(FEATURE_NAMES)) / len(FEATURE_NAMES)
        return self.rf.feature_importances_


# ─── 2. Gradient Boosting Model ───────────────────────────────────────────────

class GradientBoostingFreightModel:
    """Gradient Boosted regression trees."""

    def __init__(
        self,
        n_estimators: int = 200,
        learning_rate: float = 0.08,
        max_depth: int = 4,
        random_state: int = 42,
    ):
        self.gbm = GradientBoostingRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            subsample=0.85,
            random_state=random_state,
            loss="squared_error",
        )
        self.is_trained = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "GradientBoostingFreightModel":
        self.gbm.fit(X, y)
        self.is_trained = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_trained:
            raise RuntimeError("Model is not trained.")
        return self.gbm.predict(X)

    def feature_importances(self) -> np.ndarray:
        if not self.is_trained:
            return np.ones(len(FEATURE_NAMES)) / len(FEATURE_NAMES)
        return self.gbm.feature_importances_


# ─── 3. XGBoost Model (with graceful fallback) ────────────────────────────────

class XGBoostFreightModel:
    """XGBoost regressor wrapper, available if xgboost package is present."""

    def __init__(self, n_estimators: int = 200, learning_rate: float = 0.08, max_depth: int = 4, random_state: int = 42):
        self.is_available = importlib.util.find_spec("xgboost") is not None
        self.model = None
        self.is_trained = False
        if self.is_available:
            try:
                import xgboost as xgb
                self.model = xgb.XGBRegressor(
                    n_estimators=n_estimators,
                    learning_rate=learning_rate,
                    max_depth=max_depth,
                    subsample=0.85,
                    random_state=random_state,
                    verbosity=0,
                )
            except Exception as e:
                logger.warning(f"XGBoost installed but failed to initialize: {e}")
                self.is_available = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "XGBoostFreightModel":
        if not self.is_available or self.model is None:
            logger.info("XGBoost not available; fit skipped.")
            return self
        self.model.fit(X, y)
        self.is_trained = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_available or not self.is_trained:
            raise RuntimeError("XGBoost is not available or not trained.")
        return self.model.predict(X)


# ─── 4. Quantile Uncertainty Model ───────────────────────────────────────────

class QuantileUncertaintyModel:
    """Estimates empirical 10th and 90th percentile bounds via quantile regression."""

    def __init__(self, n_estimators: int = 150, learning_rate: float = 0.08, max_depth: int = 4, random_state: int = 42):
        self.lower_model = GradientBoostingRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            subsample=0.85,
            random_state=random_state,
            loss="quantile",
            alpha=0.10,
        )
        self.upper_model = GradientBoostingRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            subsample=0.85,
            random_state=random_state,
            loss="quantile",
            alpha=0.90,
        )
        self.is_trained = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "QuantileUncertaintyModel":
        self.lower_model.fit(X, y)
        self.upper_model.fit(X, y)
        self.is_trained = True
        return self

    def predict_bounds(self, X: np.ndarray, point_preds: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        if not self.is_trained:
            # Fallback 15% interval
            return point_preds * 0.85, point_preds * 1.15

        low = self.lower_model.predict(X)
        high = self.upper_model.predict(X)

        # Enforce consistency: low <= point <= high
        low = np.minimum(low, point_preds * 0.96)
        high = np.maximum(high, point_preds * 1.04)
        return low, high


# ─── 5. Champion FreightForecastingEnsemble ───────────────────────────────────

class FreightForecastingEnsemble:
    """
    Weighted Ensemble of:
    - 60% Gradient Boosting Regressor
    - 30% Random Forest Regressor
    - 10% Ridge Regressor (L2 regularized linear baseline)
    Provides point estimates, quantile uncertainty intervals, and feature importance drivers.
    """

    def __init__(self):
        self.gbm = GradientBoostingFreightModel()
        self.rf = RandomForestFreightModel()
        self.ridge = Ridge(alpha=2.0)
        self.scaler = StandardScaler()
        self.uncertainty = QuantileUncertaintyModel()
        self.is_trained = False
        self.metrics: Dict[str, float] = {}
        self.training_samples: int = 0
        self.base_rates: Dict[Any, float] = {}

    def fit(self, X: np.ndarray, y: np.ndarray, base_rates: Optional[Dict[Any, float]] = None) -> Dict[str, Any]:
        if base_rates:
            self.base_rates = base_rates

        if len(X) < 30:
            logger.warning(f"Insufficient training samples ({len(X)}); ensemble will use heuristic fallback.")
            return {"trained": False, "samples": len(X)}

        # Fit feature scaler for Ridge
        X_scaled = self.scaler.fit_transform(X)

        # Fit sub-models
        self.ridge.fit(X_scaled, y)
        self.gbm.fit(X, y)
        self.rf.fit(X, y)
        self.uncertainty.fit(X, y)

        self.is_trained = True
        self.training_samples = len(X)
        return {"trained": True, "samples": len(X)}

    def predict_point(self, X: np.ndarray) -> np.ndarray:
        """Predict blended point forecast for 2D feature matrix X."""
        if not self.is_trained:
            raise RuntimeError("Ensemble is not trained.")

        X_scaled = self.scaler.transform(X)
        pred_gbm = self.gbm.predict(X)
        pred_rf = self.rf.predict(X)
        pred_ridge = self.ridge.predict(X_scaled)

        # Weighted blend
        blended = 0.60 * pred_gbm + 0.30 * pred_rf + 0.10 * pred_ridge
        return np.maximum(0.50, blended)

    def predict(self, x: np.ndarray, horizon_days: int = 30) -> Dict[str, Any]:
        """
        Inference on a single 1D feature vector x.
        Returns point forecast, uncertainty bounds scaled with horizon, and confidence score.
        """
        x2d = x.reshape(1, -1)

        if not self.is_trained:
            return self._rule_based_fallback(x, horizon_days)

        point_arr = self.predict_point(x2d)
        point = float(point_arr[0])

        low_arr, high_arr = self.uncertainty.predict_bounds(x2d, point_arr)
        raw_low = float(low_arr[0])
        raw_high = float(high_arr[0])

        # Horizon scaling: uncertainty expands proportional to sqrt(horizon / 30)
        horizon_factor = math.sqrt(max(7, horizon_days) / 30.0)
        spread_low = (point - raw_low) * horizon_factor
        spread_high = (raw_high - point) * horizon_factor

        lower_bound = max(0.5, point - spread_low)
        upper_bound = point + spread_high

        # Confidence percentage (derived from validation metrics or spread)
        spread_pct = (upper_bound - lower_bound) / max(point, 1.0)
        confidence_pct = round(max(55.0, min(95.0, 100.0 - spread_pct * 35.0)), 1)

        return {
            "point": round(point, 2),
            "lower": round(lower_bound, 2),
            "upper": round(upper_bound, 2),
            "confidence_pct": confidence_pct,
        }

    def _rule_based_fallback(self, x: np.ndarray, horizon_days: int = 30) -> Dict[str, Any]:
        """Deterministic heuristic estimate if ML model is untrained."""
        vc_idx = round(float(x[2]) * 3.0)
        origin_idx = round(float(x[0]) * 4.0)

        base_by_class = {0: 18.0, 1: 13.5, 2: 10.5, 3: 7.5}
        origin_premium = {0: 1.0, 1: 2.5, 2: 1.8, 3: 1.5, 4: 0.7}

        base = base_by_class.get(vc_idx, 12.0)
        prem = origin_premium.get(origin_idx, 1.3)
        pred = base * prem

        horizon_factor = math.sqrt(max(7, horizon_days) / 30.0)
        half_width = pred * 0.15 * horizon_factor

        return {
            "point": round(pred, 2),
            "lower": round(max(0.5, pred - half_width), 2),
            "upper": round(pred + half_width, 2),
            "confidence_pct": 60.0,
        }

    def feature_importances(self) -> Dict[str, float]:
        """Blended feature importances from GBM and RF."""
        if not self.is_trained:
            return {f: round(1.0 / len(FEATURE_NAMES), 4) for f in FEATURE_NAMES}

        imp_gbm = self.gbm.feature_importances()
        imp_rf = self.rf.feature_importances()
        blended = 0.65 * imp_gbm + 0.35 * imp_rf
        total = float(np.sum(blended)) or 1.0

        return {
            FEATURE_NAMES[i]: round(float(blended[i] / total), 4)
            for i in range(len(FEATURE_NAMES))
        }

    def save(self, filepath: Path = MODEL_PATH):
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "wb") as f:
            pickle.dump(self, f)
        logger.info(f"Ensemble saved to {filepath}")

    @classmethod
    def load(cls, filepath: Path = MODEL_PATH) -> "FreightForecastingEnsemble":
        if filepath.exists():
            try:
                with open(filepath, "rb") as f:
                    obj = pickle.load(f)
                logger.info(f"Model loaded from {filepath}")
                return obj
            except Exception as e:
                logger.warning(f"Failed to load model from {filepath}: {e}. Initializing fresh instance.")
        return cls()


# Alias for backwards compatibility
FreightRateEnsemble = FreightForecastingEnsemble

# Global singleton
_model: Optional[FreightForecastingEnsemble] = None


def get_model() -> FreightForecastingEnsemble:
    global _model
    if _model is None:
        _model = FreightForecastingEnsemble.load()
    return _model


def train_model(records: List[Dict[str, Any]], base_rates: Optional[Dict[Any, float]] = None) -> Dict[str, Any]:
    """Train the model from a list of record dicts."""
    global _model
    _, X, y = process_tabular_dataset(records)
    model = FreightForecastingEnsemble()
    result = model.fit(X, y, base_rates=base_rates)
    if result.get("trained"):
        model.save()
    _model = model
    return result
