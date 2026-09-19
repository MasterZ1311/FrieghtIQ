import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "FREIGHT IQ" in data["project"]

def test_ports_endpoints():
    res = client.get("/api/v1/ports")
    assert res.status_code == 200
    ports = res.json()
    assert len(ports) >= 7
    paradip = next(p for p in ports if p["unlocode"] == "INPRT")
    assert paradip["channel_max_draft_m"] == 16.0

    # Get Paradip Detail
    res_det = client.get(f"/api/v1/ports/{paradip['id']}")
    assert res_det.status_code == 200
    p_data = res_det.json()
    berths = p_data["berths"]
    assert any(b["berth_code"] == "CB-1" for b in berths)
    assert any(b["berth_code"] == "CB-2" for b in berths)

def test_vessels_endpoints():
    res = client.get("/api/v1/vessels")
    assert res.status_code == 200
    vessels = res.json()
    assert len(vessels) >= 9
    
    # Test snapshot vessel Vishva Vijay
    vv = next(v for v in vessels if "Vishva Vijay" in v["vessel_name"])
    assert vv["is_snapshot_vessel"] is True
    assert vv["particulars"]["summer_dwt"] == 79800.0

    # Test Red Cosmos with unverified DWT (NULL)
    rc = next(v for v in vessels if "Red Cosmos" in v["vessel_name"])
    assert rc["particulars"]["summer_dwt"] is None
    assert rc["particulars"]["is_verified"] is False

def test_cargo_and_matching():
    # Fetch requirements
    res_req = client.get("/api/v1/cargo/requirements")
    assert res_req.status_code == 200
    reqs = res_req.json()
    assert len(reqs) >= 1
    req = reqs[0]

    # Run matching
    match_payload = {"requirement_id": req["id"]}
    res_match = client.post("/api/v1/matching/evaluate", json=match_payload)
    assert res_match.status_code == 200
    match_data = res_match.json()
    assert match_data["total_evaluated"] >= 9
    
    # Verify candidates exist and have rule results
    candidates = match_data["candidates"]
    assert len(candidates) >= 9
    
    # Find Red Cosmos candidate - should be UNKNOWN due to missing DWT
    rc_cand = next(c for c in candidates if "Red Cosmos" in c["vessel"]["vessel_name"])
    assert rc_cand["overall_status"] == "UNKNOWN"

def test_port_feasibility_optimizer():
    # Get vessel and port
    res_v = client.get("/api/v1/vessels")
    vv = next(v for v in res_v.json() if "Vishva Vijay" in v["vessel_name"])
    
    res_p = client.get("/api/v1/ports")
    paradip = next(p for p in res_p.json() if p["unlocode"] == "INPRT")

    # Run feasibility evaluation
    feas_payload = {
        "vessel_id": vv["id"],
        "port_id": paradip["id"],
        "cargo_quantity_mt": 75000.0
    }
    res_feas = client.post("/api/v1/optimizer/evaluate", json=feas_payload)
    assert res_feas.status_code == 200
    data = res_feas.json()
    assert data["overall_status"] in ["PASS", "CONDITIONAL"]
    assert len(data["berth_results"]) >= 4

    # CB-1 has 0.05m margin, which correctly requires tidal window assistance (CONDITIONAL)
    cb1_res = next(b for b in data["berth_results"] if b["berth"]["berth_code"] == "CB-1")
    assert cb1_res["status"] in ["PASS", "CONDITIONAL"]

    # MCB has 16.0m depth (margin > 1.5m), which is an unconditional PASS
    mcb_res = next(b for b in data["berth_results"] if b["berth"]["berth_code"] == "MCB")
    assert mcb_res["status"] == "PASS"

def test_freight_forecasting():
    res_routes = client.get("/api/v1/freight/routes")
    assert res_routes.status_code == 200
    routes = res_routes.json()
    route = next(r for r in routes if "PARADIP" in r["route_code"])

    # Generate / Fetch forecasts
    res_fc = client.get(f"/api/v1/freight/routes/{route['id']}/forecasts")
    assert res_fc.status_code == 200
    forecasts = res_fc.json()
    assert len(forecasts) >= 4  # 7d, 14d, 30d, 90d
    
    for fc in forecasts:
        assert fc["predicted_p10"] <= fc["predicted_p50"] <= fc["predicted_p90"]
        assert fc["confidence_pct"] > 0
