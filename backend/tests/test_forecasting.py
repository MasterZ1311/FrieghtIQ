"""
FreightIQ Forecasting Engine Unit & Integration Tests
=====================================================
Tests:
1. Synthetic dataset generator (determinism, physical consistency, column completeness)
2. Preprocessing & feature extraction (no lookahead data leakage, chronological split)
3. Baselines (Naive persistence, Moving Average)
4. ML models (Random Forest, Gradient Boosting, Quantile Regressors)
5. Evaluation metrics (MAE, RMSE, MAPE)
6. Prediction service schema & explainability drivers
7. Uncertainty band scaling across horizons
8. Edge cases (unseen routes, extreme horizons, missing proxies)
"""
from datetime import date, timedelta
import math
import unittest
import numpy as np
import pandas as pd

from app.ml.dataset_generator import (
    generate_full_synthetic_dataset,
    generate_route_history,
    get_distance,
    BASE_FREIGHT_RATES,
)
from app.ml.preprocessing import (
    FEATURE_NAMES,
    build_single_feature_vector,
    process_tabular_dataset,
    train_test_chronological_split,
)
from app.ml.baselines import (
    NaiveHistoricalBaseline,
    MovingAverageBaseline,
)
from app.ml.model import (
    FreightForecastingEnsemble,
    GradientBoostingFreightModel,
    RandomForestFreightModel,
    QuantileUncertaintyModel,
)
from app.ml.evaluation import (
    compute_all_metrics,
    compute_mae,
    compute_rmse,
    compute_mape,
)
from app.ml.predictor import (
    predict_freight_rate,
    DISCLAIMER_TEXT,
)


class TestDatasetGenerator(unittest.TestCase):
    """Verify synthetic dataset generator guarantees."""

    def test_determinism(self):
        """Identical random seed produces exactly identical time series."""
        run1 = generate_route_history("Australia", "Paradip", "Panamax", weeks=20, seed=42)
        run2 = generate_route_history("Australia", "Paradip", "Panamax", weeks=20, seed=42)
        self.assertEqual(len(run1), len(run2))
        for r1, r2 in zip(run1, run2):
            self.assertEqual(r1["rate_usd_per_mt"], r2["rate_usd_per_mt"])
            self.assertEqual(r1["bunker_price"], r2["bunker_price"])
            self.assertEqual(r1["congestion_index"], r2["congestion_index"])

    def test_incompatible_routes_omitted(self):
        """Capesize cannot load at Indonesian shallow draft berths."""
        res = generate_route_history("Indonesia", "Paradip", "Capesize", weeks=20)
        self.assertEqual(len(res), 0)

    def test_required_columns_and_demo_flag(self):
        """Full dataset has all required columns and is_demo=True."""
        df = generate_full_synthetic_dataset(weeks=20, seed=42)
        required = [
            "date", "origin", "destination", "vessel_class", "commodity",
            "rate_usd_per_mt", "bunker_price", "congestion_index",
            "vessel_availability", "demand_index", "commodity_index", "is_demo"
        ]
        for col in required:
            self.assertIn(col, df.columns)
        self.assertTrue((df["is_demo"] == True).all())
        self.assertTrue((df["rate_usd_per_mt"] > 0).all())


class TestPreprocessingAndLeakage(unittest.TestCase):
    """Verify feature engineering and strict chronological split."""

    def setUp(self):
        self.df = generate_full_synthetic_dataset(weeks=40, seed=42)
        self.feat_df, self.X, self.y = process_tabular_dataset(self.df)

    def test_feature_dimensions(self):
        """Engineered feature width matches FEATURE_NAMES."""
        self.assertEqual(self.X.shape[1], len(FEATURE_NAMES))
        self.assertEqual(len(self.X), len(self.y))
        self.assertEqual(len(self.feat_df), len(self.y))

    def test_no_future_leakage_in_chronological_split(self):
        """Chronological split must ensure max(train_date) < min(test_date)."""
        X_tr, y_tr, X_te, y_te, tr_meta, te_meta = train_test_chronological_split(
            self.feat_df, self.X, self.y, test_ratio=0.25
        )
        max_train_date = pd.to_datetime(tr_meta["date"]).max()
        min_test_date = pd.to_datetime(te_meta["date"]).min()

        self.assertLess(
            max_train_date,
            min_test_date,
            f"Future leakage detected: train max {max_train_date} >= test min {min_test_date}",
        )
        self.assertGreater(len(X_tr), 0)
        self.assertGreater(len(X_te), 0)


class TestBaselinesAndModels(unittest.TestCase):
    """Verify baseline heuristics and ML models."""

    def setUp(self):
        df = generate_full_synthetic_dataset(weeks=35, seed=42)
        self.feat_df, self.X, self.y = process_tabular_dataset(df)
        self.X_tr, self.y_tr, self.X_te, self.y_te, self.tr_m, self.te_m = train_test_chronological_split(
            self.feat_df, self.X, self.y, test_ratio=0.20
        )

    def test_naive_baseline(self):
        naive = NaiveHistoricalBaseline().fit(self.tr_m, self.y_tr)
        preds = naive.predict(self.te_m, self.X_te)
        self.assertEqual(len(preds), len(self.y_te))
        self.assertTrue(np.all(np.isfinite(preds)))
        self.assertTrue(np.all(preds > 0))

    def test_moving_average_baseline(self):
        ma = MovingAverageBaseline(window=4).fit(self.tr_m, self.y_tr)
        preds = ma.predict(self.te_m, self.X_te)
        self.assertEqual(len(preds), len(self.y_te))
        self.assertTrue(np.all(np.isfinite(preds)))
        self.assertTrue(np.all(preds > 0))

    def test_random_forest_model(self):
        rf = RandomForestFreightModel(n_estimators=30, max_depth=6).fit(self.X_tr, self.y_tr)
        preds = rf.predict(self.X_te)
        self.assertEqual(len(preds), len(self.y_te))
        self.assertTrue(np.all(np.isfinite(preds)))

    def test_gradient_boosting_model(self):
        gbm = GradientBoostingFreightModel(n_estimators=40, max_depth=3).fit(self.X_tr, self.y_tr)
        preds = gbm.predict(self.X_te)
        self.assertEqual(len(preds), len(self.y_te))
        self.assertTrue(np.all(np.isfinite(preds)))

    def test_uncertainty_bounds(self):
        """Quantile bounds must bracket or closely wrap predictions."""
        unc = QuantileUncertaintyModel(n_estimators=30, max_depth=3).fit(self.X_tr, self.y_tr)
        gbm = GradientBoostingFreightModel(n_estimators=30, max_depth=3).fit(self.X_tr, self.y_tr)
        pt = gbm.predict(self.X_te)
        low, high = unc.predict_bounds(self.X_te, pt)
        self.assertTrue(np.all(low <= high))
        self.assertTrue(np.all(low <= pt * 1.01))
        self.assertTrue(np.all(high >= pt * 0.99))


class TestEvaluationMetrics(unittest.TestCase):
    """Verify MAE, RMSE, MAPE metrics."""

    def test_metric_values(self):
        y_true = np.array([10.0, 20.0, 30.0], dtype=np.float64)
        y_pred = np.array([12.0, 18.0, 33.0], dtype=np.float64)
        # Errors: |10-12|=2, |20-18|=2, |30-33|=3 -> MAE = 7/3 = 2.333
        mae = compute_mae(y_true, y_pred)
        self.assertAlmostEqual(mae, 7.0 / 3.0, places=2)

        # RMSE: sqrt((4 + 4 + 9)/3) = sqrt(17/3) = 2.380
        rmse = compute_rmse(y_true, y_pred)
        self.assertAlmostEqual(rmse, math.sqrt(17.0 / 3.0), places=2)

        # MAPE: (2/10 + 2/20 + 3/30)/3 = (0.2 + 0.1 + 0.1)/3 = 0.1333 -> 13.33%
        mape = compute_mape(y_true, y_pred)
        self.assertAlmostEqual(mape, 13.33, places=1)


class TestPredictionService(unittest.TestCase):
    """Verify prediction payload structure, drivers, uncertainty, and edge cases."""

    def test_required_payload_keys(self):
        """Response dictionary must contain all 7 explicitly required keys."""
        resp = predict_freight_rate(
            origin="Australia",
            destination="Paradip",
            vessel_class="Panamax",
            commodity="Coal",
            horizon_days=30,
        )
        required_keys = [
            "current_rate",
            "predicted_rate",
            "horizon",
            "lower_bound",
            "upper_bound",
            "confidence",
            "drivers",
        ]
        for key in required_keys:
            self.assertIn(key, resp, f"Missing required forecasting key: {key}")

        # Check types
        self.assertIsInstance(resp["current_rate"], (int, float))
        self.assertIsInstance(resp["predicted_rate"], (int, float))
        self.assertIsInstance(resp["horizon"], int)
        self.assertIsInstance(resp["lower_bound"], (int, float))
        self.assertIsInstance(resp["upper_bound"], (int, float))
        self.assertIsInstance(resp["confidence"], (int, float))
        self.assertIsInstance(resp["drivers"], list)

        # Bound consistency
        self.assertLessEqual(resp["lower_bound"], resp["predicted_rate"])
        self.assertGreaterEqual(resp["upper_bound"], resp["predicted_rate"])

    def test_explainability_drivers(self):
        """Drivers must contain factor, direction, magnitude, and description."""
        resp = predict_freight_rate(
            origin="Australia",
            destination="Visakhapatnam",
            vessel_class="Supramax",
            commodity="Coal",
            horizon_days=14,
        )
        drivers = resp["drivers"]
        self.assertGreater(len(drivers), 0)
        for d in drivers:
            self.assertIn("factor", d)
            self.assertIn("direction", d)
            self.assertIn(d["direction"], ("bullish", "bearish", "neutral"))
            self.assertIn("magnitude", d)
            self.assertIn(d["magnitude"], ("high", "medium", "low"))
            self.assertIn("description", d)

    def test_horizon_uncertainty_expansion(self):
        """Longer forecast horizon must exhibit strictly wider uncertainty intervals."""
        short_fc = predict_freight_rate(
            origin="Australia",
            destination="Paradip",
            vessel_class="Panamax",
            horizon_days=7,
        )
        long_fc = predict_freight_rate(
            origin="Australia",
            destination="Paradip",
            vessel_class="Panamax",
            horizon_days=90,
        )
        short_spread = short_fc["upper_bound"] - short_fc["lower_bound"]
        long_spread = long_fc["upper_bound"] - long_fc["lower_bound"]
        self.assertGreater(
            long_spread,
            short_spread,
            f"90-day spread ({long_spread}) should be wider than 7-day spread ({short_spread})",
        )

    def test_demo_disclaimer_present(self):
        """Response explicitly flags demo status and disclaimer."""
        resp = predict_freight_rate(
            origin="Mozambique",
            destination="Dhamra",
            vessel_class="Capesize",
        )
        self.assertTrue(resp.get("is_demo", False))
        self.assertIn("[DEMO]", resp.get("disclaimer", ""))

    def test_edge_case_unknown_route(self):
        """Unseen / uncommon route falls back gracefully without crashing."""
        resp = predict_freight_rate(
            origin="NonExistentOrigin",
            destination="NonExistentPort",
            vessel_class="Panamax",
            horizon_days=30,
        )
        self.assertIn("predicted_rate", resp)
        self.assertGreater(resp["predicted_rate"], 0.0)

    def test_edge_case_with_and_without_recent_rates(self):
        """Prediction operates successfully with or without recent rates series."""
        rates = [
            {"rate_usd_per_mt": 14.5 + i * 0.1, "bunker_price": 620}
            for i in range(15)
        ]
        with_rates = predict_freight_rate(
            origin="Australia",
            destination="Paradip",
            vessel_class="Panamax",
            recent_rates=rates,
        )
        without_rates = predict_freight_rate(
            origin="Australia",
            destination="Paradip",
            vessel_class="Panamax",
            recent_rates=None,
        )
        self.assertGreater(with_rates["predicted_rate"], 0.0)
        self.assertGreater(without_rates["predicted_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
