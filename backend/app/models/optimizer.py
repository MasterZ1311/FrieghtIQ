from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.enums import FeasibilityStatus

class FeasibilityRun(Base):
    __tablename__ = "feasibility_runs"

    id = Column(String(36), primary_key=True, index=True)
    vessel_id = Column(String(36), ForeignKey("vessels.id", ondelete="CASCADE"), nullable=False, index=True)
    port_id = Column(String(36), ForeignKey("ports.id", ondelete="CASCADE"), nullable=False, index=True)
    run_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    overall_status = Column(SQLEnum(FeasibilityStatus), nullable=False, default=FeasibilityStatus.UNKNOWN)
    evaluated_berths_count = Column(Integer, default=0)
    passing_berths_count = Column(Integer, default=0)
    summary_narrative = Column(Text, nullable=True)

    # Relationships
    vessel = relationship("Vessel")
    port = relationship("Port")
    berth_results = relationship("FeasibilityBerthResult", back_populates="run", cascade="all, delete-orphan")


class FeasibilityBerthResult(Base):
    __tablename__ = "feasibility_berth_results"

    id = Column(String(36), primary_key=True, index=True)
    feasibility_run_id = Column(String(36), ForeignKey("feasibility_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    berth_id = Column(String(36), ForeignKey("berths.id", ondelete="CASCADE"), nullable=False, index=True)
    
    status = Column(SQLEnum(FeasibilityStatus), nullable=False, default=FeasibilityStatus.UNKNOWN)
    draft_clearance_m = Column(Float, nullable=True)
    loa_clearance_m = Column(Float, nullable=True)
    beam_clearance_m = Column(Float, nullable=True)
    estimated_turnaround_days = Column(Float, nullable=True)
    summary_explanation = Column(Text, nullable=False)

    # Relationships
    run = relationship("FeasibilityRun", back_populates="berth_results")
    berth = relationship("Berth")
    rule_evaluations = relationship("FeasibilityRuleEvaluation", back_populates="berth_result", cascade="all, delete-orphan")


class FeasibilityRuleEvaluation(Base):
    __tablename__ = "feasibility_rule_evaluations"

    id = Column(String(36), primary_key=True, index=True)
    berth_result_id = Column(String(36), ForeignKey("feasibility_berth_results.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_name = Column(String(50), nullable=False) # "MAX_DRAFT", "MAX_LOA", "MAX_BEAM", "AIR_DRAFT", "CARGO_GEAR"
    status = Column(SQLEnum(FeasibilityStatus), nullable=False)
    
    limit_value = Column(Float, nullable=True)
    vessel_value = Column(Float, nullable=True)
    unit = Column(String(20), default="m")
    margin = Column(Float, nullable=True) # limit - vessel_value
    is_blocking = Column(Boolean, default=True)
    narrative = Column(Text, nullable=False)

    berth_result = relationship("FeasibilityBerthResult", back_populates="rule_evaluations")
