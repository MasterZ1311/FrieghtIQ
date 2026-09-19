import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, Index
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import DecisionPipelineState, DecisionReadinessStatus


class CharteringDecision(Base):
    """
    Master record representing an orchestrated chartering decision lifecycle
    associated with a specific cargo requisition.
    """
    __tablename__ = "chartering_decisions"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    cargo_id = Column(String(36), ForeignKey("cargo_requirements.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(SQLEnum(DecisionPipelineState), default=DecisionPipelineState.DRAFT, nullable=False, index=True)
    readiness_status = Column(SQLEnum(DecisionReadinessStatus), default=DecisionReadinessStatus.PARTIAL, nullable=False)
    readiness_score = Column(Float, default=0.0)

    # Latest analytical snapshot pointers
    latest_analysis_run_id = Column(String(36), nullable=True, index=True)
    canonical_context_json = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    cargo = relationship("CargoRequirement")
    runs = relationship("AnalysisRun", back_populates="decision", cascade="all, delete-orphan")


class AnalysisRun(Base):
    """
    Persistent snapshot of an end-to-end analytical execution across
    Phases 3-11 services. Provides full reproducibility and auditing.
    """
    __tablename__ = "analysis_runs"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    decision_id = Column(String(36), ForeignKey("chartering_decisions.id", ondelete="CASCADE"), nullable=True, index=True)
    cargo_id = Column(String(36), ForeignKey("cargo_requirements.id", ondelete="SET NULL"), nullable=True, index=True)
    voyage_id = Column(String(36), nullable=True, index=True)
    vessel_id = Column(String(36), ForeignKey("vessels.id", ondelete="SET NULL"), nullable=True, index=True)
    origin_port_id = Column(String(36), ForeignKey("ports.id", ondelete="RESTRICT"), nullable=True, index=True)
    destination_port_id = Column(String(36), ForeignKey("ports.id", ondelete="RESTRICT"), nullable=True, index=True)

    context_version = Column(String(20), default="1.0.0", nullable=False)
    status = Column(SQLEnum(DecisionPipelineState), default=DecisionPipelineState.VALIDATING, nullable=False, index=True)
    stage = Column(String(50), default="INIT", nullable=False)

    # Provenance and versioning
    model_versions = Column(Text, nullable=True)     # JSON: {"forecasting": "...", "regime": "..."}
    dataset_versions = Column(Text, nullable=True)   # JSON: {"freight": "...", "ports": "..."}

    # Serialized analytical payloads
    inputs_json = Column(Text, nullable=True)
    outputs_json = Column(Text, nullable=True)
    data_quality_json = Column(Text, nullable=True)
    readiness_json = Column(Text, nullable=True)
    timeline_json = Column(Text, nullable=True)

    execution_time_ms = Column(Float, default=0.0)
    error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    decision = relationship("CharteringDecision", back_populates="runs")
    cargo = relationship("CargoRequirement")
    vessel = relationship("Vessel")
    origin_port = relationship("Port", foreign_keys=[origin_port_id])
    destination_port = relationship("Port", foreign_keys=[destination_port_id])


class AuditLog(Base):
    """
    Immutable audit trail record for compliance, executive accountability,
    and CVC/CAG transparency.
    """
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), default="SAIL-COMMERCIAL-OFFICER", nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)  # e.g., RUN_FULL_ANALYSIS, EXPORT_REPORT
    entity_type = Column(String(50), nullable=False, index=True)  # e.g., DECISION, CARGO, REPORT
    entity_id = Column(String(100), nullable=False, index=True)
    analysis_run_id = Column(String(36), nullable=True, index=True)
    details_json = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True, default="127.0.0.1")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
