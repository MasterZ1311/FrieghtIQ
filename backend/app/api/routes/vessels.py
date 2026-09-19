from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.repositories.vessel_repo import VesselRepository
from app.schemas.vessels import VesselResponse, VesselDetailResponse
from app.models.enums import VesselClass, VesselStatus

router = APIRouter(prefix="/vessels", tags=["Vessel Intelligence"])

@router.get("", response_model=List[VesselResponse])
def get_vessels(
    vessel_class: Optional[VesselClass] = Query(None, description="Filter by vessel class"),
    status_filter: Optional[VesselStatus] = Query(None, alias="status", description="Filter by status"),
    is_snapshot: Optional[bool] = Query(None, description="Filter snapshot vessels only"),
    db: Session = Depends(get_db)
):
    repo = VesselRepository(db)
    return repo.get_all_vessels(
        vessel_class=vessel_class,
        status=status_filter,
        is_snapshot_only=is_snapshot
    )

@router.get("/{vessel_id}", response_model=VesselDetailResponse)
def get_vessel_detail(vessel_id: str, db: Session = Depends(get_db)):
    repo = VesselRepository(db)
    vessel = repo.get_vessel_by_id(vessel_id)
    if not vessel:
        # Check by IMO
        vessel = repo.get_vessel_by_imo(vessel_id)
    if not vessel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vessel {vessel_id} not found")
    return vessel
