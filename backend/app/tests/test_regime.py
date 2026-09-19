import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.enums import MarketRegimeType, DataStatusType, ForecastRegimeAlignment, CargoType, VesselClass, ForecastModelType
from app.services.regime.hmm_model import HMMMarketRegimeModel
from app.services.regime.feature_service import MarketRegimeFeatureService
from app.services.regime.service import MarketRegimeService
from app.repositories.regime_repo import RegimeRepository
from app.models.freight import FreightObservation, FreightForecast

# Ensure tables exist in the test database
Base.metadata.create_all(bind=engine)
client = TestClient(app)

# -------------------------------------------------------------
# 1. Feature Engineering Tests
# -------------------------------------------------------------
def test_feature_engineering_extraction():
    now = datetime.now(timezone.utc)
    observations = []
    for i in range(60):
        d = now - timedelta(days=60 - i)
        rate = 25.0 + float(i * 0.1)
        obs = FreightObservation(
            id=f"obs-test-{i}",
            route_id="test-route",
            observation_date=d,
            freight_rate_usd_pmt=rate,
            bunker_vlsfo_usd=600.0 + i,
            baltic_index_value=1400.0 + i * 2,
            congestion_origin_days=2.0,
            congestion_dest_days=3.0,
            is_interpolated=False,
            source_type="SYNTHETIC_CALIBRATED"
        )
        observations.append(obs)

    df, cols = MarketRegimeFeatureService.extract_features(observations)
    assert len(df) == 60
    assert "rate_return_1d" in df.columns
    assert "rate_return_7d" in df.columns
    assert "rate_return_30d" in df.columns
    assert "rolling_volatility_14d" in df.columns
    assert "seasonal_signal" in df.columns
    assert "seasonal_sin" in df.columns
    assert "seasonal_cos" in df.columns
    # Check that returns are float and finite
    assert not df["rate_return_7d"].isnull().any()
    assert not df["rolling_volatility_14d"].isnull().any()

# -------------------------------------------------------------
# 2. HMM Model Training & Probability Normalization Tests
# -------------------------------------------------------------
def test_hmm_model_fit_predict_normalization():
    np.random.seed(42)
    n_samples = 150
    # Create realistic synthetic signals
    returns = np.random.normal(0.001, 0.02, n_samples)
    vol = np.abs(np.random.normal(0.015, 0.005, n_samples))
    sin_s = np.sin(np.linspace(0, 4 * np.pi, n_samples))
    cos_s = np.cos(np.linspace(0, 4 * np.pi, n_samples))

    df = pd.DataFrame({
        "rate_return_7d": returns,
        "rate_return_30d": returns * 2.5,
        "rolling_volatility_14d": vol,
        "seasonal_sin": sin_s,
        "seasonal_cos": cos_s,
        "seasonal_signal": sin_s,
    })

    model = HMMMarketRegimeModel(n_states=4, max_iter=25, random_state=42)
    model.fit(df)
    assert model.is_fitted is True
    assert len(model.state_to_regime_map) == 4

    # Check semantic mapping: must contain all 4 regimes
    semantic_regimes = set(model.state_to_regime_map.values())
    assert MarketRegimeType.BULL in semantic_regimes
    assert MarketRegimeType.BEAR in semantic_regimes
    assert MarketRegimeType.NEUTRAL in semantic_regimes
    assert MarketRegimeType.SEASONAL in semantic_regimes

    # Predict sequence
    regime_seq, gamma = model.predict(df)
    assert len(regime_seq) == n_samples
    assert gamma.shape == (n_samples, 4)

    # Check probability normalization: each row of gamma must sum to 1.0 within 1e-3
    gamma_sums = np.sum(gamma, axis=1)
    np.testing.assert_allclose(gamma_sums, 1.0, atol=1e-3)

    # Current probabilities
    probs = model.predict_current_proba(df)
    total_prob = sum(probs.values())
    assert abs(total_prob - 1.0) < 1e-3
    for r in [MarketRegimeType.BULL, MarketRegimeType.BEAR, MarketRegimeType.NEUTRAL, MarketRegimeType.SEASONAL]:
        assert r in probs
        assert 0.0 <= probs[r] <= 1.0

# -------------------------------------------------------------
# 3. Forecast × Regime Alignment Evaluation Tests
# -------------------------------------------------------------
def test_forecast_regime_alignment():
    db = SessionLocal()
    try:
        service = MarketRegimeService(db)

        # 1. Rising forecast + BULL -> ALIGNED
        fcs = [
            FreightForecast(
                id="fc-test-1", route_id="r", vessel_class=VesselClass.PANAMAX,
                model_type=ForecastModelType.TFT, horizon_days=7,
                predicted_p10=24.0, predicted_p50=26.0, predicted_p90=28.0,
                target_date=datetime.now(timezone.utc)
            ),
            FreightForecast(
                id="fc-test-2", route_id="r", vessel_class=VesselClass.PANAMAX,
                model_type=ForecastModelType.TFT, horizon_days=14,
                predicted_p10=25.0, predicted_p50=28.0, predicted_p90=31.0,
                target_date=datetime.now(timezone.utc)
            ),
        ]
        align, rationale = service._evaluate_forecast_alignment(MarketRegimeType.BULL, 0.12, fcs)
        assert align == ForecastRegimeAlignment.ALIGNED

        # 2. Rising forecast + BEAR -> DIVERGENT
        align, rationale = service._evaluate_forecast_alignment(MarketRegimeType.BEAR, 0.12, fcs)
        assert align == ForecastRegimeAlignment.DIVERGENT

        # 3. Softening forecast + BEAR -> ALIGNED
        align, rationale = service._evaluate_forecast_alignment(MarketRegimeType.BEAR, -0.10, fcs)
        assert align == ForecastRegimeAlignment.ALIGNED

        # 4. Softening forecast + BULL -> DIVERGENT
        align, rationale = service._evaluate_forecast_alignment(MarketRegimeType.BULL, -0.10, fcs)
        assert align == ForecastRegimeAlignment.DIVERGENT

        # 5. Flat forecast + NEUTRAL -> ALIGNED
        align, rationale = service._evaluate_forecast_alignment(MarketRegimeType.NEUTRAL, 0.01, fcs)
        assert align == ForecastRegimeAlignment.ALIGNED

        # 6. Insufficient forecasts -> INSUFFICIENT_DATA
        align, rationale = service._evaluate_forecast_alignment(MarketRegimeType.BULL, 0.12, [])
        assert align == ForecastRegimeAlignment.INSUFFICIENT_DATA
    finally:
        db.close()

# -------------------------------------------------------------
# 4. API Endpoint Tests
# -------------------------------------------------------------
def test_api_get_current_regime():
    res = client.get("/api/v1/regime/current?origin=port-auncb&destination=port-inprt&vessel_class=PANAMAX&cargo=COKING_COAL")
    assert res.status_code == 200
    data = res.json()
    assert "regime" in data
    assert data["regime"] in ["BULL", "BEAR", "NEUTRAL", "SEASONAL"]
    assert "probabilities" in data
    probs = data["probabilities"]
    assert "BULL" in probs
    assert "BEAR" in probs
    assert "NEUTRAL" in probs
    assert "SEASONAL" in probs
    # Probabilities must sum to ~1.0
    total_p = sum(probs.values())
    assert abs(total_p - 1.0) < 0.05
    assert "confidence" in data
    assert "forecast_alignment" in data
    assert "evidence" in data
    assert len(data["evidence"]) >= 3
    assert data["data_status"] in ["SYNTHETIC", "DEMO", "LIVE", "RECENT"]
    assert "route" in data
    assert "model" in data
    assert "dataset" in data

def test_api_get_regime_history():
    res = client.get("/api/v1/regime/history?days=30")
    assert res.status_code == 200
    history = res.json()
    assert isinstance(history, list)
    assert len(history) > 0
    point = history[-1]
    assert "date" in point
    assert "regime" in point
    assert "probabilities" in point
    assert "freight_rate" in point

def test_api_post_regime_analyze():
    payload = {
        "origin_port_id": "port-auncb",
        "destination_port_id": "port-inprt",
        "cargo_type": "COKING_COAL",
        "vessel_class": "PANAMAX"
    }
    res = client.post("/api/v1/regime/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["vessel_class"] == "PANAMAX"
    assert data["regime"] in ["BULL", "BEAR", "NEUTRAL", "SEASONAL"]
    assert data["confidence"] > 0

def test_api_get_regime_transitions():
    db = SessionLocal()
    try:
        from app.models.regime import MarketRegimeTransition
        import uuid
        # Ensure at least 1 transition exists in test database
        existing = db.query(MarketRegimeTransition).first()
        if not existing:
            t = MarketRegimeTransition(
                id=str(uuid.uuid4()),
                market_regime_id="test-regime-id",
                previous_regime=MarketRegimeType.NEUTRAL,
                new_regime=MarketRegimeType.BULL,
                transition_date=datetime.now(timezone.utc),
                confidence=0.85,
                trigger_features='{"rate_return_7d": 0.05}',
                model_version_id="hmm-v1.0-4s"
            )
            db.add(t)
            db.commit()
    finally:
        db.close()

    res = client.get("/api/v1/regime/transitions?limit=10")
    assert res.status_code == 200
    transitions = res.json()
    assert isinstance(transitions, list)
    assert len(transitions) >= 1
    t = transitions[0]
    assert "previous_regime" in t
    assert "new_regime" in t
    assert "confidence" in t
    assert "transition_date" in t

def test_api_get_regime_models():
    res = client.get("/api/v1/regime/models")
    assert res.status_code == 200
    models = res.json()
    assert isinstance(models, list)
    assert len(models) >= 1
    m = models[0]
    assert "Gaussian" in m["model_name"]
    assert m["number_of_states"] == 4
    assert m["status"] == "PRODUCTION_CALIBRATED"
    assert len(m["features"]) >= 5
