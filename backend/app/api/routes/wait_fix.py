from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.wait_fix_repo import WaitFixRepository
from app.services.wait_fix.engine import WaitFixDecisionEngine
from app.services.wait_fix.option_model import WaitOptionModel
from app.schemas.wait_fix import (
    WaitFixAnalysisResponse,
    WaitFixAnalysisRequest,
    ScenarioItem,
    OptionValueResult,
    OptionValueRequest
)
from app.models.enums import CargoType, VesselClass

router = APIRouter(prefix="/wait-fix", tags=["Wait vs Fix Decision Engine"])

def _parse_vessel_class(val: Optional[str]) -> VesselClass:
    if not val:
        return VesselClass.PANAMAX
    val_clean = str(val).upper().replace("-", "_").replace(" ", "_")
    try:
        return VesselClass(val_clean)
    except ValueError:
        for vc in VesselClass:
            if vc.value in val_clean or val_clean in vc.value:
                return vc
        return VesselClass.PANAMAX

def _parse_cargo_type(val: Optional[str]) -> CargoType:
    if not val:
        return CargoType.COKING_COAL
    val_clean = str(val).upper().replace("-", "_").replace(" ", "_")
    try:
        return CargoType(val_clean)
    except ValueError:
        for ct in CargoType:
            if val_clean in ct.value:
                return ct
        return CargoType.COKING_COAL

@router.post("/analyze", response_model=WaitFixAnalysisResponse)
def analyze_wait_vs_fix(
    request: WaitFixAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluates commercial timing economics:
    Models expected freight difference between fixing prompt tonnage vs waiting,
    factoring in P10/P50/P90 quantile projections, Gaussian HMM regime context,
    waiting risk penalties, and real-option flexibility value.
    """
    engine = WaitFixDecisionEngine(db)
    vc = _parse_vessel_class(request.vessel_class)
    ct = _parse_cargo_type(request.cargo_type)
    try:
        return engine.analyze(
            cargo_request_id=request.cargo_request_id,
            origin_port_id=request.origin_port_id or "newcastle-au",
            destination_port_id=request.destination_port_id or "paradip-in",
            cargo_type=ct,
            cargo_quantity=request.cargo_quantity or 75000.0,
            vessel_class=vc,
            decision_horizon_days=request.decision_horizon_days or 30,
            reference_fix_rate=request.reference_fix_rate
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Wait vs Fix analysis failed: {str(e)}")

@router.get("/latest", response_model=WaitFixAnalysisResponse)
def get_latest_analysis(
    cargo_request_id: Optional[str] = Query(None, description="Cargo requirement ID"),
    origin: Optional[str] = Query("newcastle-au", description="Origin port ID"),
    destination: Optional[str] = Query("paradip-in", description="Destination port ID"),
    vessel_class: Optional[str] = Query("PANAMAX", description="Vessel class"),
    db: Session = Depends(get_db)
):
    """
    Retrieves the most recent charter timing analysis for a route or runs an analysis on-demand.
    """
    engine = WaitFixDecisionEngine(db)
    vc = _parse_vessel_class(vessel_class)
    try:
        return engine.analyze(
            cargo_request_id=cargo_request_id,
            origin_port_id=origin or "newcastle-au",
            destination_port_id=destination or "paradip-in",
            vessel_class=vc
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch latest wait-fix analysis: {str(e)}")

@router.get("/history", response_model=List[WaitFixAnalysisResponse])
def get_analysis_history(
    cargo_request_id: Optional[str] = Query(None, description="Filter by cargo requirement ID"),
    limit: int = Query(20, ge=1, le=100, description="Max historical records to return"),
    db: Session = Depends(get_db)
):
    """
    Returns chronological history of prior charter-timing evaluations.
    """
    repo = WaitFixRepository(db)
    records = repo.get_analysis_history(cargo_request_id=cargo_request_id, limit=limit)
    
    # If empty, execute one analysis to seed history
    if not records:
        engine = WaitFixDecisionEngine(db)
        fresh = engine.analyze()
        return [fresh]

    # Map records
    results = []
    for r in records:
        scenarios = [
            ScenarioItem(
                scenario_name=s.scenario_name,
                rate=s.rate,
                probability=s.probability,
                freight_cost=s.freight_cost,
                difference_vs_fix=s.difference_vs_fix
            )
            for s in r.scenarios
        ]
        results.append(WaitFixAnalysisResponse(
            id=r.id,
            cargo_request_id=r.cargo_request_id,
            origin_port_id=r.origin_port_id,
            destination_port_id=r.destination_port_id,
            trade_lane=f"{r.origin_port.name if r.origin_port else r.origin_port_id} → {r.destination_port.name if r.destination_port else r.destination_port_id}",
            cargo_type=r.cargo_type,
            cargo_quantity=r.cargo_quantity,
            vessel_class=r.vessel_class,
            decision=r.decision,
            decision_confidence=r.decision_confidence,
            current_freight_rate=r.current_freight_rate,
            expected_wait_rate=r.expected_wait_rate,
            expected_fix_cost=r.expected_fix_cost,
            expected_wait_cost=r.expected_wait_cost,
            expected_modeled_difference=r.expected_modeled_difference,
            decision_deadline=r.decision_deadline,
            remaining_days=r.remaining_days,
            p10_rate=r.p10_rate,
            p50_rate=r.p50_rate,
            p90_rate=r.p90_rate,
            scenarios=scenarios,
            option_analysis=OptionValueResult(
                option_value_usd=r.wait_option_value,
                option_value_pmt=round(r.wait_option_value / r.cargo_quantity, 2) if r.wait_option_value else None,
                methodology="Real-Option Decision-Support (Black-Scholes Framework)",
                parameters={},
                status="AVAILABLE" if r.wait_option_value else "OPTION_VALUE_UNAVAILABLE",
                rationale="Historical evaluation snapshot."
            ),
            assumptions={
                "current_freight_rate": r.current_freight_rate,
                "reference_fix_rate": r.current_freight_rate,
                "cargo_quantity_mt": r.cargo_quantity,
                "decision_horizon_days": r.remaining_days,
                "remaining_days": r.remaining_days,
                "historical_volatility_annualized": 0.28,
                "discount_rate_annual": 0.05,
                "forecast_model": "Phase 5 TFT",
                "regime_model": "Phase 6 HMM",
                "dataset_version": r.dataset_version_id,
                "data_status": r.data_status
            },
            why_this_result=["Historical snapshot record."],
            what_could_change_this=["Market rate movements."],
            evidence=[],
            forecast_regime_alignment="NEUTRAL",
            data_quality={
                "forecast_data": "AVAILABLE",
                "regime_data": "AVAILABLE",
                "port_feasibility": "AVAILABLE",
                "vessel_feasibility": "AVAILABLE",
                "reference_fix_rate": "AVAILABLE",
                "overall_quality": "HIGH"
            },
            data_status=r.data_status,
            created_at=r.created_at
        ))
    return results

@router.get("/{id}/scenarios", response_model=List[ScenarioItem])
def get_analysis_scenarios(
    id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves the quantile scenario economic breakdown (LOW / CENTRAL / HIGH) for an analysis.
    """
    repo = WaitFixRepository(db)
    scenarios = repo.get_scenarios_by_analysis_id(id)
    if not scenarios:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No scenarios found for analysis {id}")
    return [
        ScenarioItem(
            scenario_name=s.scenario_name,
            rate=s.rate,
            probability=s.probability,
            freight_cost=s.freight_cost,
            difference_vs_fix=s.difference_vs_fix
        )
        for s in scenarios
    ]

@router.get("/{id}", response_model=WaitFixAnalysisResponse)
def get_analysis_by_id(
    id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves a specific charter timing analysis by ID.
    """
    repo = WaitFixRepository(db)
    record = repo.get_analysis_by_id(id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"WaitFix analysis {id} not found")
    
    scenarios = [
        ScenarioItem(
            scenario_name=s.scenario_name,
            rate=s.rate,
            probability=s.probability,
            freight_cost=s.freight_cost,
            difference_vs_fix=s.difference_vs_fix
        )
        for s in record.scenarios
    ]

    return WaitFixAnalysisResponse(
        id=record.id,
        cargo_request_id=record.cargo_request_id,
        origin_port_id=record.origin_port_id,
        destination_port_id=record.destination_port_id,
        trade_lane=f"{record.origin_port.name if record.origin_port else record.origin_port_id} → {record.destination_port.name if record.destination_port else record.destination_port_id}",
        cargo_type=record.cargo_type,
        cargo_quantity=record.cargo_quantity,
        vessel_class=record.vessel_class,
        decision=record.decision,
        decision_confidence=record.decision_confidence,
        current_freight_rate=record.current_freight_rate,
        expected_wait_rate=record.expected_wait_rate,
        expected_fix_cost=record.expected_fix_cost,
        expected_wait_cost=record.expected_wait_cost,
        expected_modeled_difference=record.expected_modeled_difference,
        decision_deadline=record.decision_deadline,
        remaining_days=record.remaining_days,
        p10_rate=record.p10_rate,
        p50_rate=record.p50_rate,
        p90_rate=record.p90_rate,
        scenarios=scenarios,
        option_analysis=OptionValueResult(
            option_value_usd=record.wait_option_value,
            option_value_pmt=round(record.wait_option_value / record.cargo_quantity, 2) if record.wait_option_value else None,
            methodology="Real-Option Decision-Support (Black-Scholes Framework)",
            parameters={},
            status="AVAILABLE" if record.wait_option_value else "OPTION_VALUE_UNAVAILABLE",
            rationale="Persisted analysis option result."
        ),
        assumptions={
            "current_freight_rate": record.current_freight_rate,
            "reference_fix_rate": record.current_freight_rate,
            "cargo_quantity_mt": record.cargo_quantity,
            "decision_horizon_days": record.remaining_days,
            "remaining_days": record.remaining_days,
            "historical_volatility_annualized": 0.28,
            "discount_rate_annual": 0.05,
            "forecast_model": "Phase 5 TFT",
            "regime_model": "Phase 6 HMM",
            "dataset_version": record.dataset_version_id,
            "data_status": record.data_status
        },
        why_this_result=["Persisted snapshot evaluation."],
        what_could_change_this=["Market rate changes."],
        evidence=[],
        forecast_regime_alignment="NEUTRAL",
        data_quality={
            "forecast_data": "AVAILABLE",
            "regime_data": "AVAILABLE",
            "port_feasibility": "AVAILABLE",
            "vessel_feasibility": "AVAILABLE",
            "reference_fix_rate": "AVAILABLE",
            "overall_quality": "HIGH"
        },
        data_status=record.data_status,
        created_at=record.created_at
    )

@router.post("/option-value", response_model=OptionValueResult)
def calculate_custom_option_value(request: OptionValueRequest):
    """
    On-demand real-option flexibility calculator (Black-76 / Black-Scholes).
    Computes economic value of postponing charter party commitment given
    spot rate, reference fix rate, decision window, volatility, and discount rate.
    """
    return WaitOptionModel.calculate_wait_option_value(
        current_freight_rate=request.current_freight_rate,
        reference_fix_rate=request.reference_fix_rate,
        cargo_quantity_mt=request.cargo_quantity,
        remaining_days=request.remaining_days,
        annualized_volatility=request.volatility_annualized or 0.28,
        discount_rate=request.discount_rate or 0.05
    )
