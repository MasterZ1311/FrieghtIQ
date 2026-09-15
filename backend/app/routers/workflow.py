"""
End-to-End Decision Workflow Router
===================================
Exposes the single unified decision pipeline connecting:
Cargo Input
-> Forecast
-> Vessel Feasibility
-> Vessel Ranking
-> Economics
-> Contract Comparison
-> Risk
-> Final Recommendation
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import EndToEndRequest, EndToEndResponse
from app.services.workflow_service import run_end_to_end_flow

router = APIRouter(tags=["End-to-End Workflow"])


@router.post(
    "/api/workflow/end-to-end",
    response_model=EndToEndResponse,
    summary="Execute Complete FreightIQ Decision Pipeline",
    description=(
        "Unified endpoint running Cargo Input -> Forecast -> Vessel Feasibility -> "
        "Vessel Ranking -> Economics -> Contract Comparison -> Risk -> Final Recommendation."
    ),
)
def end_to_end_workflow(
    payload: EndToEndRequest,
    db: Session = Depends(get_db),
):
    result = run_end_to_end_flow(
        db=db,
        origin=payload.origin,
        destination=payload.destination,
        commodity=payload.commodity,
        cargo_mt=payload.cargo_mt,
        vessel_class=payload.vessel_class,
        urgency_days=payload.urgency_days,
        annual_volume_mt=payload.annual_volume_mt,
        planning_horizon_months=payload.planning_horizon_months,
        bunker_price_usd_per_mt=payload.bunker_price_usd_per_mt,
    )
    return result


@router.post(
    "/api/recommendation/end-to-end",
    response_model=EndToEndResponse,
    summary="Execute Complete Recommendation Pipeline (Alias)",
    description="Alias endpoint for /api/workflow/end-to-end",
)
def recommendation_end_to_end(
    payload: EndToEndRequest,
    db: Session = Depends(get_db),
):
    return end_to_end_workflow(payload, db)
