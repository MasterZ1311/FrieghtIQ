"""
FreightIQ Backend Smoke Test
Run after: uvicorn app.main:app --port 8000
"""
import httpx
import json

BASE = "http://localhost:8000"

def test(name, resp):
    status = "[OK]" if resp.status_code < 400 else "[FAIL]"
    print(f"{status} {name}: {resp.status_code}")
    if resp.status_code >= 400:
        print(f"  ERROR: {resp.text[:200]}")
    return resp.status_code < 400


def run_smoke_test():
    client = httpx.Client(timeout=30)
    print("=== FreightIQ Smoke Test ===\n")

    # Health
    r = client.get(f"{BASE}/health")
    test("GET /health", r)

    # API Health
    r = client.get(f"{BASE}/api/health")
    test("GET /api/health", r)

    # Dashboard
    r = client.get(f"{BASE}/api/dashboard/summary")
    test("GET /api/dashboard/summary", r)
    if r.status_code == 200:
        data = r.json()
        print(f"   Snapshots: {len(data['rate_snapshots'])}")

    # Forecast
    r = client.post(f"{BASE}/api/forecast", json={
        "origin": "Australia",
        "destination": "Paradip",
        "vessel_class": "Panamax",
        "commodity": "Coal",
        "quantity_mt": 70000,
        "horizon": 30,
    })
    test("POST /api/forecast", r)
    if r.status_code == 200:
        d = r.json()
        print(f"   Rate: ${d['predicted_rate']}/MT | Trend: {d['trend']} | Conf: {d['confidence']}%")

    # Vessels
    r = client.post(f"{BASE}/api/vessel/recommend", json={
        "origin": "Australia",
        "destination": "Visakhapatnam",
        "commodity": "Coal",
        "quantity_mt": 70000,
    })
    test("POST /api/vessel/recommend", r)
    if r.status_code == 200:
        d = r.json()
        print(f"   Recommended: {d['recommended_class']}")

    # Port check
    r = client.post(f"{BASE}/api/port/check", json={
        "port": "Visakhapatnam",
        "vessel_class": "Panamax",
        "quantity_mt": 70000,
        "commodity": "Coal",
    })
    test("POST /api/port/check", r)
    if r.status_code == 200:
        d = r.json()
        print(f"   Compatible: {d['compatible']}")

    # Economics
    r = client.post(f"{BASE}/api/economics/calculate", json={
        "origin": "Australia",
        "destination": "Gangavaram",
        "vessel_class": "Panamax",
        "commodity": "Coal",
        "quantity_mt": 70000,
    })
    test("POST /api/economics/calculate", r)
    if r.status_code == 200:
        d = r.json()
        print(f"   TCE: ${d['tce']}/day | Margin: {d['margin_pct']}%")

    # Risk
    r = client.post(f"{BASE}/api/risk/analyze", json={
        "origin": "Russia",
        "destination": "Paradip",
        "vessel_class": "Panamax",
        "commodity": "Coal",
        "quantity_mt": 70000,
        "contract_type": "Spot",
    })
    test("POST /api/risk/analyze", r)
    if r.status_code == 200:
        d = r.json()
        print(f"   Risk Score: {d['overall_risk_score']} ({d['overall_risk_level']})")

    # Contracts
    r = client.post(f"{BASE}/api/contracts/compare", json={
        "origin": "Australia",
        "destination": "Paradip",
        "vessel_class": "Panamax",
        "commodity": "Coal",
        "quantity_mt": 70000,
        "annual_volume_mt": 500000,
        "planning_horizon_months": 12,
    })
    test("POST /api/contracts/compare", r)
    if r.status_code == 200:
        d = r.json()
        print(f"   Recommended: {d['recommended_contract']}")

    # Scenarios
    r = client.post(f"{BASE}/api/scenario/simulate", json={
        "base_origin": "Australia",
        "base_destination": "Paradip",
        "base_vessel_class": "Panamax",
        "base_commodity": "Coal",
        "base_cargo_mt": 70000,
        "scenarios": [
            {"name": "Supramax Alt", "vessel_class": "Supramax", "origin": "Australia", "destination": "Paradip", "commodity": "Coal", "cargo_mt": 57000},
            {"name": "Indonesia Route", "vessel_class": "Supramax", "origin": "Indonesia", "destination": "Paradip", "commodity": "Coal", "cargo_mt": 57000},
        ],
    })
    test("POST /api/scenario/simulate", r)
    if r.status_code == 200:
        d = r.json()
        print(f"   Best: {d['best_scenario']} | Worst: {d['worst_scenario']}")

    # End-to-End Decision Workflow
    r = client.post(f"{BASE}/api/workflow/end-to-end", json={
        "origin": "Australia",
        "destination": "Paradip",
        "commodity": "bulk cargo",
        "cargo_mt": 70000,
        "urgency_days": 30,
        "annual_volume_mt": 500000,
        "planning_horizon_months": 12,
    })
    test("POST /api/workflow/end-to-end", r)
    if r.status_code == 200:
        d = r.json()
        print(f"   Recommended Vessel: {d['recommended_vessel']} | Signal: {d['market_entry']['signal']} | Contract: {d['contracts']['recommended_contract']}")
        print(f"   TCE: ${d['economics']['tce_usd_per_day']:,.0f}/day | Risk: {d['risk']['overall_risk_score']:.1f} ({d['risk']['overall_risk_level']})")

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    run_smoke_test()

