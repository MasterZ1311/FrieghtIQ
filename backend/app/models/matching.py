from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.enums import MatchStatus

class VesselMatchRun(Base):
    __tablename__ = "vessel_match_runs"

    id = Column(String(36), primary_key=True, index=True)
    requirement_id = Column(String(36), ForeignKey("cargo_requirements.id", ondelete="CASCADE"), nullable=False, index=True)
    run_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    total_evaluated = Column(Integer, default=0)
    relevant_count = Column(Integer, default=0)
    partial_count = Column(Integer, default=0)
    not_relevant_count = Column(Integer, default=0)
    unknown_count = Column(Integer, default=0)

    # Relationships
    requirement = relationship("CargoRequirement")
    candidates = relationship("VesselMatchCandidate", back_populates="match_run", cascade="all, delete-orphan")


class VesselMatchCandidate(Base):
    __tablename__ = "vessel_match_candidates"

    id = Column(String(36), primary_key=True, index=True)
    match_run_id = Column(String(36), ForeignKey("vessel_match_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    vessel_id = Column(String(36), ForeignKey("vessels.id", ondelete="CASCADE"), nullable=False, index=True)
    
    overall_status = Column(SQLEnum(MatchStatus), nullable=False, default=MatchStatus.UNKNOWN)
    summary_explanation = Column(Text, nullable=False)
    is_data_complete = Column(Boolean, default=True)
    missing_fields = Column(String(255), nullable=True)

    # Relationships
    match_run = relationship("VesselMatchRun", back_populates="candidates")
    vessel = relationship("Vessel")
    rule_results = relationship("VesselMatchRuleResult", back_populates="candidate", cascade="all, delete-orphan")


class VesselMatchRuleResult(Base):
    __tablename__ = "vessel_match_rule_results"

    id = Column(String(36), primary_key=True, index=True)
    candidate_id = Column(String(36), ForeignKey("vessel_match_candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_name = Column(String(50), nullable=False)
    rule_category = Column(String(50), nullable=False) # e.g. "CAPACITY", "LAYCAN", "VESSEL_CLASS", "AGE"
    status = Column(SQLEnum(MatchStatus), nullable=False)
    evaluated_value = Column(String(100), nullable=True)
    required_value = Column(String(100), nullable=True)
    explanation = Column(Text, nullable=False)
    is_blocking = Column(Boolean, default=False)

    candidate = relationship("VesselMatchCandidate", back_populates="rule_results")
