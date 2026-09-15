"""
Automated Tests: Scenario Simulation Rules
==========================================
Tests what-if simulations, delta percentage calculations, and best/worst identification.
"""
import pytest
from app.services.scenario_service import simulate_scenarios


def test_scenario_simulation_deltas_and_ranking():
    """Simulating vessel and route alternatives computes accurate deltas and identifies best/worst."""
    scenarios = [
        {
            "name": "Supramax Alternative",
            "origin": "Australia",
            "destination": "Paradip",
            "vessel_class": "Supramax",
            "commodity": "Coal",
            "cargo_mt": 55000.0,
        },
        {
            "name": "Bunker Price Shock ($900/MT)",
            "origin": "Australia",
            "destination": "Paradip",
            "vessel_class": "Panamax",
            "commodity": "Coal",
            "cargo_mt": 70000.0,
            "bunker_price": 900.0,
        },
        {
            "name": "Indonesia Direct Short Route",
            "origin": "Indonesia",
            "destination": "Paradip",
            "vessel_class": "Panamax",
            "commodity": "Coal",
            "cargo_mt": 70000.0,
        },
    ]

    res = simulate_scenarios(
        db=None,
        base_origin="Australia",
        base_destination="Paradip",
        base_vessel_class="Panamax",
        base_commodity="Coal",
        base_cargo_mt=70000.0,
        scenarios=scenarios,
    )

    assert "base_scenario" in res
    assert "alternatives" in res
    assert len(res["alternatives"]) == 3
    assert "best_scenario" in res
    assert "worst_scenario" in res

    # Indonesia route is much shorter distance -> lowest total cost
    assert res["best_scenario"] in ["Indonesia Direct Short Route", "Supramax Alternative"]

    # Bunker shock at $900/MT should have positive cost delta vs base
    bunker_shock_alt = next(a for a in res["alternatives"] if "Bunker Price Shock" in a["scenario_name"])
    assert bunker_shock_alt["delta_vs_base_pct"] > 0
