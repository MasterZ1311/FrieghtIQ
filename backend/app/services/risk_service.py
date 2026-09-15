"""
Risk Engine Service
===================
Orchestrates multi-factor deterministic risk evaluations using domain rules and repositories.
"""
from typing import Optional, Dict, Any
from datetime import date
from sqlalchemy.orm import Session
from app.domain.models import Cargo
from app.domain.risk_rules import score_risk_dimensions
from app.repositories.port_repo import PortRepository
from app.repositories.vessel_repo import VesselRepository
from app.repositories.rate_repo import RateRepository
from app.services.forecast_service import forecast


def score_risk(
    db: Optional[Session],
    origin: str,
    destination: str,
    vessel_class: str,
    commodity: str,
    cargo_mt: float,
    contract_type: str = "Spot",
    laycan_start: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Coordinates multi-factor risk scoring across operational and commercial dimensions.
    """
    cargo = Cargo(
        commodity=commodity,
        quantity_mt=cargo_mt,
        origin=origin,
        destination=destination,
    )

    port_repo = PortRepository(db)
    vessel_repo = VesselRepository(db)
    rate_repo = RateRepository(db)

    dest_port = port_repo.get_by_name(destination)
    vessel = vessel_repo.get_by_class(vessel_class)

    try:
        fc = forecast(db, origin, destination, vessel_class, commodity)
        rate = fc["predicted_rate"]
        lower = fc["lower_bound"]
        upper = fc["upper_bound"]
    except Exception:
        rate = rate_repo.get_baseline_rate(origin, vessel_class)
        lower = rate * 0.90
        upper = rate * 1.12

    risk_analysis = score_risk_dimensions(
        cargo=cargo,
        vessel=vessel,
        dest_port=dest_port,
        contract_type=contract_type,
        rate_lower_bound=lower,
        rate_upper_bound=upper,
        current_predicted_rate=rate,
        laycan_date=laycan_start,
        bunker_price_usd=650.0,
    )

    risk_factors_dict = [
        {
            "category": rf.category,
            "name": rf.name,
            "level": rf.level,
            "score": rf.score,
            "description": rf.description,
            "mitigation": rf.mitigation,
        }
        for rf in risk_analysis.risk_factors
    ]

    score_val = risk_analysis.overall_risk_score
    level_val = risk_analysis.overall_risk_level

    return {
        "overall_risk_score": score_val,
        "overall_risk_level": level_val,
        "score": score_val,
        "decision": f"Risk classified as {level_val} ({score_val:.1f}/100) for {contract_type} charter on {origin}->{destination}",
        "risk_factors": risk_factors_dict,
        "component_scores": risk_analysis.component_scores,
        "top_risks": risk_analysis.top_risks,
        "recommended_actions": risk_analysis.recommended_actions,
        "disclaimer": risk_analysis.disclaimer,
    }
