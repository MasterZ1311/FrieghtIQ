from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.models.enums import VesselClass, VesselStatus

class VesselParticularsResponse(BaseModel):
    summer_dwt: Optional[float] = None
    summer_draft_m: Optional[float] = None
    loa_m: Optional[float] = None
    beam_m: Optional[float] = None
    depth_m: Optional[float] = None
    gross_tonnage: Optional[float] = None
    net_tonnage: Optional[float] = None
    grain_capacity_cbm: Optional[float] = None
    bale_capacity_cbm: Optional[float] = None
    holds_hatches_count: Optional[str] = None
    gear_summary: Optional[str] = None
    speed_ballast_knots: Optional[float] = None
    speed_laden_knots: Optional[float] = None
    consumption_laden_mtpd: Optional[float] = None
    is_verified: bool = True
    unverified_fields: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class VesselAvailabilityResponse(BaseModel):
    current_status: VesselStatus
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    current_port_name: Optional[str] = None
    destination_port_name: Optional[str] = None
    open_port_name: Optional[str] = None
    open_date_start: Optional[datetime] = None
    open_date_end: Optional[datetime] = None
    eta_open_port: Optional[datetime] = None
    data_confidence: str = "MEDIUM"
    source_evidence: str = "AIS / Broker Report"

    model_config = ConfigDict(from_attributes=True)

class OperationalSnapshotResponse(BaseModel):
    snapshot_vessel_name: str
    observed_handled_cargo_mt: float
    cargo_type: str
    discharge_port_code: str
    discharge_berth_code: Optional[str] = None
    observation_date: datetime
    data_integrity_note: str

    model_config = ConfigDict(from_attributes=True)

class VesselResponse(BaseModel):
    id: str
    imo_number: str
    vessel_name: str
    vessel_class: VesselClass
    flag: Optional[str] = None
    year_built: Optional[int] = None
    call_sign: Optional[str] = None
    classification_society: Optional[str] = None
    is_snapshot_vessel: bool = False
    particulars: Optional[VesselParticularsResponse] = None
    availability: Optional[VesselAvailabilityResponse] = None

    model_config = ConfigDict(from_attributes=True)

class VesselDetailResponse(VesselResponse):
    snapshot_records: List[OperationalSnapshotResponse] = []
