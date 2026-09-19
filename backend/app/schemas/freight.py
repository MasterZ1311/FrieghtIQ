from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.enums import VesselClass, ForecastModelType
from app.schemas.ports import PortResponse

class FreightRouteResponse(BaseModel):
    id: str
    route_code: str
    origin_port_id: str
    destination_port_id: str
    default_vessel_class: VesselClass
    distance_nm: float
    typical_duration_days: float
    origin_port: Optional[PortResponse] = None
    destination_port: Optional[PortResponse] = None

    model_config = ConfigDict(from_attributes=True)

class FreightObservationResponse(BaseModel):
    id: str
    route_id: str
    observation_date: datetime
    freight_rate_usd_pmt: float
    bunker_vlsfo_usd: Optional[float] = None
    bunker_mgo_usd: Optional[float] = None
    baltic_index_value: Optional[float] = None
    congestion_origin_days: Optional[float] = None
    congestion_dest_days: Optional[float] = None
    is_interpolated: bool = False
    source_type: str = "SYNTHETIC_DERIVED"

    model_config = ConfigDict(from_attributes=True)

class FreightForecastResponse(BaseModel):
    id: str
    route_id: str
    vessel_class: VesselClass
    model_type: ForecastModelType
    horizon_days: int
    target_date: datetime
    predicted_p10: float
    predicted_p50: float
    predicted_p90: float
    confidence_pct: float
    volatility_index: Optional[float] = None
    feature_attributions: Optional[str] = None
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class BacktestResultResponse(BaseModel):
    id: str
    route_id: str
    model_type: ForecastModelType
    horizon_days: int
    test_start_date: datetime
    test_end_date: datetime
    sample_count: int
    mae: float
    rmse: float
    mape: float
    directional_accuracy_pct: float
    pinball_loss_p10: float
    pinball_loss_p50: float
    pinball_loss_p90: float
    evaluated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ForecastGenerateRequest(BaseModel):
    route_id: str
    vessel_class: Optional[VesselClass] = None
    model_type: Optional[ForecastModelType] = ForecastModelType.TFT
    horizons: Optional[List[int]] = [7, 14, 30, 90]
