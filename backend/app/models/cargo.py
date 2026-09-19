from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.enums import CargoType, RequirementStatus

class CargoRequirement(Base):
    __tablename__ = "cargo_requirements"

    id = Column(String(36), primary_key=True, index=True)
    requirement_code = Column(String(30), unique=True, index=True, nullable=False) # e.g. "CR-2026-001"
    title = Column(String(200), nullable=False)
    cargo_type = Column(SQLEnum(CargoType), nullable=False, index=True)
    quantity_mt = Column(Float, nullable=False)
    tolerance_pct = Column(Float, default=10.0) # MOLOO: More or Less Owner's Option +/- 10%
    
    # Port references
    load_port_id = Column(String(36), ForeignKey("ports.id"), nullable=False)
    discharge_port_id = Column(String(36), ForeignKey("ports.id"), nullable=False)
    
    # Laycan window (dates when vessel must be ready to load)
    laycan_start = Column(DateTime, nullable=False)
    laycan_end = Column(DateTime, nullable=False)
    
    # Chartering constraints
    target_freight_usd_pmt = Column(Float, nullable=True)
    max_vessel_age_years = Column(Integer, default=15)
    preferred_vessel_classes = Column(String(100), default="PANAMAX,KAMSARMAX")
    gear_requirement = Column(String(50), default="ANY") # GEARLESS, GEARED, ANY
    
    status = Column(SQLEnum(RequirementStatus), default=RequirementStatus.MARKET_SCAN, nullable=False)
    created_by = Column(String(100), default="SAIL Commercial Division")
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    load_port = relationship("Port", foreign_keys=[load_port_id])
    discharge_port = relationship("Port", foreign_keys=[discharge_port_id])
    handling_logs = relationship("CargoHandlingLog", back_populates="requirement", cascade="all, delete-orphan")


class CargoHandlingLog(Base):
    __tablename__ = "cargo_handling_logs"

    id = Column(String(36), primary_key=True, index=True)
    requirement_id = Column(String(36), ForeignKey("cargo_requirements.id", ondelete="CASCADE"), nullable=False, index=True)
    vessel_id = Column(String(36), ForeignKey("vessels.id"), nullable=True)
    port_id = Column(String(36), ForeignKey("ports.id"), nullable=False)
    berth_id = Column(String(36), ForeignKey("berths.id"), nullable=True)
    
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    quantity_handled_mt = Column(Float, nullable=False)
    average_rate_tpd = Column(Float, nullable=True)
    weather_delays_hours = Column(Float, default=0.0)
    remarks = Column(Text, nullable=True)

    requirement = relationship("CargoRequirement", back_populates="handling_logs")
