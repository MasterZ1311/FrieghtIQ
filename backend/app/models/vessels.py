from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.enums import VesselClass, VesselStatus

class Vessel(Base):
    __tablename__ = "vessels"

    id = Column(String(36), primary_key=True, index=True)
    imo_number = Column(String(10), unique=True, index=True, nullable=False)
    vessel_name = Column(String(100), nullable=False, index=True)
    vessel_class = Column(SQLEnum(VesselClass), nullable=False, index=True)
    flag = Column(String(50), nullable=True)
    year_built = Column(Integer, nullable=True)
    call_sign = Column(String(20), nullable=True)
    classification_society = Column(String(50), nullable=True)
    is_snapshot_vessel = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    particulars = relationship("VesselParticulars", back_populates="vessel", uselist=False, cascade="all, delete-orphan")
    availability = relationship("VesselAvailability", back_populates="vessel", uselist=False, cascade="all, delete-orphan")
    snapshot_records = relationship("OperationalSnapshotVessel", back_populates="vessel", cascade="all, delete-orphan")


class VesselParticulars(Base):
    __tablename__ = "vessel_particulars"

    id = Column(String(36), primary_key=True, index=True)
    vessel_id = Column(String(36), ForeignKey("vessels.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    summer_dwt = Column(Float, nullable=True)
    summer_draft_m = Column(Float, nullable=True)
    loa_m = Column(Float, nullable=True)
    beam_m = Column(Float, nullable=True)
    depth_m = Column(Float, nullable=True)
    gross_tonnage = Column(Float, nullable=True)
    net_tonnage = Column(Float, nullable=True)
    grain_capacity_cbm = Column(Float, nullable=True)
    bale_capacity_cbm = Column(Float, nullable=True)
    holds_hatches_count = Column(String(20), nullable=True)
    gear_summary = Column(String(100), nullable=True) # e.g. "4 x 30t Cranes + Grabs" or "Gearless"
    speed_ballast_knots = Column(Float, nullable=True)
    speed_laden_knots = Column(Float, nullable=True)
    consumption_laden_mtpd = Column(Float, nullable=True)
    
    # Metadata flag to show if true dimensions are verified or partial
    is_verified = Column(Boolean, default=True)
    unverified_fields = Column(String(255), nullable=True)

    vessel = relationship("Vessel", back_populates="particulars")


class VesselAvailability(Base):
    __tablename__ = "vessel_availabilities"

    id = Column(String(36), primary_key=True, index=True)
    vessel_id = Column(String(36), ForeignKey("vessels.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    current_status = Column(SQLEnum(VesselStatus), nullable=False, default=VesselStatus.BALLAST_TRANSIT)
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    current_port_name = Column(String(100), nullable=True)
    destination_port_name = Column(String(100), nullable=True)
    
    # Open window for next employment
    open_port_name = Column(String(100), nullable=True)
    open_date_start = Column(DateTime, nullable=True)
    open_date_end = Column(DateTime, nullable=True)
    eta_open_port = Column(DateTime, nullable=True)
    
    data_confidence = Column(String(20), default="MEDIUM") # HIGH, MEDIUM, LOW, UNCONFIRMED
    source_evidence = Column(String(100), default="AIS / Broker Report")
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    vessel = relationship("Vessel", back_populates="availability")


class OperationalSnapshotVessel(Base):
    """
    Explicit model for vessels originating from operational handling records.
    Ensures handling cargo quantity is NEVER conflated with true vessel deadweight (DWT).
    """
    __tablename__ = "operational_snapshot_vessels"

    id = Column(String(36), primary_key=True, index=True)
    vessel_id = Column(String(36), ForeignKey("vessels.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_vessel_name = Column(String(100), nullable=False)
    observed_handled_cargo_mt = Column(Float, nullable=False)
    cargo_type = Column(String(50), nullable=False)
    discharge_port_code = Column(String(30), nullable=False) # e.g. "INPRT"
    discharge_berth_code = Column(String(30), nullable=True)
    observation_date = Column(DateTime, nullable=False)
    data_integrity_note = Column(
        Text,
        default="Observed handled cargo reflects voyage parcel size, NOT true vessel deadweight capacity. DWT marked UNKNOWN if not separately verified."
    )

    vessel = relationship("Vessel", back_populates="snapshot_records")
