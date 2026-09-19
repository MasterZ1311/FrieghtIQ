from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.repositories.freight_repo import FreightRepository
from app.services.forecasting.service import FreightForecastService
from app.schemas.freight import (
    FreightRouteResponse,
    FreightObservationResponse,
    FreightForecastResponse,
    BacktestResultResponse,
    ForecastGenerateRequest,
)
from app.models.enums import ForecastModelType

router = APIRouter(prefix="/freight", tags=["Freight Forecasting Engine"])

@router.get("/routes", response_model=List[FreightRouteResponse])
def get_all_routes(db: Session = Depends(get_db)):
    repo = FreightRepository(db)
    return repo.get_all_routes()

@router.get("/routes/{route_id}/observations", response_model=List[FreightObservationResponse])
def get_route_observations(
    route_id: str,
    days: int = Query(365, description="Historical lookback days"),
    db: Session = Depends(get_db)
):
    repo = FreightRepository(db)
    return repo.get_observations(route_id=route_id, limit=days)

@router.get("/routes/{route_id}/forecasts", response_model=List[FreightForecastResponse])
def get_route_forecasts(
    route_id: str,
    model_type: Optional[ForecastModelType] = Query(None, description="Forecast model type"),
    db: Session = Depends(get_db)
):
    repo = FreightRepository(db)
    forecasts = repo.get_latest_forecasts(route_id=route_id, model_type=model_type)
    if not forecasts:
        # Generate on the fly
        service = FreightForecastService(db)
        try:
            forecasts = service.generate_route_forecasts(
                route_id=route_id,
                model_type=model_type or ForecastModelType.TFT
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return forecasts

@router.get("/routes/{route_id}/backtest", response_model=List[BacktestResultResponse])
def get_backtest_results(route_id: str, db: Session = Depends(get_db)):
    repo = FreightRepository(db)
    results = repo.get_backtest_results(route_id=route_id)
    return results

@router.post("/forecasts/generate", response_model=List[FreightForecastResponse])
def generate_forecasts(request: ForecastGenerateRequest, db: Session = Depends(get_db)):
    service = FreightForecastService(db)
    try:
        return service.generate_route_forecasts(
            route_id=request.route_id,
            vessel_class=request.vessel_class,
            model_type=request.model_type or ForecastModelType.TFT,
            horizons=request.horizons
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
