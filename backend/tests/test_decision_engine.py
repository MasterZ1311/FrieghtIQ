import pytest
from datetime import date
from app.database import SessionLocal
from app.services.vessel_service import recommend_vessels
from app.services.market_entry_service import generate_signal
from app.services.contract_service import compare_contracts
from app.services.idle_service import calculate_idle_scenario
from app.services.risk_service import score_risk
from app.domain.risk_rules import RISK_WEIGHTS


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_vessel_selection_panamax_preferred_for_standard_coal(db):
    res = recommend_vessels(
        db=db,
        origin="Australia",
        destination="Visakhapatnam",
        commodity="Coal",
        cargo_mt=70000,
    )
    assert res["recommended_class"] == "Panamax"
    assert len(res["alternatives"]) == 4
    assert len(res["ranked_summary"]) == 4

    top_summary = res["ranked_summary"][0]
    assert "Panamax" in top_summary
    assert "—" in top_summary

    capesize_opt = next(o for o in res["alternatives"] if o["vessel_class"] == "Capesize")
    assert not capesize_opt["is_feasible"]
    assert capesize_opt["feasibility_status"] == "Infeasible"
    assert capesize_opt["fit_score"] == 0.0
    assert any("infeasible" in s.lower() for s in res["ranked_summary"] if "Capesize" in s)

    panamax_opt = next(o for o in res["alternatives"] if o["vessel_class"] == "Panamax")
    assert panamax_opt["is_feasible"]
    assert panamax_opt["fit_score"] > 70.0
    assert panamax_opt["voyage_days"] > 0.0
    assert panamax_opt["turnaround_days"] > 0.0
    assert panamax_opt["handling_rate_mt_day"] > 0.0
    assert panamax_opt["total_voyage_cost_usd"] > 0.0
    assert panamax_opt["cost_per_mt_usd"] > 0.0
    assert panamax_opt["deadheading_proxy_days"] > 0.0
    assert panamax_opt["idle_risk_score"] > 0.0
    assert len(panamax_opt["reasons"]) >= 3
    assert len(panamax_opt["score_breakdown"]) == 5


def test_vessel_selection_shallow_river_port_haldia(db):
    res = recommend_vessels(
        db=db,
        origin="Australia",
        destination="Haldia",
        commodity="Coal",
        cargo_mt=35000,
    )
    for vc in ["Capesize", "Panamax"]:
        opt = next(o for o in res["alternatives"] if o["vessel_class"] == vc)
        assert not opt["is_feasible"]
        assert "Infeasible" in opt["feasibility_status"]


def test_vessel_selection_deepwater_capesize_gangavaram(db):
    res = recommend_vessels(
        db=db,
        origin="Australia",
        destination="Gangavaram",
        commodity="Iron Ore",
        cargo_mt=160000,
    )
    assert res["recommended_class"] == "Capesize"
    cape_opt = next(o for o in res["alternatives"] if o["vessel_class"] == "Capesize")
    assert cape_opt["is_feasible"]
    assert cape_opt["fit_score"] > 75.0

    for vc in ["Handysize", "Supramax", "Panamax"]:
        opt = next(o for o in res["alternatives"] if o["vessel_class"] == vc)
        assert not opt["is_feasible"]


def test_vessel_selection_underutilization_penalty(db):
    res = recommend_vessels(
        db=db,
        origin="Australia",
        destination="Visakhapatnam",
        commodity="Coal",
        cargo_mt=15000,
    )
    panamax_opt = next(o for o in res["alternatives"] if o["vessel_class"] == "Panamax")
    assert any("under-utilization" in r.lower() for r in panamax_opt["reasons"])


def test_market_entry_urgent_horizon_returns_charter_now(db):
    res = generate_signal(
        db=db,
        origin="Australia",
        destination="Paradip",
        vessel_class="Panamax",
        commodity="Coal",
        cargo_mt=70000,
        urgency_days=5,
    )
    assert res["signal"] == "CHARTER_NOW"
    assert any("urgency" in r.lower() or "laycan" in r.lower() for r in res["reasons"])
    assert res["contract_horizon_days"] == 5


def test_market_entry_falling_trend_sufficient_horizon_returns_wait(db):
    res = generate_signal(
        db=db,
        origin="Australia",
        destination="Paradip",
        vessel_class="Panamax",
        commodity="Coal",
        cargo_mt=70000,
        urgency_days=45,
    )
    assert res["signal"] in ["WAIT", "MONITOR"]
    assert res["z_score"] is not None
    assert res["uncertainty_usd_per_mt"] > 0.0
    assert len(res["alternative_strategies"]) == 3


def test_market_entry_multi_criteria_no_arbitrary_single_threshold(db):
    urgent = generate_signal(db, "Australia", "Paradip", "Panamax", "Coal", 70000, urgency_days=7)
    relaxed = generate_signal(db, "Australia", "Paradip", "Panamax", "Coal", 70000, urgency_days=45)

    assert urgent["signal"] == "CHARTER_NOW"
    assert relaxed["signal"] in ["WAIT", "MONITOR"]
    assert urgent["best_entry_window"] != relaxed["best_entry_window"]


def test_contract_optimization_compares_all_four_strategies(db):
    res = compare_contracts(
        db=db,
        origin="Australia",
        destination="Paradip",
        vessel_class="Panamax",
        commodity="Coal",
        cargo_mt=70000,
        annual_volume_mt=500000,
        planning_horizon_months=12,
    )
    options = res["options"]
    assert len(options) == 4
    contract_types = [o["contract_type"] for o in options]
    assert "Spot" in contract_types
    assert "3-Voyage" in contract_types
    assert "6-Voyage" in contract_types
    assert "12-Voyage" in contract_types

    rates = {o["contract_type"]: o["cost_per_mt"] for o in options}
    assert rates["Spot"] >= rates["3-Voyage"] >= rates["6-Voyage"] >= rates["12-Voyage"]

    spot_opt = next(o for o in options if o["contract_type"] == "Spot")
    term12_opt = next(o for o in options if o["contract_type"] == "12-Voyage")
    assert spot_opt["savings_vs_spot_usd"] == 0.0
    assert spot_opt["exposure_pct"] == 100.0
    assert term12_opt["savings_vs_spot_usd"] > 0.0
    assert term12_opt["exposure_pct"] == 0.0

    assert res["recommended_contract"] in ["Spot", "3-Voyage", "6-Voyage", "12-Voyage"]
    assert res["blended_strategy"] is not None


def test_idle_scenario_all_six_scenarios_simulated(db):
    res = calculate_idle_scenario(
        db=db,
        origin="Australia",
        destination="Paradip",
        vessel_class="Panamax",
        commodity="Coal",
        cargo_mt=70000,
        waiting_days=5.5,
    )
    scenarios = res["simulated_scenarios"]
    assert len(scenarios) == 6

    expected_types = {
        "low_demand",
        "port_congestion",
        "delayed_berth",
        "vessel_waiting",
        "alternate_employment",
        "repositioning",
    }
    actual_types = {s["scenario_type"] for s in scenarios}
    assert actual_types == expected_types

    for sc in scenarios:
        assert sc["financial_impact_usd"] > 0.0
        assert sc["mitigation_benefit_usd"] > 0.0
        assert len(sc["suggested_mitigation"]) > 10
        assert len(sc["operational_action"]) > 10


def test_idle_scenario_zero_waiting_days(db):
    res = calculate_idle_scenario(
        db=db,
        origin="Australia",
        destination="Paradip",
        vessel_class="Panamax",
        commodity="Coal",
        cargo_mt=70000,
        waiting_days=0.0,
    )
    assert res["waiting_days"] == 0.0
    assert res["demurrage_incurred_usd"] == 0.0
    assert res["anchorage_idle_bunker_usd"] == 0.0


def test_risk_engine_all_six_component_scores_and_weights(db):
    res = score_risk(
        db=db,
        origin="Australia",
        destination="Paradip",
        vessel_class="Panamax",
        commodity="Coal",
        cargo_mt=70000,
        contract_type="Spot",
    )
    comp = res["component_scores"]
    assert "freight_volatility" in comp
    assert "port_congestion" in comp
    assert "vessel_availability" in comp
    assert "fuel_bunker_exposure" in comp
    assert "schedule_risk" in comp
    assert "contract_exposure" in comp

    for k, v in comp.items():
        assert 0.0 <= v <= 100.0, f"Component {k} out of bounds: {v}"

    assert 0.0 <= res["overall_risk_score"] <= 100.0
    assert res["overall_risk_level"] in ["Low", "Medium", "High", "Critical"]
    assert sum(RISK_WEIGHTS.values()) == pytest.approx(1.0, 0.001)


def test_risk_engine_100_percent_deterministic(db):
    r1 = score_risk(db, "Russia", "Paradip", "Capesize", "Coal", 150000, "Spot")
    r2 = score_risk(db, "Russia", "Paradip", "Capesize", "Coal", 150000, "Spot")
    r3 = score_risk(db, "Russia", "Paradip", "Capesize", "Coal", 150000, "Spot")

    assert r1["overall_risk_score"] == r2["overall_risk_score"] == r3["overall_risk_score"]
    assert r1["component_scores"] == r2["component_scores"] == r3["component_scores"]
    assert [f["score"] for f in r1["risk_factors"]] == [f["score"] for f in r2["risk_factors"]]


def test_risk_engine_contract_structure_sensitivity(db):
    r_spot = score_risk(db, "Australia", "Paradip", "Panamax", "Coal", 70000, "Spot")
    r_12v = score_risk(db, "Australia", "Paradip", "Panamax", "Coal", 70000, "12-Voyage")

    assert r_spot["component_scores"]["contract_exposure"] > r_12v["component_scores"]["contract_exposure"]
    assert r_spot["overall_risk_score"] > r_12v["overall_risk_score"]


def test_risk_engine_monsoon_schedule_sensitivity(db):
    r_monsoon = score_risk(db, "Australia", "Paradip", "Panamax", "Coal", 70000, "Spot", laycan_start=date(2026, 7, 15))
    r_dry = score_risk(db, "Australia", "Paradip", "Panamax", "Coal", 70000, "Spot", laycan_start=date(2026, 2, 15))

    assert r_monsoon["component_scores"]["schedule_risk"] > r_dry["component_scores"]["schedule_risk"]
