"""
FreightIQ Core Domain Models
============================
Pure domain representations independent of persistence or transport layers.
All models reflect maritime dry-bulk shipping logic.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import date


@dataclass
class Cargo:
    commodity: str
    quantity_mt: float
    origin: str
    destination: str
    laycan: Optional[str] = None
    contract_duration: Optional[str] = None

    def __post_init__(self):
        if self.quantity_mt <= 0:
            raise ValueError(f"Cargo quantity must be positive, got {self.quantity_mt}")


@dataclass
class Vessel:
    vessel_type: str
    capacity_mt: float
    loa: float
    beam: float
    draft: float
    speed: float
    daily_cost: float
    dwt_min: float = 0.0
    dwt_max: float = 0.0
    fuel_consumption_mt_day: float = 0.0
    is_demo: bool = True

    def __post_init__(self):
        if not self.dwt_max:
            self.dwt_max = self.capacity_mt
        if not self.dwt_min:
            self.dwt_min = self.capacity_mt * 0.6


@dataclass
class Port:
    name: str
    country: str
    region: str
    max_loa: float
    max_beam: float
    max_draft: float
    handling_rate: float
    berth_constraints: List[str] = field(default_factory=list)
    max_dwt: float = 200000.0
    berths: int = 4
    tide_restricted: bool = False
    congestion_level: str = "medium"
    avg_turnaround_days: float = 4.0
    port_dues_usd: float = 25000.0
    suitable_commodities: List[str] = field(default_factory=list)
    notes: str = ""
    is_demo: bool = True


@dataclass
class Forecast:
    current_rate: float
    predicted_rate: float
    horizon: int
    lower_bound: float
    upper_bound: float
    confidence: float
    drivers: List[Dict[str, Any]]
    trend: str = "stable"
    disclaimer: str = "[DEMO] Synthetic rate forecast for demonstration purposes."


@dataclass
class Recommendation:
    decision: str
    score: float
    confidence: float
    reasons: List[str]
    warnings: List[str]
    recommended_class: str = ""
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    ranked_summary: List[str] = field(default_factory=list)
    reasoning: str = ""
    disclaimer: str = "[DEMO] Synthetic vessel recommendation."


@dataclass
class Contract:
    contract_type: str
    voyages: int
    estimated_cost: float
    estimated_savings: float
    risk: str
    duration: str = ""
    rate_usd_per_mt: float = 0.0
    flexibility_score: float = 50.0
    risk_score: float = 50.0
    recommended: bool = False
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)


@dataclass
class RiskFactor:
    category: str
    name: str
    level: str
    score: float
    description: str
    mitigation: str


@dataclass
class RiskAnalysis:
    overall_risk_score: float
    overall_risk_level: str
    risk_factors: List[RiskFactor]
    top_risks: List[str]
    recommended_actions: List[str]
    component_scores: Dict[str, float] = field(default_factory=dict)
    disclaimer: str = "[DEMO] Deterministic synthetic risk evaluation."


@dataclass
class ScenarioResult:
    scenario_name: str
    vessel_class: str
    freight_rate_usd_per_mt: float
    tce_usd_per_day: float
    total_cost_usd: float
    voyage_days: float
    risk_score: float
    delta_vs_base_pct: float = 0.0


@dataclass
class ScenarioSimulation:
    base_scenario: ScenarioResult
    alternatives: List[ScenarioResult]
    best_scenario: str
    worst_scenario: str
    disclaimer: str = "[DEMO] Synthetic scenario simulation."
