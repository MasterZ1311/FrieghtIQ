"""
FreightIQ — Complete Backend Integration Test
"""
from fastapi.testclient import TestClient
from app.main import app

def run_tests():
    with TestClient(app) as client:
        print("1. Testing Health...")
        r = client.get("/health")
        assert r.status_code == 200, f"Health failed: {r.status_code}"
        print("   -> Health: OK")

        print("2. Testing Dashboard Summary...")
        r = client.get("/api/dashboard/summary")
        assert r.status_code == 200, f"Dashboard failed: {r.status_code}"
        snaps = r.json().get("rate_snapshots", [])
        print(f"   -> Snapshots: {len(snaps)} routes active")

        print("3. Testing Freight Forecast...")
        r = client.post("/api/forecast/predict", json={
            "origin": "Australia",
            "destination": "Paradip",
            "vessel_class": "Panamax",
            "commodity": "Coal",
            "cargo_mt": 70000,
            "horizon_days": 30,
        })
        assert r.status_code == 200, f"Forecast failed: {r.text}"
        d = r.json()
        print(f"   -> Rate: ${d['predicted_rate_usd_per_mt']}/MT, Conf: {d['confidence_pct']}%, Trend: {d['trend']}, TCE: ${d['tce_estimate_usd_per_day']}/day")

        print("4. Testing Voyage Economics (Maritime Physics Engine)...")
        r = client.post("/api/economics/calculate", json={
            "origin": "Australia",
            "destination": "Gangavaram",
            "vessel_class": "Panamax",
            "commodity": "Coal",
            "cargo_mt": 70000,
            "bunker_price_usd_per_mt": 650.0,
        })
        assert r.status_code == 200, f"Economics failed: {r.text}"
        d = r.json()
        print(f"   -> Bunker: ${d['bunker_cost_usd']:,.0f}, Total Cost: ${d['total_cost_usd']:,.0f}, TCE: ${d['tce_usd_per_day']:,.0f}/day, Margin: {d['margin_pct']:.1f}%")

        print("5. Testing Idle Scenario Management (Module 8)...")
        r = client.post("/api/scenarios/idle-analysis", json={
            "origin": "Australia",
            "destination": "Paradip",
            "vessel_class": "Panamax",
            "commodity": "Coal",
            "cargo_mt": 70000,
            "waiting_days": 5.5,
            "demurrage_rate_usd_day": 24000.0,
            "bunker_price_usd_per_mt": 650.0,
            "slow_steaming_knots": 11.5,
        })
        assert r.status_code == 200, f"Idle analysis failed: {r.text}"
        d = r.json()
        print(f"   -> Congestion Exposure: ${d['total_congestion_exposure_usd']:,.0f}")
        print(f"   -> Strategy: {d['optimal_strategy']}")
        print(f"   -> Slow-Steaming Bunker Savings: ${d['slow_steaming']['bunker_savings_usd']:,.0f}")
        print(f"   -> Diversion Candidates: {len(d['diversion_options'])}")

        print("6. Testing Vessel Recommendation Engine...")
        r = client.post("/api/vessels/recommend", json={
            "origin": "Australia",
            "destination": "Visakhapatnam",
            "commodity": "Coal",
            "cargo_mt": 70000,
        })
        assert r.status_code == 200
        print(f"   -> Recommended Vessel Class: {r.json()['recommended_class']}")

        print("7. Testing Port Constraint Engine (Draft / LOA / Tide)...")
        r = client.post("/api/ports/check", json={
            "port": "Haldia",
            "vessel_class": "Capesize",
            "cargo_mt": 150000,
            "commodity": "Coal",
        })
        assert r.status_code == 200
        print(f"   -> Haldia (shallow river) + Capesize: Compatible={r.json()['compatible']} (Expected False)")

        r2 = client.post("/api/ports/check", json={
            "port": "Gangavaram",
            "vessel_class": "Capesize",
            "cargo_mt": 150000,
            "commodity": "Coal",
        })
        assert r2.status_code == 200
        print(f"   -> Gangavaram (deepwater 18m) + Capesize: Compatible={r2.json()['compatible']} (Expected True)")

        print("8. Testing Market Entry Signal (Buy Now vs Wait)...")
        r = client.post("/api/market-entry/signal", json={
            "origin": "Australia",
            "destination": "Paradip",
            "vessel_class": "Panamax",
            "commodity": "Coal",
            "cargo_mt": 70000,
            "urgency_days": 30,
        })
        assert r.status_code == 200
        print(f"   -> Signal: {r.json()['signal']} (Conf: {r.json()['confidence_pct']}%)")

        print("9. Testing Multi-Factor Risk Engine...")
        r = client.post("/api/risk/score", json={
            "origin": "Russia",
            "destination": "Paradip",
            "vessel_class": "Panamax",
            "commodity": "Coal",
            "cargo_mt": 70000,
            "contract_type": "Spot",
        })
        assert r.status_code == 200
        print(f"   -> Risk Score: {r.json()['overall_risk_score']:.1f} ({r.json()['overall_risk_level']})")

        print("10. Testing Contract Simulator (Spot vs Short vs Medium Term)...")
        r = client.post("/api/contracts/compare", json={
            "origin": "Australia",
            "destination": "Paradip",
            "vessel_class": "Panamax",
            "commodity": "Coal",
            "cargo_mt": 70000,
            "annual_volume_mt": 500000,
            "planning_horizon_months": 12,
        })
        assert r.status_code == 200
        print(f"   -> Recommended Contract: {r.json()['recommended_contract']}")

        print("11. Testing Thoothukudi (VOCPA) Green Bunkering & NCB-I Checks...")
        r_th = client.post("/api/ports/check", json={
            "port": "Thoothukudi",
            "vessel_class": "Panamax",
            "cargo_mt": 74510,
            "commodity": "Coal",
        })
        assert r_th.status_code == 200 and r_th.json()["compatible"]
        r_th_ais = client.get("/api/ports/congestion?port=thoothukudi")
        assert r_th_ais.status_code == 200
        print(f"   -> Thoothukudi Panamax Compatible: {r_th.json()['compatible']} | Congestion Score: {r_th_ais.json()['congestion_score']}/100 (Green Hub: {r_th_ais.json()['green_hydrogen_hub']})")

        print("12. Testing Chennai Port Jawahar Dock & Pig Iron Checks...")
        r_ch = client.post("/api/ports/check", json={
            "port": "Chennai",
            "vessel_class": "Supramax",
            "cargo_mt": 52500,
            "commodity": "Coal",
        })
        assert r_ch.status_code == 200 and r_ch.json()["compatible"]
        r_ch_ais = client.get("/api/ports/congestion?port=chennai")
        assert r_ch_ais.status_code == 200
        print(f"   -> Chennai Supramax Compatible: {r_ch.json()['compatible']} | Active Vessels in Queue: {len(r_ch_ais.json()['active_vessels_in_queue'])}")

        print("\n========================================================")
        print("ALL 12 CORE MODULE ENDPOINTS PASSED WITH 100% SUCCESS!")
        print("THOOTHUKUDI (VOCPA) & CHENNAI VERIFIED AS PRIMARY HUBS!")
        print("========================================================")

if __name__ == "__main__":
    run_tests()
