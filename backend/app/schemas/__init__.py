"""
FreightIQ Pydantic Schemas
==========================
Request and Response models for all API endpoints with strong validation,
clean domain mapping, and dual backward-compatibility.
"""
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator


# ─── Shared Base Models ────────────────────────────────────────────────────────

class InfluencingFactor(BaseModel):
    factor: str
    direction: str = "neutral"  # "bullish" | "bearish" | "neutral"
    magnitude: str = "medium"   # "high" | "medium" | "low"
    description: str


class PortConstraint(BaseModel):
    constraint: str
    status: str                 # "OK" | "WARNING" | "FAIL"
    detail: str


class RiskFactorModel(BaseModel):
    category: str
    name: str
    level: str                  # "Low" | "Medium" | "High" | "Critical"
    score: float
    description: str
    mitigation: str


class ScenarioResultModel(BaseModel):
    scenario_name: str
    vessel_class: str
    freight_rate_usd_per_mt: float
    tce_usd_per_day: float
    total_cost_usd: float
    voyage_days: float
    risk_score: float
    delta_vs_base_pct: float = 0.0


# ─── 1. Forecast Schemas ───────────────────────────────────────────────────────

class ForecastRequest(BaseModel):
    origin: str = Field(..., min_length=1, description="Origin port or country (e.g. Australia, Newcastle)")
    destination: str = Field(..., min_length=1, description="Destination port (e.g. Paradip, Visakhapatnam)")
    vessel_class: str = Field(default="Panamax", description="Vessel class: Handysize, Supramax, Panamax, Capesize")
    vessel_type: Optional[str] = None
    commodity: str = Field(default="Coal", description="Commodity type: Coal, Iron Ore, Grain, Fertilizer, Bauxite")
    quantity_mt: Optional[float] = Field(default=None, gt=0, le=400000, description="Cargo payload in metric tonnes")
    cargo_mt: Optional[float] = Field(default=None, gt=0, le=400000, description="Alias for quantity_mt")
    horizon: Optional[int] = Field(default=None, ge=1, le=365, description="Forecast horizon in days")
    horizon_days: Optional[int] = Field(default=None, ge=1, le=365, description="Alias for horizon")
    laycan: Optional[str] = Field(default=None, description="Laycan date or window")
    laycan_start: Optional[date] = Field(default=None, description="Laycan starting date")

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            # Normalize cargo quantity
            qty = values.get("quantity_mt") or values.get("cargo_mt") or 70000.0
            values["quantity_mt"] = float(qty)
            values["cargo_mt"] = float(qty)
            # Normalize vessel class
            vc = values.get("vessel_type") or values.get("vessel_class") or "Panamax"
            values["vessel_class"] = str(vc)
            values["vessel_type"] = str(vc)
            # Normalize horizon
            hz = values.get("horizon") or values.get("horizon_days") or 30
            values["horizon"] = int(hz)
            values["horizon_days"] = int(hz)
        return values


# Backward compatible alias
FreightForecastRequest = ForecastRequest


class ForecastResponse(BaseModel):
    # Core domain fields
    current_rate: float
    predicted_rate: float
    horizon: int
    lower_bound: float
    upper_bound: float
    confidence: float
    drivers: List[InfluencingFactor]

    # Additional metadata and frontend compatibility
    origin: str
    destination: str
    vessel_class: str
    commodity: str
    current_rate_usd_per_mt: float
    predicted_rate_usd_per_mt: float
    confidence_pct: float
    horizon_days: int
    tce_estimate_usd_per_day: float
    trend: str = "stable"
    influencing_factors: List[InfluencingFactor]
    disclaimer: str = "[DEMO] This is a synthetic forecast for demonstration purposes. Not real market data."
    generated_at: datetime


# Backward compatible alias
FreightForecastResponse = ForecastResponse


# ─── 2. Vessel Recommendation Schemas ──────────────────────────────────────────

class VesselOption(BaseModel):
    vessel_class: str
    dwt_range: str
    recommended: bool
    fit_score: float
    estimated_freight_usd_per_mt: float
    voyage_days: float
    tce_usd_per_day: float
    port_compatible: bool
    reasons: List[str]
    warnings: List[str]
    is_feasible: Optional[bool] = None
    feasibility_status: Optional[str] = None
    turnaround_days: Optional[float] = None
    handling_rate_mt_day: Optional[float] = None
    total_voyage_cost_usd: Optional[float] = None
    cost_per_mt_usd: Optional[float] = None
    deadheading_proxy_days: Optional[float] = None
    idle_risk_score: Optional[float] = None
    score_breakdown: Optional[Dict[str, float]] = None


class VesselRecommendRequest(BaseModel):
    origin: str = Field(..., min_length=1)
    destination: str = Field(..., min_length=1)
    commodity: str = Field(default="Coal")
    quantity_mt: Optional[float] = Field(default=None, gt=0, le=400000)
    cargo_mt: Optional[float] = Field(default=None, gt=0, le=400000)
    laycan: Optional[str] = None
    laycan_start: Optional[date] = None
    budget_usd_per_mt: Optional[float] = Field(default=None, ge=0)

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            qty = values.get("quantity_mt") or values.get("cargo_mt") or 70000.0
            values["quantity_mt"] = float(qty)
            values["cargo_mt"] = float(qty)
        return values


class VesselRecommendResponse(BaseModel):
    # Core domain fields
    decision: str
    score: float
    confidence: float
    reasons: List[str]
    warnings: List[str]

    # Frontend compatibility fields
    recommended_class: str
    alternatives: List[VesselOption]
    ranked_summary: Optional[List[str]] = None
    reasoning: str
    disclaimer: str = "[DEMO] Vessel recommendations use synthetic operational parameters."


# ─── 3. Port Check Schemas ─────────────────────────────────────────────────────

class PortCheckRequest(BaseModel):
    port: str = Field(..., min_length=1)
    vessel_class: Optional[str] = Field(default="Panamax")
    vessel_type: Optional[str] = None
    quantity_mt: Optional[float] = Field(default=None, gt=0, le=400000)
    cargo_mt: Optional[float] = Field(default=None, gt=0, le=400000)
    commodity: str = Field(default="Coal")

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            qty = values.get("quantity_mt") or values.get("cargo_mt") or 70000.0
            values["quantity_mt"] = float(qty)
            values["cargo_mt"] = float(qty)
            vc = values.get("vessel_type") or values.get("vessel_class") or "Panamax"
            values["vessel_class"] = str(vc)
            values["vessel_type"] = str(vc)
        return values


class PortCheckResponse(BaseModel):
    port: str
    vessel_class: str
    compatible: bool
    constraints: List[PortConstraint]
    berth_constraints: List[str] = Field(default_factory=list)
    turnaround_days: float
    port_dues_usd: float
    handling_rate: float
    handling_rate_mt_day: float
    notes: str
    disclaimer: str = "[DEMO] Port compatibility verified against synthetic navigational limits."


# ─── 4. Voyage Economics Schemas ───────────────────────────────────────────────

class EconomicsRequest(BaseModel):
    origin: str = Field(..., min_length=1)
    destination: str = Field(..., min_length=1)
    vessel_class: Optional[str] = Field(default="Panamax")
    vessel_type: Optional[str] = None
    commodity: str = Field(default="Coal")
    quantity_mt: Optional[float] = Field(default=None, gt=0, le=400000)
    cargo_mt: Optional[float] = Field(default=None, gt=0, le=400000)
    freight_rate_usd_per_mt: Optional[float] = Field(default=None, ge=0)
    bunker_price_usd_per_mt: float = Field(default=650.0, gt=0, le=3000)
    port_days_origin: float = Field(default=2.0, ge=0)
    port_days_dest: Optional[float] = Field(default=None, ge=0)
    laycan_start: Optional[date] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            qty = values.get("quantity_mt") or values.get("cargo_mt") or 70000.0
            values["quantity_mt"] = float(qty)
            values["cargo_mt"] = float(qty)
            vc = values.get("vessel_type") or values.get("vessel_class") or "Panamax"
            values["vessel_class"] = str(vc)
            values["vessel_type"] = str(vc)
        return values


class EconomicsResponse(BaseModel):
    origin: str
    destination: str
    vessel_type: str
    vessel_class: str
    quantity_mt: float
    cargo_mt: float
    distance_nm: float
    sea_days: float
    port_days: float
    total_voyage_days: float
    freight_revenue: float
    freight_revenue_usd: float
    freight_rate: float
    freight_rate_usd_per_mt: float
    bunker_cost: float
    bunker_cost_usd: float
    port_dues: float
    port_dues_usd: float
    canal_dues: float
    canal_dues_usd: float
    opex: float
    opex_usd: float
    total_cost: float
    total_cost_usd: float
    cost_per_mt: float
    gross_profit: float
    gross_profit_usd: float
    tce: float
    tce_usd_per_day: float
    breakeven_rate: float
    breakeven_rate_usd_per_mt: float
    margin_pct: float
    disclaimer: str = "[DEMO] Economics calculated using synthetic/estimated data."


# ─── 5. Contract Comparison Schemas ────────────────────────────────────────────

class ContractOption(BaseModel):
    contract_type: str
    voyages: int
    duration: str
    rate_usd_per_mt: float
    estimated_cost: float
    total_cost_usd: float
    estimated_savings: float
    risk: str
    flexibility_score: float
    risk_score: float
    recommended: bool
    pros: List[str]
    cons: List[str]
    cost_per_mt: Optional[float] = None
    savings_vs_spot_usd: Optional[float] = None
    exposure_pct: Optional[float] = None


class ContractCompareRequest(BaseModel):
    origin: str = Field(..., min_length=1)
    destination: str = Field(..., min_length=1)
    vessel_class: Optional[str] = Field(default="Panamax")
    vessel_type: Optional[str] = None
    commodity: str = Field(default="Coal")
    quantity_mt: Optional[float] = Field(default=None, gt=0, le=400000)
    cargo_mt: Optional[float] = Field(default=None, gt=0, le=400000)
    annual_volume_mt: float = Field(default=500000.0, gt=0)
    planning_horizon_months: int = Field(default=12, ge=1, le=60)

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            qty = values.get("quantity_mt") or values.get("cargo_mt") or 70000.0
            values["quantity_mt"] = float(qty)
            values["cargo_mt"] = float(qty)
            vc = values.get("vessel_type") or values.get("vessel_class") or "Panamax"
            values["vessel_class"] = str(vc)
            values["vessel_type"] = str(vc)
        return values


class ContractCompareResponse(BaseModel):
    contracts: List[ContractOption]
    options: List[ContractOption]
    recommended_contract: str
    blended_strategy: Optional[str]
    expected_saving_vs_spot: float
    reasoning: str
    disclaimer: str = "[DEMO] Contract comparison uses synthetic rate projections."


# ─── 6. Risk Schemas ───────────────────────────────────────────────────────────

class RiskRequest(BaseModel):
    origin: str = Field(..., min_length=1)
    destination: str = Field(..., min_length=1)
    vessel_class: Optional[str] = Field(default="Panamax")
    vessel_type: Optional[str] = None
    commodity: str = Field(default="Coal")
    quantity_mt: Optional[float] = Field(default=None, gt=0, le=400000)
    cargo_mt: Optional[float] = Field(default=None, gt=0, le=400000)
    contract_type: str = Field(default="Spot")
    laycan_start: Optional[date] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            qty = values.get("quantity_mt") or values.get("cargo_mt") or 70000.0
            values["quantity_mt"] = float(qty)
            values["cargo_mt"] = float(qty)
            vc = values.get("vessel_type") or values.get("vessel_class") or "Panamax"
            values["vessel_class"] = str(vc)
            values["vessel_type"] = str(vc)
        return values


class RiskResponse(BaseModel):
    overall_risk_score: float
    overall_risk_level: str
    score: float
    decision: str
    risk_factors: List[RiskFactorModel]
    top_risks: List[str]
    recommended_actions: List[str]
    component_scores: Optional[Dict[str, float]] = None
    disclaimer: str = "[DEMO] Risk scores are synthetic model outputs."


# ─── 7. Scenario Schemas ───────────────────────────────────────────────────────

class ScenarioRequest(BaseModel):
    base_origin: str = Field(..., min_length=1)
    base_destination: str = Field(..., min_length=1)
    base_vessel_class: str = Field(default="Panamax")
    base_commodity: str = Field(default="Coal")
    base_cargo_mt: Optional[float] = Field(default=None, gt=0, le=400000)
    base_quantity_mt: Optional[float] = Field(default=None, gt=0, le=400000)
    scenarios: List[Dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            qty = values.get("base_quantity_mt") or values.get("base_cargo_mt") or 70000.0
            values["base_quantity_mt"] = float(qty)
            values["base_cargo_mt"] = float(qty)
        return values


# Backward compatible alias
ScenarioResult = ScenarioResultModel


class ScenarioResponse(BaseModel):
    base_scenario: ScenarioResultModel
    alternatives: List[ScenarioResultModel]
    best_scenario: str
    worst_scenario: str
    disclaimer: str = "[DEMO] Scenario outputs are synthetic model simulations."


# ─── 8. Existing Idle & Market Entry Schemas (Maintained for full system compatibility)

class IdleScenarioRequest(BaseModel):
    origin: str = "Australia"
    destination: str = "Paradip"
    vessel_class: str = "Panamax"
    commodity: str = "Coal"
    cargo_mt: float = Field(default=70000, ge=1000, le=400000)
    waiting_days: Optional[float] = Field(default=None, ge=0, le=30)
    demurrage_rate_usd_day: Optional[float] = Field(default=None, ge=0)
    bunker_price_usd_per_mt: float = Field(default=650.0, ge=100, le=2000)
    slow_steaming_knots: float = Field(default=11.5, ge=8.0, le=16.0)


class PortDiversionOption(BaseModel):
    alternative_port: str
    distance_delta_nm: float
    turnaround_days: float
    congestion_level: str
    port_dues_delta_usd: float
    net_savings_usd: float
    recommendation: str


class SlowSteamingAnalysis(BaseModel):
    normal_speed_kn: float
    normal_sea_days: float
    normal_sea_bunker_cost_usd: float
    slow_speed_kn: float
    slow_sea_days: float
    slow_sea_bunker_cost_usd: float
    bunker_savings_usd: float
    absorbed_waiting_days: float
    remaining_waiting_days: float
    net_economic_benefit_usd: float


class IdleScenarioResponse(BaseModel):
    destination: str
    vessel_class: str
    waiting_days: float
    demurrage_rate_usd_day: float
    laytime_allowed_days: float
    actual_port_days: float
    anchorage_idle_bunker_usd: float
    anchorage_vessel_cost_usd: float
    total_waiting_cost_usd: float
    demurrage_incurred_usd: float
    dispatch_earned_usd: float
    total_congestion_exposure_usd: float
    slow_steaming: SlowSteamingAnalysis
    diversion_options: List[PortDiversionOption]
    optimal_strategy: str
    actionable_recommendations: List[str]
    disclaimer: str = "[DEMO] Idle scenario calculations use synthetic operational parameters."


class MarketEntryRequest(BaseModel):
    origin: str
    destination: str
    vessel_class: str = "Panamax"
    commodity: str = "Coal"
    cargo_mt: float = Field(default=70000, ge=1000, le=400000)
    urgency_days: int = Field(default=30, ge=0, le=180)


class MarketEntryResponse(BaseModel):
    signal: str
    confidence_pct: float
    recommendation: str
    reasons: List[str]
    warnings: List[str]
    best_entry_window: str
    estimated_savings_usd: float
    alternative_strategies: List[Dict[str, Any]]
    disclaimer: str = "[DEMO] Market entry signals are based on synthetic model outputs."


# ─── 8. End-to-End Decision Suite Schemas ─────────────────────────────────────

class EndToEndRequest(BaseModel):
    origin: str = Field(default="Australia", min_length=1)
    destination: str = Field(default="Paradip", min_length=1)
    commodity: str = Field(default="Coal")
    cargo_mt: float = Field(default=70000.0, gt=0, le=400000)
    vessel_class: Optional[str] = Field(default=None)
    urgency_days: int = Field(default=30, ge=0, le=180)
    annual_volume_mt: float = Field(default=500000.0, gt=0)
    planning_horizon_months: int = Field(default=12, ge=1, le=36)
    bunker_price_usd_per_mt: float = Field(default=650.0, ge=100, le=2000)


class FinalRecommendationSummary(BaseModel):
    recommended_vessel: str
    optimal_timing_signal: str
    recommended_contract: str
    port_status: str
    overall_risk_level: str
    overall_fit_score: float
    estimated_freight_usd_per_mt: float
    total_voyage_cost_usd: float
    tce_usd_per_day: float
    breakeven_rate_usd_per_mt: float
    margin_pct: float
    action_items: List[str]


class EndToEndResponse(BaseModel):
    origin: str
    destination: str
    commodity: str
    cargo_mt: float
    distance_nm: float
    forecast: FreightForecastResponse
    vessel_feasibility: List[VesselOption]
    recommended_vessel: str
    port_compatibility: PortCheckResponse
    all_ports_compatibility: Dict[str, PortCheckResponse]
    market_entry: MarketEntryResponse
    economics: EconomicsResponse
    contracts: ContractCompareResponse
    risk: RiskResponse
    final_recommendation: FinalRecommendationSummary
    explanation: str
    disclaimer: str = "[DEMO] End-to-end evaluation calculated from synthetic and simulated maritime operational models."

