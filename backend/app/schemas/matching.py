from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.models.enums import MatchStatus
from app.schemas.vessels import VesselResponse

class MatchingRuleResultResponse(BaseModel):
    rule_name: str
    rule_category: str
    status: MatchStatus
    evaluated_value: Optional[str] = None
    required_value: Optional[str] = None
    explanation: str
    is_blocking: bool = False

    model_config = ConfigDict(from_attributes=True)

class MatchingCandidateResponse(BaseModel):
    id: str
    vessel_id: str
    vessel: Optional[VesselResponse] = None
    overall_status: MatchStatus
    summary_explanation: str
    is_data_complete: bool
    missing_fields: Optional[str] = None
    rule_results: List[MatchingRuleResultResponse] = []

    model_config = ConfigDict(from_attributes=True)

class MatchingRunResponse(BaseModel):
    id: str
    requirement_id: str
    run_timestamp: datetime
    total_evaluated: int
    relevant_count: int
    partial_count: int
    not_relevant_count: int
    unknown_count: int
    candidates: List[MatchingCandidateResponse] = []

    model_config = ConfigDict(from_attributes=True)

class MatchingRunRequest(BaseModel):
    requirement_id: str
    candidate_vessel_ids: Optional[List[str]] = None
