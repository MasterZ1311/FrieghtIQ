from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.models.enums import FeasibilityStatus
from app.schemas.ports import BerthResponse, PortResponse
from app.schemas.vessels import VesselResponse

class FeasibilityRuleResponse(BaseModel):
    rule_name: str
    status: FeasibilityStatus
    limit_value: Optional[float] = None
    vessel_value: Optional[float] = None
    unit: str = "m"
    margin: Optional[float] = None
    is_blocking: bool = True
    narrative: str

    model_config = ConfigDict(from_attributes=True)

class BerthFeasibilityResponse(BaseModel):
    id: str
    berth_id: str
    berth: Optional[BerthResponse] = None
    status: FeasibilityStatus
    draft_clearance_m: Optional[float] = None
    loa_clearance_m: Optional[float] = None
    beam_clearance_m: Optional[float] = None
    estimated_turnaround_days: Optional[float] = None
    summary_explanation: str
    rule_evaluations: List[FeasibilityRuleResponse] = []

    model_config = ConfigDict(from_attributes=True)

class FeasibilityRunResponse(BaseModel):
    id: str
    vessel_id: str
    port_id: str
    vessel: Optional[VesselResponse] = None
    port: Optional[PortResponse] = None
    run_timestamp: datetime
    overall_status: FeasibilityStatus
    evaluated_berths_count: int
    passing_berths_count: int
    summary_narrative: Optional[str] = None
    berth_results: List[BerthFeasibilityResponse] = []

    model_config = ConfigDict(from_attributes=True)

class FeasibilityEvaluateRequest(BaseModel):
    vessel_id: str
    port_id: str
    cargo_quantity_mt: Optional[float] = None
