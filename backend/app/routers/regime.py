"""
Market Regime Router — FreightIQ 2.0
Provides endpoints for HMM regime detection, current state, and historical snapshots.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.regime_service import get_current_regime, get_regime_history

router = APIRouter(prefix="/api/regime", tags=["regime"])


class RegimeRequest(BaseModel):
    bci_series: Optional[List[float]] = Field(
        default=None,
        description="Optional list of recent BCI index values (chronological order). If omitted, latest 30 points are pulled from database."
    )
    days_window: int = Field(default=30, ge=7, le=90)


@router.post("/detect")
def detect_regime(req: RegimeRequest, db: Session = Depends(get_db)):
    """
    Detect the market regime for a custom BCI series or DB records.
    Returns regime name, confidence, transition probabilities, and chartering recommendation.
    """
    return get_current_regime(db, bci_series=req.bci_series)


@router.get("/history")
def regime_history(limit: int = 30, db: Session = Depends(get_db)):
    """
    Retrieve recent historical regime detection records from database.
    """
    return get_regime_history(db, limit=limit)


@router.get("/current")
def current_regime(db: Session = Depends(get_db)):
    """
    Get current market regime based on latest database indicators.
    """
    return get_current_regime(db)
