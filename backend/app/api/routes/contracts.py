from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import ContractStrategyType, DecisionConfidence, DataStatusType
from app.repositories.contracts_repo import ContractStrategyRepository
from app.repositories.cargo_repo import CargoRepository
from app.repositories.wait_fix_repo import WaitFixRepository
from app.services.contracts.engine import ContractStrategyEngine
from app.services.contracts.hybrid_strategy import HybridContractStrategy, CoverageTierResult
from app.services.contracts.break_even import BreakEvenService, BreakEvenAnalysisResult
from app.schemas.contracts import (
    ContractAnalysisRequest,
    CoverageSimulationRequest,
    StrategyComparisonResponse,
    StrategyDetailRecordResponse,
    StrategyScenarioItemResponse
)

router = APIRouter(prefix="/contracts", tags=["Contract Strategy Engine"])

@router.post("/analyze", response_model=StrategyComparisonResponse, status_code=status.HTTP_200_OK)
def analyze_contracts(
    payload: ContractAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Simulate and evaluate contract procurement strategies:
    SPOT, SHORT_TERM_MULTIPLE_VOYAGE, and MEDIUM_TERM_MULTIPLE_VOYAGE.
    Evaluates multi-voyage parcel scheduling, market exposure, flexibility, and break-even points.
    """
    total_qty = payload.total_requirement_mt or 300000.0
    parcel_qty = payload.parcel_size_mt or 75000.0
    origin_id = payload.origin_port_id or "newcastle-au"
    dest_id = payload.destination_port_id or "paradip-in"
    cargo_type = payload.cargo_type or "COKING_COAL"
    vessel_class = payload.vessel_class or "PANAMAX"
    horizon_days = payload.planning_horizon_days or 180
    ref_rate = payload.reference_contract_rate

    # If cargo_request_id provided, supplement context
    if payload.cargo_request_id:
        req = CargoRepository.get_requirement_by_id(db, payload.cargo_request_id)
        if req:
            total_qty = req.quantity_mt
            origin_id = req.load_port_id
            dest_id = req.discharge_port_id
            cargo_type = req.cargo_type
            if req.target_freight_usd_pmt and not ref_rate:
                ref_rate = req.target_freight_usd_pmt

    # Check port compatibility (Newcastlemax / large vessels at shallow ports trigger FAIL / CONDITIONAL)
    v_upper = str(vessel_class).upper()
    if "NEWCASTLEMAX" in v_upper or ("CAPESIZE" in v_upper and "HALDIA" in str(dest_id).upper()):
        port_status = "FAIL"
    elif "CAPESIZE" in v_upper:
        port_status = "CONDITIONAL"
    else:
        port_status = "PASS"

    # Run analytical engine
    analysis = ContractStrategyEngine.analyze_strategies(
        total_requirement_mt=total_qty,
        parcel_size_mt=parcel_qty,
        origin_port_id=origin_id,
        destination_port_id=dest_id,
        cargo_type=cargo_type,
        vessel_class=vessel_class,
        planning_horizon_days=horizon_days,
        reference_contract_rate=ref_rate or 24.00,
        cargo_request_id=payload.cargo_request_id,
        port_feasibility=port_status,
        current_spot_rate=24.50,
        p10_rate=22.80,
        p50_rate=24.10,
        p90_rate=26.50,
        regime_type="BEAR",
        regime_probability=0.65,
        wait_fix_decision="MONITOR",
        volatility_annualized=0.28
    )

    # Persist in database
    ContractStrategyRepository.save_analysis(db, analysis)

    return StrategyComparisonResponse(
        cargo_request_id=analysis.cargo_request_id,
        trade_lane=analysis.trade_lane,
        total_requirement_mt=analysis.total_requirement_mt,
        parcel_size_mt=analysis.parcel_size_mt,
        planning_horizon_days=analysis.planning_horizon_days,
        voyage_plan=analysis.voyage_plan,
        strategies=analysis.strategies,
        scenario_matrix=analysis.scenario_matrix,
        break_even_analysis=analysis.break_even_analysis,
        coverage_spectrum=analysis.coverage_spectrum,
        port_feasibility_status=analysis.port_feasibility_status,
        data_provenance=analysis.data_provenance,
        decision_confidence=analysis.decision_confidence,
        created_at=analysis.created_at
    )

@router.get("/{id}", response_model=StrategyDetailRecordResponse)
def get_strategy(
    id: str,
    db: Session = Depends(get_db)
):
    """Retrieve persisted strategy evaluation record by ID."""
    strat = ContractStrategyRepository.get_by_id(db, id)
    if not strat:
        raise HTTPException(status_code=404, detail=f"Contract strategy {id} not found.")

    scenarios = ContractStrategyRepository.get_scenarios(db, id)
    scen_resp = [
        StrategyScenarioItemResponse(
            id=s.id,
            scenario_name=s.scenario_name,
            market_assumption=s.market_assumption or "",
            rate=s.rate,
            quantity=s.quantity,
            cost=s.cost,
            probability=s.probability
        )
        for s in scenarios
    ]

    return StrategyDetailRecordResponse(
        id=strat.id,
        cargo_request_id=strat.cargo_request_id,
        strategy_type=strat.strategy_type,
        contract_duration=strat.contract_duration,
        voyage_count=strat.voyage_count,
        total_quantity=strat.total_quantity,
        contracted_quantity=strat.contracted_quantity,
        spot_quantity=strat.spot_quantity,
        reference_rate=strat.reference_rate,
        expected_rate=strat.expected_rate,
        expected_cost=strat.expected_cost,
        p10_cost=strat.p10_cost,
        p50_cost=strat.p50_cost,
        p90_cost=strat.p90_cost,
        market_exposure=strat.market_exposure,
        flexibility_measure=strat.flexibility_measure,
        risk_adjusted_cost=strat.risk_adjusted_cost,
        break_even_rate=strat.break_even_rate,
        decision_confidence=strat.decision_confidence,
        data_status=strat.data_status,
        created_at=strat.created_at,
        scenarios=scen_resp
    )

@router.get("/{id}/comparison", response_model=StrategyComparisonResponse)
def get_strategy_comparison(
    id: str,
    db: Session = Depends(get_db)
):
    """Retrieve or re-generate strategy comparison containing the specified strategy."""
    strat = ContractStrategyRepository.get_by_id(db, id)
    if not strat:
        raise HTTPException(status_code=404, detail=f"Contract strategy {id} not found.")

    analysis = ContractStrategyEngine.analyze_strategies(
        total_requirement_mt=strat.total_quantity,
        parcel_size_mt=75000.0,
        planning_horizon_days=180,
        reference_contract_rate=strat.reference_rate or 24.00,
        cargo_request_id=strat.cargo_request_id
    )

    return StrategyComparisonResponse(
        cargo_request_id=analysis.cargo_request_id,
        trade_lane=analysis.trade_lane,
        total_requirement_mt=analysis.total_requirement_mt,
        parcel_size_mt=analysis.parcel_size_mt,
        planning_horizon_days=analysis.planning_horizon_days,
        voyage_plan=analysis.voyage_plan,
        strategies=analysis.strategies,
        scenario_matrix=analysis.scenario_matrix,
        break_even_analysis=analysis.break_even_analysis,
        coverage_spectrum=analysis.coverage_spectrum,
        port_feasibility_status=analysis.port_feasibility_status,
        data_provenance=analysis.data_provenance,
        decision_confidence=analysis.decision_confidence,
        created_at=analysis.created_at
    )

@router.get("/{id}/scenarios", response_model=List[StrategyScenarioItemResponse])
def get_strategy_scenarios(
    id: str,
    db: Session = Depends(get_db)
):
    """Retrieve market environment outcome scenarios for a strategy."""
    scenarios = ContractStrategyRepository.get_scenarios(db, id)
    if not scenarios:
        # Check if strategy exists
        strat = ContractStrategyRepository.get_by_id(db, id)
        if not strat:
            raise HTTPException(status_code=404, detail=f"Contract strategy {id} not found.")
    return [
        StrategyScenarioItemResponse(
            id=s.id,
            scenario_name=s.scenario_name,
            market_assumption=s.market_assumption or "",
            rate=s.rate,
            quantity=s.quantity,
            cost=s.cost,
            probability=s.probability
        )
        for s in scenarios
    ]

@router.get("/{id}/break-even", response_model=BreakEvenAnalysisResult)
def get_strategy_break_even(
    id: str,
    db: Session = Depends(get_db)
):
    """Compute and retrieve break-even spot rate analysis for a strategy."""
    strat = ContractStrategyRepository.get_by_id(db, id)
    if not strat:
        raise HTTPException(status_code=404, detail=f"Contract strategy {id} not found.")

    return BreakEvenService.calculate_break_even(
        current_spot_rate=24.50,
        contract_reference_rate=strat.reference_rate or strat.expected_rate,
        total_quantity_mt=strat.total_quantity,
        planning_horizon_days=180
    )

@router.post("/coverage", response_model=CoverageTierResult)
def simulate_coverage(
    payload: CoverageSimulationRequest
):
    """
    Simulate interactive hybrid coverage ratio (0% to 100%).
    Computes contracted vs spot volume, blended rate, expected cost, P10/P90 spread,
    market exposure, and operational flexibility index.
    """
    return HybridContractStrategy.evaluate_coverage(
        total_requirement_mt=payload.total_quantity,
        coverage_percentage=payload.coverage_percentage,
        contract_rate=payload.contract_rate,
        spot_expected_rate=payload.spot_expected_rate,
        spot_p10_rate=payload.spot_p10,
        spot_p90_rate=payload.spot_p90,
        volatility_annualized=payload.volatility,
        planning_horizon_days=payload.planning_horizon_days
    )
