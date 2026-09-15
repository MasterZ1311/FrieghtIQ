"""
Risk Engine Router
==================
Endpoints:
- POST /api/risk/analyze (Core endpoint)
- POST /api/risk/score (Compatibility alias)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import RiskRequest, RiskResponse
from app.services import score_risk

router = APIRouter(tags=["Risk Engine"])


@router.post("/api/risk/analyze", response_model=RiskResponse, summary="Analyze deterministic multi-factor shipping risk")
@router.post("/api/risk/score", response_model=RiskResponse, include_in_schema=False)
@router.post("/api/risks/analyze", response_model=RiskResponse, include_in_schema=False)
def risk_analyze(req: RiskRequest, db: Session = Depends(get_db)):
    """
    Evaluates 8-factor shipping risk: freight, congestion, availability, geopolitical, seasonal, port, contract, and bunker.
    """
    try:
        result = score_risk(
            db=db,
            origin=req.origin,
            destination=req.destination,
            vessel_class=req.vessel_class or "Panamax",
            commodity=req.commodity,
            cargo_mt=req.cargo_mt or 70000.0,
            contract_type=req.contract_type or "Spot",
            laycan_start=req.laycan_start,
        )
        return RiskResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Risk analysis failed: {str(e)}")
