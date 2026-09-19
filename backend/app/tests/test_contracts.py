import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.contracts.voyage_planning import VoyagePlanningService
from app.services.contracts.spot_model import SpotContractCostModel
from app.services.contracts.multiple_voyage_model import MultipleVoyageCostModel
from app.services.contracts.hybrid_strategy import HybridContractStrategy
from app.services.contracts.flexibility import FlexibilityCostModel
from app.services.contracts.market_exposure import MarketExposureModel
from app.services.contracts.risk_adjusted_cost import RiskAdjustedCostService
from app.services.contracts.break_even import BreakEvenService
from app.services.contracts.engine import ContractStrategyEngine
from app.models.enums import ContractStrategyType, DecisionConfidence

client = TestClient(app)

def test_voyage_planning_exact_multiple():
    """Test 300,000 MT / 75,000 MT = 4 full voyages with 0 remainder."""
    res = VoyagePlanningService.plan_voyages(
        total_requirement_mt=300000.0,
        voyage_parcel_mt=75000.0,
        planning_horizon_days=180
    )
    assert res.expected_voyages == 4
    assert res.full_voyages == 4
    assert res.remainder_mt == 0.0
    assert len(res.schedule) == 4
    assert sum(s.parcel_mt for s in res.schedule) == 300000.0

def test_voyage_planning_with_remainder():
    """Test non-divisible requirement preserves remainder cargo without loss."""
    res = VoyagePlanningService.plan_voyages(
        total_requirement_mt=200000.0,
        voyage_parcel_mt=75000.0,
        planning_horizon_days=180
    )
    assert res.expected_voyages == 3 # 2 full + 1 remainder
    assert res.full_voyages == 2
    assert res.remainder_mt == 50000.0
    assert len(res.schedule) == 3
    assert res.schedule[-1].is_remainder is True
    assert res.schedule[-1].parcel_mt == 50000.0
    assert sum(s.parcel_mt for s in res.schedule) == 200000.0

def test_spot_contract_cost_model():
    """Test multi-voyage spot exposure calculations and quantile ordering."""
    voyages = [
        {"voyage_number": 1, "parcel_mt": 75000, "departure_day": 0},
        {"voyage_number": 2, "parcel_mt": 75000, "departure_day": 45},
        {"voyage_number": 3, "parcel_mt": 75000, "departure_day": 90},
        {"voyage_number": 4, "parcel_mt": 75000, "departure_day": 135},
    ]
    res = SpotContractCostModel.calculate_spot_exposure(
        voyages=voyages,
        current_spot_rate=24.50,
        p10_rate=22.80,
        p50_rate=24.10,
        p90_rate=26.50
    )
    assert res.total_quantity_mt == 300000.0
    assert res.p10_rate <= res.p50_rate <= res.p90_rate
    assert res.p10_cost <= res.p50_cost <= res.p90_cost
    assert len(res.voyage_breakdown) == 4

def test_multiple_voyage_cost_model_available():
    """Test multiple voyage cost model when reference rate is provided."""
    res = MultipleVoyageCostModel.calculate_contract_cost(
        contracted_quantity_mt=300000.0,
        voyage_count=4,
        parcel_size_mt=75000.0,
        contract_duration_str="180 Days",
        reference_rate_usd_pmt=24.00,
        volume_concession_pct=0.03 # 3% discount
    )
    assert res.rate_status == "AVAILABLE"
    assert res.contract_rate == round(24.00 * 0.97, 2)
    assert res.contract_freight_cost == round(res.contract_rate * 300000.0, 2)
    assert res.is_scenario_based is False

def test_multiple_voyage_cost_model_unavailable():
    """Test missing reference rate properly flags REFERENCE_RATE_UNAVAILABLE."""
    res = MultipleVoyageCostModel.calculate_contract_cost(
        contracted_quantity_mt=300000.0,
        voyage_count=4,
        parcel_size_mt=75000.0,
        contract_duration_str="180 Days",
        reference_rate_usd_pmt=None
    )
    assert res.rate_status == "REFERENCE_RATE_UNAVAILABLE"
    assert res.contract_rate is None
    assert res.contract_freight_cost is None
    assert res.is_scenario_based is True

def test_hybrid_contract_strategy_coverage_tiers():
    """Test 0%, 25%, 50%, 75%, 100% coverage tiers and quantity conservation."""
    tiers = [0.0, 25.0, 50.0, 75.0, 100.0]
    total_qty = 300000.0

    for cov in tiers:
        res = HybridContractStrategy.evaluate_coverage(
            total_requirement_mt=total_qty,
            coverage_percentage=cov,
            contract_rate=23.28,
            spot_expected_rate=24.30,
            spot_p10_rate=22.80,
            spot_p90_rate=26.50
        )
        # Mathematical identity: contracted + spot == total
        assert round(res.contracted_quantity_mt + res.spot_quantity_mt, 1) == total_qty
        assert res.p10_cost <= res.expected_cost <= res.p90_cost

    # Verify boundary properties:
    pure_spot = HybridContractStrategy.evaluate_coverage(total_qty, 0.0, 23.28, 24.30, 22.80, 26.50)
    full_contract = HybridContractStrategy.evaluate_coverage(total_qty, 100.0, 23.28, 24.30, 22.80, 26.50)

    assert pure_spot.flexibility_measure > full_contract.flexibility_measure
    assert pure_spot.market_exposure > full_contract.market_exposure
    assert pure_spot.cost_range_usd > full_contract.cost_range_usd # Full contract has 0 spot cost spread

def test_flexibility_and_exposure_models():
    """Test trade-off: Spot offers higher flexibility and higher market exposure."""
    spot_flex = FlexibilityCostModel.evaluate(contract_duration_days=0, contracted_share=0.0)
    coa_flex = FlexibilityCostModel.evaluate(contract_duration_days=180, contracted_share=1.0)
    assert spot_flex.flexibility_score > coa_flex.flexibility_score

    spot_exp = MarketExposureModel.evaluate(spot_quantity_mt=300000, total_quantity_mt=300000, expected_spot_rate=24.50)
    coa_exp = MarketExposureModel.evaluate(spot_quantity_mt=0, total_quantity_mt=300000, expected_spot_rate=24.50)
    assert spot_exp.exposure_score > coa_exp.exposure_score

def test_risk_adjusted_cost():
    """Test risk-adjusted cost formula: expected + uncertainty + commitment."""
    res = RiskAdjustedCostService.calculate_risk_adjusted_cost(
        expected_freight_cost=7200000.0,
        total_quantity_mt=300000.0,
        spot_quantity_mt=150000.0,
        contracted_quantity_mt=150000.0,
        p50_spot_rate=24.00,
        p90_spot_rate=26.50
    )
    assert res.total_risk_adjusted_cost == round(
        res.expected_freight_cost + res.uncertainty_adjustment_usd + res.commitment_adjustment_usd, 2
    )
    assert res.uncertainty_adjustment_usd > 0
    assert res.commitment_adjustment_usd > 0

def test_break_even_analysis():
    """Test break-even spot rate threshold calculation."""
    res = BreakEvenService.calculate_break_even(
        current_spot_rate=24.50,
        contract_reference_rate=23.50,
        total_quantity_mt=300000.0,
        planning_horizon_days=180
    )
    assert res.status == "AVAILABLE"
    assert res.modeled_break_even_spot_rate_usd_pmt == 23.50
    assert res.rate_delta_usd_pmt == round(23.50 - 24.50, 2)

def test_api_contract_analyze_and_sub_routes():
    """Test end-to-end API routes for contract strategy engine."""
    payload = {
        "total_requirement_mt": 300000,
        "parcel_size_mt": 75000,
        "planning_horizon_days": 180,
        "reference_contract_rate": 24.00,
        "origin_port_id": "newcastle-au",
        "destination_port_id": "paradip-in",
        "vessel_class": "PANAMAX"
    }
    # 1. Analyze
    resp = client.post("/api/v1/contracts/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert "strategies" in data
    assert "SPOT" in data["strategies"]
    assert "SHORT_TERM_MULTIPLE_VOYAGE" in data["strategies"]
    assert "MEDIUM_TERM_MULTIPLE_VOYAGE" in data["strategies"]
    assert len(data["scenario_matrix"]) == 9 # 3 strategies x 3 market scenarios
    assert len(data["coverage_spectrum"]) == 5 # 0, 25, 50, 75, 100%

    strat_id = data["strategies"]["MEDIUM_TERM_MULTIPLE_VOYAGE"]["id"]

    # 2. Get by ID
    get_resp = client.get(f"/api/v1/contracts/{strat_id}")
    assert get_resp.status_code == 200
    strat_data = get_resp.json()
    assert strat_data["id"] == strat_id
    assert strat_data["total_quantity"] == 300000.0

    # 3. Get Comparison by ID
    comp_resp = client.get(f"/api/v1/contracts/{strat_id}/comparison")
    assert comp_resp.status_code == 200

    # 4. Get Scenarios by ID
    scen_resp = client.get(f"/api/v1/contracts/{strat_id}/scenarios")
    assert scen_resp.status_code == 200
    assert len(scen_resp.json()) == 3

    # 5. Get Break-even by ID
    be_resp = client.get(f"/api/v1/contracts/{strat_id}/break-even")
    assert be_resp.status_code == 200
    assert be_resp.json()["status"] == "AVAILABLE"

    # 6. Coverage Simulation
    cov_resp = client.post("/api/v1/contracts/coverage", json={
        "total_quantity": 300000,
        "coverage_percentage": 75,
        "contract_rate": 23.28,
        "spot_expected_rate": 24.30,
        "spot_p10": 22.80,
        "spot_p90": 26.50
    })
    assert cov_resp.status_code == 200
    cov_data = cov_resp.json()
    assert cov_data["contracted_quantity_mt"] == 225000.0
    assert cov_data["spot_quantity_mt"] == 75000.0

def test_edge_cases_and_port_gating():
    """Test error handling for zero quantities and Newcastlemax port gating."""
    with pytest.raises(ValueError):
        VoyagePlanningService.plan_voyages(0, 75000)

    with pytest.raises(ValueError):
        VoyagePlanningService.plan_voyages(300000, 0)

    # Newcastlemax vessel class at Paradip triggers port FAIL gating
    resp = client.post("/api/v1/contracts/analyze", json={
        "total_requirement_mt": 300000,
        "parcel_size_mt": 75000,
        "vessel_class": "NEWCASTLEMAX"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["port_feasibility_status"] == "FAIL"
    assert data["decision_confidence"] == DecisionConfidence.LOW
