import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.enums import (
    RiskType,
    RiskSeverity,
    RiskStatus,
    TidalWindowStatus,
    CongestionIndicator,
    DataStatusType,
)
from app.services.risk import (
    WeatherRiskService,
    SyntheticWeatherAdapter,
    PublicWeatherAdapter,
    LicensedWeatherAdapter,
    TidalGateScheduler,
    CongestionRiskService,
    SyntheticCongestionAdapter,
    PortOperationalRiskService,
    TimingRiskService,
    IdleRiskService,
    DataQualityRiskService,
    RiskAggregationService,
    RiskEngine,
)
from app.repositories.risk_repo import RiskRepository

client = TestClient(app)


# ==============================================================================
# 1. WEATHER INTELLIGENCE TESTS
# ==============================================================================

def test_weather_provider_pattern():
    """Verify provider architecture and fallback handling."""
    synth = SyntheticWeatherAdapter()
    weather = synth.get_current_weather("port-inprt", "Paradip Port")
    assert weather is not None
    assert weather["is_synthetic"] is True
    assert "wind_speed_knots" in weather
    assert "wave_height_m" in weather

    # Public adapter fallback
    public = PublicWeatherAdapter(fallback_adapter=synth)
    res_pub = public.get_current_weather("port-inprt")
    assert res_pub["data_source"] == "PUBLIC_FALLBACK"

    # Licensed adapter fallback
    licensed = LicensedWeatherAdapter(fallback_adapter=synth)
    res_lic = licensed.get_current_weather("port-inprt")
    assert res_lic["data_source"] == "LICENSED_FALLBACK"


def test_weather_bulk_cargo_rain_stoppage():
    """Test precipitation impact on dry bulk moisture-sensitive commodities."""
    service = WeatherRiskService()
    
    # Low rain / dry conditions
    mock_provider = SyntheticWeatherAdapter()
    eval_res = service.evaluate_weather_risk("port-inprt", "Paradip Port", cargo_type="COKING_COAL")
    assert eval_res["port_id"] == "port-inprt"
    assert eval_res["severity"] in [RiskSeverity.LOW.value, RiskSeverity.MEDIUM.value, RiskSeverity.HIGH.value, RiskSeverity.CRITICAL.value]
    assert "estimated_weather_delay_hours" in eval_res


def test_weather_forecast_generation():
    """Test 7-day marine forecast generation."""
    synth = SyntheticWeatherAdapter()
    forecast = synth.get_weather_forecast("port-inprt", days=7, port_name="Paradip")
    assert len(forecast) == 7
    for f in forecast:
        assert "wind_speed_knots" in f
        assert "wave_height_m" in f
        assert "precipitation_mm" in f


# ==============================================================================
# 2. TIDAL GATE SCHEDULER TESTS
# ==============================================================================

def test_tidal_gate_missing_draft_returns_unknown():
    """STRICT REQUIREMENT: Missing vessel draft must return UNKNOWN, never inferred from DWT."""
    res = TidalGateScheduler.evaluate_ukc_feasibility(
        vessel_draft_m=None,
        berth_draft_m=14.5,
        port_id="port-inprt"
    )
    assert res["status"] == TidalWindowStatus.UNKNOWN.value
    assert res["vessel_draft_m"] is None
    assert "cannot be determined" in res["explanation"]
    assert "will not be inferred from DWT" in res["explanation"]


def test_tidal_gate_missing_berth_draft_returns_unknown():
    """Missing berth draft must return UNKNOWN."""
    res = TidalGateScheduler.evaluate_ukc_feasibility(
        vessel_draft_m=12.5,
        berth_draft_m=None,
        port_id="port-inprt"
    )
    assert res["status"] == TidalWindowStatus.UNKNOWN.value
    assert res["available_depth_m"] is None


def test_tidal_gate_all_tide_pass():
    """Vessel draft clears even at Mean Low Water -> PASS."""
    # Berth depth 16.0m, draft 12.0m + 0.5m UKC = 12.5m required depth. MLW is +0.4m -> 16.4m available depth.
    res = TidalGateScheduler.evaluate_ukc_feasibility(
        vessel_draft_m=12.0,
        berth_draft_m=16.0,
        port_id="port-inprt",
        port_name="Paradip Port",
        required_ukc_m=0.5
    )
    assert res["status"] == TidalWindowStatus.PASS.value
    assert res["ukc_margin_m"] > 0
    assert "All-tide accessibility confirmed" in res["explanation"]


def test_tidal_gate_conditional_high_water_required():
    """Vessel draft cannot clear low water but clears high water -> CONDITIONAL."""
    # Haldia: MHW +5.8m, MLW +1.1m. Berth depth 8.5m.
    # Vessel draft 12.0m + 0.5m UKC = 12.5m required.
    # At low water: 8.5 + 1.1 = 9.6m (fails).
    # At high water: 8.5 + 5.8 = 14.3m (passes!).
    res = TidalGateScheduler.evaluate_ukc_feasibility(
        vessel_draft_m=12.0,
        berth_draft_m=8.5,
        port_id="port-inhal",
        port_name="Haldia Dock Complex",
        required_ukc_m=0.5
    )
    assert res["status"] == TidalWindowStatus.CONDITIONAL.value
    assert "Tidal gate dependency" in res["explanation"]
    assert len(res["high_water_slots"]) > 0


def test_tidal_gate_physical_depth_failure():
    """Vessel draft exceeds even maximum spring high water -> FAIL."""
    # Berth depth 8.0m, MHW 2.5m -> max peak 10.5m.
    # Vessel draft 14.0m + 0.5m UKC = 14.5m required.
    res = TidalGateScheduler.evaluate_ukc_feasibility(
        vessel_draft_m=14.0,
        berth_draft_m=8.0,
        port_id="port-inprt",
        port_name="Paradip Port",
        required_ukc_m=0.5
    )
    assert res["status"] == TidalWindowStatus.FAIL.value
    assert "Physical depth failure" in res["explanation"]
    assert res["ukc_margin_m"] < 0


def test_tidal_window_generation():
    """Verify semi-diurnal high and low water windows."""
    now = datetime.now(timezone.utc)
    slots = TidalGateScheduler.generate_tidal_windows(
        port_id="port-inhal",
        start_time=now,
        days=2,
        port_name="Haldia",
        berth_draft=8.5
    )
    assert len(slots) >= 6
    hw_slots = [s for s in slots if s["event_type"] == "HIGH_WATER"]
    lw_slots = [s for s in slots if s["event_type"] == "LOW_WATER"]
    assert len(hw_slots) > 0
    assert len(lw_slots) > 0


# ==============================================================================
# 3. PORT CONGESTION INTELLIGENCE TESTS
# ==============================================================================

def test_congestion_risk_evaluation():
    """Verify queue metrics and demurrage financial exposure."""
    service = CongestionRiskService()
    res = service.evaluate_congestion_risk(
        port_id="port-inprt",
        port_name="Paradip Port",
        vessel_class="PANAMAX",
        laytime_allowed_hours=24.0,
        demurrage_rate_usd_per_day=18000.0
    )
    assert res["indicator"] in [CongestionIndicator.MODERATE.value, CongestionIndicator.SEVERE.value]
    assert res["avg_wait_hours"] > 0
    assert res["demurrage_exposure_usd"] is not None
    assert res["demurrage_hours"] >= 0
    assert len(res["history"]) == 14


def test_congestion_no_demurrage_within_laytime():
    """Verify demurrage is zero when expected wait is within laytime."""
    service = CongestionRiskService()
    res = service.evaluate_congestion_risk(
        port_id="port-indhm",
        port_name="Dhamra Port",
        vessel_class="PANAMAX",
        laytime_allowed_hours=72.0, # Generous laytime
        demurrage_rate_usd_per_day=18000.0
    )
    assert res["demurrage_hours"] == 0.0
    assert res["demurrage_exposure_usd"] == 0.0


# ==============================================================================
# 4. TIMING & OPERATIONAL RISK TESTS
# ==============================================================================

def test_timing_laycan_breach_is_critical():
    """If ETA > laycan cancelling date -> CRITICAL."""
    now = datetime.now(timezone.utc)
    eta = now + timedelta(days=10)
    laycan_to = now + timedelta(days=8)
    
    res = TimingRiskService.evaluate_laycan_risk(
        eta=eta,
        laycan_from=now + timedelta(days=5),
        laycan_to=laycan_to,
        vessel_name="MV Vishva Vijay"
    )
    assert res["severity"] == RiskSeverity.CRITICAL.value
    assert res["buffer_hours"] < 0
    assert "CRITICAL LAYCAN BREACH" in res["explanation"]


def test_timing_laycan_tight_buffer_is_high():
    """If buffer is under 24 hours -> HIGH."""
    now = datetime.now(timezone.utc)
    eta = now + timedelta(days=5, hours=10)
    laycan_to = now + timedelta(days=6) # 14h buffer
    
    res = TimingRiskService.evaluate_laycan_risk(
        eta=eta,
        laycan_from=now + timedelta(days=4),
        laycan_to=laycan_to
    )
    assert res["severity"] == RiskSeverity.HIGH.value
    assert 0 < res["buffer_hours"] < 24.0


def test_timing_missing_eta_returns_unknown():
    """Missing ETA or Laycan returns UNKNOWN."""
    res = TimingRiskService.evaluate_laycan_risk(
        eta=None,
        laycan_from=None,
        laycan_to=datetime.now(timezone.utc)
    )
    assert res["severity"] == RiskSeverity.UNKNOWN.value


def test_data_quality_service():
    """Quantifies data gaps and staleness without guessing."""
    now = datetime.now(timezone.utc)
    res = DataQualityRiskService.evaluate_data_quality(
        entity_type="VESSEL",
        entity_id="vessel-001",
        provided_fields={"draft": 12.0, "loa": None},
        required_fields=["draft", "loa", "beam"],
        timestamp_field=now - timedelta(hours=60) # Stale
    )
    assert res["is_stale"] is True
    assert "loa" in res["missing_fields"]
    assert "beam" in res["missing_fields"]
    assert res["confidence"] == "LOW_CONFIDENCE"
    assert res["severity"] == RiskSeverity.HIGH.value


# ==============================================================================
# 5. RISK AGGREGATION & RISK ENGINE TESTS
# ==============================================================================

def test_risk_aggregation_deterministic_hierarchy():
    """Aggregates with strict deterministic rule: CRITICAL > HIGH > MEDIUM > LOW."""
    assert RiskAggregationService.determine_overall_severity(["LOW", "MEDIUM", "CRITICAL"]) == "CRITICAL"
    assert RiskAggregationService.determine_overall_severity(["LOW", "HIGH", "MEDIUM"]) == "HIGH"
    assert RiskAggregationService.determine_overall_severity(["LOW", "MEDIUM", "LOW"]) == "MEDIUM"
    assert RiskAggregationService.determine_overall_severity(["LOW", "LOW"]) == "LOW"
    assert RiskAggregationService.determine_overall_severity(["UNKNOWN", "UNKNOWN"]) == "UNKNOWN"


def test_risk_engine_port_evaluation():
    """Verify comprehensive port operational risk evaluation."""
    engine = RiskEngine()
    res = engine.evaluate_port_risk(
        port_id="port-inprt",
        port_name="Paradip Port",
        vessel_draft_m=14.0,
        berth_draft_m=16.0,
        cargo_type="COKING_COAL"
    )
    assert res["port_id"] == "port-inprt"
    assert "overall_severity" in res
    assert "congestion" in res["components"]
    assert "weather" in res["components"]
    assert "tidal" in res["components"]
    assert "operations" in res["components"]
    assert "financial_exposure" in res
    assert res["financial_exposure"]["total_exposure_usd"] >= 0


def test_risk_engine_voyage_evaluation():
    """Verify end-to-end voyage risk evaluation combining origin, dest, vessel, timing."""
    engine = RiskEngine()
    now = datetime.now(timezone.utc)
    res = engine.evaluate_voyage_risk(
        origin_port_id="port-auncb",
        origin_port_name="Newcastle Port",
        destination_port_id="port-inprt",
        destination_port_name="Paradip Port",
        vessel_name="MV Vishva Vijay",
        vessel_class="PANAMAX",
        vessel_draft_m=14.2,
        origin_berth_draft_m=15.2,
        destination_berth_draft_m=16.0,
        cargo_type="COKING_COAL",
        eta_origin=now + timedelta(days=12),
        laycan_from=now + timedelta(days=10),
        laycan_to=now + timedelta(days=14)
    )
    assert res["origin_port"]["id"] == "port-auncb"
    assert res["destination_port"]["id"] == "port-inprt"
    assert "timing_risk" in res
    assert "data_quality" in res
    assert res["overall_severity"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"]
    assert res["financial_exposure"]["total_exposure_usd"] >= 0


# ==============================================================================
# 6. REST API INTEGRATION TESTS
# ==============================================================================

def test_api_get_risk_summary():
    """GET /api/v1/risk returns unified risk summary."""
    response = client.get("/api/v1/risk")
    assert response.status_code == 200
    data = response.json()
    assert "total_active_events" in data
    assert "overall_operational_severity" in data
    assert "total_financial_exposure_usd" in data
    assert "events" in data
    assert len(data["events"]) > 0


def test_api_get_risk_events_filtered():
    """GET /api/v1/risk/events supports multi-category filters."""
    response = client.get("/api/v1/risk/events?severity=HIGH")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    for e in events:
        assert e["severity"] == "HIGH"


def test_api_get_congestion_ports():
    """GET /api/v1/congestion/ports returns port congestion records."""
    response = client.get("/api/v1/congestion/ports")
    assert response.status_code == 200
    records = response.json()
    assert len(records) > 0
    assert "waiting_vessels_count" in records[0]


def test_api_analyze_port_congestion():
    """POST /api/v1/congestion/analyze evaluates queue and demurrage."""
    response = client.post("/api/v1/congestion/analyze?port_id=port-inprt&vessel_class=PANAMAX&laytime_allowed_hours=36")
    assert response.status_code == 200
    data = response.json()
    assert data["port_id"] == "port-inprt"
    assert "demurrage_exposure_usd" in data


def test_api_get_weather_port():
    """GET /api/v1/weather/ports/{port_id} returns weather & forecast."""
    response = client.get("/api/v1/weather/ports/port-inprt")
    assert response.status_code == 200
    data = response.json()
    assert data["port_id"] == "port-inprt"
    assert "handling_stoppage_risk" in data
    assert len(data["forecast"]) == 7


def test_api_get_tidal_windows():
    """GET /api/v1/tidal/ports/{port_id} returns tidal windows."""
    response = client.get("/api/v1/tidal/ports/port-inhal")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_api_post_tidal_evaluate():
    """POST /api/v1/tidal/evaluate returns strict UKC assessment."""
    payload = {
        "port_id": "port-inhal",
        "vessel_draft_m": 12.0,
        "berth_draft_m": 8.5,
        "required_ukc_m": 0.5
    }
    response = client.post("/api/v1/tidal/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["PASS", "CONDITIONAL", "FAIL", "UNKNOWN"]
    assert "explanation" in data


def test_api_post_voyage_risk_analyze():
    """POST /api/v1/risk/analyze/voyage returns full voyage risk breakdown."""
    payload = {
        "origin_port_id": "port-auncb",
        "destination_port_id": "port-inprt",
        "vessel_class": "PANAMAX",
        "vessel_draft_m": 14.0,
        "origin_berth_draft_m": 15.2,
        "destination_berth_draft_m": 16.0,
        "cargo_type": "COKING_COAL"
    }
    response = client.post("/api/v1/risk/analyze/voyage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "overall_severity" in data
    assert "financial_exposure" in data
    assert "origin_port" in data
    assert "destination_port" in data
