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


@router.post("/carbon-adjusted", summary="Calculate voyage disbursements with CII rating and EU ETS carbon pricing")
def calculate_carbon(req: EconomicsRequest, db: Session = Depends(get_db)):
    """
    Computes full voyage economics plus CII rating tier (A-E), EU ETS allowance cost,
    total carbon-adjusted voyage expenditure, and Virtual Arrival slow-steaming carbon savings.
    """
    from app.services.economics_service import calculate_carbon_adjusted
    try:
        base_result = calculate_economics(
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
        return calculate_carbon_adjusted(
            base_result=base_result,
            vessel_class=req.vessel_class or "Panamax",
            route_via_suez=bool(req.route_via_suez),
            voyage_days=base_result.get("voyage_days", base_result.get("total_voyage_days", 30.0)),
            cargo_mt=req.cargo_mt or 70000.0,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Carbon-adjusted economics calculation failed: {str(e)}")

