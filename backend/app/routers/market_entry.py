"""Market Entry Signal Router"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import MarketEntryRequest, MarketEntryResponse
from app.services import generate_signal

router = APIRouter(prefix="/api/market-entry", tags=["Market Entry"])


@router.post("/signal", response_model=MarketEntryResponse)
def market_entry(req: MarketEntryRequest, db: Session = Depends(get_db)):
    vc = req.vessel_class.value if hasattr(req.vessel_class, "value") else str(req.vessel_class)
    comm = req.commodity.value if hasattr(req.commodity, "value") else str(req.commodity)
    result = generate_signal(
        db=db,
        origin=req.origin,
        destination=req.destination,
        vessel_class=vc,
        commodity=comm,
        cargo_mt=req.cargo_mt,
        urgency_days=req.urgency_days,
    )
    return MarketEntryResponse(**result)
