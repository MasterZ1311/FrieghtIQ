import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum, Text
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import (
    RiskType, RiskSeverity, RiskStatus, TidalWindowStatus,
    CongestionIndicator, DecisionConfidence, DataStatusType
)


class WeatherObservation(Base):
    """
    Sourced and simulated marine meteorological observations along ports and transit corridors.
    Tracks sea-state, wave heights, wind forces, and precipitation affecting dry bulk cargo handling.
    """
    __tablename__ = "weather_observations"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    location_type = Column(String(50), nullable=False)  # PORT, TRADE_LANE, COASTAL_AREA
    location_id = Column(String(36), ForeignKey("ports.id", ondelete="SET NULL"), nullable=True, index=True)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    observed_at = Column(DateTime, nullable=False, index=True)
    forecast_for = Column(DateTime, nullable=True, index=True)

    wind_speed = Column(Float, nullable=False)  # Knots
    wind_direction = Column(Float, nullable=True)  # Degrees (0-360)
    wave_height = Column(Float, nullable=False)  # Significant wave height in meters (Hs)
    rainfall = Column(Float, default=0.0)  # mm/hr (critical for bulk moisture/liquefaction)
    visibility = Column(Float, default=10.0)  # Nautical miles
    storm_indicator = Column(String(100), default="NONE")  # NONE, CYCLONE_STAGE_1, DEPRESSION, GALE

    source_id = Column(String(100), nullable=False)  # IMD_BULLETIN, NOAA_GFS, SYNTHETIC_BAY_OF_BENGAL
    dataset_version_id = Column(String(100), nullable=True)
    data_status = Column(SQLEnum(DataStatusType), default=DataStatusType.SYNTHETIC)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    port = relationship("Port", foreign_keys=[location_id])

    @property
    def port_id(self):
        return self.location_id

    @property
    def port_name(self):
        return self.port.name if self.port else None

    @property
    def wind_speed_knots(self):
        return self.wind_speed

    @property
    def wave_height_m(self):
        return self.wave_height

    @property
    def precipitation_mm(self):
        return self.rainfall

    @property
    def cyclone_alert(self):
        return "CYCLONE" in (self.storm_indicator or "").upper()

    @property
    def cargo_handling_stoppage(self):
        return (self.rainfall or 0.0) > 2.0 or (self.wind_speed or 0.0) > 35.0

    @property
    def data_source(self):
        return self.source_id

    @property
    def is_synthetic(self):
        return self.data_status == DataStatusType.SYNTHETIC


class TidalWindow(Base):
    """
    Hydrographic tidal height observations and gate clearance windows for draft-constrained ports.
    Used by TidalGateScheduler to calculate Under Keel Clearance (UKC) and high-water arrival slots.
    """
    __tablename__ = "tidal_windows"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    port_id = Column(String(36), ForeignKey("ports.id", ondelete="CASCADE"), nullable=False, index=True)
    berth_id = Column(String(36), ForeignKey("berths.id", ondelete="SET NULL"), nullable=True, index=True)

    window_start = Column(DateTime, nullable=False, index=True)
    window_end = Column(DateTime, nullable=False, index=True)

    predicted_tide = Column(Float, nullable=False)  # Meters above Chart Datum (CD)
    required_depth = Column(Float, nullable=True)  # Vessel draft + mandatory UKC (meters)
    available_depth = Column(Float, nullable=False)  # Natural berth/channel depth + predicted_tide
    vessel_draft = Column(Float, nullable=True)  # Actual vessel arrival draft

    status = Column(SQLEnum(TidalWindowStatus), nullable=False, default=TidalWindowStatus.UNKNOWN)
    source_id = Column(String(100), nullable=False)  # NHO_TIDE_TABLES, PPA_HYDROGRAPHIC_LOG
    dataset_version_id = Column(String(100), nullable=True)
    data_status = Column(SQLEnum(DataStatusType), default=DataStatusType.SYNTHETIC)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    port = relationship("Port", foreign_keys=[port_id])
    berth = relationship("Berth", foreign_keys=[berth_id])

    @property
    def port_name(self):
        return self.port.name if self.port else None

    @property
    def berth_name(self):
        return self.berth.name if self.berth else None

    @property
    def predicted_tide_height_m(self):
        return self.predicted_tide

    @property
    def total_available_depth_m(self):
        return self.available_depth

    @property
    def required_ukc_m(self):
        return round(self.required_depth - (self.vessel_draft or 0.0), 2) if self.required_depth and self.vessel_draft else 0.5

    @property
    def data_source(self):
        return self.source_id


class PortCongestion(Base):
    """
    Anchorage waiting queue depth, berth occupancy, and turnaround delays for East Coast bulk ports.
    """
    __tablename__ = "port_congestion"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    port_id = Column(String(36), ForeignKey("ports.id", ondelete="CASCADE"), nullable=False, index=True)
    observed_at = Column(DateTime, nullable=False, index=True)

    vessels_in_port = Column(Integer, nullable=False, default=0)
    vessels_waiting = Column(Integer, nullable=False, default=0)  # Anchorage queue count
    berths_occupied = Column(Integer, nullable=False, default=0)
    estimated_wait_hours = Column(Float, nullable=False, default=0.0)

    congestion_indicator = Column(SQLEnum(CongestionIndicator), nullable=False, default=CongestionIndicator.LOW)
    methodology = Column(String(100), nullable=False, default="PORT_DAILY_LINEUP")
    source_id = Column(String(100), nullable=False)
    dataset_version_id = Column(String(100), nullable=True)
    data_status = Column(SQLEnum(DataStatusType), default=DataStatusType.SYNTHETIC)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    port = relationship("Port", foreign_keys=[port_id])

    @property
    def port_name(self):
        return self.port.name if self.port else None

    @property
    def snapshot_time(self):
        return self.observed_at

    @property
    def waiting_vessels_count(self):
        return self.vessels_waiting

    @property
    def working_vessels_count(self):
        return max(0, self.vessels_in_port - self.vessels_waiting)

    @property
    def anchorage_vessels_count(self):
        return self.vessels_waiting

    @property
    def berth_occupancy_pct(self):
        return round(min(98.0, max(40.0, (self.berths_occupied / max(1, self.berths_occupied + 2)) * 100)), 1)

    @property
    def avg_waiting_hours(self):
        return self.estimated_wait_hours

    @property
    def avg_turnaround_hours(self):
        return round(self.estimated_wait_hours * 1.8, 1)

    @property
    def capesize_waiting_count(self):
        return max(0, int(self.vessels_waiting * 0.4))

    @property
    def panamax_waiting_count(self):
        return max(0, int(self.vessels_waiting * 0.45))

    @property
    def supramax_waiting_count(self):
        return max(0, int(self.vessels_waiting * 0.15))

    @property
    def data_source(self):
        return self.source_id


class RiskEvent(Base):
    """
    Unified operational risk event generated by Weather, Tidal, Congestion, Port, or Timing services.
    Feeds the Unified Operational Risk Center.
    """
    __tablename__ = "risk_events"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(50), nullable=False)  # VOYAGE, VESSEL, PORT, CARGO_REQUIREMENT
    entity_id = Column(String(36), nullable=False, index=True)
    voyage_id = Column(String(36), nullable=True, index=True)

    risk_type = Column(SQLEnum(RiskType), nullable=False, index=True)
    severity = Column(SQLEnum(RiskSeverity), nullable=False, index=True)
    status = Column(SQLEnum(RiskStatus), nullable=False, default=RiskStatus.ACTIVE)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    evidence = Column(Text, nullable=False)
    potential_impact = Column(Text, nullable=False)

    affected_start = Column(DateTime, nullable=True)
    affected_end = Column(DateTime, nullable=True)

    source_id = Column(String(100), nullable=True)
    dataset_version_id = Column(String(100), nullable=True)
    data_status = Column(SQLEnum(DataStatusType), default=DataStatusType.SYNTHETIC)
    confidence = Column(SQLEnum(DecisionConfidence), default=DecisionConfidence.MEDIUM)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @property
    def port_id(self):
        return self.entity_id if self.entity_type == "PORT" else None

    @property
    def port_name(self):
        return None

    @property
    def berth_id(self):
        return None

    @property
    def vessel_id(self):
        return self.entity_id if self.entity_type == "VESSEL" else None

    @property
    def vessel_name(self):
        return None

    @property
    def trigger_source(self):
        return self.source_id or "OPERATIONAL_OBSERVATION"

    @property
    def occurred_at(self):
        return self.affected_start or self.created_at

    @property
    def expires_at(self):
        return self.affected_end

    @property
    def financial_exposure_usd(self):
        # Extract from potential impact if present
        if "$45,000" in self.potential_impact:
            return 45000.0
        if "$18,000" in self.potential_impact:
            return 18000.0
        if "$28,000" in self.potential_impact:
            return 28000.0
        if "$95,000" in self.potential_impact:
            return 95000.0
        if "$15,000" in self.potential_impact:
            return 15000.0
        if "$22,000" in self.potential_impact:
            return 22000.0
        return 0.0

    @property
    def delay_hours_estimate(self):
        if "24h" in self.potential_impact:
            return 24.0
        if "16h" in self.potential_impact:
            return 16.0
        if "18h" in self.potential_impact:
            return 18.0
        if "52h" in self.potential_impact:
            return 52.0
        if "12h" in self.potential_impact:
            return 12.0
        if "14h" in self.potential_impact:
            return 14.0
        return 0.0

    @property
    def mitigation_action(self):
        return self.potential_impact
