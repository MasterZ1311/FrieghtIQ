from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.repositories.port_repo import PortRepository
from app.schemas.ports import PortResponse, PortDetailResponse, BerthResponse

router = APIRouter(prefix="/ports", tags=["Ports & Constraints"])

@router.get("", response_model=List[PortResponse])
def get_all_ports(db: Session = Depends(get_db)):
    repo = PortRepository(db)
    return repo.get_all_ports()

@router.get("/{port_id}", response_model=PortDetailResponse)
def get_port_detail(port_id: str, db: Session = Depends(get_db)):
    repo = PortRepository(db)
    port = repo.get_port_by_id(port_id)
    if not port:
        # Check by UNLOCODE fallback
        port = repo.get_port_by_unlocode(port_id.upper())
    if not port:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Port {port_id} not found")
    return port

@router.get("/{port_id}/berths", response_model=List[BerthResponse])
def get_port_berths(port_id: str, db: Session = Depends(get_db)):
    repo = PortRepository(db)
    return repo.get_berths_for_port(port_id)
