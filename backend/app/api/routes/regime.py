from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.regime_repo import RegimeRepository
from app.services.regime.service import MarketRegimeService
from app.schemas.regime import (
    CurrentRegimeResponse,
    RegimeHistoryPoint,
    RegimeAnalysisRequest,
    RegimeTransitionResponse,
    RegimeModelInfo,
)
from app.models.enums import CargoType, VesselClass, MarketRegimeType

router = APIRouter(prefix="/regime", tags=["Market Regime Detection Engine"])

def _parse_vessel_class(val: Optional[str]) -> VesselClass:
    if not val:
        return VesselClass.PANAMAX
    val_clean = str(val).upper().replace("-", "_").replace(" ", "_")
    try:
        return VesselClass(val_clean)
    except ValueError:
        # Check substring
        for vc in VesselClass:
            if vc.value in val_clean or val_clean in vc.value:
                return vc
        return VesselClass.PANAMAX

def _parse_cargo_type(val: Optional[str]) -> CargoType:
    if not val:
        return CargoType.COKING_COAL
    val_clean = str(val).upper().replace("-", "_").replace(" ", "_")
    try:
        return CargoType(val_clean)
    except ValueError:
        # Check substring (e.g. coal -> COKING_COAL)
        for ct in CargoType:
            if val_clean in ct.value:
                return ct
        return CargoType.COKING_COAL

@router.get("/current", response_model=CurrentRegimeResponse)
def get_current_regime(
    origin: Optional[str] = Query("newcastle-au", description="Origin port ID or UNLOCODE"),
    destination: Optional[str] = Query("paradip-in", description="Destination port ID or UNLOCODE"),
    cargo: Optional[str] = Query("COKING_COAL", description="Cargo type"),
    vessel_class: Optional[str] = Query("PANAMAX", description="Vessel class"),
    db: Session = Depends(get_db)
):
    """
    Classifies the current freight-market regime state for a given trade lane and vessel class.
    Returns current regime, probabilities, evidence, model metadata, dataset provenance,
    and forecast-regime alignment.
    """
    service = MarketRegimeService(db)
    vc = _parse_vessel_class(vessel_class)
    ct = _parse_cargo_type(cargo)
    try:
        return service.analyze_regime(
            origin_port_id=origin or "newcastle-au",
            destination_port_id=destination or "paradip-in",
            cargo_type=ct,
            vessel_class=vc
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Regime analysis error: {str(e)}")

@router.get("/history", response_model=List[RegimeHistoryPoint])
def get_regime_history(
    origin: Optional[str] = Query("newcastle-au", description="Origin port ID"),
    destination: Optional[str] = Query("paradip-in", description="Destination port ID"),
    vessel_class: Optional[str] = Query("PANAMAX", description="Vessel class"),
    days: int = Query(90, ge=7, le=730, description="Lookback days"),
    db: Session = Depends(get_db)
):
    """
    Returns chronological historical sequence of regime classifications and probability distributions.
    """
    service = MarketRegimeService(db)
    vc = _parse_vessel_class(vessel_class)
    try:
        return service.get_regime_history(
            origin_port_id=origin or "newcastle-au",
            destination_port_id=destination or "paradip-in",
            vessel_class=vc,
            limit=days
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch regime history: {str(e)}")

@router.post("/analyze", response_model=CurrentRegimeResponse)
def analyze_regime(
    request: RegimeAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Executes on-demand regime analysis.
    """
    service = MarketRegimeService(db)
    vc = _parse_vessel_class(request.vessel_class)
    ct = _parse_cargo_type(request.cargo_type)
    try:
        return service.analyze_regime(
            origin_port_id=request.origin_port_id,
            destination_port_id=request.destination_port_id,
            cargo_type=ct,
            vessel_class=vc
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Regime analysis execution error: {str(e)}")

@router.get("/transitions", response_model=List[RegimeTransitionResponse])
def get_regime_transitions(
    trade_lane: Optional[str] = Query(None, description="Trade lane filter (e.g. AU-NEW-IN-PAR)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum transitions to return"),
    db: Session = Depends(get_db)
):
    """
    Retrieves chronological record of detected regime transitions with trigger features and confidence.
    """
    repo = RegimeRepository(db)
    transitions = repo.get_transitions(trade_lane=trade_lane, limit=limit)
    
    # Map to schema response ensuring current_regime alias is set
    response_items = []
    for t in transitions:
        response_items.append(RegimeTransitionResponse(
            id=t.id,
            market_regime_id=t.market_regime_id,
            previous_regime=t.previous_regime,
            new_regime=t.new_regime,
            current_regime=t.new_regime,
            transition_date=t.transition_date,
            confidence=t.confidence,
            trigger_features=t.trigger_features,
            model_version_id=t.model_version_id,
            created_at=t.created_at
        ))
    return response_items

@router.get("/models", response_model=List[RegimeModelInfo])
def get_regime_models(db: Session = Depends(get_db)):
    """
    Returns registered market regime detection model specifications, architecture parameters,
    and validation methodology.
    """
    return [
        RegimeModelInfo(
            model_name="Gaussian Hidden Markov Model (HMM)",
            model_type="Continuous-State Gaussian Emission HMM",
            version="hmm-v1.0-4s",
            number_of_states=4,
            training_period="2022-01-01 to 2026-01-01 (4-year rolling calibration)",
            dataset_version="SYNTHETIC_BALTIC_V2026",
            validation_method="Chronological Out-of-Sample Walk-Forward & Transition Stability",
            status="PRODUCTION_CALIBRATED",
            features=[
                "rate_return_7d (Trailing 7-Day Log Return)",
                "rate_return_30d (Trailing 30-Day Cumulative Return)",
                "rolling_volatility_14d (14-Day Standard Deviation)",
                "seasonal_sin (Annual Fourier Harmonic Sinusoid)",
                "seasonal_cos (Annual Fourier Harmonic Cosine)",
                "bunker_change_7d (VLSFO Bunker Fuel Price Shift)",
                "congestion_change_7d (Port Queuing Vessel Count Shift)",
                "forecast_slope (Phase 5 TFT Forward Projection Slope)"
            ]
        ),
        RegimeModelInfo(
            model_name="Ensemble Regime Classifier (Experimental)",
            model_type="Markov-Switching Autoregressive (MS-AR)",
            version="ms-ar-v0.9b",
            number_of_states=4,
            training_period="2023-01-01 to 2026-01-01",
            dataset_version="SYNTHETIC_BALTIC_V2026",
            validation_method="Chronological Holdout (Last 6 Months)",
            status="RESEARCH_CANDIDATE",
            features=[
                "rate_return_7d",
                "rolling_volatility_30d",
                "market_index_change"
            ]
        )
    ]
