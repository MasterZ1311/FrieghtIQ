import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum, Text
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import (
    EmploymentEventType, IdleScenarioType, RepositioningDecision,
    DecisionConfidence, DataStatusType
)

class VesselEmploymentEvent(Base):
    """
    Sourced and estimated vessel employment lifecycle events:
    Voyage transits, discharge, loading, anchorage waiting, and ballast repositioning legs.
    """
    __tablename__ = "vessel_employment_events"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    vessel_id = Column(String(36), ForeignKey("vessels.id", ondelete="CASCADE"), nullable=False, index=True)

    event_type = Column(SQLEnum(EmploymentEventType), nullable=False)
    voyage_id = Column(String(36), nullable=True)
    cargo_request_id = Column(String(36), ForeignKey("cargo_requirements.id", ondelete="SET NULL"), nullable=True, index=True)

    origin_port_id = Column(String(36), ForeignKey("ports.id"), nullable=True)
    destination_port_id = Column(String(36), ForeignKey("ports.id"), nullable=True)

    event_start = Column(DateTime, nullable=False)
    event_end = Column(DateTime, nullable=True)
    status = Column(String(50), default="SCHEDULED") # COMPLETED, ACTIVE, SCHEDULED, ESTIMATED
    source_id = Column(String(100), nullable=True)
    data_status = Column(SQLEnum(DataStatusType), default=DataStatusType.SYNTHETIC)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    vessel = relationship("Vessel")
    cargo_request = relationship("CargoRequirement")
    origin_port = relationship("Port", foreign_keys=[origin_port_id])
    destination_port = relationship("Port", foreign_keys=[destination_port_id])


class IdleScenario(Base):
    """
    Detected or modeled vessel idle risk scenarios:
    Early arrivals, employment gaps, port delays, or demand shortages.
    """
    __tablename__ = "idle_scenarios"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    vessel_id = Column(String(36), ForeignKey("vessels.id", ondelete="CASCADE"), nullable=False, index=True)
    voyage_id = Column(String(36), nullable=True)

    scenario_type = Column(SQLEnum(IdleScenarioType), nullable=False, index=True)
    current_location = Column(String(100), nullable=False)
    next_known_employment = Column(String(255), nullable=True)

    estimated_available_at = Column(DateTime, nullable=True)
    estimated_next_employment_at = Column(DateTime, nullable=True)

    idle_days = Column(Float, nullable=True) # NULL if next employment unknown
    idle_cost = Column(Float, nullable=True) # NULL if daily cost unavailable
    confidence = Column(SQLEnum(DecisionConfidence), nullable=False, default=DecisionConfidence.MEDIUM)
    data_status = Column(SQLEnum(DataStatusType), default=DataStatusType.SYNTHETIC)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    vessel = relationship("Vessel")
    repositioning_options = relationship("RepositioningOption", back_populates="idle_scenario", cascade="all, delete-orphan")


class RepositioningOption(Base):
    """
    Evaluated ballast repositioning candidate for an idle or completing vessel:
    Connects current availability port with an alternative cargo load port.
    """
    __tablename__ = "repositioning_options"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    idle_scenario_id = Column(String(36), ForeignKey("idle_scenarios.id", ondelete="CASCADE"), nullable=True, index=True)
    vessel_id = Column(String(36), ForeignKey("vessels.id", ondelete="CASCADE"), nullable=False, index=True)

    target_port_id = Column(String(36), ForeignKey("ports.id"), nullable=False, index=True)
    target_cargo_request_id = Column(String(36), ForeignKey("cargo_requirements.id", ondelete="SET NULL"), nullable=True, index=True)

    distance = Column(Float, nullable=False) # Nautical miles
    distance_method = Column(String(50), default="NAUTICAL_CHART") # "NAUTICAL_CHART" or "GEODESIC_APPROXIMATION"
    estimated_sailing_days = Column(Float, nullable=False)

    estimated_bunker_cost = Column(Float, nullable=True) # NULL if consumption/price unsourced
    estimated_total_cost = Column(Float, nullable=True)

    port_compatibility = Column(String(50), default="PASS") # PASS, CONDITIONAL, FAIL, UNKNOWN
    timing_compatibility = Column(String(50), default="ON_TIME") # ON_TIME, TIGHT, MISSED_LAYCAN, UNKNOWN

    status = Column(SQLEnum(RepositioningDecision), nullable=False, default=RepositioningDecision.UNKNOWN)
    data_status = Column(SQLEnum(DataStatusType), default=DataStatusType.SYNTHETIC)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    idle_scenario = relationship("IdleScenario", back_populates="repositioning_options")
    vessel = relationship("Vessel")
    target_port = relationship("Port")
    target_cargo_request = relationship("CargoRequirement")
