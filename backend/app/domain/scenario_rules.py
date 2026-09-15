"""
Scenario Simulation Domain Rules
================================
Pure domain logic for running multi-scenario what-if comparisons,
calculating cost/risk deltas against a baseline, and ranking outcomes.
"""
from typing import Dict, Any, List, Callable
from app.domain.models import ScenarioResult, ScenarioSimulation


def run_scenario_simulation(
    base_calc_fn: Callable[[], Dict[str, Any]],
    alt_scenarios_calc_fn: List[Callable[[], Dict[str, Any]]],
) -> ScenarioSimulation:
    """
    Executes base and alternative scenario calculations and computes delta metrics.
    """
    base_data = base_calc_fn()
    base_cost = base_data["total_cost_usd"]

    base_result = ScenarioResult(
        scenario_name=base_data.get("scenario_name", "Base Scenario"),
        vessel_class=base_data["vessel_class"],
        freight_rate_usd_per_mt=round(base_data["freight_rate_usd_per_mt"], 2),
        tce_usd_per_day=round(base_data["tce_usd_per_day"], 0),
        total_cost_usd=round(base_cost, 0),
        voyage_days=round(base_data["voyage_days"], 1),
        risk_score=round(base_data["risk_score"], 1),
        delta_vs_base_pct=0.0,
    )

    alternatives: List[ScenarioResult] = []
    for fn in alt_scenarios_calc_fn:
        alt_data = fn()
        alt_cost = alt_data["total_cost_usd"]
        delta_pct = ((alt_cost - base_cost) / max(base_cost, 1.0)) * 100.0

        alternatives.append(ScenarioResult(
            scenario_name=alt_data.get("scenario_name", "Alternative"),
            vessel_class=alt_data["vessel_class"],
            freight_rate_usd_per_mt=round(alt_data["freight_rate_usd_per_mt"], 2),
            tce_usd_per_day=round(alt_data["tce_usd_per_day"], 0),
            total_cost_usd=round(alt_cost, 0),
            voyage_days=round(alt_data["voyage_days"], 1),
            risk_score=round(alt_data["risk_score"], 1),
            delta_vs_base_pct=round(delta_pct, 2),
        ))

    all_options = [base_result] + alternatives
    best_scenario = min(all_options, key=lambda x: x.total_cost_usd).scenario_name
    worst_scenario = max(all_options, key=lambda x: x.total_cost_usd).scenario_name

    return ScenarioSimulation(
        base_scenario=base_result,
        alternatives=alternatives,
        best_scenario=best_scenario,
        worst_scenario=worst_scenario,
    )
