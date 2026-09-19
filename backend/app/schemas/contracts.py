from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from app.models.enums import ContractStrategyType, DecisionConfidence, DataStatusType
from app.services.contracts.voyage_planning import VoyagePlanningResult
from app.services.contracts.engine import StrategyDetail, ScenarioMatrixCell
from app.services.contracts.hybrid_strategy import CoverageTierResult
from app.services.contracts.break_even import BreakEvenAnalysisResult

class ContractAnalysisRequest(BaseModel):
    cargo_request_id: Optional[str] = None
    origin_port_id: Optional[str] = "newcastle-au"
    destination_port_id: Optional[str] = "paradip-in"
    cargo_type: Optional[str] = "COKING_COAL"
    total_requirement_mt: Optional[float] = 300000.0
    parcel_size_mt: Optional[float] = 75000.0
    vessel_class: Optional[str] = "PANAMAX"
    planning_horizon_days: Optional[int] = 180
    reference_contract_rate: Optional[float] = 24.00

class CoverageSimulationRequest(BaseModel):
    total_quantity: float = 300000.0
    coverage_percentage: float = 50.0 # 0 to 100
    contract_rate: float = 23.28
    spot_expected_rate: float = 24.30
    spot_p10: float = 22.80
    spot_p90: float = 26.50
    volatility: float = 0.28
    planning_horizon_days: int = 180

class StrategyComparisonResponse(BaseModel):
    cargo_request_id: Optional[str]
    trade_lane: str
    total_requirement_mt: float
    parcel_size_mt: float
    planning_horizon_days: int
    voyage_plan: VoyagePlanningResult
    strategies: Dict[str, StrategyDetail]
    scenario_matrix: List[ScenarioMatrixCell]
    break_even_analysis: BreakEvenAnalysisResult
    coverage_spectrum: List[CoverageTierResult]
    port_feasibility_status: str
    data_provenance: Dict[str, Any]
    decision_confidence: DecisionConfidence
    created_at: str

class StrategyScenarioItemResponse(BaseModel):
    id: str
    scenario_name: str
    market_assumption: str
    rate: float
    quantity: float
    cost: float
    probability: float

class StrategyDetailRecordResponse(BaseModel):
    id: str
    cargo_request_id: Optional[str]
    strategy_type: ContractStrategyType
    contract_duration: str
    voyage_count: int
    total_quantity: float
    contracted_quantity: float
    spot_quantity: float
    reference_rate: Optional[float]
    expected_rate: float
    expected_cost: float
    p10_cost: float
    p50_cost: float
    p90_cost: float
    market_exposure: float
    flexibility_measure: float
    risk_adjusted_cost: float
    break_even_rate: Optional[float]
    decision_confidence: DecisionConfidence
    data_status: DataStatusType
    created_at: datetime
    scenarios: List[StrategyScenarioItemResponse] = []
