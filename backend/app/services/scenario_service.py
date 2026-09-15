"""
Scenario Simulation Service
===========================
Orchestrates multi-scenario what-if simulations using domain rules and service economics.
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.domain.scenario_rules import run_scenario_simulation
from app.services.economics_service import calculate_economics
from app.services.risk_service import score_risk


def simulate_scenarios(
    db: Optional[Session],
    base_origin: str,
    base_destination: str,
    base_vessel_class: str,
    base_commodity: str,
    base_cargo_mt: float,
    scenarios: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Executes base scenario and alternative scenario calculations and builds simulation summary.
    """
    def make_calc_fn(orig, dest, vc, comm, qty, name, bunker=None, rate=None):
        def _calc():
            econ = calculate_economics(
                db=db,
                origin=orig,
                destination=dest,
                vessel_class=vc,
                commodity=comm,
                cargo_mt=qty,
                freight_rate_usd_per_mt=rate,
                bunker_price_usd_per_mt=bunker or 650.0,
            )
            rsk = score_risk(
                db=db,
                origin=orig,
                destination=dest,
                vessel_class=vc,
                commodity=comm,
                cargo_mt=qty,
            )
            return {
                "scenario_name": name,
                "vessel_class": vc,
                "freight_rate_usd_per_mt": econ["freight_rate_usd_per_mt"],
                "tce_usd_per_day": econ["tce_usd_per_day"],
                "total_cost_usd": econ["total_cost_usd"],
                "voyage_days": econ["total_voyage_days"],
                "risk_score": rsk["overall_risk_score"],
            }
        return _calc

    base_calc_fn = make_calc_fn(
        orig=base_origin,
        dest=base_destination,
        vc=base_vessel_class,
        comm=base_commodity,
        qty=base_cargo_mt,
        name="Base Scenario",
    )

    alt_calc_fns = []
    for sc in scenarios:
        orig = sc.get("origin", base_origin)
        dest = sc.get("destination", base_destination)
        vc = sc.get("vessel_class", base_vessel_class)
        comm = sc.get("commodity", base_commodity)
        qty = sc.get("cargo_mt") or sc.get("quantity_mt") or base_cargo_mt
        name = sc.get("name", f"{vc} via {orig}")
        bunker = sc.get("bunker_price") or sc.get("bunker_price_usd_per_mt")
        rate = sc.get("freight_rate_override") or sc.get("freight_rate_usd_per_mt")

        alt_calc_fns.append(make_calc_fn(orig, dest, vc, comm, qty, name, bunker, rate))

    simulation = run_scenario_simulation(
        base_calc_fn=base_calc_fn,
        alt_scenarios_calc_fn=alt_calc_fns,
    )

    base_dict = {
        "scenario_name": simulation.base_scenario.scenario_name,
        "vessel_class": simulation.base_scenario.vessel_class,
        "freight_rate_usd_per_mt": simulation.base_scenario.freight_rate_usd_per_mt,
        "tce_usd_per_day": simulation.base_scenario.tce_usd_per_day,
        "total_cost_usd": simulation.base_scenario.total_cost_usd,
        "voyage_days": simulation.base_scenario.voyage_days,
        "risk_score": simulation.base_scenario.risk_score,
        "delta_vs_base_pct": simulation.base_scenario.delta_vs_base_pct,
    }

    alt_dicts = [
        {
            "scenario_name": alt.scenario_name,
            "vessel_class": alt.vessel_class,
            "freight_rate_usd_per_mt": alt.freight_rate_usd_per_mt,
            "tce_usd_per_day": alt.tce_usd_per_day,
            "total_cost_usd": alt.total_cost_usd,
            "voyage_days": alt.voyage_days,
            "risk_score": alt.risk_score,
            "delta_vs_base_pct": alt.delta_vs_base_pct,
        }
        for alt in simulation.alternatives
    ]

    return {
        "base_scenario": base_dict,
        "alternatives": alt_dicts,
        "best_scenario": simulation.best_scenario,
        "worst_scenario": simulation.worst_scenario,
        "disclaimer": simulation.disclaimer,
    }
