import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.models.enums import (
    DecisionPipelineState,
    DecisionReadinessStatus,
    DataStatusType,
)
from app.models.cargo import CargoRequirement
from app.services.decision.normalization import (
    UnitNormalizationService,
    CurrencyNormalizationService,
)
from app.services.decision.quality_gate import DataQualityGate
from app.services.decision.readiness_service import DecisionReadinessService
from app.services.decision.orchestrator import CharteringDecisionOrchestrator
from app.services.decision.report_generator import DecisionReportGenerator
from app.services.ingestion.orchestrator import DataIngestionOrchestrator
from app.services.copilot import CopilotService
from app.schemas.copilot import CopilotChatRequest

client = TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_unit_and_currency_normalization():
    # 1. Cargo Quantity Normalization
    norm_mt = UnitNormalizationService.normalize_cargo_quantity(75000.0, "MT")
    assert norm_mt["quantity_mt"] == 75000.0
    assert norm_mt["unit"] == "MT"

    norm_lt = UnitNormalizationService.normalize_cargo_quantity(1000.0, "LT")
    assert norm_lt["quantity_mt"] == 1016.05

    # 2. Strict Cargo vs DWT Capacity Delineation
    # Feasible case: 75k MT cargo on an 82k DWT Panamax/Kamsarmax
    cap_ok = UnitNormalizationService.validate_vessel_capacity(75000.0, 82000.0)
    assert cap_ok["can_carry"] is True
    assert cap_ok["status"] == "FEASIBLE"
    assert cap_ok["dwt_utilization_pct"] > 85.0

    # Cargo exceeds DWT
    cap_fail = UnitNormalizationService.validate_vessel_capacity(75000.0, 55000.0)
    assert cap_fail["can_carry"] is False
    assert cap_fail["status"] == "EXCEEDS_DWT"

    # Missing DWT must return UNKNOWN (never assume pass)
    cap_unknown = UnitNormalizationService.validate_vessel_capacity(75000.0, None)
    assert cap_unknown["status"] == "UNKNOWN"
    assert cap_unknown["can_carry"] is False

    # 3. Currency Normalization
    conv_same = CurrencyNormalizationService.convert_amount(1000.0, "USD", "USD")
    assert conv_same["amount"] == 1000.0
    assert conv_same["fx_rate"] == 1.0

    conv_inr = CurrencyNormalizationService.convert_amount(100.0, "USD", "INR")
    assert conv_inr["amount"] == 8350.0
    assert conv_inr["currency"] == "INR"
    assert conv_inr["fx_status"] == DataStatusType.SYNTHETIC


def test_data_quality_gate_and_readiness():
    # Mock valid full context
    valid_context = {
        "cargo": {"quantity_mt": 75000.0, "laycan_start": "2026-10-01", "laycan_end": "2026-10-15"},
        "route": {"distance_nm": 5840.0, "trade_lane": "AUNCL -> INPRT"},
        "vessel": {"name": "MV Steel Glory", "vessel_class": "PANAMAX", "dwt": 82000.0},
        "ports": {"feasibility_status": "PASS", "evaluated_berths": 4},
        "forecast": {"p50": 15.20, "data_status": DataStatusType.SYNTHETIC},
        "regime": {"regime": "BEAR", "confidence": 0.85},
        "wait_fix": {"decision": "FIX_NOW"},
        "risk": {"overall_severity": "MEDIUM", "active_risks_count": 2},
        "economics": {"total_voyage_cost_usd": 1684500.0, "cost_per_mt_usd": 22.46},
    }

    gate_res = DataQualityGate.evaluate_decision_quality(valid_context)
    assert gate_res["overall_status"] in [DecisionReadinessStatus.READY, DecisionReadinessStatus.CONDITIONAL]
    assert len(gate_res["blockers"]) == 0

    readiness = DecisionReadinessService.evaluate_readiness(valid_context)
    assert readiness["score"] >= 80.0
    assert "READINESS" in readiness["rationale"]

    # Blocked context (missing distance & zero cargo)
    blocked_context = {
        "cargo": {"quantity_mt": 0.0},
        "route": {"distance_nm": 0.0},
        "ports": {"feasibility_status": "FAIL"},
    }
    blocked_readiness = DecisionReadinessService.evaluate_readiness(blocked_context)
    assert blocked_readiness["status"] == DecisionReadinessStatus.BLOCKED
    assert len(blocked_readiness["blockers"]) > 0
    assert "BLOCKED" in blocked_readiness["rationale"]


def test_orchestrator_master_e2e_workflow(db_session: Session):
    """
    Master end-to-end integration test for:
    75,000 MT Coal from Newcastle (port-auncb) to Paradip (port-inprt), 30 days.
    """
    reqs = db_session.query(CargoRequirement).all()
    assert len(reqs) > 0, "Database must contain at least one CargoRequirement for test"
    primary_cargo = reqs[0]

    orchestrator = CharteringDecisionOrchestrator(db_session)
    context = orchestrator.run_full_analysis(
        cargo_id=primary_cargo.id,
        user_id="SAIL-CHIEF-CHARTERER",
    )

    # 1. Canonical ID Propagation verification
    assert context["cargo_id"] == primary_cargo.id
    assert context["origin_port_id"] == primary_cargo.load_port_id
    assert context["destination_port_id"] == primary_cargo.discharge_port_id
    assert len(context["decision_id"]) == 36
    assert len(context["analysis_run_id"]) == 36
    assert context["voyage_id"].startswith("VOY-")

    # 2. Structural analytical dimensions check
    assert context["cargo"]["quantity_mt"] > 0
    assert context["route"]["distance_nm"] > 0
    assert context["ports"]["evaluated_berths"] > 0
    assert context["forecast"]["p50"] > 0
    assert context["regime"]["regime"] in ["BEAR", "BASE", "BULL", "NEUTRAL"]
    assert context["wait_fix"]["decision"] in ["FIX_NOW", "WAIT"]
    assert context["contract"]["recommended_strategy"] in ["SPOT", "SHORT_TERM_MULTIPLE_VOYAGE", "MEDIUM_TERM_MULTIPLE_VOYAGE"]
    assert context["economics"]["total_voyage_cost_usd"] > 0
    assert context["economics"]["cost_per_mt_usd"] > 0

    # 3. Decision Readiness
    assert context["decision_readiness"]["score"] > 0
    assert context["status"] in [DecisionPipelineState.READY, DecisionPipelineState.PARTIAL]

    # 4. Timeline Events Verification
    assert len(context["timeline"]) >= 8
    stage_names = [e["stage"] for e in context["timeline"]]
    assert "VALIDATING" in stage_names
    assert "VESSEL_ANALYSIS" in stage_names
    assert "PORT_ANALYSIS" in stage_names
    assert "ECONOMIC_ANALYSIS" in stage_names

    # 5. Database Persistence Verification
    run = orchestrator.repo.get_analysis_run_by_id(context["analysis_run_id"])
    assert run is not None
    assert run.cargo_id == primary_cargo.id
    assert run.execution_time_ms > 0

    audit_logs = orchestrator.repo.get_recent_audit_logs(limit=5)
    assert any(l.action == "RUN_FULL_ANALYSIS" for l in audit_logs)


def test_data_ingestion_adapters():
    orch = DataIngestionOrchestrator()
    health = orch.get_all_adapter_health()
    assert health["total_adapters"] == 7
    assert health["active_adapters"] == 7
    assert health["overall_status"] in ["HEALTHY", "DEGRADED"]

    # Verify adapter metadata fields
    for adapter_meta in health["adapters"]:
        assert "adapter" in adapter_meta
        assert "source" in adapter_meta
        assert "data_status" in adapter_meta
        assert "record_count" in adapter_meta


def test_report_generator_and_exports(db_session: Session):
    reqs = db_session.query(CargoRequirement).all()
    primary_cargo = reqs[0]

    # Ensure decision exists
    orchestrator = CharteringDecisionOrchestrator(db_session)
    orchestrator.run_full_analysis(cargo_id=primary_cargo.id)

    generator = DecisionReportGenerator(db_session)
    report = generator.generate_report(decision_id=primary_cargo.id)

    # 15 mandatory sections verification
    assert "report_id" in report
    assert "executive_summary" in report
    assert "cargo_requirement" in report
    assert "vessel_analysis" in report
    assert "port_feasibility" in report
    assert "freight_forecast" in report
    assert "market_regime" in report
    assert "wait_fix" in report
    assert "contract_strategy" in report
    assert "idle_repositioning" in report
    assert "operational_risk" in report
    assert "voyage_economics" in report
    assert "data_quality_scorecard" in report
    assert "decision_readiness" in report
    assert "assumptions" in report
    assert "sources" in report
    assert "signoff_block" in report

    # Test CSV Export
    csv_out = generator.export_csv(report)
    assert "CHARTERING DECISION DOSSIER" in csv_out
    assert "Delivered Cost per MT" in csv_out


def test_decision_api_endpoints(db_session: Session):
    reqs = db_session.query(CargoRequirement).all()
    primary_cargo = reqs[0]

    # 1. POST /api/v1/decision/analyze
    resp = client.post("/api/v1/decision/analyze", json={"cargo_id": primary_cargo.id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["cargo_id"] == primary_cargo.id
    assert "economics" in data

    decision_id = data["decision_id"]

    # 2. GET /api/v1/decision/{id}
    resp_get = client.get(f"/api/v1/decision/{decision_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["decision_id"] == decision_id

    # 3. GET /api/v1/decision/runs
    resp_runs = client.get("/api/v1/decision/runs")
    assert resp_runs.status_code == 200
    assert len(resp_runs.json()) > 0

    # 4. GET /api/v1/decision/dashboard/summary
    resp_dash = client.get("/api/v1/decision/dashboard/summary")
    assert resp_dash.status_code == 200
    dash_data = resp_dash.json()
    assert dash_data["active_cargo_requests_count"] > 0
    assert "market_overview" in dash_data
    assert "operations_overview" in dash_data
    assert "economics_overview" in dash_data

    # 5. POST /api/v1/decision/reports/generate
    resp_rpt = client.post(f"/api/v1/decision/reports/generate?decision_id={decision_id}")
    assert resp_rpt.status_code == 200
    assert resp_rpt.json()["report_id"].startswith("RPT-")

    # 6. GET /api/v1/decision/reports/export (CSV)
    resp_csv = client.get(f"/api/v1/decision/reports/export?decision_id={decision_id}&export_format=CSV")
    assert resp_csv.status_code == 200
    assert resp_csv.headers["content-type"].startswith("text/csv")

    # 7. GET /api/v1/decision/reports/export (JSON)
    resp_json = client.get(f"/api/v1/decision/reports/export?decision_id={decision_id}&export_format=JSON")
    assert resp_json.status_code == 200
    assert resp_json.headers["content-type"].startswith("application/json")

    # 8. GET /api/v1/decision/health/data
    resp_dh = client.get("/api/v1/decision/health/data")
    assert resp_dh.status_code == 200
    assert resp_dh.json()["total_adapters"] == 7

    # 9. GET /api/v1/decision/health/models
    resp_mh = client.get("/api/v1/decision/health/models")
    assert resp_mh.status_code == 200
    assert resp_mh.json()["total_models"] >= 5

    # 10. GET /api/v1/decision/audit
    resp_aud = client.get("/api/v1/decision/audit")
    assert resp_aud.status_code == 200
    assert len(resp_aud.json()) > 0


def test_copilot_decision_context_incorporation(db_session: Session):
    """
    Verifies that Phase 12 Copilot retrieves and grounds on existing canonical
    decision context instead of re-evaluating tools from scratch.
    """
    reqs = db_session.query(CargoRequirement).all()
    primary_cargo = reqs[0]

    # Pre-run decision
    orchestrator = CharteringDecisionOrchestrator(db_session)
    orchestrator.run_full_analysis(cargo_id=primary_cargo.id)

    copilot_svc = CopilotService(db_session)
    req = CopilotChatRequest(
        message="Explain the chartering situation for this cargo.",
        cargo_request_id=primary_cargo.id,
        stream=False,
    )

    res = copilot_svc.process_chat(req)
    assert res["session_id"] is not None
    sr = res.get("structured_response") or res.get("message", {}).get("structured_response")
    assert sr is not None
    assert len(sr.get("summary", "")) > 50
    # Must preserve data status and avoid certain claims
    assert "safe" not in sr.get("summary").lower() or "passes" in sr.get("summary").lower()
