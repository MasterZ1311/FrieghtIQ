from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.enums import DataSourceType, ConstraintSeverity

class Port(Base):
    __tablename__ = "ports"

    id = Column(String(36), primary_key=True, index=True)
    unlocode = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False, index=True)
    country = Column(String(50), nullable=False, default="India")
    coast = Column(String(50), nullable=True)  # e.g. "East Coast India"
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Approach Channel Parameters
    channel_max_draft_m = Column(Float, nullable=True)
    channel_max_loa_m = Column(Float, nullable=True)
    channel_max_beam_m = Column(Float, nullable=True)
    tide_range_m = Column(Float, nullable=True)
    night_navigation = Column(Boolean, default=True)
    tug_requirement_count = Column(Integer, default=2)
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    berths = relationship("Berth", back_populates="port", cascade="all, delete-orphan")
    constraints = relationship("PortConstraint", back_populates="port", cascade="all, delete-orphan")
    data_sources = relationship("PortDataSource", back_populates="port", cascade="all, delete-orphan")


class Berth(Base):
    __tablename__ = "berths"

    id = Column(String(36), primary_key=True, index=True)
    port_id = Column(String(36), ForeignKey("ports.id", ondelete="CASCADE"), nullable=False, index=True)
    berth_code = Column(String(30), nullable=False, index=True)
    berth_name = Column(String(100), nullable=False)
    berth_type = Column(String(50), nullable=False) # e.g. "Mechanised Coal", "Dry Bulk", "Multipurpose"
    
    # Hard Physical Constraints
    max_loa_m = Column(Float, nullable=True)
    max_beam_m = Column(Float, nullable=True)
    max_draft_m = Column(Float, nullable=True)
    max_air_draft_m = Column(Float, nullable=True)
    max_dwt = Column(Float, nullable=True)
    
    # Handling Productivity
    discharge_rate_tpd = Column(Float, nullable=True) # Tons Per Day
    loading_rate_tpd = Column(Float, nullable=True)
    equipment_summary = Column(String(255), nullable=True)
    night_berthing = Column(Boolean, default=True)
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    port = relationship("Port", back_populates="berths")
    constraints = relationship("BerthConstraint", back_populates="berth", cascade="all, delete-orphan")


class PortConstraint(Base):
    __tablename__ = "port_constraints"

    id = Column(String(36), primary_key=True, index=True)
    port_id = Column(String(36), ForeignKey("ports.id", ondelete="CASCADE"), nullable=False, index=True)
    constraint_type = Column(String(50), nullable=False) # e.g. "DRAFT", "LOA", "TIDE", "PILOTAGE"
    parameter_name = Column(String(100), nullable=False)
    limit_value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    severity = Column(SQLEnum(ConstraintSeverity), default=ConstraintSeverity.BLOCKING)
    condition_description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    port = relationship("Port", back_populates="constraints")


class BerthConstraint(Base):
    __tablename__ = "berth_constraints"

    id = Column(String(36), primary_key=True, index=True)
    berth_id = Column(String(36), ForeignKey("berths.id", ondelete="CASCADE"), nullable=False, index=True)
    constraint_type = Column(String(50), nullable=False)
    parameter_name = Column(String(100), nullable=False)
    limit_value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    severity = Column(SQLEnum(ConstraintSeverity), default=ConstraintSeverity.BLOCKING)
    condition_description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    berth = relationship("Berth", back_populates="constraints")


class PortDataSource(Base):
    __tablename__ = "port_data_sources"

    id = Column(String(36), primary_key=True, index=True)
    port_id = Column(String(36), ForeignKey("ports.id", ondelete="CASCADE"), nullable=False, index=True)
    source_name = Column(String(100), nullable=False)
    source_type = Column(SQLEnum(DataSourceType), nullable=False)
    doc_reference = Column(String(100), nullable=True)
    publication_date = Column(DateTime, nullable=True)
    verified = Column(Boolean, default=True)
    verified_by = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    port = relationship("Port", back_populates="data_sources")


class ConstraintVersion(Base):
    __tablename__ = "constraint_versions"

    id = Column(String(36), primary_key=True, index=True)
    entity_type = Column(String(30), nullable=False) # "PORT" or "BERTH"
    entity_id = Column(String(36), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    change_summary = Column(Text, nullable=False)
    updated_by = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
