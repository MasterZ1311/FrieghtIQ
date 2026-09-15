"""
Vessel Recommendation Service
==============================
Orchestrates vessel evaluation across candidate classes using domain rules,
port constraints, route distances, and freight rate forecasts.
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.domain.models import Cargo
from app.domain.vessel_rules import evaluate_vessel_candidate, rank_vessel_options
from app.repositories.port_repo import PortRepository
from app.repositories.vessel_repo import VesselRepository
from app.repositories.route_repo import RouteRepository
from app.repositories.rate_repo import RateRepository
from app.services.forecast_service import forecast


def recommend_vessels(
    db: Optional[Session],
    origin: str,
    destination: str,
    commodity: str,
    cargo_mt: float,
    budget_usd_per_mt: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Coordinates vessel feasibility checking and returns ranked recommendations.
    """
    cargo = Cargo(
        commodity=commodity,
        quantity_mt=cargo_mt,
        origin=origin,
        destination=destination,
    )

    port_repo = PortRepository(db)
    vessel_repo = VesselRepository(db)
    route_repo = RouteRepository(db)
    rate_repo = RateRepository(db)

    dest_port = port_repo.get_by_name(destination)
    distance_nm = route_repo.get_distance_nm(origin, destination)
    all_vessels = vessel_repo.list_classes()

    candidate_results: List[Dict[str, Any]] = []
    for vessel in all_vessels:
        # Forecast or baseline freight rate
        try:
            fc = forecast(
                db=db,
                origin=origin,
                destination=destination,
                vessel_class=vessel.vessel_type,
                commodity=commodity,
                horizon_days=30,
            )
            est_rate = fc["predicted_rate"]
        except Exception:
            est_rate = rate_repo.get_baseline_rate(origin, vessel.vessel_type)

        eval_res = evaluate_vessel_candidate(
            vessel=vessel,
            cargo=cargo,
            dest_port=dest_port,
            estimated_freight_usd_per_mt=est_rate,
            distance_nm=distance_nm,
            budget_usd_per_mt=budget_usd_per_mt,
        )
        candidate_results.append(eval_res)

    recommendation = rank_vessel_options(
        candidates=candidate_results,
        cargo=cargo,
        dest_port=dest_port,
    )

    return {
        "decision": recommendation.decision,
        "score": recommendation.score,
        "confidence": recommendation.confidence,
        "reasons": recommendation.reasons,
        "warnings": recommendation.warnings,
        "recommended_class": recommendation.recommended_class,
        "alternatives": recommendation.alternatives,
        "ranked_summary": getattr(recommendation, "ranked_summary", []),
        "reasoning": recommendation.reasoning,
        "disclaimer": recommendation.disclaimer,
    }
