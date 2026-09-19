from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.optimizer.service import VesselPortOptimizerService
from app.repositories.optimizer_repo import OptimizerRepository
from app.schemas.optimizer import FeasibilityEvaluateRequest, FeasibilityRunResponse

router = APIRouter(prefix="/optimizer", tags=["Vessel-Port Feasibility Optimizer"])

@router.post("/evaluate", response_model=FeasibilityRunResponse)
def evaluate_vessel_port_feasibility(request: FeasibilityEvaluateRequest, db: Session = Depends(get_db)):
    service = VesselPortOptimizerService(db)
    try:
        run = service.evaluate_feasibility(
            vessel_id=request.vessel_id,
            port_id=request.port_id,
            cargo_quantity_mt=request.cargo_quantity_mt
        )
        return run
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/vessels/{vessel_id}/ports/{port_id}/latest", response_model=FeasibilityRunResponse)
def get_latest_feasibility_run(vessel_id: str, port_id: str, db: Session = Depends(get_db)):
    repo = OptimizerRepository(db)
    run = repo.get_latest_run(vessel_id=vessel_id, port_id=port_id)
    if not run:
        service = VesselPortOptimizerService(db)
        try:
            run = service.evaluate_feasibility(vessel_id=vessel_id, port_id=port_id)
            return run
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return run
