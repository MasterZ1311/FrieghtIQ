"""
FreightIQ Model Registry & Configuration
========================================
Lightweight, zero-external-dependency model registry.
Tracks:
- Active champion model ("ensemble", "gradient_boosting", "random_forest", etc.)
- Model version and training timestamp
- Chronological validation benchmarks across all candidates (MAE, RMSE, MAPE, R²)
- Feature schemas and training metadata
- Model artifact persistence
"""
from __future__ import annotations
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

REGISTRY_FILE = Path(__file__).parent / "model_registry.json"


class ModelRegistry:
    """Manages model metadata, active champion selection, and benchmark history."""

    def __init__(self, registry_path: Path = REGISTRY_FILE):
        self.registry_path = registry_path
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load registry from {self.registry_path}: {e}")

        # Default registry metadata
        return {
            "version": "1.0.0",
            "active_model": "FreightForecastingEnsemble",
            "active_model_type": "ensemble",
            "status": "ready",
            "is_demo": True,
            "disclaimer": "[DEMO] Synthetic forecast for demonstration purposes. Not real market data.",
            "last_trained_at": None,
            "training_samples": 0,
            "champion_metrics": {
                "mae": None,
                "rmse": None,
                "mape_pct": None,
                "r2": None,
            },
            "benchmarks": {},
            "features_used": [],
        }

    def save(self):
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def register_training_run(
        self,
        active_model_name: str,
        champion_metrics: Dict[str, float],
        benchmarks: Dict[str, Dict[str, float]],
        training_samples: int,
        features: list[str],
    ):
        """Record the outcome of a training and benchmarking pipeline run."""
        self.data["active_model"] = active_model_name
        self.data["active_model_type"] = active_model_name.lower()
        self.data["last_trained_at"] = datetime.utcnow().isoformat()
        self.data["training_samples"] = training_samples
        self.data["champion_metrics"] = champion_metrics
        self.data["benchmarks"] = benchmarks
        self.data["features_used"] = features
        self.data["status"] = "trained"
        self.save()

    @property
    def active_model_name(self) -> str:
        return self.data.get("active_model", "FreightForecastingEnsemble")

    @property
    def champion_metrics(self) -> Dict[str, Any]:
        return self.data.get("champion_metrics", {})

    @property
    def benchmarks(self) -> Dict[str, Any]:
        return self.data.get("benchmarks", {})

    def get_summary(self) -> Dict[str, Any]:
        return {
            "version": self.data.get("version"),
            "active_model": self.active_model_name,
            "last_trained_at": self.data.get("last_trained_at"),
            "training_samples": self.data.get("training_samples"),
            "champion_metrics": self.champion_metrics,
            "benchmarks": self.benchmarks,
            "is_demo": True,
        }


# Global registry singleton
_registry: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
