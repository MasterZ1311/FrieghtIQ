"""
Voyage Economics Service
========================
Orchestrates maritime voyage economics calculations using domain rules and repositories.
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.domain.models import Cargo
from app.domain.economics_rules import calculate_voyage_economics
from app.repositories.port_repo import PortRepository
from app.repositories.vessel_repo import VesselRepository
from app.repositories.route_repo import RouteRepository
from app.repositories.rate_repo import RateRepository
from app.services.forecast_service import forecast


def calculate_economics(
    db: Optional[Session],
    origin: str,
    destination: str,
    vessel_class: str,
    commodity: str,
    cargo_mt: float,
    freight_rate_usd_per_mt: Optional[float] = None,
    bunker_price_usd_per_mt: float = 650.0,
    port_days_origin: float = 2.0,
    port_days_dest: Optional[float] = None,
    laycan_start=None,
) -> Dict[str, Any]:
    """
    Coordinates voyage economics calculations across domain rules and repository inputs.
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
    vessel = vessel_repo.get_by_class(vessel_class)
    distance_nm = route_repo.get_distance_nm(origin, destination)

    # Freight rate lookup if not manually specified
    if freight_rate_usd_per_mt is None:
        try:
            fc = forecast(
                db=db,
                origin=origin,
                destination=destination,
                vessel_class=vessel_class,
                commodity=commodity,
                laycan_start=laycan_start,
            )
            freight_rate_usd_per_mt = fc["predicted_rate"]
        except Exception:
            freight_rate_usd_per_mt = rate_repo.get_baseline_rate(origin, vessel_class)

    result = calculate_voyage_economics(
        cargo=cargo,
        vessel=vessel,
        dest_port=dest_port,
        distance_nm=distance_nm,
        freight_rate_usd_per_mt=freight_rate_usd_per_mt,
        bunker_price_usd_per_mt=bunker_price_usd_per_mt,
        port_days_origin=port_days_origin,
        port_days_dest=port_days_dest,
    )
    return result
