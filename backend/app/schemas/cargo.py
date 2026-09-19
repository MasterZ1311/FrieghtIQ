from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.models.enums import CargoType, RequirementStatus
from app.schemas.ports import PortResponse

class CargoHandlingLogResponse(BaseModel):
    id: str
    requirement_id: str
    vessel_id: Optional[str] = None
    port_id: str
    berth_id: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    quantity_handled_mt: float
    average_rate_tpd: Optional[float] = None
    remarks: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class CargoRequirementCreate(BaseModel):
    title: str
    cargo_type: CargoType
    quantity_mt: float
    tolerance_pct: float = 10.0
    load_port_id: str
    discharge_port_id: str
    laycan_start: datetime
    laycan_end: datetime
    target_freight_usd_pmt: Optional[float] = None
    max_vessel_age_years: int = 15
    preferred_vessel_classes: str = "PANAMAX,KAMSARMAX"
    gear_requirement: str = "ANY"
    notes: Optional[str] = None

class CargoRequirementResponse(BaseModel):
    id: str
    requirement_code: str
    title: str
    cargo_type: CargoType
    quantity_mt: float
    tolerance_pct: float
    load_port_id: str
    discharge_port_id: str
    load_port: Optional[PortResponse] = None
    discharge_port: Optional[PortResponse] = None
    laycan_start: datetime
    laycan_end: datetime
    target_freight_usd_pmt: Optional[float] = None
    max_vessel_age_years: int
    preferred_vessel_classes: str
    gear_requirement: str
    status: RequirementStatus
    created_by: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CargoRequirementDetailResponse(CargoRequirementResponse):
    handling_logs: List[CargoHandlingLogResponse] = []
