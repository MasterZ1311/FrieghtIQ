from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from app.models.enums import (
    VesselEmploymentState,
    EmploymentEventType,
    IdleScenarioType,
    RepositioningDecision,
    DeadheadRiskLevel,
    DecisionConfidence,
    DataStatusType,
    EmploymentCompatibility,
)


class VesselEmploymentEventItem(BaseModel):
    id: str
    vessel_id: str
    event_type: EmploymentEventType
    voyage_id: Optional[str] = None
    cargo_request_id: Optional[str] = None
    origin_port_id: Optional[str] = None
    origin_port_name: Optional[str] = None
    destination_port_id: Optional[str] = None
    destination_port_name: Optional[str] = None
    event_start: datetime
    event_end: Optional[datetime] = None
    status: str
    source_id: Optional[str] = None
    data_status: DataStatusType

    class Config:
        from_attributes = True


class IdleScenarioItem(BaseModel):
    id: str
    vessel_id: str
    vessel_name: Optional[str] = None
    vessel_class: Optional[str] = None
    voyage_id: Optional[str] = None
    scenario_type: IdleScenarioType
    current_location: str
    next_known_employment: Optional[str] = None
    estimated_available_at: Optional[datetime] = None
    estimated_next_employment_at: Optional[datetime] = None
    idle_days: Optional[float] = None
    idle_cost: Optional[float] = None
    confidence: DecisionConfidence
    data_status: DataStatusType
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RepositioningOptionItem(BaseModel):
    id: str
    idle_scenario_id: Optional[str] = None
    vessel_id: str
    vessel_name: Optional[str] = None
    target_port_id: str
    target_port_name: Optional[str] = None
    target_cargo_request_id: Optional[str] = None
    cargo_name: Optional[str] = None
    cargo_quantity_mt: Optional[float] = None
    distance: float
    distance_method: str
    estimated_sailing_days: float
    estimated_bunker_cost: Optional[float] = None
    estimated_total_cost: Optional[float] = None
    port_compatibility: str
    timing_compatibility: str
    status: RepositioningDecision
    data_status: DataStatusType
    created_at: datetime

    class Config:
        from_attributes = True


class FleetIdleOverviewResponse(BaseModel):
    dataset_coverage_count: int
    active_vessels_count: int
    idle_risk_count: int
    currently_idle_count: int
    repositioning_count: int
    unknown_state_count: int
    dataset_coverage_label: str
    data_provenance: Dict[str, Any]


class VesselEmploymentSummaryItem(BaseModel):
    vessel_id: str
    vessel_name: str
    vessel_class: str
    current_location: str
    current_voyage: Optional[str] = None
    current_status: str
    employment_state: VesselEmploymentState
    state_explanation: str
    estimated_availability: Optional[datetime] = None
    next_known_employment: Optional[str] = None
    estimated_next_employment_at: Optional[datetime] = None
    idle_days: Optional[float] = None
    idle_exposure_label: str
    idle_risk_level: str
    idle_cost: Optional[float] = None
    daily_cost_label: str
    is_data_complete: bool
    data_confidence: DecisionConfidence
    data_status: DataStatusType
    last_updated: Optional[datetime] = None


class VesselEmploymentTimelineResponse(BaseModel):
    vessel_id: str
    vessel_name: str
    vessel_class: str
    employment_state: VesselEmploymentState
    current_location: str
    current_status: str
    is_verified_particulars: bool
    estimated_availability: Optional[datetime] = None
    next_known_employment: Optional[str] = None
    estimated_next_employment_at: Optional[datetime] = None
    idle_days: Optional[float] = None
    idle_cost: Optional[float] = None
    data_status: DataStatusType
    data_freshness_label: str
    events: List[VesselEmploymentEventItem]
    active_scenario: Optional[IdleScenarioItem] = None
    repositioning_options: List[RepositioningOptionItem] = []


class IdleAnalysisRequest(BaseModel):
    vessel_id: str
    daily_vessel_cost_assumption: Optional[float] = None
    scenario_type: Optional[IdleScenarioType] = IdleScenarioType.EMPLOYMENT_GAP


class RepositioningAnalysisRequest(BaseModel):
    vessel_id: str
    target_port_id: str
    target_cargo_request_id: Optional[str] = None
    speed_assumption_knots: Optional[float] = 12.5
    bunker_price_usd: Optional[float] = 620.0
    daily_vessel_cost_assumption: Optional[float] = None
