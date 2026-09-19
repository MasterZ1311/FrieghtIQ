import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, Boolean
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import (
    CostComponentType,
    VoyageScenarioType,
    SpeedScenarioStatus,
    DataStatusType,
)


class VoyageEconomicAnalysis(Base):
    """
    Master record for comprehensive voyage-level economic modeling.
    Aggregates freight, bunker, port, charter time, expected delay/demurrage,
    and repositioning expenses into transparent financial KPIs.
    """
    __tablename__ = "voyage_economic_analyses"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    voyage_id = Column(String(36), nullable=True, index=True)
    cargo_request_id = Column(String(36), ForeignKey("cargo_requirements.id", ondelete="SET NULL"), nullable=True, index=True)
    vessel_id = Column(String(36), ForeignKey("vessels.id", ondelete="SET NULL"), nullable=True, index=True)
    origin_port_id = Column(String(36), ForeignKey("ports.id", ondelete="RESTRICT"), nullable=False, index=True)
    destination_port_id = Column(String(36), ForeignKey("ports.id", ondelete="RESTRICT"), nullable=False, index=True)

    distance_nm = Column(Float, nullable=False)
    cargo_quantity_mt = Column(Float, nullable=False)

    # Itemized Cost Totals (USD)
    freight_cost = Column(Float, nullable=False, default=0.0)
    bunker_cost = Column(Float, nullable=False, default=0.0)
    port_cost = Column(Float, nullable=False, default=0.0)
    time_cost = Column(Float, nullable=False, default=0.0)
    delay_cost = Column(Float, nullable=False, default=0.0)
    repositioning_cost = Column(Float, nullable=False, default=0.0)
    other_cost = Column(Float, nullable=False, default=0.0)

    # Delivered Financial Totals
    total_cost = Column(Float, nullable=False, default=0.0)
    cost_per_mt = Column(Float, nullable=False, default=0.0)

    currency = Column(String(10), default="USD", nullable=False)
    data_status = Column(SQLEnum(DataStatusType), default=DataStatusType.SYNTHETIC, nullable=False)
    model_version = Column(String(100), default="VOYAGE_ECONOMICS_V1.0", nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    cargo_request = relationship("CargoRequirement")
    vessel = relationship("Vessel")
    origin_port = relationship("Port", foreign_keys=[origin_port_id])
    destination_port = relationship("Port", foreign_keys=[destination_port_id])

    components = relationship("VoyageCostComponent", back_populates="analysis", cascade="all, delete-orphan")
    speed_scenarios = relationship("SpeedScenario", back_populates="analysis", cascade="all, delete-orphan")
    scenarios = relationship("VoyageScenario", back_populates="analysis", cascade="all, delete-orphan")


class VoyageCostComponent(Base):
    """
    Granular cost component item representing an individual line-item
    in the voyage financial ledger (e.g. VLSFO bunker, port dues, tuggage, demurrage exposure).
    """
    __tablename__ = "voyage_cost_components"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String(36), ForeignKey("voyage_economic_analyses.id", ondelete="CASCADE"), nullable=False, index=True)

    component_type = Column(SQLEnum(CostComponentType), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    unit = Column(String(50), default="USD", nullable=False) # e.g. "USD", "USD/MT", "USD/DAY", "MT"
    quantity = Column(Float, nullable=True)
    rate = Column(Float, nullable=True)

    # Lineage and Provenance
    source_id = Column(String(100), nullable=True)
    dataset_version_id = Column(String(100), nullable=True)
    data_status = Column(SQLEnum(DataStatusType), default=DataStatusType.SYNTHETIC, nullable=False)
    assumption = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    analysis = relationship("VoyageEconomicAnalysis", back_populates="components")


class SpeedScenario(Base):
    """
    Evaluated speed scenario for hydrodynamic cubic fuel curve analysis
    and virtual arrival synchronization.
    """
    __tablename__ = "speed_scenarios"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String(36), ForeignKey("voyage_economic_analyses.id", ondelete="CASCADE"), nullable=False, index=True)

    speed_knots = Column(Float, nullable=False)
    sailing_hours = Column(Float, nullable=False)
    sailing_days = Column(Float, nullable=False)
    fuel_consumption = Column(Float, nullable=True) # MT/day consumption at this speed
    fuel_consumed = Column(Float, nullable=True) # Total MT consumed over voyage
    bunker_price = Column(Float, nullable=True) # USD/MT
    bunker_cost = Column(Float, nullable=True) # USD
    time_cost = Column(Float, nullable=True) # USD
    delay_exposure = Column(Float, nullable=True) # USD
    total_cost = Column(Float, nullable=True) # USD
    cost_per_mt = Column(Float, nullable=True) # USD/MT

    status = Column(SQLEnum(SpeedScenarioStatus), default=SpeedScenarioStatus.EVALUATED, nullable=False)
    assumptions = Column(Text, nullable=True) # JSON or text notes

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    analysis = relationship("VoyageEconomicAnalysis", back_populates="speed_scenarios")


class VoyageScenario(Base):
    """
    Multidimensional voyage scenario model evaluating BASE, LOW_COST,
    HIGH_COST, DELAY, SLOW_STEAM, and FAST_TRANSIT operational states.
    """
    __tablename__ = "voyage_scenarios"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String(36), ForeignKey("voyage_economic_analyses.id", ondelete="CASCADE"), nullable=False, index=True)

    scenario_name = Column(SQLEnum(VoyageScenarioType), nullable=False, index=True)
    freight_rate = Column(Float, nullable=True) # USD/MT
    bunker_price = Column(Float, nullable=True) # USD/MT
    speed = Column(Float, nullable=True) # Knots
    port_delay_hours = Column(Float, nullable=True) # Hours
    idle_days = Column(Float, nullable=True) # Days
    total_cost = Column(Float, nullable=False) # USD
    cost_per_mt = Column(Float, nullable=False) # USD/MT

    assumptions = Column(Text, nullable=True)
    data_status = Column(SQLEnum(DataStatusType), default=DataStatusType.SYNTHETIC, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    analysis = relationship("VoyageEconomicAnalysis", back_populates="scenarios")
