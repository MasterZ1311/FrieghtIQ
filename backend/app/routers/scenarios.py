"""
Scenario Simulation Router
==========================
Endpoints:
- POST /api/scenario/simulate (Core endpoint)
- POST /api/scenarios/simulate (Compatibility alias)
- POST /api/scenarios/idle-analysis
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    ScenarioRequest,
    ScenarioResponse,
    IdleScenarioRequest,
    IdleScenarioResponse,
)
from app.services import simulate_scenarios, calculate_idle_scenario

router = APIRouter(tags=["Scenario Simulation"])


@router.post("/api/scenario/simulate", response_model=ScenarioResponse, summary="Simulate multi-scenario what-if trade alternatives")
@router.post("/api/scenarios/simulate", response_model=ScenarioResponse, include_in_schema=False)
def simulate(req: ScenarioRequest, db: Session = Depends(get_db)):
    """
    Simulates what-if alternatives (bunker shock, route deviation, vessel switch) and computes cost deltas.
    """
    try:
        result = simulate_scenarios(
            db=db,
            base_origin=req.base_origin,
            base_destination=req.base_destination,
            base_vessel_class=req.base_vessel_class,
            base_commodity=req.base_commodity,
            base_cargo_mt=req.base_cargo_mt or 70000.0,
            scenarios=req.scenarios,
        )
        return ScenarioResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Scenario simulation failed: {str(e)}")


@router.post("/api/scenarios/idle-analysis", response_model=IdleScenarioResponse, summary="Anchorage waiting & slow-steaming economics")
def idle_analysis(req: IdleScenarioRequest, db: Session = Depends(get_db)):
    """
    Analyzes port delay exposure, demurrage risks, slow-steaming fuel savings, and diversion options.
    """
    try:
        result = calculate_idle_scenario(
            db=db,
            origin=req.origin,
            destination=req.destination,
            vessel_class=req.vessel_class,
            commodity=req.commodity,
            cargo_mt=req.cargo_mt,
            waiting_days=req.waiting_days,
            demurrage_rate_usd_day=req.demurrage_rate_usd_day,
            bunker_price_usd_per_mt=req.bunker_price_usd_per_mt,
            slow_steaming_knots=req.slow_steaming_knots,
        )
        return IdleScenarioResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Idle scenario calculation failed: {str(e)}")
