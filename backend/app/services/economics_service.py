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


CII_RATE_IMPACT = {"A": 0, "B": 0, "C": 0, "D": -1000, "E": -2000}  # $/day
EU_ETS_PRICE_EUR = 65.0
EUR_TO_USD = 1.08


def calculate_carbon_adjusted(
    base_result: Dict[str, Any],
    vessel_class: str,
    route_via_suez: bool = False,
    voyage_days: Optional[float] = None,
    cargo_mt: float = 70000.0,
) -> Dict[str, Any]:
    """
    Augments standard voyage disbursements with Carbon Intensity Indicator (CII)
    tiering and EU Emissions Trading System (EU ETS) surcharges.
    """
    days = voyage_days or base_result.get("voyage_days", base_result.get("total_voyage_days", 30.0))
    fuel_mt = base_result.get("bunker_consumption_mt", base_result.get("total_bunker_mt", 1000.0))
    co2_mt = fuel_mt * 3.17  # IMO standard factor for VLSFO: 3.17 t-CO2/t-fuel

    # Annualized operational carbon intensity estimate
    cii_score = co2_mt / (cargo_mt * max(days, 1.0) + 1e-9)

    if cii_score > 0.006:
        rating = "E"
    elif cii_score > 0.005:
        rating = "D"
    elif cii_score > 0.004:
        rating = "C"
    elif cii_score > 0.003:
        rating = "B"
    else:
        rating = "A"

    charter_adj = CII_RATE_IMPACT.get(rating, 0) * days

    eu_ets_cost = 0.0
    if route_via_suez:
        # ~35% of Mediterranean/Red Sea leg subject to EU ETS scope
        eu_fraction = 0.35
        eu_ets_cost = co2_mt * eu_fraction * EU_ETS_PRICE_EUR * EUR_TO_USD

    standard_cost = base_result.get("total_voyage_cost_usd", 2000000.0)
    carbon_total = standard_cost + eu_ets_cost + charter_adj

    carbon_data = {
        "co2_emitted_mt": round(co2_mt, 1),
        "co2_per_cargo_mt_kg": round(co2_mt * 1000.0 / (cargo_mt + 1e-9), 2),
        "cii_rating": rating,
        "eu_ets_cost_usd": round(eu_ets_cost, 0),
        "cii_charter_rate_impact_usd": round(charter_adj, 0),
        "carbon_surcharge_total_usd": round(eu_ets_cost + charter_adj, 0),
        "carbon_adjusted_total_usd": round(carbon_total, 0),
        "carbon_saving_if_slow_steam_usd": round(co2_mt * 0.22 * 650.0 * 0.5, 0),
    }

    return {
        **base_result,
        "carbon_analysis": carbon_data,
    }

