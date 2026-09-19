import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.enums import (
    VesselEmploymentState,
    EmploymentEventType,
    IdleScenarioType,
    RepositioningDecision,
    DeadheadRiskLevel,
    EmploymentCompatibility,
    VesselStatus,
    DataStatusType,
)
from app.models.ports import Port
from app.models.vessels import Vessel
from app.models.cargo import CargoRequirement
from app.services.idle.state_machine import EmploymentStateMachine
from app.services.idle.idle_exposure import IdleExposureService
from app.services.idle.idle_cost import IdleCostService
from app.services.idle.distance_service import StaticDemoDistanceProvider, RouteDistanceService
from app.services.idle.repositioning_service import RepositioningService
from app.services.idle.deadhead_risk import DeadheadRiskService
from app.services.idle.economics_service import RepositioningEconomicsService
from app.services.idle.alternative_employment import AlternativeEmploymentService
from app.repositories.idle_repo import IdleRepository

client = TestClient(app)


# ==============================================================================
# 1. STATE MACHINE TESTS
# ==============================================================================

def test_state_machine_transitions_valid_sequence():
    """
    Test standard valid lifecycle transition:
    EMPLOYED -> VOYAGE_COMPLETING -> AVAILABLE -> NEXT_EMPLOYMENT_PENDING -> IDLE
    """
    assert EmploymentStateMachine.is_transition_valid(
        VesselEmploymentState.EMPLOYED, VesselEmploymentState.VOYAGE_COMPLETING
    )
    assert EmploymentStateMachine.is_transition_valid(
        VesselEmploymentState.VOYAGE_COMPLETING, VesselEmploymentState.AVAILABLE
    )
    assert EmploymentStateMachine.is_transition_valid(
        VesselEmploymentState.AVAILABLE, VesselEmploymentState.NEXT_EMPLOYMENT_PENDING
    )
    assert EmploymentStateMachine.is_transition_valid(
        VesselEmploymentState.NEXT_EMPLOYMENT_PENDING, VesselEmploymentState.REPOSITIONING
    )
    assert EmploymentStateMachine.is_transition_valid(
        VesselEmploymentState.REPOSITIONING, VesselEmploymentState.EMPLOYED
    )


def test_state_machine_invalid_transitions():
    """Direct jump from EMPLOYED to IDLE or REPOSITIONING without completion is invalid."""
    assert not EmploymentStateMachine.is_transition_valid(
        VesselEmploymentState.EMPLOYED, VesselEmploymentState.IDLE
    )
    assert not EmploymentStateMachine.is_transition_valid(
        VesselEmploymentState.VOYAGE_COMPLETING, VesselEmploymentState.REPOSITIONING
    )


def test_state_machine_evaluation_evidence_driven():
    """Test state deduction strictly adheres to evidence."""
    now = datetime.now(timezone.utc)

    # 1. Unverified particulars and unconfirmed waiting orders -> UNKNOWN
    state, expl = EmploymentStateMachine.evaluate_state(
        vessel_status=VesselStatus.WAITING_ORDERS,
        is_verified_particulars=False,
        has_current_voyage=False,
        voyage_completion_date=None,
        next_employment_confirmed=False,
        idle_days_observed=None,
        now=now
    )
    assert state == VesselEmploymentState.UNKNOWN

    # 2. Laden transit with completion in 24 hours -> VOYAGE_COMPLETING
    state, expl = EmploymentStateMachine.evaluate_state(
        vessel_status=VesselStatus.LADEN_TRANSIT,
        is_verified_particulars=True,
        has_current_voyage=True,
        voyage_completion_date=now + timedelta(hours=24),
        next_employment_confirmed=False,
        idle_days_observed=None,
        now=now
    )
    assert state == VesselEmploymentState.VOYAGE_COMPLETING

    # 3. Anchorage waiting > 3 days idle without fixture -> IDLE
    state, expl = EmploymentStateMachine.evaluate_state(
        vessel_status=VesselStatus.AT_ANCHORAGE,
        is_verified_particulars=True,
        has_current_voyage=False,
        voyage_completion_date=None,
        next_employment_confirmed=False,
        idle_days_observed=5.5,
        now=now
    )
    assert state == VesselEmploymentState.IDLE

    # 4. Anchorage waiting < 3 days -> IDLE_RISK
    state, expl = EmploymentStateMachine.evaluate_state(
        vessel_status=VesselStatus.AT_ANCHORAGE,
        is_verified_particulars=True,
        has_current_voyage=False,
        voyage_completion_date=None,
        next_employment_confirmed=False,
        idle_days_observed=1.2,
        now=now
    )
    assert state == VesselEmploymentState.IDLE_RISK


# ==============================================================================
# 2. IDLE EXPOSURE & COST TESTS
# ==============================================================================

def test_idle_exposure_calculation():
    """Potential Idle Days = Next Employment - Available Time (strict integrity)."""
    t1 = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)

    days, narrative = IdleExposureService.calculate_idle_days(t1, t2)
    assert days == 8.0

    # Missing next employment must return None, NEVER substitute 0
    days_none, _ = IdleExposureService.calculate_idle_days(t1, None)
    assert days_none is None

    # Missing availability must return None
    days_none2, _ = IdleExposureService.calculate_idle_days(None, t2)
    assert days_none2 is None


def test_idle_cost_calculation():
    """Idle Cost = Idle Days × Daily Vessel Cost (no fake cost)."""
    cost, expl = IdleCostService.calculate_idle_cost(
        idle_days=5.0, daily_vessel_cost=15000.0, cost_source_label="Test Charter Rate"
    )
    assert cost == 75000.0

    # Missing daily cost must return None (UNAVAILABLE)
    cost_unavail, expl_unavail = IdleCostService.calculate_idle_cost(
        idle_days=5.0, daily_vessel_cost=None
    )
    assert cost_unavail is None
    assert "DAILY VESSEL COST: NOT AVAILABLE" in expl_unavail

    # Missing idle days must return None
    cost_no_days, _ = IdleCostService.calculate_idle_cost(
        idle_days=None, daily_vessel_cost=15000.0
    )
    assert cost_no_days is None


# ==============================================================================
# 3. ROUTE DISTANCE TESTS
# ==============================================================================

def test_route_distance_provider():
    """Test database route match, geodesic approximation fallback, and label integrity."""
    db = SessionLocal()
    try:
        provider = StaticDemoDistanceProvider()
        p_paradip = db.query(Port).filter(Port.unlocode == "INPRT").first()
        p_newcastle = db.query(Port).filter(Port.unlocode == "AUNCB").first()
        p_vizag = db.query(Port).filter(Port.unlocode == "INVTZ").first()

        assert p_paradip is not None
        assert p_newcastle is not None
        assert p_vizag is not None

        # 1. Direct DB FreightRoute (Newcastle -> Paradip)
        dist, method, expl = provider.get_distance(p_newcastle, p_paradip, db=db)
        assert dist is not None
        assert method == "NAUTICAL_CHART"

        # 2. Geodesic Approximation Fallback (Paradip -> Vizag without explicit FreightRoute record)
        dist_geo, method_geo, expl_geo = provider.get_distance(p_paradip, p_vizag, db=None)
        assert dist_geo is not None
        assert method_geo == "GEODESIC_APPROXIMATION"
        assert "GEODESIC APPROXIMATION" in expl_geo

        # 3. Same port distance
        dist_same, method_same, _ = provider.get_distance(p_paradip, p_paradip, db=db)
        assert dist_same == 0.0
        assert method_same == "SAME_PORT"
    finally:
        db.close()


# ==============================================================================
# 4. REPOSITIONING SERVICE & BUNKER ECONOMICS
# ==============================================================================

def test_repositioning_sailing_time_and_speed_label():
    """Sailing Time = Distance / (Speed * 24). Speed assumption must be explicitly displayed."""
    # 3600 NM @ 12.5 knots = 3600 / 300 = 12.0 days
    days, speed_label = RepositioningService.calculate_sailing_time(3600.0, 12.5)
    assert days == 12.0
    assert speed_label == "Speed assumption: 12.5 knots"

    # Missing speed returns None
    days_none, label_none = RepositioningService.calculate_sailing_time(3600.0, None)
    assert days_none is None
    assert "UNAVAILABLE" in label_none


def test_repositioning_bunker_cost_integrity():
    """Bunker Cost = (Fuel Consumption MT/day * Sailing Days) * Bunker Price $/MT."""
    # 10 days * 25 MT/day = 250 MT. 250 MT * $600 = $150,000
    cost, expl = RepositioningService.calculate_bunker_cost(
        sailing_days=10.0, fuel_consumption_mtpd=25.0, bunker_price_usd_per_mt=600.0
    )
    assert cost == 150000.0

    # Missing bunker price must return None (UNAVAILABLE)
    cost_no_price, expl_no_price = RepositioningService.calculate_bunker_cost(
        sailing_days=10.0, fuel_consumption_mtpd=25.0, bunker_price_usd_per_mt=None
    )
    assert cost_no_price is None
    assert "UNAVAILABLE" in expl_no_price


def test_repositioning_timing_laycan_evaluation():
    """Test ON_TIME, TIGHT, and MISSED_LAYCAN classifications."""
    avail = datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc)
    lay_start = datetime(2026, 10, 10, 0, 0, tzinfo=timezone.utc)
    lay_end = datetime(2026, 10, 15, 0, 0, tzinfo=timezone.utc)

    # 1. 10 days sailing -> arrives Oct 11 (comfortably inside laycan)
    status_on_time, eta1, _ = RepositioningService.evaluate_timing(avail, 10.0, lay_start, lay_end)
    assert status_on_time == "ON_TIME"

    # 2. 14 days sailing -> arrives Oct 15 (less than 1.5 days buffer before lay_end)
    status_tight, eta2, _ = RepositioningService.evaluate_timing(avail, 14.0, lay_start, lay_end)
    assert status_tight == "TIGHT"

    # 3. 18 days sailing -> arrives Oct 19 (after lay_end)
    status_missed, eta3, _ = RepositioningService.evaluate_timing(avail, 18.0, lay_start, lay_end)
    assert status_missed == "MISSED_LAYCAN"


# ==============================================================================
# 5. DEADHEAD RISK EVALUATION
# ==============================================================================

def test_deadhead_risk_rules():
    """Test documented, explainable rule logic."""
    # 1. Port FAIL -> HIGH risk
    risk, expl = DeadheadRiskService.evaluate_risk(
        distance_nm=1200.0, port_compatibility="FAIL", timing_compatibility="ON_TIME",
        has_secured_cargo=True, is_data_complete=True
    )
    assert risk == DeadheadRiskLevel.HIGH

    # 2. Missed laycan -> HIGH risk
    risk_m, _ = DeadheadRiskService.evaluate_risk(
        distance_nm=1200.0, port_compatibility="PASS", timing_compatibility="MISSED_LAYCAN",
        has_secured_cargo=True, is_data_complete=True
    )
    assert risk_m == DeadheadRiskLevel.HIGH

    # 3. Long unhedged ballast > 2500 NM without secured cargo -> HIGH risk
    risk_spec, _ = DeadheadRiskService.evaluate_risk(
        distance_nm=3200.0, port_compatibility="PASS", timing_compatibility="ON_TIME",
        has_secured_cargo=False, is_data_complete=True
    )
    assert risk_spec == DeadheadRiskLevel.HIGH

    # 4. Short ballast <= 1500 NM with PASS and ON_TIME -> LOW risk
    risk_low, _ = DeadheadRiskService.evaluate_risk(
        distance_nm=800.0, port_compatibility="PASS", timing_compatibility="ON_TIME",
        has_secured_cargo=True, is_data_complete=True
    )
    assert risk_low == DeadheadRiskLevel.LOW

    # 5. Incomplete data -> UNKNOWN
    risk_unk, _ = DeadheadRiskService.evaluate_risk(
        distance_nm=None, port_compatibility="PASS", timing_compatibility="ON_TIME",
        has_secured_cargo=True, is_data_complete=False
    )
    assert risk_unk == DeadheadRiskLevel.UNKNOWN


# ==============================================================================
# 6. REPOSITIONING ECONOMICS COMPARISON
# ==============================================================================

def test_economics_comparison_incomplete_without_revenue():
    """Commercial freight revenue must not be invented; returns ECONOMIC_COMPARISON_INCOMPLETE."""
    res = RepositioningEconomicsService.compare_strategies(
        vessel_name="Vishva Vijay",
        idle_days=8.0,
        daily_vessel_cost=14000.0,
        repositioning_options=[{
            "target_port_name": "Newcastle",
            "cargo_name": "Coking Coal",
            "sailing_days": 13.2,
            "distance_nm": 3950.0,
            "distance_method": "NAUTICAL_CHART",
            "estimated_bunker_cost": 108500.0,
            "estimated_total_cost": 293300.0
        }],
        commercial_revenue_usd=None # Unrecorded
    )
    assert res["vessel_name"] == "Vishva Vijay"
    assert "Revenue and net TCE cannot be fabricated" in res["revenue_status"]
    assert res["wait_strategy"]["estimated_total_cost"] == 112000.0
    assert len(res["repositioning_strategies"]) == 1


# ==============================================================================
# 7. INTEGRATION & API ENDPOINTS
# ==============================================================================

def test_api_get_idle_vessels_fleet_overview():
    """GET /api/v1/idle/vessels must return dataset-backed counts without claiming global fleet."""
    res = client.get("/api/v1/idle/vessels")
    assert res.status_code == 200
    data = res.json()
    assert "overview" in data
    assert "vessels" in data

    overview = data["overview"]
    # Exactly 9 vessels exist in the database
    assert overview["dataset_coverage_count"] == 9
    assert "9 vessels in current dataset" in overview["dataset_coverage_label"]
    assert len(data["vessels"]) == 9


def test_api_get_idle_scenarios():
    """GET /api/v1/idle/scenarios returns seeded scenarios."""
    res = client.get("/api/v1/idle/scenarios")
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) >= 3

    # Vishva Vijay scenario
    sc_vv = next((s for s in scenarios if s["vessel_id"] == "vessel-vishva-vijay"), None)
    assert sc_vv is not None
    assert sc_vv["scenario_type"] == "EMPLOYMENT_GAP"
    assert sc_vv["idle_days"] == 8.0

    # Lyric Harmony scenario (unknown next fixture, idle_days is None)
    sc_lh = next((s for s in scenarios if s["vessel_id"] == "vessel-lyric-harmony"), None)
    assert sc_lh is not None
    assert sc_lh["idle_days"] is None


def test_api_post_idle_analyze_vessel():
    """POST /api/v1/idle/analyze analyzes single vessel alternatives and economics."""
    payload = {
        "vessel_id": "vessel-vishva-vijay",
        "daily_vessel_cost_assumption": 14000.0,
        "scenario_type": "EMPLOYMENT_GAP"
    }
    res = client.post("/api/v1/idle/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["vessel_id"] == "vessel-vishva-vijay"
    assert "alternative_candidates" in data
    assert "repositioning_options" in data
    assert "economics_comparison" in data
    assert data["daily_cost_status"] == "SOURCED_OR_CONFIGURED"


def test_api_post_repositioning_analyze():
    """POST /api/v1/repositioning/analyze computes transit and deadhead risk."""
    db = SessionLocal()
    try:
        newcastle = db.query(Port).filter(Port.unlocode == "AUNCB").first()
        assert newcastle is not None
        payload = {
            "vessel_id": "vessel-vishva-vijay",
            "target_port_id": newcastle.id,
            "speed_assumption_knots": 13.0,
            "bunker_price_usd": 620.0,
            "daily_vessel_cost_assumption": 14000.0
        }
        res = client.post("/api/v1/repositioning/analyze", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["speed_knots"] == 13.0
        assert "Speed assumption: 13.0 knots" in data["speed_label"]
        assert data["sailing_days"] is not None
        assert data["deadhead_risk"] in ["LOW", "MEDIUM", "HIGH", "UNKNOWN"]
    finally:
        db.close()


def test_api_get_vessel_employment_timeline():
    """GET /api/v1/vessels/{id}/employment-timeline returns timeline events."""
    res = client.get("/api/v1/vessels/vessel-vishva-vijay/employment-timeline")
    assert res.status_code == 200
    data = res.json()
    assert data["vessel_id"] == "vessel-vishva-vijay"
    assert len(data["events"]) >= 2
    assert data["employment_state"] in [
        VesselEmploymentState.EMPLOYED.value,
        VesselEmploymentState.VOYAGE_COMPLETING.value,
        VesselEmploymentState.AVAILABLE.value,
        VesselEmploymentState.NEXT_EMPLOYMENT_PENDING.value,
        VesselEmploymentState.IDLE_RISK.value,
        VesselEmploymentState.IDLE.value,
        VesselEmploymentState.REPOSITIONING.value,
    ]
