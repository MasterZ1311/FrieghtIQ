"""
FreightIQ Comprehensive Integration Test Suite
==============================================
Validates:
1. Primary Scenario: Australia -> Paradip (70,000 MT bulk cargo, Handysize, Supramax, Panamax, Capesize)
2. Route 2: Indonesia -> Visakhapatnam (55,000 MT coal)
3. Route 3: Mozambique -> Gangavaram (150,000 MT coal, Capesize deepwater)
4. Route 4: United States -> Paradip (70,000 MT coal, Suez routing)
5. All individual modular endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_primary_scenario_australia_to_paradip():
    """
    Mandatory Scenario:
    Australia -> Paradip
    Cargo: bulk cargo (70,000 MT)
    Vessel options: Handysize, Supramax, Panamax, Capesize
    Must produce:
    - freight forecast
    - recommended vessel
    - port compatibility
    - market entry recommendation
    - voyage economics
    - contract comparison
    - risk score
    - explanation
    """
    payload = {
        "origin": "Australia",
        "destination": "Paradip",
        "commodity": "bulk cargo",
        "cargo_mt": 70000.0,
        "urgency_days": 30,
        "annual_volume_mt": 500000.0,
        "planning_horizon_months": 12,
        "bunker_price_usd_per_mt": 650.0,
    }

    resp = client.post("/api/workflow/end-to-end", json=payload)
    assert resp.status_code == 200, f"Workflow failed: {resp.text}"
    data = resp.json()

    # 1. Freight Forecast
    assert "forecast" in data
    fc = data["forecast"]
    assert "predicted_rate_usd_per_mt" in fc
    assert fc["predicted_rate_usd_per_mt"] > 0
    assert "trend" in fc
    assert fc["trend"] in ["rising", "falling", "stable"]
    assert "confidence_pct" in fc
    assert fc["confidence_pct"] > 0
    assert "lower_bound" in fc and "upper_bound" in fc

    # 2. Recommended Vessel & Feasibility across Handysize, Supramax, Panamax, Capesize
    assert "vessel_feasibility" in data
    feasibility_list = data["vessel_feasibility"]
    vessel_classes_present = {v["vessel_class"] for v in feasibility_list}
    expected_classes = {"Handysize", "Supramax", "Panamax", "Capesize"}
    assert expected_classes.issubset(vessel_classes_present), f"Missing vessels: {expected_classes - vessel_classes_present}"

    # Verify Panamax is recommended for 70k MT to Paradip
    assert data["recommended_vessel"] == "Panamax"

    # Verify Capesize port compatibility at Paradip (Draft 18.0m > Paradip 14.5m limit -> Incompatible/False)
    all_ports = data["all_ports_compatibility"]
    assert all_ports["Capesize"]["compatible"] is False
    assert all_ports["Panamax"]["compatible"] is True
    assert all_ports["Supramax"]["compatible"] is True
    assert all_ports["Handysize"]["compatible"] is True

    # 3. Port Compatibility
    assert "port_compatibility" in data
    port_comp = data["port_compatibility"]
    assert port_comp["port"] == "Paradip"
    assert port_comp["compatible"] is True  # for Panamax

    # 4. Market Entry Recommendation
    assert "market_entry" in data
    me = data["market_entry"]
    assert "signal" in me
    assert me["signal"] in ["BUY_NOW", "WAIT", "CAUTIOUS_BUY", "HEDGE", "CHARTER_NOW"]
    assert "best_entry_window" in me
    assert "recommendation" in me

    # 5. Voyage Economics
    assert "economics" in data
    econ = data["economics"]
    assert econ["distance_nm"] > 4000
    assert econ["total_cost_usd"] > 0
    assert econ["freight_revenue_usd"] > 0
    assert "tce_usd_per_day" in econ
    assert "breakeven_rate_usd_per_mt" in econ
    assert "margin_pct" in econ

    # 6. Contract Comparison
    assert "contracts" in data
    contracts = data["contracts"]
    assert len(contracts["options"]) >= 3
    contract_types = {o["contract_type"] for o in contracts["options"]}
    assert "Spot" in contract_types
    assert "recommended_contract" in contracts

    # 7. Risk Score
    assert "risk" in data
    risk = data["risk"]
    assert 0 <= risk["overall_risk_score"] <= 100
    assert risk["overall_risk_level"] in ["Low", "Medium", "High", "Critical"]
    assert len(risk["risk_factors"]) > 0

    # 8. Explanation & Final Recommendation
    assert "explanation" in data
    assert len(data["explanation"]) > 50
    assert "Panamax" in data["explanation"]
    assert "Paradip" in data["explanation"]

    assert "final_recommendation" in data
    fin = data["final_recommendation"]
    assert fin["recommended_vessel"] == "Panamax"
    assert fin["port_status"] == "Compatible"
    assert len(fin["action_items"]) > 0


def test_additional_route_indonesia_to_vizag():
    """Route 2: Indonesia -> Visakhapatnam (55,000 MT Supramax Coal)"""
    resp = client.post("/api/workflow/end-to-end", json={
        "origin": "Indonesia",
        "destination": "Visakhapatnam",
        "commodity": "Coal",
        "cargo_mt": 55000.0,
        "urgency_days": 21,
    })
    assert resp.status_code == 200
    d = resp.json()
    assert d["recommended_vessel"] in ["Supramax", "Panamax"]
    assert d["port_compatibility"]["port"] == "Visakhapatnam"
    assert d["port_compatibility"]["compatible"] is True
    assert d["economics"]["distance_nm"] > 0
    assert len(d["explanation"]) > 30


def test_additional_route_mozambique_to_gangavaram():
    """Route 3: Mozambique -> Gangavaram (150,000 MT Capesize Coal to deepwater 18m port)"""
    resp = client.post("/api/workflow/end-to-end", json={
        "origin": "Mozambique",
        "destination": "Gangavaram",
        "commodity": "Coal",
        "cargo_mt": 150000.0,
        "urgency_days": 45,
    })
    assert resp.status_code == 200
    d = resp.json()
    # Gangavaram is 18m deepwater port -> Capesize compatible
    assert d["all_ports_compatibility"]["Capesize"]["compatible"] is True
    assert d["recommended_vessel"] == "Capesize"
    assert d["economics"]["cargo_mt"] == 150000.0


def test_additional_route_usa_to_paradip():
    """Route 4: United States -> Paradip (70,000 MT Coal via Suez)"""
    resp = client.post("/api/workflow/end-to-end", json={
        "origin": "United States",
        "destination": "Paradip",
        "commodity": "Coal",
        "cargo_mt": 70000.0,
        "urgency_days": 30,
    })
    assert resp.status_code == 200
    d = resp.json()
    assert d["economics"]["distance_nm"] > 10000  # Long haul
    assert d["recommended_vessel"] == "Panamax"
    assert d["all_ports_compatibility"]["Capesize"]["compatible"] is False


def test_modular_endpoints():
    """Test all 9 individual core module endpoints"""
    # 1. Dashboard summary
    r = client.get("/api/dashboard/summary")
    assert r.status_code == 200
    assert len(r.json()["rate_snapshots"]) > 0

    # 2. Forecast predict
    r = client.post("/api/forecast/predict", json={
        "origin": "Australia",
        "destination": "Paradip",
        "vessel_class": "Panamax",
        "commodity": "Coal",
        "cargo_mt": 70000,
        "horizon_days": 30,
    })
    assert r.status_code == 200

    # 3. Vessels recommend
    r = client.post("/api/vessels/recommend", json={
        "origin": "Australia",
        "destination": "Paradip",
        "commodity": "Coal",
        "cargo_mt": 70000,
    })
    assert r.status_code == 200

    # 4. Port check
    r = client.post("/api/ports/check", json={
        "port": "Paradip",
        "vessel_class": "Capesize",
        "cargo_mt": 150000,
        "commodity": "Coal",
    })
    assert r.status_code == 200
    assert r.json()["compatible"] is False

    # 5. Economics calculate
    r = client.post("/api/economics/calculate", json={
        "origin": "Australia",
        "destination": "Paradip",
        "vessel_class": "Panamax",
        "commodity": "Coal",
        "cargo_mt": 70000,
    })
    assert r.status_code == 200

    # 6. Market entry signal
    r = client.post("/api/market-entry/signal", json={
        "origin": "Australia",
        "destination": "Paradip",
        "vessel_class": "Panamax",
        "commodity": "Coal",
        "cargo_mt": 70000,
        "urgency_days": 30,
    })
    assert r.status_code == 200

    # 7. Risk score
    r = client.post("/api/risk/score", json={
        "origin": "Australia",
        "destination": "Paradip",
        "vessel_class": "Panamax",
        "commodity": "Coal",
        "cargo_mt": 70000,
        "contract_type": "Spot",
    })
    assert r.status_code == 200

    # 8. Contracts compare
    r = client.post("/api/contracts/compare", json={
        "origin": "Australia",
        "destination": "Paradip",
        "vessel_class": "Panamax",
        "commodity": "Coal",
        "cargo_mt": 70000,
    })
    assert r.status_code == 200

    # 9. Scenarios idle-analysis
    r = client.post("/api/scenarios/idle-analysis", json={
        "origin": "Australia",
        "destination": "Paradip",
        "vessel_class": "Panamax",
        "commodity": "Coal",
        "cargo_mt": 70000,
        "waiting_days": 5.0,
    })
    assert r.status_code == 200
