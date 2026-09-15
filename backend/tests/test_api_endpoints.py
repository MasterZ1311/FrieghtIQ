"""
Automated Integration Tests: All API Endpoints
==============================================
Validates HTTP status codes, request/response models, validation rules,
and deterministic demo responses across all 8 required endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_api_health():
    """GET /api/health returns operational status and demo disclaimer."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "FreightIQ" in data["service"]
    assert "[DEMO]" in data["disclaimer"]


def test_post_api_forecast():
    """POST /api/forecast returns point estimate, confidence interval, and drivers."""
    payload = {
        "origin": "Australia",
        "destination": "Paradip",
        "vessel_class": "Panamax",
        "commodity": "Coal",
        "quantity_mt": 70000,
        "horizon": 30,
    }
    response = client.post("/api/forecast", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "current_rate" in data
    assert "predicted_rate" in data
    assert "horizon" in data
    assert "lower_bound" in data
    assert "upper_bound" in data
    assert "confidence" in data
    assert "drivers" in data
    assert len(data["drivers"]) > 0
    assert data["lower_bound"] <= data["predicted_rate"] <= data["upper_bound"]


def test_post_api_vessel_recommend():
    """POST /api/vessel/recommend returns recommended vessel, score, reasons, and warnings."""
    payload = {
        "origin": "Australia",
        "destination": "Visakhapatnam",
        "commodity": "Coal",
        "quantity_mt": 70000,
        "budget_usd_per_mt": 15.0,
    }
    response = client.post("/api/vessel/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "decision" in data
    assert "score" in data
    assert "confidence" in data
    assert "reasons" in data
    assert "warnings" in data
    assert "recommended_class" in data
    assert data["recommended_class"] == "Panamax"
    assert len(data["reasons"]) > 0


def test_post_api_port_check():
    """POST /api/port/check returns port physical compatibility and constraints."""
    payload = {
        "port": "Haldia",
        "vessel_class": "Capesize",
        "quantity_mt": 150000,
        "commodity": "Coal",
    }
    response = client.post("/api/port/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "compatible" in data
    assert data["compatible"] is False
    assert "constraints" in data
    assert "handling_rate" in data
    assert "turnaround_days" in data


def test_post_api_economics_calculate():
    """POST /api/economics/calculate returns full maritime cost breakdown and TCE."""
    payload = {
        "origin": "Australia",
        "destination": "Gangavaram",
        "vessel_class": "Panamax",
        "commodity": "Coal",
        "quantity_mt": 70000,
        "bunker_price_usd_per_mt": 650.0,
    }
    response = client.post("/api/economics/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "freight_revenue" in data
    assert "bunker_cost" in data
    assert "port_dues" in data
    assert "canal_dues" in data
    assert "opex" in data
    assert "total_cost" in data
    assert "cost_per_mt" in data
    assert "tce" in data
    assert "margin_pct" in data
    assert data["total_cost"] > 0


def test_post_api_contracts_compare():
    """POST /api/contracts/compare returns contract options and strategic recommendations."""
    payload = {
        "origin": "Australia",
        "destination": "Paradip",
        "vessel_class": "Panamax",
        "commodity": "Coal",
        "quantity_mt": 70000,
        "annual_volume_mt": 500000,
        "planning_horizon_months": 12,
    }
    response = client.post("/api/contracts/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "contracts" in data
    assert len(data["contracts"]) == 4
    assert "recommended_contract" in data
    assert "expected_saving_vs_spot" in data
    assert "reasoning" in data


def test_post_api_risk_analyze():
    """POST /api/risk/analyze returns multi-factor risk scores, top risks, and actions."""
    payload = {
        "origin": "Russia",
        "destination": "Paradip",
        "vessel_class": "Panamax",
        "commodity": "Coal",
        "quantity_mt": 70000,
        "contract_type": "Spot",
    }
    response = client.post("/api/risk/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "overall_risk_score" in data
    assert "overall_risk_level" in data
    assert "risk_factors" in data
    assert len(data["risk_factors"]) == 6
    assert "top_risks" in data
    assert "recommended_actions" in data


def test_post_api_scenario_simulate():
    """POST /api/scenario/simulate compares base against alternative what-if cases."""
    payload = {
        "base_origin": "Australia",
        "base_destination": "Paradip",
        "base_vessel_class": "Panamax",
        "base_commodity": "Coal",
        "base_cargo_mt": 70000,
        "scenarios": [
            {
                "name": "Supramax Alternative",
                "vessel_class": "Supramax",
                "origin": "Australia",
                "destination": "Paradip",
                "commodity": "Coal",
                "cargo_mt": 55000,
            }
        ],
    }
    response = client.post("/api/scenario/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "base_scenario" in data
    assert "alternatives" in data
    assert "best_scenario" in data
    assert "worst_scenario" in data


def test_validation_errors_rejected_cleanly():
    """Validation rejects negative or invalid inputs with HTTP 422."""
    # Negative cargo quantity
    bad_payload = {
        "origin": "Australia",
        "destination": "Paradip",
        "quantity_mt": -5000,
    }
    response = client.post("/api/forecast", json=bad_payload)
    assert response.status_code == 422

    # Negative bunker price
    bad_econ = {
        "origin": "Australia",
        "destination": "Paradip",
        "quantity_mt": 70000,
        "bunker_price_usd_per_mt": -100,
    }
    response2 = client.post("/api/economics/calculate", json=bad_econ)
    assert response2.status_code == 422
