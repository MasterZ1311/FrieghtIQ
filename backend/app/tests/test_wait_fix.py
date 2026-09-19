import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.enums import (
    WaitFixDecision, DecisionConfidence, CargoType, VesselClass,
    FeasibilityStatus, DataStatusType
)
from app.services.wait_fix.economics import FreightEconomicImpactService
from app.services.wait_fix.scenarios import WaitFixScenarioService
from app.services.wait_fix.waiting_cost import WaitingCostModel
from app.services.wait_fix.option_model import WaitOptionModel
from app.services.wait_fix.confidence import DecisionConfidenceService
from app.services.wait_fix.engine import WaitFixDecisionEngine
from app.repositories.wait_fix_repo import WaitFixRepository

# Ensure tables are registered
Base.metadata.create_all(bind=engine)
client = TestClient(app)

# -------------------------------------------------------------
# 1. Freight Economics Tests
# -------------------------------------------------------------
def test_freight_economic_calculations():
    cost = FreightEconomicImpactService.calculate_total_freight_cost(25.0, 75000.0)
    assert cost == 1875000.0

    diff = FreightEconomicImpactService.calculate_cost_difference(1875000.0, 1800000.0)
    assert diff == 75000.0 # $75k saving by waiting

    diff_fix = FreightEconomicImpactService.calculate_cost_difference(1800000.0, 1875000.0)
    assert diff_fix == -75000.0 # $75k saving by fixing now

    pct = FreightEconomicImpactService.calculate_savings_percentage(75000.0, 1875000.0)
    assert pct == 4.0

    with pytest.raises(ValueError):
        FreightEconomicImpactService.calculate_total_freight_cost(25.0, 0.0)

# -------------------------------------------------------------
# 2. Scenario Discretization & Probability Normalization Tests
# -------------------------------------------------------------
def test_wait_fix_scenario_discretization():
    p10 = 23.0
    p50 = 25.0
    p90 = 28.0
    qty = 75000.0
    fix_rate = 26.0

    scenarios, exp_rate, fix_cost, exp_wait_cost, exp_diff = WaitFixScenarioService.generate_scenarios(
        p10=p10, p50=p50, p90=p90, quantity_mt=qty, reference_fix_rate=fix_rate
    )

    assert len(scenarios) == 3
    names = [s.scenario_name for s in scenarios]
    assert "LOW" in names
    assert "CENTRAL" in names
    assert "HIGH" in names

    # Verify probability normalization
    total_prob = sum(s.probability for s in scenarios)
    assert abs(total_prob - 1.0) < 1e-4

    # Verify expected wait rate: 23*0.3 + 25*0.4 + 28*0.3 = 6.9 + 10.0 + 8.4 = 25.30
    expected_calc_rate = round(23.0 * 0.30 + 25.0 * 0.40 + 28.0 * 0.30, 2)
    assert exp_rate == expected_calc_rate
    assert exp_wait_cost == round(expected_calc_rate * qty, 2)
    assert fix_cost == round(fix_rate * qty, 2)
    assert exp_diff == round(fix_cost - exp_wait_cost, 2)

# -------------------------------------------------------------
# 3. Waiting Cost & Risk Model Tests
# -------------------------------------------------------------
def test_waiting_cost_model():
    eval_standard = WaitingCostModel.calculate_waiting_risk_penalty(
        p10=22.0, p50=25.0, p90=28.0, current_rate=25.0,
        quantity_mt=75000.0, remaining_days=20, decision_horizon_days=30
    )
    assert eval_standard["total_risk_penalty_usd"] > 0
    assert eval_standard["urgency_multiplier"] == 1.0

    # Urgent deadline escalates urgency multiplier
    eval_urgent = WaitingCostModel.calculate_waiting_risk_penalty(
        p10=22.0, p50=25.0, p90=28.0, current_rate=25.0,
        quantity_mt=75000.0, remaining_days=1, decision_horizon_days=30
    )
    assert eval_urgent["urgency_multiplier"] == 3.0
    assert eval_urgent["total_risk_penalty_usd"] > eval_standard["total_risk_penalty_usd"]

# -------------------------------------------------------------
# 4. Real Option Flexibility Valuation Tests
# -------------------------------------------------------------
def test_wait_option_model_valid_and_expired():
    # Valid parameters
    res_valid = WaitOptionModel.calculate_wait_option_value(
        current_freight_rate=25.0,
        reference_fix_rate=25.0,
        cargo_quantity_mt=75000.0,
        remaining_days=30,
        annualized_volatility=0.25,
        discount_rate=0.05
    )
    assert res_valid.status == "AVAILABLE"
    assert res_valid.option_value_usd is not None
    assert res_valid.option_value_usd > 0
    assert res_valid.option_value_pmt is not None

    # Expired decision window -> OPTION_VALUE_UNAVAILABLE
    res_expired = WaitOptionModel.calculate_wait_option_value(
        current_freight_rate=25.0,
        reference_fix_rate=25.0,
        cargo_quantity_mt=75000.0,
        remaining_days=0
    )
    assert res_expired.status == "OPTION_VALUE_UNAVAILABLE"
    assert res_expired.option_value_usd is None

# -------------------------------------------------------------
# 5. Decision Confidence Service Tests
# -------------------------------------------------------------
def test_decision_confidence_service():
    conf_high = DecisionConfidenceService.evaluate_confidence(
        forecast_confidence_pct=90.0,
        regime_probability=0.95,
        remaining_days=25,
        port_feasibility=FeasibilityStatus.PASS,
        data_status=DataStatusType.SYNTHETIC,
        modeled_difference_pct=5.0
    )
    assert conf_high == DecisionConfidence.HIGH

    conf_penalized = DecisionConfidenceService.evaluate_confidence(
        forecast_confidence_pct=60.0,
        regime_probability=0.55,
        remaining_days=1, # Near deadline
        port_feasibility=FeasibilityStatus.CONDITIONAL, # Port warning
        data_status=DataStatusType.STALE, # Stale data
        modeled_difference_pct=0.2 # Small difference
    )
    assert conf_penalized == DecisionConfidence.LOW

# -------------------------------------------------------------
# 6. API Endpoint Tests
# -------------------------------------------------------------
def test_api_post_wait_fix_analyze():
    payload = {
        "origin_port_id": "port-auncb",
        "destination_port_id": "port-inprt",
        "cargo_type": "COKING_COAL",
        "cargo_quantity": 75000.0,
        "vessel_class": "PANAMAX",
        "decision_horizon_days": 30
    }
    res = client.post("/api/v1/wait-fix/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "decision" in data
    assert data["decision"] in ["WAIT", "FIX_NOW", "MONITOR", "DECISION_WINDOW_EXPIRED", "NOT_EVALUABLE"]
    assert "decision_confidence" in data
    assert "expected_modeled_difference" in data
    assert len(data["scenarios"]) == 3
    assert "option_analysis" in data
    assert "assumptions" in data
    assert "why_this_result" in data

def test_api_get_wait_fix_latest():
    res = client.get("/api/v1/wait-fix/latest?origin=port-auncb&destination=port-inprt&vessel_class=PANAMAX")
    assert res.status_code == 200
    data = res.json()
    assert "decision" in data
    assert "expected_fix_cost" in data
    assert "expected_wait_cost" in data

def test_api_get_wait_fix_history():
    res = client.get("/api/v1/wait-fix/history?limit=5")
    assert res.status_code == 200
    records = res.json()
    assert isinstance(records, list)
    assert len(records) >= 1

def test_api_get_wait_fix_by_id_and_scenarios():
    # Fetch latest to get an id
    res_latest = client.get("/api/v1/wait-fix/latest")
    assert res_latest.status_code == 200
    analysis_id = res_latest.json()["id"]

    # Get by ID
    res_id = client.get(f"/api/v1/wait-fix/{analysis_id}")
    assert res_id.status_code == 200
    assert res_id.json()["id"] == analysis_id

    # Get scenarios
    res_sc = client.get(f"/api/v1/wait-fix/{analysis_id}/scenarios")
    assert res_sc.status_code == 200
    scenarios = res_sc.json()
    assert len(scenarios) == 3

def test_api_post_option_value():
    payload = {
        "current_freight_rate": 26.0,
        "reference_fix_rate": 26.0,
        "cargo_quantity": 75000.0,
        "remaining_days": 21,
        "volatility_annualized": 0.28,
        "discount_rate": 0.05
    }
    res = client.post("/api/v1/wait-fix/option-value", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "AVAILABLE"
    assert data["option_value_usd"] > 0
