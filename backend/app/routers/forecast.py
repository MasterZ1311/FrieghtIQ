"""
Freight Forecast Router
=======================
Endpoints:
- POST /api/forecast (Core endpoint)
- POST /api/forecast/predict (Compatibility alias)
- GET  /api/forecast/history
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ForecastRequest, ForecastResponse
from app.services import forecast, get_history

router = APIRouter(prefix="/api/forecast", tags=["Freight Forecast"])


@router.post("", response_model=ForecastResponse, summary="Predict freight rates and key drivers")
@router.post("/", response_model=ForecastResponse, include_in_schema=False)
@router.post("/predict", response_model=ForecastResponse, include_in_schema=False)
def predict_freight(req: ForecastRequest, db: Session = Depends(get_db)):
    """
    Produces deterministic forward rate projections with econometric drivers.
    """
    try:
        result = forecast(
            db=db,
            origin=req.origin,
            destination=req.destination,
            vessel_class=req.vessel_class,
            commodity=req.commodity,
            horizon_days=req.horizon_days or 30,
            laycan_start=req.laycan_start,
        )
        return ForecastResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Freight forecast failed: {str(e)}")


@router.get("/history", summary="Historical weekly freight rates")
def freight_history(
    origin: str = Query(..., min_length=1),
    destination: str = Query(..., min_length=1),
    vessel_class: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """Returns weekly historical freight rates for a route."""
    history = get_history(db, origin, destination, vessel_class)
    return {
        "data": history,
        "disclaimer": "[DEMO] Synthetic historical data for demonstration only.",
    }


@router.get("/registry", summary="Model Registry metadata and benchmark comparison")
def get_forecasting_registry():
    """Returns active model metadata, parameters, and chronological benchmark metrics."""
    from app.ml.registry import get_model_registry
    return get_model_registry().get_summary()

