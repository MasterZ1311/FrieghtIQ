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
