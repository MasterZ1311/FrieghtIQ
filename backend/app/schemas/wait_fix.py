from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.enums import (
    WaitFixDecision, DecisionConfidence, WaitFixScenarioType,
    CargoType, VesselClass, DataStatusType, ForecastRegimeAlignment
)

class ScenarioItem(BaseModel):
    scenario_name: str # "LOW", "CENTRAL", "HIGH"
    rate: float
    probability: float
    freight_cost: float
    difference_vs_fix: float

    model_config = ConfigDict(from_attributes=True)

class OptionValueResult(BaseModel):
    option_value_usd: Optional[float] = None
    option_value_pmt: Optional[float] = None
    methodology: str
    parameters: Dict[str, Any]
    status: str # "AVAILABLE", "OPTION_VALUE_UNAVAILABLE"
    rationale: str

class WaitFixAssumptions(BaseModel):
    current_freight_rate: float
    reference_fix_rate: float
    cargo_quantity_mt: float
    decision_horizon_days: int
    remaining_days: int
    historical_volatility_annualized: float
    discount_rate_annual: float
    forecast_model: str
    regime_model: str
    dataset_version: str
    data_status: DataStatusType

class WaitFixEvidenceItem(BaseModel):
    factor_name: str
    observed_value: str
    impact_on_decision: str # "FAVORS_WAIT", "FAVORS_FIX", "NEUTRAL"
    weight: float
    description: str

class DataQualityReport(BaseModel):
    forecast_data: str # "AVAILABLE", "PARTIAL", "STALE", "UNAVAILABLE", "SYNTHETIC"
    regime_data: str
    port_feasibility: str
    vessel_feasibility: str
    reference_fix_rate: str
    overall_quality: str # "HIGH", "MEDIUM", "LOW"

class WaitFixAnalysisResponse(BaseModel):
    id: str
    cargo_request_id: Optional[str] = None
    origin_port_id: str
    destination_port_id: str
    trade_lane: str
    cargo_type: CargoType
    cargo_quantity: float
    vessel_class: VesselClass
    decision: WaitFixDecision
    decision_confidence: DecisionConfidence
    current_freight_rate: float
    expected_wait_rate: float
    expected_fix_cost: float
    expected_wait_cost: float
    expected_modeled_difference: float
    decision_deadline: Optional[datetime] = None
    remaining_days: int
    p10_rate: float
    p50_rate: float
    p90_rate: float
    scenarios: List[ScenarioItem]
    option_analysis: OptionValueResult
    assumptions: WaitFixAssumptions
    why_this_result: List[str]
    what_could_change_this: List[str]
    evidence: List[WaitFixEvidenceItem]
    forecast_regime_alignment: ForecastRegimeAlignment
    data_quality: DataQualityReport
    data_status: DataStatusType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WaitFixAnalysisRequest(BaseModel):
    cargo_request_id: Optional[str] = None
    origin_port_id: Optional[str] = "newcastle-au"
    destination_port_id: Optional[str] = "paradip-in"
    cargo_type: Optional[CargoType] = CargoType.COKING_COAL
    cargo_quantity: Optional[float] = 75000.0
    vessel_class: Optional[VesselClass] = VesselClass.PANAMAX
    decision_horizon_days: Optional[int] = 30
    reference_fix_rate: Optional[float] = None

class OptionValueRequest(BaseModel):
    current_freight_rate: float
    reference_fix_rate: float
    cargo_quantity: float
    remaining_days: int
    volatility_annualized: Optional[float] = None
    discount_rate: Optional[float] = 0.05
