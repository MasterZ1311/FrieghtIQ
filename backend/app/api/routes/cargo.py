from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.repositories.cargo_repo import CargoRepository
from app.schemas.cargo import (
    CargoRequirementCreate,
    CargoRequirementResponse,
    CargoRequirementDetailResponse
)

router = APIRouter(prefix="/cargo", tags=["Cargo Requirements"])

@router.get("/requirements", response_model=List[CargoRequirementResponse])
def get_cargo_requirements(db: Session = Depends(get_db)):
    repo = CargoRepository(db)
    return repo.get_all_requirements()

@router.post("/requirements", response_model=CargoRequirementResponse, status_code=status.HTTP_201_CREATED)
def create_cargo_requirement(req_in: CargoRequirementCreate, db: Session = Depends(get_db)):
    repo = CargoRepository(db)
    return repo.create_requirement(req_in)

@router.get("/requirements/{requirement_id}", response_model=CargoRequirementDetailResponse)
def get_cargo_requirement_detail(requirement_id: str, db: Session = Depends(get_db)):
    repo = CargoRepository(db)
    req = repo.get_requirement_by_id(requirement_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cargo requirement {requirement_id} not found")
    return req
