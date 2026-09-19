from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.models.enums import (
    CostComponentType,
    VoyageScenarioType,
    SpeedScenarioStatus,
    DataStatusType,
)


class CostComponentItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    component_type: CostComponentType
    amount: float
    currency: str = "USD"
    unit: str = "USD"
    quantity: Optional[float] = None
    rate: Optional[float] = None
    source_id: Optional[str] = None
    data_status: DataStatusType = DataStatusType.SYNTHETIC
    assumption: Optional[str] = None


class SpeedScenarioItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    speed_knots: float
    sailing_hours: float
    sailing_days: float
    fuel_consumption: Optional[float] = None
    fuel_consumed: Optional[float] = None
    bunker_price: Optional[float] = None
    bunker_cost: Optional[float] = None
    time_cost: Optional[float] = None
    delay_exposure: Optional[float] = None
    total_cost: Optional[float] = None
    cost_per_mt: Optional[float] = None
    status: SpeedScenarioStatus = SpeedScenarioStatus.EVALUATED
    assumptions: Optional[str] = None


class VoyageScenarioItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    scenario_name: VoyageScenarioType
    freight_rate: Optional[float] = None
    bunker_price: Optional[float] = None
    speed: Optional[float] = None
    port_delay_hours: Optional[float] = None
    idle_days: Optional[float] = None
    total_cost: float
    cost_per_mt: float
    assumptions: Optional[str] = None
    data_status: DataStatusType = DataStatusType.SYNTHETIC


class VoyageEconomicsAnalysisRequest(BaseModel):
    origin_port_id: str = "newcastle-au"
    destination_port_id: str = "paradip-in"
    cargo_quantity_mt: float = 75000.0
    cargo_type: str = "COKING_COAL"
    vessel_id: Optional[str] = None
    cargo_request_id: Optional[str] = None
    voyage_id: Optional[str] = None
    custom_speed_knots: Optional[float] = None
    custom_freight_rate_usd_per_mt: Optional[float] = None
    custom_bunker_price_usd_per_mt: Optional[float] = None
    custom_daily_hire_usd: Optional[float] = None
    congestion_delay_hours: Optional[float] = None
    weather_delay_hours: Optional[float] = None
    tidal_delay_hours: Optional[float] = None
    laytime_allowed_hours: float = 36.0
    demurrage_rate_usd_per_day: Optional[float] = None
    ballast_distance_nm: float = 0.0
    idle_days: float = 0.0


class BunkerCalculationRequest(BaseModel):
    distance_nm: float = 5850.0
    speed_knots: float = 11.5
    consumption_mtpd: Optional[float] = 32.0
    bunker_price_usd_per_mt: Optional[float] = None
    port_days: float = 4.5
    port_consumption_mtpd: float = 3.5
    fuel_grade: str = "VLSFO"
    hub_location: str = "SINGAPORE"


class BunkerCalculationResponse(BaseModel):
    distance_nm: Optional[float]
    speed_knots: Optional[float]
    sailing_hours: float
    sailing_days: float
    sea_consumption_mtpd: Optional[float] = None
    port_days: float = 0.0
    port_consumption_mtpd: Optional[float] = None
    fuel_consumed_mt: Optional[float]
    bunker_price_usd_per_mt: Optional[float]
    bunker_cost_usd: Optional[float]
    fuel_grade: str
    hub_location: str
    source: Optional[str] = None
    data_status: DataStatusType
    is_calculable: bool
    explanation: str


class BunkerPriceResponse(BaseModel):
    port_name: str
    fuel_grade: str
    price_usd_per_mt: float
    description: str
    source: str
    observed_at: str
    data_status: str


class SpeedAnalysisRequest(BaseModel):
    distance_nm: float = 5850.0
    cargo_quantity_mt: float = 75000.0
    baseline_speed_knots: float = 13.0
    baseline_consumption_mtpd: float = 32.0
    bunker_price_usd_per_mt: float = 628.50
    daily_charter_rate_usd: float = 16200.0
    port_cost_usd: float = 312000.0
    candidate_speeds: Optional[List[float]] = None


class SpeedBreakEvenResponse(BaseModel):
    is_evaluable: bool
    break_even_speed_knots: Optional[float] = None
    economic_speed_range_min: Optional[float] = None
    economic_speed_range_max: Optional[float] = None
    marginal_steps: List[Dict[str, Any]]
    daily_charter_rate_usd: Optional[float] = None
    bunker_price_usd_per_mt: Optional[float] = None
    data_status: DataStatusType
    verdict: str
    explanation: str


class SensitivityAnalysisRequest(BaseModel):
    distance_nm: float = 5850.0
    base_cargo_quantity_mt: float = 75000.0
    base_freight_rate_usd_per_mt: float = 14.50
    base_bunker_price_usd_per_mt: float = 628.50
    base_speed_knots: float = 11.5
    base_daily_charter_rate_usd: float = 16200.0
    base_port_cost_usd: float = 312000.0
    base_port_delay_hours: float = 0.0
    baseline_consumption_mtpd: float = 32.0
    baseline_speed_knots: float = 13.0
    laytime_allowed_hours: float = 36.0
    demurrage_rate_usd_per_day: float = 18000.0


class SensitivityAnalysisResponse(BaseModel):
    baseline: Dict[str, Any]
    bunker_sensitivity: List[Dict[str, Any]]
    freight_sensitivity: List[Dict[str, Any]]
    speed_sensitivity: List[Dict[str, Any]]
    delay_sensitivity: List[Dict[str, Any]]
    cargo_sensitivity: List[Dict[str, Any]]
    hire_rate_sensitivity: List[Dict[str, Any]]
    data_status: DataStatusType


class EconomicDataQualityReport(BaseModel):
    overall_confidence: str
    items: List[Dict[str, Any]]
    limitations_explanation: str


class VoyageEconomicsAnalysisResponse(BaseModel):
    id: str
    origin_port_id: str
    origin_port_name: str
    origin_unlocode: str
    destination_port_id: str
    destination_port_name: str
    destination_unlocode: str
    distance_nm: float
    cargo_quantity_mt: float
    cargo_type: str
    vessel_id: Optional[str] = None
    vessel_name: str
    vessel_class: str
    operating_speed_knots: float
    sailing_days: float
    total_voyage_days: float

    # Costs
    freight_cost_usd: float
    freight_rate_usd_per_mt: float
    bunker_cost_usd: float
    bunker_price_usd_per_mt: float
    port_cost_usd: float
    time_cost_usd: float
    daily_charter_rate_usd: float
    delay_cost_usd: float
    demurrage_hours: float
    repositioning_cost_usd: float
    other_cost_usd: float = 0.0
    total_voyage_cost_usd: float
    cost_per_mt_usd: float
    currency: str = "USD"
    data_status: DataStatusType

    # Sub-engines
    components: List[Dict[str, Any]]
    scenarios: List[Dict[str, Any]]
    speed_analysis: Dict[str, Any]
    break_even: Dict[str, Any]
    sensitivity: Dict[str, Any]
    data_quality_report: EconomicDataQualityReport
    explanation: str
