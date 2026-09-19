import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum, Text
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import (
    ContractStrategyType, MarketScenarioType, DecisionConfidence, DataStatusType
)

class ContractStrategy(Base):
    """
    Persisted contract procurement strategy evaluation record.
    Evaluates SPOT, SHORT_TERM_MULTIPLE_VOYAGE, and MEDIUM_TERM_MULTIPLE_VOYAGE
    options against forward freight forecasts, market regimes, and port/vessel constraints.
    """
    __tablename__ = "contract_strategies"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    cargo_request_id = Column(String(36), ForeignKey("cargo_requirements.id", ondelete="SET NULL"), nullable=True, index=True)

    strategy_type = Column(SQLEnum(ContractStrategyType), nullable=False, index=True)
    contract_duration = Column(String(100), nullable=False) # e.g. "Single Voyage", "90 Days (3 Months)", "180 Days (6 Months)"
    voyage_count = Column(Integer, nullable=False, default=1)

    total_quantity = Column(Float, nullable=False) # Total required Metric Tonnes
    contracted_quantity = Column(Float, nullable=False) # Contracted MT
    spot_quantity = Column(Float, nullable=False) # Uncommitted / Spot MT

    reference_rate = Column(Float, nullable=True) # Contract/benchmark rate (USD/MT), null if unavailable
    expected_rate = Column(Float, nullable=False) # Weighted blended freight rate (USD/MT)
    expected_cost = Column(Float, nullable=False) # Total modeled freight cost (USD)

    p10_cost = Column(Float, nullable=False) # Optimistic low-rate scenario cost (USD)
    p50_cost = Column(Float, nullable=False) # Central base-rate scenario cost (USD)
    p90_cost = Column(Float, nullable=False) # Adverse high-rate scenario cost (USD)

    market_exposure = Column(Float, nullable=False) # 0.0 - 1.0 (proportion exposed to spot volatility)
    flexibility_measure = Column(Float, nullable=False) # 0.0 - 1.0 (operational/cancellation flexibility)
    risk_adjusted_cost = Column(Float, nullable=False) # Freight cost + uncertainty adj + commitment adj

    break_even_rate = Column(Float, nullable=True) # USD/MT break-even spot rate vs contract
    decision_confidence = Column(SQLEnum(DecisionConfidence), nullable=False, default=DecisionConfidence.MEDIUM)

    # Lineage / Provenance references
    forecast_id = Column(String(36), nullable=True)
    regime_id = Column(String(36), nullable=True)
    wait_fix_analysis_id = Column(String(36), ForeignKey("wait_fix_analyses.id", ondelete="SET NULL"), nullable=True, index=True)
    model_version_id = Column(String(100), default="CONTRACT_STRATEGY_V1.0")
    dataset_version_id = Column(String(100), default="FREIGHT-SYNTH-2026-Q1")
    data_status = Column(SQLEnum(DataStatusType), default=DataStatusType.SYNTHETIC)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    cargo_request = relationship("CargoRequirement")
    wait_fix_analysis = relationship("WaitFixAnalysis")
    scenarios = relationship("ContractStrategyScenario", back_populates="strategy", cascade="all, delete-orphan")


class ContractStrategyScenario(Base):
    """
    Market environment outcome scenario (BEAR / BASE / BULL)
    for a specific contract strategy evaluation.
    """
    __tablename__ = "contract_strategy_scenarios"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String(36), ForeignKey("contract_strategies.id", ondelete="CASCADE"), nullable=False, index=True)

    scenario_name = Column(String(50), nullable=False) # "BEAR", "BASE", "BULL"
    market_assumption = Column(Text, nullable=True) # Documented assumptions
    rate = Column(Float, nullable=False) # USD / MT blended rate
    quantity = Column(Float, nullable=False) # Metric Tonnes
    cost = Column(Float, nullable=False) # Total USD = rate * quantity
    probability = Column(Float, nullable=False, default=0.33) # Probability weight (0.0 - 1.0)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    strategy = relationship("ContractStrategy", back_populates="scenarios")
