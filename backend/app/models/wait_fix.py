import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum, Text
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import (
    CargoType, VesselClass, WaitFixDecision, DecisionConfidence,
    DataStatusType, WaitFixScenarioType
)

class WaitFixAnalysis(Base):
    """
    Persisted commercial charter-timing evaluation record.
    Captures modeled expected difference between fixing prompt tonnage vs waiting,
    incorporating Phase 3 cargo requirements, Phase 4 port feasibility,
    Phase 5 TFT quantile projections, and Phase 6 Gaussian HMM market regimes.
    """
    __tablename__ = "wait_fix_analyses"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    cargo_request_id = Column(String(36), ForeignKey("cargo_requirements.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Trade lane attributes
    origin_port_id = Column(String(36), ForeignKey("ports.id"), nullable=False, index=True)
    destination_port_id = Column(String(36), ForeignKey("ports.id"), nullable=False, index=True)
    cargo_type = Column(SQLEnum(CargoType), nullable=False)
    cargo_quantity = Column(Float, nullable=False) # Metric Tonnes
    vessel_class = Column(SQLEnum(VesselClass), nullable=False)

    # Spot & Forecast Quantiles (USD / MT)
    current_freight_rate = Column(Float, nullable=False) # Reference fix benchmark
    p10_rate = Column(Float, nullable=False)
    p50_rate = Column(Float, nullable=False)
    p90_rate = Column(Float, nullable=False)

    # Modeled Economics (USD / MT & Total USD)
    expected_wait_rate = Column(Float, nullable=False)
    expected_fix_cost = Column(Float, nullable=False) # Reference Fix Rate * Quantity
    expected_wait_cost = Column(Float, nullable=False) # Expected Rate * Quantity
    expected_modeled_difference = Column(Float, nullable=False) # Fix Cost - Wait Cost

    # Real-Option Flexibility Value (USD, nullable if unavailable)
    wait_option_value = Column(Float, nullable=True)

    # Decision Recommendation & Confidence
    decision = Column(SQLEnum(WaitFixDecision), nullable=False, index=True)
    decision_confidence = Column(SQLEnum(DecisionConfidence), nullable=False)
    
    # Decision Window
    decision_deadline = Column(DateTime, nullable=True)
    remaining_days = Column(Integer, nullable=False)

    # Lineage / Provenance references
    forecast_id = Column(String(36), nullable=True)
    regime_id = Column(String(36), nullable=True)
    model_version_id = Column(String(100), default="WAIT_FIX_V1.0")
    dataset_version_id = Column(String(100), default="SYNTHETIC_BALTIC_V2026")
    data_status = Column(SQLEnum(DataStatusType), default=DataStatusType.SYNTHETIC)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    cargo_request = relationship("CargoRequirement")
    origin_port = relationship("Port", foreign_keys=[origin_port_id])
    destination_port = relationship("Port", foreign_keys=[destination_port_id])
    scenarios = relationship("WaitFixScenario", back_populates="analysis", cascade="all, delete-orphan")


class WaitFixScenario(Base):
    """
    Quantile economic outcome scenario (LOW / CENTRAL / HIGH)
    derived from P10, P50, and P90 forecast distribution.
    """
    __tablename__ = "wait_fix_scenarios"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String(36), ForeignKey("wait_fix_analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    scenario_name = Column(String(50), nullable=False) # "LOW", "CENTRAL", "HIGH"
    rate = Column(Float, nullable=False) # USD / MT
    probability = Column(Float, nullable=False) # 0.0 - 1.0 (Sums to 1.0)
    freight_cost = Column(Float, nullable=False) # Rate * Quantity (USD)
    difference_vs_fix = Column(Float, nullable=False) # Fix Cost - Scenario Cost (USD)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    analysis = relationship("WaitFixAnalysis", back_populates="scenarios")
