"""
FreightIQ ML Package
====================
Deterministic, explainable forecasting and data layer for freight rate analytics.
"""
from app.ml.dataset_generator import (
    generate_full_synthetic_dataset,
    generate_route_history,
    get_distance,
    BASE_FREIGHT_RATES,
    ROUTE_DISTANCES,
)
from app.ml.preprocessing import (
    build_single_feature_vector,
    process_tabular_dataset,
    train_test_chronological_split,
    extract_seasonality_features,
    FEATURE_NAMES,
)
from app.ml.baselines import (
    NaiveHistoricalBaseline,
    MovingAverageBaseline,
)
from app.ml.model import (
    FreightForecastingEnsemble,
    FreightRateEnsemble,
    RandomForestFreightModel,
    GradientBoostingFreightModel,
    XGBoostFreightModel,
    QuantileUncertaintyModel,
    get_model,
    train_model,
)
from app.ml.registry import (
    ModelRegistry,
    get_model_registry,
)
from app.ml.evaluation import (
    compute_all_metrics,
    compute_mae,
    compute_rmse,
    compute_mape,
    format_benchmark_table,
)
from app.ml.predictor import (
    predict_freight_rate,
    DISCLAIMER_TEXT,
)
from app.ml.train import (
    run_training_pipeline,
)

__all__ = [
    "generate_full_synthetic_dataset",
    "generate_route_history",
    "get_distance",
    "BASE_FREIGHT_RATES",
    "ROUTE_DISTANCES",
    "build_single_feature_vector",
    "process_tabular_dataset",
    "train_test_chronological_split",
    "extract_seasonality_features",
    "FEATURE_NAMES",
    "NaiveHistoricalBaseline",
    "MovingAverageBaseline",
    "FreightForecastingEnsemble",
    "FreightRateEnsemble",
    "RandomForestFreightModel",
    "GradientBoostingFreightModel",
    "XGBoostFreightModel",
    "QuantileUncertaintyModel",
    "get_model",
    "train_model",
    "ModelRegistry",
    "get_model_registry",
    "compute_all_metrics",
    "compute_mae",
    "compute_rmse",
    "compute_mape",
    "format_benchmark_table",
    "predict_freight_rate",
    "DISCLAIMER_TEXT",
    "run_training_pipeline",
]
