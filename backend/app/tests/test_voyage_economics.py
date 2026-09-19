import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.enums import (
    DataStatusType,
    CostComponentType,
    VoyageScenarioType,
    SpeedScenarioStatus,
)
from app.services.economics.bunker_service import BunkerPriceProvider, BunkerCostService
from app.services.economics.port_cost_service import (
    PublicPortTariffAdapter,
    SyntheticPortCostAdapter,
    PortCostService,
)
from app.services.economics.time_cost_service import TimeCostService
from app.services.economics.delay_cost_service import DelayCostService
from app.services.economics.repositioning_cost_service import RepositioningCostService
from app.services.economics.speed_scenario_service import SpeedScenarioService
from app.services.economics.speed_break_even_service import SpeedBreakEvenService
from app.services.economics.voyage_scenario_service import VoyageScenarioService
from app.services.economics.sensitivity_service import SensitivityService
from app.services.economics.voyage_economics_service import VoyageEconomicsService

client = TestClient(app)


# ----------------------------------------------------
# 1. BUNKER COST ENGINE TESTS
# ----------------------------------------------------

def test_bunker_cost_valid_calculation():
    res = BunkerCostService.calculate_bunker_cost(
        distance_nm=5850.0,
        speed_knots=11.5,
        consumption_mtpd=32.0,
        bunker_price_usd_per_mt=628.50,
        port_days=4.0,
        port_consumption_mtpd=3.0
    )
    assert res["is_calculable"] is True
    assert res["sailing_hours"] == round(5850.0 / 11.5, 2)
    assert res["sailing_days"] == round(res["sailing_hours"] / 24.0, 3)
    assert res["fuel_consumed_mt"] > 0
    assert res["bunker_cost_usd"] > 0
    assert res["fuel_consumed_mt"] == round((res["sailing_days"] * 32.0) + (4.0 * 3.0), 2)
    assert res["bunker_cost_usd"] == round(res["fuel_consumed_mt"] * 628.50, 2)


def test_bunker_cost_missing_consumption_returns_unknown():
    res = BunkerCostService.calculate_bunker_cost(
        distance_nm=5850.0,
        speed_knots=11.5,
        consumption_mtpd=None,
        bunker_price_usd_per_mt=628.50
    )
    assert res["is_calculable"] is False
    assert res["data_status"] == DataStatusType.UNKNOWN
    assert res["fuel_consumed_mt"] is None
    assert res["bunker_cost_usd"] is None
    assert "unavailable" in res["explanation"].lower()


def test_bunker_cost_invalid_speed_or_distance():
    res1 = BunkerCostService.calculate_bunker_cost(
        distance_nm=0.0,
        speed_knots=11.5,
        consumption_mtpd=32.0,
        bunker_price_usd_per_mt=628.50
    )
    assert res1["is_calculable"] is False
    assert res1["data_status"] == DataStatusType.UNKNOWN

    res2 = BunkerCostService.calculate_bunker_cost(
        distance_nm=5850.0,
        speed_knots=-2.0,
        consumption_mtpd=32.0,
        bunker_price_usd_per_mt=628.50
    )
    assert res2["is_calculable"] is False


def test_bunker_price_provider_benchmarks():
    prices = BunkerPriceProvider.get_prices()
    assert len(prices) >= 8
    hubs = {p["port_name"] for p in prices}
    assert "SINGAPORE" in hubs
    assert "ROTTERDAM" in hubs
    assert "PARADIP" in hubs
    assert "NEWCASTLE" in hubs

    sg_vlsfo = BunkerPriceProvider.get_price("SINGAPORE", "VLSFO")
    assert sg_vlsfo is not None
    assert sg_vlsfo["price_usd_per_mt"] > 500.0


# ----------------------------------------------------
# 2. PORT COST ENGINE TESTS
# ----------------------------------------------------

def test_port_cost_service_public_tariffs():
    adapter = PublicPortTariffAdapter()
    res = adapter.calculate_port_disbursement(
        port_unlocode="INPRT",
        port_name="Paradip Port",
        operation_type="DISCHARGE",
        cargo_tonnage_mt=75000.0,
        vessel_grt=45000.0
    )
    assert res["is_supported"] is True
    assert res["data_status"] == DataStatusType.PUBLIC
    assert res["total_port_cost_usd"] > 100000.0
    comp_types = [c["component_type"] for c in res["components"]]
    assert CostComponentType.PORT_DUES in comp_types
    assert CostComponentType.BERTH_CHARGES in comp_types
    assert CostComponentType.CARGO_HANDLING in comp_types


def test_port_cost_service_unrecorded_port_fallback():
    service = PortCostService()
    res = service.calculate_voyage_port_costs(
        origin_unlocode="UNKNOWN1",
        origin_name="Unknown Port Alpha",
        destination_unlocode="UNKNOWN2",
        destination_name="Unknown Port Beta",
        cargo_quantity_mt=50000.0
    )
    assert res["total_port_cost_usd"] > 0
    assert res["data_status"] == DataStatusType.SYNTHETIC


# ----------------------------------------------------
# 3. TIME COST ENGINE TESTS
# ----------------------------------------------------

def test_time_cost_valid_calculation():
    res = TimeCostService.calculate_time_cost(
        sailing_days=21.2,
        port_days=4.5,
        waiting_days=1.5,
        daily_charter_rate_usd=16200.0,
        daily_opex_usd=2500.0,
        cargo_quantity_mt=75000.0
    )
    assert res["is_calculable"] is True
    assert res["total_voyage_days"] == 27.2
    assert res["charter_hire_cost_usd"] == round(27.2 * 16200.0, 2)
    assert res["opex_cost_usd"] == round(27.2 * 2500.0, 2)
    assert res["total_time_cost_usd"] == round(res["charter_hire_cost_usd"] + res["opex_cost_usd"], 2)


def test_time_cost_missing_hire_rate_returns_unknown():
    res = TimeCostService.calculate_time_cost(
        sailing_days=20.0,
        port_days=4.0,
        daily_charter_rate_usd=None,
        vessel_class=None,
        allow_benchmark_fallback=False
    )
    assert res["is_calculable"] is False
    assert res["data_status"] == DataStatusType.UNKNOWN
    assert res["total_time_cost_usd"] is None


# ----------------------------------------------------
# 4. DELAY & DEMURRAGE EXPOSURE TESTS
# ----------------------------------------------------

def test_delay_cost_exposure_vs_actual_demurrage():
    res = DelayCostService.calculate_delay_exposure(
        congestion_wait_hours=48.0,
        weather_stoppage_hours=12.0,
        tidal_wait_hours=6.0,
        laytime_allowed_hours=36.0,
        demurrage_rate_usd_per_day=18000.0,
        cargo_quantity_mt=75000.0
    )
    assert res["is_actual_demurrage"] is False
    assert res["exposure_classification"] == "EXPECTED_DEMURRAGE_EXPOSURE"
    assert res["total_delay_hours"] == 66.0
    assert res["net_demurrage_hours"] == 30.0 # 66 - 36
    assert res["demurrage_exposure_usd"] == round((30.0 / 24.0) * 18000.0, 2)


def test_delay_cost_within_laytime_zero_exposure():
    res = DelayCostService.calculate_delay_exposure(
        congestion_wait_hours=12.0,
        weather_stoppage_hours=6.0,
        tidal_wait_hours=0.0,
        laytime_allowed_hours=36.0
    )
    assert res["net_demurrage_hours"] == 0.0
    assert res["demurrage_exposure_usd"] == 0.0


# ----------------------------------------------------
# 5. REPOSITIONING COST TESTS
# ----------------------------------------------------

def test_repositioning_cost_already_at_port():
    res = RepositioningCostService.calculate_repositioning_cost(
        ballast_distance_nm=0.0,
        is_already_at_load_port=True
    )
    assert res["is_positioned"] is True
    assert res["total_repositioning_cost_usd"] == 0.0


def test_repositioning_cost_ballast_transit():
    res = RepositioningCostService.calculate_repositioning_cost(
        ballast_distance_nm=2400.0,
        ballast_speed_knots=12.0,
        ballast_consumption_mtpd=26.0,
        bunker_price_usd_per_mt=628.50,
        idle_days=2.0,
        daily_idle_cost_usd=5000.0
    )
    assert res["is_positioned"] is False
    assert res["ballast_sailing_days"] == round((2400.0 / 12.0) / 24.0, 2)
    assert res["repositioning_bunker_cost_usd"] > 0
    assert res["idle_cost_usd"] == 10000.0
    assert res["total_repositioning_cost_usd"] == round(res["repositioning_bunker_cost_usd"] + 10000.0, 2)


# ----------------------------------------------------
# 6. SPEED SCENARIO & BREAK-EVEN TESTS
# ----------------------------------------------------

def test_speed_scenario_service_cubic_admiralty_curve():
    res = SpeedScenarioService.evaluate_speed_scenarios(
        distance_nm=5850.0,
        baseline_speed_knots=13.0,
        baseline_consumption_mtpd=32.0,
        bunker_price_usd_per_mt=628.50,
        daily_charter_rate_usd=16200.0,
        candidate_speeds=[10.0, 11.0, 12.0, 13.0, 14.0]
    )
    assert res["can_determine_optimum"] is True
    scenarios = res["scenarios"]
    assert len(scenarios) == 5

    # Verify cubic relationship: F(14) > F(13) > F(12) > F(10)
    burn_10 = next(s for s in scenarios if s["speed_knots"] == 10.0)["fuel_consumption_mtpd"]
    burn_13 = next(s for s in scenarios if s["speed_knots"] == 13.0)["fuel_consumption_mtpd"]
    burn_14 = next(s for s in scenarios if s["speed_knots"] == 14.0)["fuel_consumption_mtpd"]

    assert burn_10 < burn_13 < burn_14
    assert round(burn_13, 1) == 32.0

    # Ensure economically preferred speed status is assigned
    statuses = [s["status"] for s in scenarios]
    assert SpeedScenarioStatus.ECONOMICALLY_PREFERRED in statuses
    assert "Economically preferred speed under available assumptions" in res["verdict_label"]


def test_speed_scenario_service_speed_exceeds_bounds():
    res = SpeedScenarioService.evaluate_speed_scenarios(
        distance_nm=5850.0,
        candidate_speeds=[6.0, 12.0, 16.0],
        max_vessel_speed_knots=14.5,
        min_vessel_speed_knots=7.5
    )
    s_low = next(s for s in res["scenarios"] if s["speed_knots"] == 6.0)
    s_high = next(s for s in res["scenarios"] if s["speed_knots"] == 16.0)
    assert s_low["status"] == SpeedScenarioStatus.SUBOPTIMAL
    assert s_high["status"] == SpeedScenarioStatus.SPEED_EXCEEDS_RATING


def test_speed_break_even_service_calculation():
    res = SpeedBreakEvenService.calculate_break_even(
        distance_nm=5850.0,
        baseline_consumption_mtpd=32.0,
        baseline_speed_knots=13.0,
        bunker_price_usd_per_mt=628.50,
        daily_charter_rate_usd=16200.0
    )
    assert res["is_evaluable"] is True
    assert res["break_even_speed_knots"] is not None
    assert 9.5 <= res["break_even_speed_knots"] <= 13.5
    assert len(res["marginal_steps"]) > 0


def test_speed_break_even_service_missing_data():
    res = SpeedBreakEvenService.calculate_break_even(
        distance_nm=5850.0,
        baseline_consumption_mtpd=None,
        bunker_price_usd_per_mt=628.50
    )
    assert res["is_evaluable"] is False
    assert "Insufficient data to determine economic speed." in res["verdict"]


# ----------------------------------------------------
# 7. VOYAGE SCENARIOS & SENSITIVITY TESTS
# ----------------------------------------------------

def test_voyage_scenarios_all_six_canonical():
    scenarios = VoyageScenarioService.generate_scenarios(
        distance_nm=5850.0,
        cargo_quantity_mt=75000.0
    )
    assert len(scenarios) == 6
    names = {s["scenario_name"] for s in scenarios}
    assert VoyageScenarioType.BASE in names
    assert VoyageScenarioType.LOW_COST in names
    assert VoyageScenarioType.HIGH_COST in names
    assert VoyageScenarioType.DELAY in names
    assert VoyageScenarioType.SLOW_STEAM in names
    assert VoyageScenarioType.FAST_TRANSIT in names

    base = next(s for s in scenarios if s["scenario_name"] == VoyageScenarioType.BASE)
    low = next(s for s in scenarios if s["scenario_name"] == VoyageScenarioType.LOW_COST)
    high = next(s for s in scenarios if s["scenario_name"] == VoyageScenarioType.HIGH_COST)
    assert low["total_cost"] < base["total_cost"] < high["total_cost"]


def test_sensitivity_service_multivariable():
    res = SensitivityService.calculate_sensitivities(
        distance_nm=5850.0,
        base_cargo_quantity_mt=75000.0
    )
    assert len(res["bunker_sensitivity"]) == 5
    assert len(res["freight_sensitivity"]) == 5
    assert len(res["speed_sensitivity"]) == 7
    assert len(res["delay_sensitivity"]) == 6
    assert len(res["cargo_sensitivity"]) == 5
    assert len(res["hire_rate_sensitivity"]) == 5


# ----------------------------------------------------
# 8. MASTER ORCHESTRATOR & DATA QUALITY TESTS
# ----------------------------------------------------

def test_voyage_economics_master_orchestrator():
    db = SessionLocal()
    try:
        service = VoyageEconomicsService(db=db)
        res = service.analyze_voyage_economics(
            origin_port_id="newcastle-au",
            destination_port_id="paradip-in",
            cargo_quantity_mt=75000.0,
            cargo_type="COKING_COAL",
            persist=False
        )
        assert res["total_voyage_cost_usd"] > 0
        assert res["cost_per_mt_usd"] > 0
        assert res["freight_cost_usd"] > 0
        assert res["bunker_cost_usd"] > 0
        assert res["port_cost_usd"] > 0
        assert res["time_cost_usd"] > 0

        # Verify Data Quality Scorecard
        dq = res["data_quality_report"]
        assert dq["overall_confidence"] in ["HIGH", "MEDIUM", "LOW"]
        assert len(dq["items"]) >= 5
    finally:
        db.close()


# ----------------------------------------------------
# 9. API INTEGRATION TESTS
# ----------------------------------------------------

def test_api_get_voyage_economics_latest():
    response = client.get("/api/v1/voyage-economics/latest")
    assert response.status_code == 200
    data = response.json()
    assert "total_voyage_cost_usd" in data
    assert "cost_per_mt_usd" in data
    assert len(data["scenarios"]) == 6
    assert len(data["components"]) > 0


def test_api_post_voyage_economics_analyze():
    payload = {
        "origin_port_id": "newcastle-au",
        "destination_port_id": "paradip-in",
        "cargo_quantity_mt": 75000.0,
        "cargo_type": "COKING_COAL",
        "custom_speed_knots": 12.0,
        "custom_freight_rate_usd_per_mt": 15.00
    }
    response = client.post("/api/v1/voyage-economics/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["freight_rate_usd_per_mt"] == 15.00
    assert data["operating_speed_knots"] == 12.0


def test_api_bunker_calculate_and_prices():
    calc_res = client.post("/api/v1/bunker/calculate", json={
        "distance_nm": 5850.0,
        "speed_knots": 11.5,
        "consumption_mtpd": 32.0,
        "bunker_price_usd_per_mt": 630.0
    })
    assert calc_res.status_code == 200
    assert calc_res.json()["is_calculable"] is True
    assert calc_res.json()["bunker_cost_usd"] > 0

    prices_res = client.get("/api/v1/bunker/prices")
    assert prices_res.status_code == 200
    assert len(prices_res.json()) >= 5


def test_api_speed_break_even():
    res = client.post("/api/v1/speed/break-even", json={
        "distance_nm": 5850.0,
        "cargo_quantity_mt": 75000.0,
        "baseline_speed_knots": 13.0,
        "baseline_consumption_mtpd": 32.0,
        "bunker_price_usd_per_mt": 628.50,
        "daily_charter_rate_usd": 16200.0
    })
    assert res.status_code == 200
    assert res.json()["is_evaluable"] is True
    assert res.json()["break_even_speed_knots"] is not None


def test_api_voyage_sensitivity():
    res = client.post("/api/v1/voyage-economics/sensitivity", json={
        "distance_nm": 5850.0,
        "base_cargo_quantity_mt": 75000.0,
        "base_freight_rate_usd_per_mt": 14.50,
        "base_bunker_price_usd_per_mt": 628.50
    })
    assert res.status_code == 200
    assert "bunker_sensitivity" in res.json()
    assert len(res.json()["bunker_sensitivity"]) == 5
