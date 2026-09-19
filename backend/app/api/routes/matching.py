from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.matching.service import VesselMatchingService
from app.repositories.matching_repo import MatchingRepository
from app.schemas.matching import MatchingRunRequest, MatchingRunResponse

router = APIRouter(prefix="/matching", tags=["Cargo-Vessel Matching"])

@router.post("/evaluate", response_model=MatchingRunResponse)
def evaluate_matching(request: MatchingRunRequest, db: Session = Depends(get_db)):
    service = VesselMatchingService(db)
    try:
        run = service.execute_matching_run(
            requirement_id=request.requirement_id,
            candidate_vessel_ids=request.candidate_vessel_ids
        )
        return run
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/requirements/{requirement_id}/latest", response_model=MatchingRunResponse)
def get_latest_matching_run(requirement_id: str, db: Session = Depends(get_db)):
    repo = MatchingRepository(db)
    run = repo.get_latest_for_requirement(requirement_id)
    if not run:
        # Run matching on-the-fly if not previously executed
        service = VesselMatchingService(db)
        try:
            run = service.execute_matching_run(requirement_id=requirement_id)
            return run
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return run
