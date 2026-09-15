"""
Freight Forecast Service
========================
Coordinates econometric ML forecasting with fallback mechanisms.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import date
from sqlalchemy.orm import Session
from app.models import FreightRate
from app.ml.predictor import predict_freight_rate
from app.ml.model import train_model, get_model
from app.repositories.rate_repo import RateRepository

logger = logging.getLogger(__name__)


def get_recent_rates(db: Optional[Session], origin: str, destination: str, vessel_class: str, n: int = 20) -> List[Dict[str, Any]]:
    rate_repo = RateRepository(db)
    return rate_repo.get_recent_rates(origin, destination, vessel_class, limit=n)


def get_history(db: Optional[Session], origin: str, destination: str, vessel_class: str) -> List[Dict[str, Any]]:
    if db:
        try:
            rows = (
                db.query(FreightRate)
                .filter(
                    FreightRate.origin == origin,
                    FreightRate.destination == destination,
                    FreightRate.vessel_class == vessel_class,
                )
                .order_by(FreightRate.date.asc())
                .all()
            )
            if rows:
                return [
                    {
                        "date": str(r.date),
                        "rate": r.rate_usd_per_mt,
                        "tce": r.tce_usd_per_day,
                        "bunker": r.bunker_price,
                        "congestion": r.congestion_index,
                        "demand": r.demand_index,
                    }
                    for r in rows
                ]
        except Exception as e:
            logger.warning(f"Error fetching history from DB: {e}")

    # Fallback synthetic history
    from app.seed.seed_data import generate_freight_history
    history_records = generate_freight_history(origin, destination, vessel_class, "Coal", weeks=52)
    return [
        {
            "date": str(r["date"]),
            "rate": r["rate_usd_per_mt"],
            "tce": r.get("tce_usd_per_day", 15000),
            "bunker": r.get("bunker_price", 650),
            "congestion": r.get("congestion_index", 0.5),
            "demand": r.get("demand_index", 0.55),
        }
        for r in history_records
    ]


def ensure_model_trained(db: Optional[Session], force: bool = False):
    model = get_model()
    if not force and model.is_trained:
        return
    if db:
        try:
            logger.info("Training ML model from DB data...")
            rows = db.query(FreightRate).all()
            if rows:
                records = [
                    {
                        "date": r.date,
                        "origin": r.origin,
                        "destination": r.destination,
                        "vessel_class": r.vessel_class,
                        "commodity": r.commodity,
                        "rate_usd_per_mt": r.rate_usd_per_mt,
                        "bunker_price": r.bunker_price,
                        "congestion_index": r.congestion_index,
                        "vessel_availability": r.vessel_availability,
                        "demand_index": r.demand_index,
                    }
                    for r in rows
                ]
                train_model(records)
                logger.info("ML Model trained successfully from DB data.")
                return
        except Exception as e:
            logger.warning(f"DB model training encountered issue: {e}. Model will use pre-trained weights or synthetic baseline.")


def forecast(
    db: Optional[Session],
    origin: str,
    destination: str,
    vessel_class: str,
    commodity: str = "Coal",
    horizon_days: int = 30,
    laycan_start=None,
) -> Dict[str, Any]:
    """
    Produces forward freight rate projection with explainability drivers.
    """
    if db:
        ensure_model_trained(db)
    recent = get_recent_rates(db, origin, destination, vessel_class)
    return predict_freight_rate(
        origin=origin,
        destination=destination,
        vessel_class=vessel_class,
        commodity=commodity,
        horizon_days=horizon_days,
        laycan_start=laycan_start,
        recent_rates=recent,
    )
