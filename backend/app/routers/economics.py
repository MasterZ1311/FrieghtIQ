"""
Voyage Economics Router
=======================
Endpoint:
- POST /api/economics/calculate
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import EconomicsRequest, EconomicsResponse
from app.services import calculate_economics

router = APIRouter(prefix="/api/economics", tags=["Voyage Economics"])


@router.post("/calculate", response_model=EconomicsResponse, summary="Calculate voyage disbursements, total cost, and TCE")
def calculate(req: EconomicsRequest, db: Session = Depends(get_db)):
    """
    Computes full voyage disbursements, bunker fuel usage, and Time Charter Equivalent (TCE).
    """
    try:
        result = calculate_economics(
            db=db,
            origin=req.origin,
            destination=req.destination,
            vessel_class=req.vessel_class or "Panamax",
            commodity=req.commodity,
            cargo_mt=req.cargo_mt or 70000.0,
            freight_rate_usd_per_mt=req.freight_rate_usd_per_mt,
            bunker_price_usd_per_mt=req.bunker_price_usd_per_mt,
            port_days_origin=req.port_days_origin,
            port_days_dest=req.port_days_dest,
            laycan_start=req.laycan_start,
        )
        return EconomicsResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Economics calculation failed: {str(e)}")
