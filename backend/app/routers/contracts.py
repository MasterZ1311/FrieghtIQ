"""
Contract Comparison Router
==========================
Endpoints:
- POST /api/contracts/compare
- POST /api/contract/compare
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ContractCompareRequest, ContractCompareResponse
from app.services import compare_contracts

router = APIRouter(tags=["Contract Comparison"])


@router.post("/api/contracts/compare", response_model=ContractCompareResponse, summary="Compare Spot vs COA vs Time Charter")
@router.post("/api/contract/compare", response_model=ContractCompareResponse, include_in_schema=False)
def compare(req: ContractCompareRequest, db: Session = Depends(get_db)):
    """
    Compares charter contract structures across volume horizons and rate forecasts.
    """
    try:
        result = compare_contracts(
            db=db,
            origin=req.origin,
            destination=req.destination,
            vessel_class=req.vessel_class or "Panamax",
            commodity=req.commodity,
            cargo_mt=req.cargo_mt or 70000.0,
            annual_volume_mt=req.annual_volume_mt,
            planning_horizon_months=req.planning_horizon_months,
        )
        return ContractCompareResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Contract comparison failed: {str(e)}")
