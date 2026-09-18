"""
Port Compatibility Router
=========================
Endpoints:
- POST /api/port/check
- POST /api/ports/check
- GET  /api/ports/list
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import PortCheckRequest, PortCheckResponse
from app.services import check_compatibility, list_ports

router = APIRouter(tags=["Port Compatibility"])


@router.post("/api/port/check", response_model=PortCheckResponse, summary="Check physical and operational port compatibility")
@router.post("/api/ports/check", response_model=PortCheckResponse, include_in_schema=False)
def check_port(req: PortCheckRequest, db: Session = Depends(get_db)):
    """
    Evaluates physical draft, LOA, beam, DWT, and tidal limits at port.
    """
    try:
        result = check_compatibility(
            db=db,
            port_name=req.port,
            vessel_class=req.vessel_class or "Panamax",
            cargo_mt=req.cargo_mt or 70000.0,
            commodity=req.commodity,
        )
        return PortCheckResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Port compatibility check failed: {str(e)}")


@router.get("/api/ports/list", summary="List port database entries")
@router.get("/api/port/list", include_in_schema=False)
def get_ports(region: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """List all ports, optionally filtered by region (origin/destination)."""
    return {"ports": list_ports(db, region=region)}


@router.get("/api/ports/congestion", summary="Get AIS-derived port congestion and anchorage data")
def port_congestion(
    port: str = Query("paradip", description="Port name (e.g. paradip, haldia, visakhapatnam)"),
    db: Session = Depends(get_db),
):
    """
    Returns AIS anchorage count, congestion score (0-100), estimated delays,
    demurrage risk, and Virtual Arrival speed-reduction bunker savings.
    """
    from app.services.ais_service import get_port_congestion, get_all_ports_congestion
    if port.lower() in ("all", "*"):
        return {"ports": get_all_ports_congestion(db)}
    return get_port_congestion(port, db)


@router.get("/api/ports/tidal-windows", summary="Get tidal gate entry windows for tide-gated ports")
def tidal_windows(
    port: str = Query("haldia", description="Tide-gated port name (haldia, gopalpur, sagar)"),
    days: int = Query(7, ge=1, le=30, description="Forecast horizon in days"),
    db: Session = Depends(get_db),
):
    """
    Returns harmonic high water windows, maximum safe draft per window,
    and compatible vessel classes for draft-constrained Indian ports.
    """
    from app.services.tidal_service import get_tidal_windows as _get_tidal
    return _get_tidal(port=port, days=days, db=db)

