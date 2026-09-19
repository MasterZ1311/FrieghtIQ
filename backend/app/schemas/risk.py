from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from app.models.enums import (
    RiskType,
    RiskSeverity,
    RiskStatus,
    TidalWindowStatus,
    CongestionIndicator,
    DataStatusType,
)


# ----------------------------------------------------
# Weather Schemas
# ----------------------------------------------------

class WeatherObservationSchema(BaseModel):
    id: str
    port_id: str
    port_name: Optional[str] = None
    observed_at: datetime
    temperature_c: Optional[float] = None
    wind_speed_knots: Optional[float] = None
    wind_direction_deg: Optional[int] = None
    gust_speed_knots: Optional[float] = None
    wave_height_m: Optional[float] = None
    swell_height_m: Optional[float] = None
    precipitation_mm: Optional[float] = None
    visibility_km: Optional[float] = None
    pressure_hpa: Optional[float] = None
    cyclone_alert: bool = False
    cargo_handling_stoppage: bool = False
    data_source: str = "SYNTHETIC"
    is_synthetic: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WeatherEvaluationResponse(BaseModel):
    port_id: str
    port_name: Optional[str] = None
    severity: str
    current_weather: Optional[Dict[str, Any]] = None
    forecast: List[Dict[str, Any]] = []
    handling_stoppage_risk: str
    navigation_risk: str
    estimated_weather_delay_hours: float
    explanations: List[str] = []
    mitigations: List[str] = []
    data_source: str
    is_synthetic: bool


# ----------------------------------------------------
# Tidal Schemas
# ----------------------------------------------------

class TidalWindowSchema(BaseModel):
    id: str
    port_id: str
    port_name: Optional[str] = None
    berth_id: Optional[str] = None
    berth_name: Optional[str] = None
    window_start: datetime
    window_end: datetime
    peak_water_time: Optional[datetime] = None
    predicted_tide_height_m: Optional[float] = None
    berth_depth_cd_m: Optional[float] = None
    total_available_depth_m: Optional[float] = None
    required_ukc_m: float = 0.5
    status: TidalWindowStatus = TidalWindowStatus.UNKNOWN
    explanation: Optional[str] = None
    data_source: str = "SYNTHETIC"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TidalEvaluationRequest(BaseModel):
    port_id: str
    port_name: Optional[str] = None
    berth_id: Optional[str] = None
    vessel_draft_m: Optional[float] = None
    berth_draft_m: Optional[float] = None
    channel_draft_m: Optional[float] = None
    required_ukc_m: float = 0.5
    arrival_time: Optional[datetime] = None


class TidalEvaluationResponse(BaseModel):
    status: str
    vessel_draft_m: Optional[float] = None
    berth_draft_m: Optional[float] = None
    required_ukc_m: Optional[float] = None
    required_depth_m: Optional[float] = None
    available_depth_m: Optional[float] = None
    ukc_margin_m: Optional[float] = None
    high_water_slots: List[Dict[str, Any]] = []
    recommended_window: Optional[Dict[str, Any]] = None
    explanation: str
    mitigation: str


# ----------------------------------------------------
# Congestion Schemas
# ----------------------------------------------------

class PortCongestionSchema(BaseModel):
    id: str
    port_id: str
    port_name: Optional[str] = None
    snapshot_time: datetime
    waiting_vessels_count: int = 0
    working_vessels_count: int = 0
    anchorage_vessels_count: int = 0
    berth_occupancy_pct: float = 0.0
    avg_waiting_hours: float = 0.0
    avg_turnaround_hours: float = 0.0
    congestion_indicator: CongestionIndicator = CongestionIndicator.UNKNOWN
    capesize_waiting_count: int = 0
    panamax_waiting_count: int = 0
    supramax_waiting_count: int = 0
    data_source: str = "SYNTHETIC"
    data_status: DataStatusType = DataStatusType.DEMO
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CongestionEvaluationResponse(BaseModel):
    port_id: str
    port_name: Optional[str] = None
    severity: str
    indicator: str
    congestion_data: Optional[Dict[str, Any]] = None
    history: List[Dict[str, Any]] = []
    vessel_class: str
    avg_wait_hours: float
    laytime_allowed_hours: float
    demurrage_exposure_usd: Optional[float] = None
    demurrage_hours: float
    explanations: List[str] = []
    mitigations: List[str] = []
    data_source: str
    is_synthetic: bool = True


# ----------------------------------------------------
# Risk Event Schemas
# ----------------------------------------------------

class RiskEventSchema(BaseModel):
    id: str
    risk_type: RiskType
    severity: RiskSeverity
    status: RiskStatus
    port_id: Optional[str] = None
    port_name: Optional[str] = None
    berth_id: Optional[str] = None
    vessel_id: Optional[str] = None
    vessel_name: Optional[str] = None
    voyage_id: Optional[str] = None
    title: str
    description: str
    trigger_source: str
    occurred_at: datetime
    expires_at: Optional[datetime] = None
    financial_exposure_usd: Optional[float] = None
    delay_hours_estimate: Optional[float] = None
    mitigation_action: Optional[str] = None
    data_status: DataStatusType = DataStatusType.DEMO
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RiskEventCreate(BaseModel):
    risk_type: RiskType
    severity: RiskSeverity
    status: RiskStatus = RiskStatus.ACTIVE
    port_id: Optional[str] = None
    port_name: Optional[str] = None
    berth_id: Optional[str] = None
    vessel_id: Optional[str] = None
    vessel_name: Optional[str] = None
    voyage_id: Optional[str] = None
    title: str
    description: str
    trigger_source: str = "OPERATIONAL_OBSERVATION"
    occurred_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    financial_exposure_usd: Optional[float] = None
    delay_hours_estimate: Optional[float] = None
    mitigation_action: Optional[str] = None
    data_status: DataStatusType = DataStatusType.DEMO


# ----------------------------------------------------
# Unified Risk Summary & Voyage Schemas
# ----------------------------------------------------

class UnifiedRiskSummaryResponse(BaseModel):
    total_active_events: int
    critical_events_count: int
    high_events_count: int
    medium_events_count: int
    low_events_count: int
    overall_operational_severity: str
    total_financial_exposure_usd: float
    total_delay_hours: float
    events: List[RiskEventSchema]
    top_risk_ports: List[Dict[str, Any]]
    provenance_breakdown: Dict[str, int]


class PortRiskEvaluationResponse(BaseModel):
    port_id: str
    port_name: Optional[str] = None
    overall_severity: str
    primary_drivers: List[Dict[str, Any]]
    financial_exposure: Dict[str, Any]
    total_delay_hours: float
    components: Dict[str, Any]
    explanations: List[str]
    mitigations: List[str]


class VoyageRiskEvaluationRequest(BaseModel):
    origin_port_id: str
    origin_port_name: Optional[str] = None
    destination_port_id: str
    destination_port_name: Optional[str] = None
    vessel_id: Optional[str] = None
    vessel_name: Optional[str] = None
    vessel_class: Optional[str] = "PANAMAX"
    vessel_draft_m: Optional[float] = None
    origin_berth_draft_m: Optional[float] = None
    destination_berth_draft_m: Optional[float] = None
    cargo_type: Optional[str] = "COKING_COAL"
    eta_origin: Optional[datetime] = None
    laycan_from: Optional[datetime] = None
    laycan_to: Optional[datetime] = None
    charter_hire_usd_per_day: float = 20000.0


class VoyageRiskEvaluationResponse(BaseModel):
    origin_port: Dict[str, Any]
    destination_port: Dict[str, Any]
    timing_risk: Dict[str, Any]
    data_quality: Dict[str, Any]
    overall_severity: str
    primary_drivers: List[Dict[str, Any]]
    financial_exposure: Dict[str, Any]
    total_delay_hours: float
    explanations: List[str]
    mitigations: List[str]
