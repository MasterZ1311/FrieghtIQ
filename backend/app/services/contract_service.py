"""
Contract Comparison Service
===========================
Orchestrates contract evaluation across Spot, Short-Term COA, and Medium-Term Time Charter
by coordinating rate forecasts and pure domain contract rules.
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.domain.contract_rules import evaluate_contracts
from app.repositories.rate_repo import RateRepository
from app.services.forecast_service import forecast


def compare_contracts(
    db: Optional[Session],
    origin: str,
    destination: str,
    vessel_class: str,
    commodity: str,
    cargo_mt: float,
    annual_volume_mt: float = 500000.0,
    planning_horizon_months: int = 12,
) -> Dict[str, Any]:
    """
    Coordinates forward rate projections and domain contract optimization rules.
    """
    rate_repo = RateRepository(db)

    # 1. Fetch current (30-day) and future (180-day) forecasts
    try:
        fc_current = forecast(db, origin, destination, vessel_class, commodity, horizon_days=30)
        spot_rate = fc_current.get("predicted_rate", fc_current.get("predicted_rate_usd_per_mt", 12.0))
        trend = fc_current.get("trend", "stable")
    except Exception:
        spot_rate = rate_repo.get_baseline_rate(origin, vessel_class)
        trend = "stable"

    try:
        fc_future = forecast(db, origin, destination, vessel_class, commodity, horizon_days=180)
        future_rate = fc_future.get("predicted_rate", fc_future.get("predicted_rate_usd_per_mt", spot_rate * 1.05))
    except Exception:
        future_rate = spot_rate * 1.05

    result = evaluate_contracts(
        spot_rate_usd_per_mt=spot_rate,
        future_rate_usd_per_mt=future_rate,
        cargo_quantity_mt=cargo_mt,
        annual_volume_mt=annual_volume_mt,
        planning_horizon_months=planning_horizon_months,
        trend=trend,
    )
    return result
