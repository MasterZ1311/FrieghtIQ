from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.enums import MarketRegimeType, DataStatusType, ForecastRegimeAlignment, CargoType, VesselClass

class RegimeProbabilities(BaseModel):
    BULL: float
    BEAR: float
    NEUTRAL: float
    SEASONAL: float

    model_config = ConfigDict(from_attributes=True)

class RegimeEvidenceItem(BaseModel):
    signal_name: str
    current_value: float
    baseline_value: Optional[float] = None
    signal_direction: str # "POSITIVE", "NEGATIVE", "FLAT", "CYCLIC"
    relative_weight: float
    interpretation: str

class RegimeModelInfo(BaseModel):
    model_name: str
    model_type: str
    version: str
    number_of_states: int
    training_period: str
    dataset_version: str
    validation_method: str
    status: str
    features: Optional[List[str]] = None

class RegimeDatasetInfo(BaseModel):
    source: str
    dataset_name: str
    dataset_version: str
    observation_count: int
    last_updated: datetime
    data_status: DataStatusType
    disclaimer: str

class RegimeTransitionResponse(BaseModel):
    id: str
    market_regime_id: str
    previous_regime: MarketRegimeType
    new_regime: MarketRegimeType
    current_regime: Optional[MarketRegimeType] = None
    transition_date: datetime
    confidence: float
    trigger_features: Optional[str] = None
    model_version_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CurrentRegimeResponse(BaseModel):
    route_code: str
    trade_lane: str
    origin_port_id: Optional[str] = None
    destination_port_id: Optional[str] = None
    cargo_type: CargoType
    vessel_class: VesselClass
    regime: MarketRegimeType
    probabilities: RegimeProbabilities
    confidence: float
    current_duration_days: int
    historical_avg_duration_days: Optional[float] = None
    historical_median_duration_days: Optional[float] = None
    transition_frequency_per_year: Optional[float] = None
    forecast_alignment: ForecastRegimeAlignment
    forecast_alignment_rationale: str
    evidence: List[RegimeEvidenceItem]
    model: RegimeModelInfo
    dataset: RegimeDatasetInfo
    data_status: DataStatusType
    detected_at: datetime
    route: Optional[Dict[str, Any]] = None

class RegimeHistoryPoint(BaseModel):
    date: datetime
    regime: MarketRegimeType
    probabilities: RegimeProbabilities
    freight_rate: float

class RegimeAnalysisRequest(BaseModel):
    origin_port_id: str
    destination_port_id: str
    cargo_type: Optional[CargoType] = CargoType.COKING_COAL
    vessel_class: Optional[VesselClass] = VesselClass.PANAMAX
