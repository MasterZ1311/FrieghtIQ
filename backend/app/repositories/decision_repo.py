import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload

from app.models.integration import CharteringDecision, AnalysisRun, AuditLog
from app.models.enums import DecisionPipelineState, DecisionReadinessStatus


class DecisionRepository:
    """
    Data access layer for Chartering Decisions, Analysis Runs, and Audit Trail.
    """

    def __init__(self, db: Session):
        self.db = db

    # ----------------- CHARTERING DECISIONS -----------------

    def create_decision(
        self,
        title: str,
        cargo_id: Optional[str] = None,
        status: DecisionPipelineState = DecisionPipelineState.DRAFT,
        readiness_status: DecisionReadinessStatus = DecisionReadinessStatus.PARTIAL,
        readiness_score: float = 0.0,
        canonical_context: Optional[Dict[str, Any]] = None,
    ) -> CharteringDecision:
        decision = CharteringDecision(
            id=str(uuid.uuid4()),
            title=title,
            cargo_id=cargo_id,
            status=status,
            readiness_status=readiness_status,
            readiness_score=readiness_score,
            canonical_context_json=json.dumps(canonical_context) if canonical_context else None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(decision)
        self.db.commit()
        self.db.refresh(decision)
        return decision

    def get_decision_by_id(self, decision_id: str) -> Optional[CharteringDecision]:
        return (
            self.db.query(CharteringDecision)
            .options(joinedload(CharteringDecision.cargo))
            .filter(CharteringDecision.id == decision_id)
            .first()
        )

    def get_decision_by_cargo_id(self, cargo_id: str) -> Optional[CharteringDecision]:
        return (
            self.db.query(CharteringDecision)
            .options(joinedload(CharteringDecision.cargo))
            .filter(CharteringDecision.cargo_id == cargo_id)
            .order_by(CharteringDecision.created_at.desc())
            .first()
        )

    def get_all_decisions(self, limit: int = 50, offset: int = 0) -> List[CharteringDecision]:
        return (
            self.db.query(CharteringDecision)
            .options(joinedload(CharteringDecision.cargo))
            .order_by(CharteringDecision.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def update_decision_context(
        self,
        decision_id: str,
        canonical_context: Dict[str, Any],
        status: DecisionPipelineState,
        readiness_status: DecisionReadinessStatus,
        readiness_score: float,
        latest_analysis_run_id: Optional[str] = None,
    ) -> Optional[CharteringDecision]:
        decision = self.get_decision_by_id(decision_id)
        if not decision:
            return None

        decision.canonical_context_json = json.dumps(canonical_context)
        decision.status = status
        decision.readiness_status = readiness_status
        decision.readiness_score = readiness_score
        if latest_analysis_run_id:
            decision.latest_analysis_run_id = latest_analysis_run_id
        decision.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(decision)
        return decision

    # ----------------- ANALYSIS RUNS -----------------

    def create_analysis_run(
        self,
        cargo_id: Optional[str],
        voyage_id: Optional[str],
        vessel_id: Optional[str],
        origin_port_id: Optional[str],
        destination_port_id: Optional[str],
        decision_id: Optional[str] = None,
        context_version: str = "1.0.0",
        inputs: Optional[Dict[str, Any]] = None,
    ) -> AnalysisRun:
        run = AnalysisRun(
            id=str(uuid.uuid4()),
            decision_id=decision_id,
            cargo_id=cargo_id,
            voyage_id=voyage_id,
            vessel_id=vessel_id,
            origin_port_id=origin_port_id,
            destination_port_id=destination_port_id,
            context_version=context_version,
            status=DecisionPipelineState.VALIDATING,
            stage="INIT",
            inputs_json=json.dumps(inputs) if inputs else None,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def update_analysis_run(
        self,
        run_id: str,
        status: DecisionPipelineState,
        stage: str,
        outputs: Optional[Dict[str, Any]] = None,
        data_quality: Optional[Dict[str, Any]] = None,
        readiness: Optional[Dict[str, Any]] = None,
        timeline: Optional[List[Dict[str, Any]]] = None,
        model_versions: Optional[Dict[str, Any]] = None,
        dataset_versions: Optional[Dict[str, Any]] = None,
        execution_time_ms: float = 0.0,
        error: Optional[str] = None,
    ) -> Optional[AnalysisRun]:
        run = self.get_analysis_run_by_id(run_id)
        if not run:
            return None

        run.status = status
        run.stage = stage
        if outputs:
            run.outputs_json = json.dumps(outputs)
        if data_quality:
            run.data_quality_json = json.dumps(data_quality)
        if readiness:
            run.readiness_json = json.dumps(readiness)
        if timeline:
            run.timeline_json = json.dumps(timeline)
        if model_versions:
            run.model_versions = json.dumps(model_versions)
        if dataset_versions:
            run.dataset_versions = json.dumps(dataset_versions)
        run.execution_time_ms = execution_time_ms
        run.error = error
        if status in [DecisionPipelineState.READY, DecisionPipelineState.PARTIAL, DecisionPipelineState.FAILED, DecisionPipelineState.BLOCKED]:
            run.completed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(run)
        return run

    def get_analysis_run_by_id(self, run_id: str) -> Optional[AnalysisRun]:
        return (
            self.db.query(AnalysisRun)
            .options(
                joinedload(AnalysisRun.cargo),
                joinedload(AnalysisRun.vessel),
                joinedload(AnalysisRun.origin_port),
                joinedload(AnalysisRun.destination_port),
            )
            .filter(AnalysisRun.id == run_id)
            .first()
        )

    def get_all_analysis_runs(self, limit: int = 50, offset: int = 0) -> List[AnalysisRun]:
        return (
            self.db.query(AnalysisRun)
            .order_by(AnalysisRun.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_runs_for_decision(self, decision_id: str, limit: int = 10) -> List[AnalysisRun]:
        return (
            self.db.query(AnalysisRun)
            .filter(AnalysisRun.decision_id == decision_id)
            .order_by(AnalysisRun.created_at.desc())
            .limit(limit)
            .all()
        )

    # ----------------- AUDIT TRAIL -----------------

    def record_audit(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        user_id: str = "SAIL-COMMERCIAL-OFFICER",
        analysis_run_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = "127.0.0.1",
    ) -> AuditLog:
        log = AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            analysis_run_id=analysis_run_id,
            details_json=json.dumps(details) if details else None,
            ip_address=ip_address,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_recent_audit_logs(self, limit: int = 50) -> List[AuditLog]:
        return (
            self.db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
