from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.enums import (
    CargoType,
    VesselClass,
    DataStatusType,
    DecisionPipelineState,
    DecisionReadinessStatus,
    RiskSeverity,
)


class DecisionTimelineEvent(BaseModel):
    stage: str
    label: str
    status: str  # "COMPLETED", "FAILED", "RUNNING", "SKIPPED", "PENDING"
    timestamp: str
    duration_ms: float = 0.0
    details: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class CargoContextData(BaseModel):
    id: str
    requirement_code: str
    title: str
    commodity: str
    cargo_type: str
    quantity_mt: float
    tolerance_pct: float = 10.0
    load_port_id: str
    load_port_name: str
    discharge_port_id: str
    discharge_port_name: str
    laycan_start: str
    laycan_end: str
    decision_horizon_days: int = 30
    target_freight_usd_pmt: Optional[float] = None
    data_status: DataStatusType = DataStatusType.VERIFIED


class RouteContextData(BaseModel):
    origin_port_id: str
    origin_port_name: str
    origin_unlocode: str
    origin_country: str
    destination_port_id: str
    destination_port_name: str
    destination_unlocode: str
    destination_country: str
    distance_nm: float = 5840.0
    trade_lane: str = "AUNCL -> INPRT"
    ballast_distance_nm: float = 0.0
    data_status: DataStatusType = DataStatusType.VERIFIED


class VesselContextData(BaseModel):
    id: str
    name: str
    imo: str
    vessel_class: str
    dwt: float
    draft_m: float
    beam_m: float
    loa_m: float
    speed_laden_knots: float = 12.5
    speed_ballast_knots: float = 13.0
    consumption_laden_mtpd: float = 28.5
    match_score: float = 90.0
    match_status: str = "RELEVANT"
    match_summary: Optional[str] = None
    data_status: DataStatusType = DataStatusType.VERIFIED


class PortsContextData(BaseModel):
    origin_constraints: List[Dict[str, Any]] = Field(default_factory=list)
    destination_constraints: List[Dict[str, Any]] = Field(default_factory=list)
    evaluated_berths: int = 4
    feasibility_status: str = "PASS"
    summary: str = "Passes draft, beam, and LOA limitations at destination berths."
    data_status: DataStatusType = DataStatusType.VERIFIED


class ForecastContextData(BaseModel):
    route_code: str = "AUNCL-INPRT"
    p10: float = 13.80
    p50: float = 15.20
    p90: float = 17.10
    currency: str = "USD"
    unit: str = "USD/MT"
    model_version: str = "TFT_WALK_FORWARD_V1"
    dataset_version: str = "FREIGHT_DATASET_DEMO"
    data_status: DataStatusType = DataStatusType.SYNTHETIC


class RegimeContextData(BaseModel):
    regime: str = "BEAR"
    probabilities: Dict[str, float] = Field(default_factory=lambda: {"BEAR": 0.20, "BASE": 0.65, "BULL": 0.15})
    forecast_alignment: str = "ALIGNED"
    confidence: float = 0.85
    data_status: DataStatusType = DataStatusType.CALCULATED


class WaitFixContextData(BaseModel):
    decision: str = "FIX_NOW"
    decision_confidence: str = "HIGH"
    current_freight_rate: float = 15.20
    expected_wait_rate: float = 15.85
    expected_savings_usd: float = 28500.0
    option_value_usd: Optional[float] = 12400.0
    recommendation_rationale: str = "Forward rate surge risk exceeds current spot level."
    data_status: DataStatusType = DataStatusType.CALCULATED


class ContractContextData(BaseModel):
    recommended_strategy: str = "SPOT"
    spot_cost_usd: float = 1140000.0
    short_term_cost_usd: float = 1205000.0
    medium_term_cost_usd: float = 1260000.0
    total_requirement_mt: float = 75000.0
    confidence: str = "HIGH"
    data_status: DataStatusType = DataStatusType.CALCULATED


class IdleContextData(BaseModel):
    daily_holding_cost_usd: float = 8500.0
    days_idle: float = 0.0
    risk_level: str = "LOW"
    repositioning_decision: str = "DO_NOT_REPOSITION"
    ballast_distance_nm: float = 0.0
    data_status: DataStatusType = DataStatusType.CALCULATED


class RiskContextData(BaseModel):
    overall_severity: str = "MEDIUM"
    active_risks_count: int = 3
    congestion_indicator: str = "MODERATE"
    avg_queue_days: float = 1.5
    weather_severity: str = "LOW"
    tidal_status: str = "PASS"
    safe_ukc_m: float = 1.2
    financial_exposure_usd: float = 27250.0
    data_status: DataStatusType = DataStatusType.RECENT


class EconomicsContextData(BaseModel):
    total_voyage_cost_usd: float = 1684500.0
    cost_per_mt_usd: float = 22.46
    distance_nm: float = 5840.0
    freight_cost_usd: float = 1140000.0
    bunker_cost_usd: float = 385000.0
    port_cost_usd: float = 78500.0
    time_cost_usd: float = 53750.0
    delay_cost_usd: float = 27250.0
    repositioning_cost_usd: float = 0.0
    currency: str = "USD"
    data_status: DataStatusType = DataStatusType.CALCULATED


class DataQualityContextData(BaseModel):
    overall_status: DataStatusType = DataStatusType.SYNTHETIC
    confidence_score: float = 0.88
    items: List[Dict[str, Any]] = Field(default_factory=list)
    limitations_explanation: str = "Delivered assessment combines deterministic rule evaluations with synthetic/demo forward freight curves."


class DecisionReadinessData(BaseModel):
    status: DecisionReadinessStatus = DecisionReadinessStatus.READY
    score: float = 88.0
    blockers: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    rationale: str = "All essential technical, navigational, and commercial inputs have been verified."


class VoyageDecisionContext(BaseModel):
    """
    Canonical, versioned decision context unifying Phases 3-11 analytics.
    Propagates consistent entity keys and provenance.
    """
    context_version: str = "1.0.0"
    decision_id: str
    analysis_run_id: str
    cargo_id: str
    voyage_id: str
    vessel_id: Optional[str] = None
    origin_port_id: str
    destination_port_id: str

    status: DecisionPipelineState = DecisionPipelineState.READY

    cargo: CargoContextData
    route: RouteContextData
    vessel: Optional[VesselContextData] = None
    ports: PortsContextData
    forecast: ForecastContextData
    regime: RegimeContextData
    wait_fix: WaitFixContextData
    contract: ContractContextData
    idle: IdleContextData
    risk: RiskContextData
    economics: EconomicsContextData

    data_quality: DataQualityContextData
    decision_readiness: DecisionReadinessData
    timeline: List[DecisionTimelineEvent] = Field(default_factory=list)

    generated_at: str
    model_config = ConfigDict(from_attributes=True)


class AnalysisRunCreateRequest(BaseModel):
    cargo_id: str
    voyage_id: Optional[str] = None
    vessel_id: Optional[str] = None
    origin_port_id: Optional[str] = None
    destination_port_id: Optional[str] = None
    user_id: Optional[str] = "SAIL-COMMERCIAL-OFFICER"


class AnalysisRunSchema(BaseModel):
    id: str
    decision_id: Optional[str] = None
    cargo_id: Optional[str] = None
    voyage_id: Optional[str] = None
    vessel_id: Optional[str] = None
    origin_port_id: Optional[str] = None
    destination_port_id: Optional[str] = None
    context_version: str
    status: DecisionPipelineState
    stage: str
    execution_time_ms: float
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AnalysisRunDetailSchema(AnalysisRunSchema):
    model_versions: Optional[Dict[str, Any]] = None
    dataset_versions: Optional[Dict[str, Any]] = None
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    data_quality: Optional[Dict[str, Any]] = None
    readiness: Optional[Dict[str, Any]] = None
    timeline: Optional[List[DecisionTimelineEvent]] = None


class CharteringDecisionSchema(BaseModel):
    id: str
    title: str
    cargo_id: Optional[str] = None
    status: DecisionPipelineState
    readiness_status: DecisionReadinessStatus
    readiness_score: float
    latest_analysis_run_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CharteringDecisionDetailSchema(CharteringDecisionSchema):
    canonical_context: Optional[VoyageDecisionContext] = None


class VoyageDecisionReportSchema(BaseModel):
    report_id: str
    decision_id: str
    analysis_run_id: str
    generated_at: str
    title: str
    classification: str = "SAIL CONFIDENTIAL / TENDER BRIEFING"

    executive_summary: str
    cargo_requirement: Dict[str, Any]
    vessel_analysis: Dict[str, Any]
    port_feasibility: Dict[str, Any]
    freight_forecast: Dict[str, Any]
    market_regime: Dict[str, Any]
    wait_fix: Dict[str, Any]
    contract_strategy: Dict[str, Any]
    idle_repositioning: Dict[str, Any]
    operational_risk: Dict[str, Any]
    voyage_economics: Dict[str, Any]
    data_quality_scorecard: Dict[str, Any]
    decision_readiness: Dict[str, Any]
    assumptions: List[str]
    sources: List[Dict[str, Any]]
    signoff_block: Dict[str, Any]


class ReportExportRequest(BaseModel):
    decision_id: str
    format: str = "JSON"  # "PDF", "CSV", "JSON"


class ExecutiveDashboardSummarySchema(BaseModel):
    active_cargo_requests_count: int
    pending_decisions_count: int
    matched_vessels_count: int
    high_risk_voyages_count: int
    partial_analyses_count: int

    primary_decision: Optional[Dict[str, Any]] = None

    market_overview: Dict[str, Any]
    operations_overview: Dict[str, Any]
    economics_overview: Dict[str, Any]
    audit_events_recent: List[Dict[str, Any]] = Field(default_factory=list)


class AdminDataHealthSchema(BaseModel):
    overall_status: str
    total_adapters: int
    active_adapters: int
    adapters: List[Dict[str, Any]]


class AdminModelHealthSchema(BaseModel):
    total_models: int
    models: List[Dict[str, Any]]


class AuditLogSchema(BaseModel):
    id: str
    user_id: str
    action: str
    entity_type: str
    entity_id: str
    analysis_run_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
