from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.models.enums import ConstraintSeverity, DataSourceType

class BerthConstraintResponse(BaseModel):
    id: str
    constraint_type: str
    parameter_name: str
    limit_value: float
    unit: str
    severity: ConstraintSeverity
    condition_description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class BerthResponse(BaseModel):
    id: str
    port_id: str
    berth_code: str
    berth_name: str
    berth_type: str
    max_loa_m: Optional[float] = None
    max_beam_m: Optional[float] = None
    max_draft_m: Optional[float] = None
    max_air_draft_m: Optional[float] = None
    max_dwt: Optional[float] = None
    discharge_rate_tpd: Optional[float] = None
    loading_rate_tpd: Optional[float] = None
    equipment_summary: Optional[str] = None
    night_berthing: bool = True
    constraints: List[BerthConstraintResponse] = []

    model_config = ConfigDict(from_attributes=True)

class PortConstraintResponse(BaseModel):
    id: str
    port_id: str
    constraint_type: str
    parameter_name: str
    limit_value: float
    unit: str
    severity: ConstraintSeverity
    condition_description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PortDataSourceResponse(BaseModel):
    id: str
    source_name: str
    source_type: DataSourceType
    doc_reference: Optional[str] = None
    publication_date: Optional[datetime] = None
    verified: bool = True
    verified_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PortResponse(BaseModel):
    id: str
    unlocode: str
    name: str
    country: str
    coast: Optional[str] = None
    latitude: float
    longitude: float
    channel_max_draft_m: Optional[float] = None
    channel_max_loa_m: Optional[float] = None
    channel_max_beam_m: Optional[float] = None
    tide_range_m: Optional[float] = None
    night_navigation: bool = True
    tug_requirement_count: int = 2
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PortDetailResponse(PortResponse):
    berths: List[BerthResponse] = []
    constraints: List[PortConstraintResponse] = []
    data_sources: List[PortDataSourceResponse] = []
