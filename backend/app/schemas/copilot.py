from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import (
    CopilotRole,
    CopilotPlanStatus,
    CopilotToolStatus,
    DataStatusType,
)


class ToolDefinitionSchema(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    permission: str = "READ" # "READ", "ANALYZE", "WRITE"
    timeout_sec: int = 10
    data_requirements: List[str] = Field(default_factory=list)
    source: str = "FREIGHT_IQ_SERVICE"


class ToolResultSchema(BaseModel):
    tool_name: str
    status: CopilotToolStatus
    data: Optional[Dict[str, Any]] = None
    source: str = "FREIGHT_IQ"
    data_status: DataStatusType = DataStatusType.SYNTHETIC
    dataset_version_id: Optional[str] = None
    model_version: Optional[str] = None
    observed_at: Optional[str] = None
    last_updated: Optional[str] = None
    currency: str = "USD"
    unit: Optional[str] = None
    assumption: Optional[str] = None
    execution_time_ms: float = 0.0
    error: Optional[str] = None


class CopilotPlanStepSchema(BaseModel):
    step_number: int
    tool_name: str
    reason: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    status: CopilotToolStatus = CopilotToolStatus.PENDING


class CopilotPlanSchema(BaseModel):
    id: str
    session_id: str
    user_goal: str
    steps: List[CopilotPlanStepSchema] = Field(default_factory=list)
    status: CopilotPlanStatus = CopilotPlanStatus.PLANNED
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CopilotPlanRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    cargo_request_id: Optional[str] = None
    vessel_id: Optional[str] = None
    voyage_id: Optional[str] = None


class CopilotToolCallSchema(BaseModel):
    id: str
    session_id: str
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    status: CopilotToolStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[float] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class StructuredCopilotResponse(BaseModel):
    """
    Standardized traceable JSON response structure synthesized by Copilot
    from verified tool results.
    """
    summary: str
    findings: List[str] = Field(default_factory=list)
    decision_context: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    risks: List[Dict[str, Any]] = Field(default_factory=list)
    economics: Dict[str, Any] = Field(default_factory=dict)
    assumptions: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    data_quality: Dict[str, Any] = Field(default_factory=dict)
    actions: List[Dict[str, Any]] = Field(default_factory=list)


class CopilotMessageSchema(BaseModel):
    id: str
    session_id: str
    role: CopilotRole
    content: str
    structured_response: Optional[StructuredCopilotResponse] = None
    plan_id: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CopilotSessionSchema(BaseModel):
    id: str
    title: str
    cargo_request_id: Optional[str] = None
    vessel_id: Optional[str] = None
    voyage_id: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    message_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class CopilotSessionDetailSchema(BaseModel):
    session: CopilotSessionSchema
    messages: List[CopilotMessageSchema] = Field(default_factory=list)
    latest_plan: Optional[CopilotPlanSchema] = None
    tool_calls: List[CopilotToolCallSchema] = Field(default_factory=list)


class CopilotChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    stream: bool = False
    cargo_request_id: Optional[str] = None
    vessel_id: Optional[str] = None
    voyage_id: Optional[str] = None
    scenario_preset: Optional[str] = None
