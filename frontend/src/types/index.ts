/**
 * FreightIQ TypeScript Type Definitions
 */

export type VesselClass = 'Handysize' | 'Supramax' | 'Panamax' | 'Capesize'
export type Origin = 'Australia' | 'United States' | 'Mozambique' | 'Russia' | 'Indonesia' | 'South Africa'
export type Destination = 'Paradip' | 'Visakhapatnam' | 'Gangavaram' | 'Gopalpur' | 'Dhamra' | 'Sagar-Sandheads' | 'Haldia'
export type Commodity = 'Coal' | 'Iron Ore' | 'Grain' | 'Fertilizer' | 'Bauxite'
export type ContractType = 'Spot' | 'Short-Term' | 'Medium-Term' | 'Long-Term'
export type ContractDurationOption =
  | 'Spot Single Voyage'
  | '3-Month Short-Term COA'
  | '6-Month Medium-Term COA'
  | '12-Month Long-Term Volume'
export type RiskLevel = 'Low' | 'Medium' | 'High' | 'Critical'
export type Trend = 'rising' | 'falling' | 'stable'
export type SignalType = 'BUY_NOW' | 'WAIT' | 'CAUTIOUS_BUY' | 'HEDGE'
export type MarketEntryAction = 'CHARTER NOW' | 'WAIT' | 'MONITOR'
export type ConstraintStatus = 'OK' | 'WARNING' | 'FAIL'
export type FeasibilityStatus = 'Feasible' | 'Restricted' | 'Sub-optimal'
export type IdleRiskLevel = 'Low' | 'Moderate' | 'Elevated' | 'High'

export interface ApiResponseMeta {
  isDemoData: boolean
  sourceLabel: string
  disclaimer: string
  timestamp: string
}

export interface InfluencingFactor {
  factor: string
  direction: 'bullish' | 'bearish' | 'neutral'
  magnitude: 'high' | 'medium' | 'low'
  description: string
}

export interface FreightForecastResponse {
  origin: string
  destination: string
  vessel_class: string
  commodity: string
  current_rate_usd_per_mt: number
  predicted_rate_usd_per_mt: number
  lower_bound: number
  upper_bound: number
  confidence_pct: number
  horizon_days: number
  tce_estimate_usd_per_day: number
  trend: Trend
  influencing_factors: InfluencingFactor[]
  disclaimer: string
  generated_at: string
  isDemoData?: boolean
}

export interface ForecastChartPoint {
  date: string
  actual_rate?: number
  predicted_rate?: number
  lower_bound?: number
  upper_bound?: number
  tce?: number
  type: 'historical' | 'forecast'
}

export interface VesselOption {
  vessel_class: VesselClass
  dwt_range: string
  recommended: boolean
  fit_score: number
  estimated_freight_usd_per_mt: number
  voyage_days: number
  tce_usd_per_day: number
  port_compatible: boolean
  reasons: string[]
  warnings: string[]
}

export interface VesselClassComparison {
  vessel_class: VesselClass
  dwt_range: string
  feasibility: FeasibilityStatus
  estimated_freight_usd_per_mt: number
  cargo_capacity_mt: string
  optimal_parcel_mt: number
  port_compatibility: string
  port_compatible: boolean
  estimated_turnaround_days: number
  idle_risk: IdleRiskLevel
  idle_cost_risk_usd: number
  overall_score: number
  fuel_burn_sea_mt_day: number
  daily_hire_usd: number
  reasons: string[]
  warnings: string[]
}

export interface VesselRecommendResponse {
  recommended_class: VesselClass
  alternatives: VesselOption[]
  detailed_comparison: VesselClassComparison[]
  reasoning: string
  disclaimer: string
  isDemoData?: boolean
}

export interface PortConstraint {
  constraint: string
  status: ConstraintStatus
  detail: string
}

export interface PortCheckResponse {
  port: string
  vessel_class: string
  compatible: boolean
  constraints: PortConstraint[]
  turnaround_days: number
  port_dues_usd: number
  handling_rate_mt_day: number
  max_draft_m: number
  vessel_draft_m: number
  notes: string
  disclaimer?: string
  isDemoData?: boolean
}

export interface EconomicsResponse {
  origin: string
  destination: string
  vessel_class: string
  cargo_mt: number
  distance_nm: number
  sea_days: number
  port_days: number
  total_voyage_days: number
  freight_revenue_usd: number
  freight_rate_usd_per_mt: number
  bunker_cost_usd: number
  port_dues_usd: number
  canal_dues_usd: number
  opex_usd: number
  total_cost_usd: number
  gross_profit_usd: number
  tce_usd_per_day: number
  breakeven_rate_usd_per_mt: number
  margin_pct: number
  disclaimer: string
  isDemoData?: boolean
}

export interface MarketEntryResponse {
  action: MarketEntryAction
  signal: SignalType
  current_rate_usd_per_mt: number
  predicted_rate_usd_per_mt: number
  expected_movement_usd: number
  expected_movement_pct: number
  confidence_pct: number
  potential_savings_usd: number
  recommendation: string
  reasons: string[]
  warnings: string[]
  best_entry_window: string
  estimated_savings_usd: number
  alternative_strategies: {
    strategy: string
    description: string
    pros: string[]
    cons: string[]
  }[]
  disclaimer: string
  isDemoData?: boolean
}

export interface RiskFactor {
  category: string
  name: string
  level: RiskLevel
  score: number
  description: string
  mitigation: string
}

export interface AlertItem {
  id: string
  title: string
  severity: 'Critical' | 'High' | 'Medium' | 'Info'
  category: 'Port Congestion' | 'Weather & Monsoon' | 'Bunker Fuel' | 'Geopolitical' | 'Market Volatility'
  location: string
  timestamp: string
  description: string
  recommended_action: string
  impact_indicator: string
}

export interface RiskResponse {
  overall_risk_score: number
  overall_risk_level: RiskLevel
  risk_factors: RiskFactor[]
  alerts: AlertItem[]
  top_risks: string[]
  recommended_actions: string[]
  disclaimer: string
  isDemoData?: boolean
}

export interface ContractOption {
  contract_type: string
  duration: string
  rate_usd_per_mt: number
  total_cost_usd: number
  cost_per_month_usd: number
  flexibility_score: number
  risk_score: number
  recommended: boolean
  breakeven_freight_usd: number
  pros: string[]
  cons: string[]
}

export interface ContractCompareResponse {
  options: ContractOption[]
  recommended_contract: string
  blended_strategy: string | null
  expected_saving_vs_spot: number
  reasoning: string
  annual_volume_mt: number
  monthly_cashflow: {
    month: string
    spot_cost: number
    short_term_cost: number
    medium_term_cost: number
  }[]
  disclaimer: string
  isDemoData?: boolean
}

export interface ScenarioResult {
  scenario_name: string
  vessel_class: string
  origin: string
  destination: string
  freight_rate_usd_per_mt: number
  tce_usd_per_day: number
  total_cost_usd: number
  voyage_days: number
  bunker_cost_usd: number
  risk_score: number
  delta_vs_base_pct: number
}

export interface ScenarioResponse {
  base_scenario: ScenarioResult
  alternatives: ScenarioResult[]
  best_scenario: string
  worst_scenario: string
  disclaimer: string
  isDemoData?: boolean
}

export interface DashboardSummary {
  rate_snapshots: {
    route: string
    origin: string
    destination: string
    vessel_class: VesselClass
    current_rate: number
    predicted_rate: number
    trend: Trend
    confidence_pct: number
    tce: number
    market_action: MarketEntryAction
    savings_usd: number
  }[]
  executive_kpis: {
    current_freight_indication: number
    forecast_freight: number
    forecast_trend: Trend
    market_entry_action: MarketEntryAction
    recommended_vessel: VesselClass
    estimated_voyage_cost: number
    contract_recommendation: string
    risk_score: number
    risk_level: RiskLevel
    potential_savings: number
  }
  market_entry_highlight: MarketEntryResponse
  disclaimer: string
  isDemoData?: boolean
}

export interface HistoryDataPoint {
  date: string
  rate: number
  tce: number
  bunker: number
  congestion: number
  demand: number
}

export interface Port {
  name: string
  country: string
  region: string
  max_dwt: number
  max_draft_m: number
  max_loa_m: number
  max_beam_m: number
  berths: number
  tide_restricted: boolean
  congestion_level: 'Low' | 'Moderate' | 'Heavy' | 'Severe'
  avg_turnaround_days: number
  handling_rate_mt_day: number
  suitable_commodities: string[]
  latitude: number
  longitude: number
  notes: string
}

export interface PortDiversionOption {
  alternative_port: string
  distance_delta_nm: number
  turnaround_days: number
  congestion_level: string
  port_dues_delta_usd: number
  net_savings_usd: number
  recommendation: string
}

export interface SlowSteamingAnalysis {
  normal_speed_kn: number
  normal_sea_days: number
  normal_sea_bunker_cost_usd: number
  slow_speed_kn: number
  slow_sea_days: number
  slow_sea_bunker_cost_usd: number
  bunker_savings_usd: number
  absorbed_waiting_days: number
  remaining_waiting_days: number
  net_economic_benefit_usd: number
}

export interface IdleScenarioResponse {
  destination: string
  vessel_class: string
  waiting_days: number
  demurrage_rate_usd_day: number
  laytime_allowed_days: number
  actual_port_days: number
  anchorage_idle_bunker_usd: number
  anchorage_vessel_cost_usd: number
  total_waiting_cost_usd: number
  demurrage_incurred_usd: number
  dispatch_earned_usd: number
  total_congestion_exposure_usd: number
  slow_steaming: SlowSteamingAnalysis
  diversion_options: PortDiversionOption[]
  optimal_strategy: string
  actionable_recommendations: string[]
  disclaimer: string
  isDemoData?: boolean
}

export interface IdleScenarioRequest {
  origin?: string
  destination?: string
  vessel_class?: VesselClass
  commodity?: Commodity
  cargo_mt?: number
  waiting_days?: number
  demurrage_rate_usd_day?: number
  bunker_price_usd_per_mt?: number
  slow_steaming_knots?: number
}

export interface CargoPlanWorkflowInput {
  origin: Origin
  destination: Destination
  commodity: Commodity
  cargo_mt: number
  laycan_start: string
  laycan_end: string
  contract_duration: ContractDurationOption
}

export interface CargoPlanEvaluationResult {
  plan_id: string
  input: CargoPlanWorkflowInput
  feasibility: FeasibilityStatus
  recommended_vessel: VesselClass
  estimated_freight_usd_per_mt: number
  total_voyage_cost_usd: number
  bunker_cost_usd: number
  port_dues_usd: number
  voyage_days: number
  tce_estimate_usd_per_day: number
  port_compatibility: {
    status: ConstraintStatus
    max_draft_m: number
    vessel_draft_m: number
    notes: string
  }
  market_signal: MarketEntryAction
  laycan_risk: {
    congestion_score: number
    turnaround_days: number
    weather_risk: string
  }
  contract_recommendation: {
    strategy: string
    potential_savings_usd: number
    reason: string
  }
  created_at: string
}

// ─── End-to-End Decision Suite ────────────────────────────────────────────────

export interface EndToEndRequest {
  origin: string
  destination: string
  commodity: Commodity | string
  cargo_mt: number
  vessel_class?: VesselClass | string
  urgency_days?: number
  annual_volume_mt?: number
  planning_horizon_months?: number
  bunker_price_usd_per_mt?: number
}

export interface FinalRecommendationSummary {
  recommended_vessel: string
  optimal_timing_signal: string
  recommended_contract: string
  port_status: string
  overall_risk_level: string
  overall_fit_score: number
  estimated_freight_usd_per_mt: number
  total_voyage_cost_usd: number
  tce_usd_per_day: number
  breakeven_rate_usd_per_mt: number
  margin_pct: number
  action_items: string[]
}

export interface EndToEndResponse {
  origin: string
  destination: string
  commodity: string
  cargo_mt: number
  distance_nm: number
  forecast: FreightForecastResponse
  vessel_feasibility: VesselOption[]
  recommended_vessel: string
  port_compatibility: PortCheckResponse
  all_ports_compatibility: Record<string, PortCheckResponse>
  market_entry: MarketEntryResponse
  economics: EconomicsResponse
  contracts: ContractCompareResponse
  risk: RiskResponse
  final_recommendation: FinalRecommendationSummary
  explanation: string
  disclaimer: string
}

