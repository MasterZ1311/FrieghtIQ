"""
FreightIQ Domain Package
========================
Pure domain models and maritime business rules.
"""
from app.domain.models import (
    Cargo,
    Vessel,
    Port,
    Forecast,
    Recommendation,
    Contract,
    RiskFactor,
    RiskAnalysis,
    ScenarioResult,
    ScenarioSimulation,
)
from app.domain.port_rules import evaluate_port_compatibility
from app.domain.vessel_rules import evaluate_vessel_candidate, rank_vessel_options
from app.domain.economics_rules import calculate_voyage_economics
from app.domain.contract_rules import evaluate_contracts
from app.domain.risk_rules import score_risk_dimensions
from app.domain.scenario_rules import run_scenario_simulation

__all__ = [
    "Cargo",
    "Vessel",
    "Port",
    "Forecast",
    "Recommendation",
    "Contract",
    "RiskFactor",
    "RiskAnalysis",
    "ScenarioResult",
    "ScenarioSimulation",
    "evaluate_port_compatibility",
    "evaluate_vessel_candidate",
    "rank_vessel_options",
    "calculate_voyage_economics",
    "evaluate_contracts",
    "score_risk_dimensions",
    "run_scenario_simulation",
]
