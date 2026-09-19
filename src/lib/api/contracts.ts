import { apiClient } from './client';
import { DecisionConfidence } from './wait_fix';
import { DataStatusType } from './regime';

export type ContractStrategyType = 'SPOT' | 'SHORT_TERM_MULTIPLE_VOYAGE' | 'MEDIUM_TERM_MULTIPLE_VOYAGE';

export interface VoyageScheduleItem {
  voyage_number: number;
  parcel_mt: number;
  is_remainder: boolean;
  estimated_departure_day: number;
  estimated_laycan_window: string;
}

export interface VoyagePlanningResult {
  total_requirement_mt: number;
  voyage_parcel_mt: number;
  full_voyages: number;
  remainder_mt: number;
  expected_voyages: number;
  total_planned_mt: number;
  voyage_frequency_days: number;
  planning_horizon_days: number;
  schedule: VoyageScheduleItem[];
}

export interface StrategyScenarioItem {
  scenario_name: string;
  market_assumption: string;
  rate: number;
  quantity: number;
  cost: number;
  probability: number;
}

export interface StrategyDetail {
  id?: string | null;
  strategy_type: ContractStrategyType;
  strategy_label: string;
  contract_duration: string;
  voyage_count: number;
  total_quantity: number;
  contracted_quantity: number;
  spot_quantity: number;
  reference_rate?: number | null;
  expected_rate: number;
  expected_cost: number;
  p10_cost: number;
  p50_cost: number;
  p90_cost: number;
  market_exposure: number;
  flexibility_measure: number;
  risk_adjusted_cost: number;
  break_even_rate?: number | null;
  decision_confidence: DecisionConfidence;
  scenarios: StrategyScenarioItem[];
  why_this_fits: string[];
  key_trade_off: string;
  data_status: DataStatusType;
}

export interface ScenarioMatrixCell {
  strategy_type: ContractStrategyType;
  scenario_name: string;
  freight_rate_usd_pmt: number;
  freight_cost_usd: number;
  market_assumption: string;
}

export interface BreakEvenAnalysisResult {
  reference_contract_rate_usd_pmt?: number | null;
  modeled_break_even_spot_rate_usd_pmt?: number | null;
  current_spot_rate_usd_pmt: number;
  rate_delta_usd_pmt?: number | null;
  rate_delta_pct?: number | null;
  total_quantity_mt: number;
  planning_horizon_days: number;
  status: 'AVAILABLE' | 'REFERENCE_RATE_UNAVAILABLE' | string;
  methodology_label: string;
  assumptions_summary: string;
  decision_interpretation: string;
}

export interface CoverageTierResult {
  coverage_percentage: number;
  contracted_quantity_mt: number;
  spot_quantity_mt: number;
  blended_expected_rate: number;
  expected_cost: number;
  p10_cost: number;
  p90_cost: number;
  cost_range_usd: number;
  market_exposure: number;
  flexibility_measure: number;
  risk_adjusted_cost: number;
  summary_label: string;
}

export interface ContractAnalysisRequest {
  cargo_request_id?: string;
  origin_port_id?: string;
  destination_port_id?: string;
  cargo_type?: string;
  total_requirement_mt?: number;
  parcel_size_mt?: number;
  vessel_class?: string;
  planning_horizon_days?: number;
  reference_contract_rate?: number;
}

export interface CoverageSimulationRequest {
  total_quantity: number;
  coverage_percentage: number;
  contract_rate: number;
  spot_expected_rate: number;
  spot_p10: number;
  spot_p90: number;
  volatility?: number;
  planning_horizon_days?: number;
}

export interface StrategyComparisonResponse {
  cargo_request_id?: string | null;
  trade_lane: string;
  total_requirement_mt: number;
  parcel_size_mt: number;
  planning_horizon_days: number;
  voyage_plan: VoyagePlanningResult;
  strategies: Record<string, StrategyDetail>;
  scenario_matrix: ScenarioMatrixCell[];
  break_even_analysis: BreakEvenAnalysisResult;
  coverage_spectrum: CoverageTierResult[];
  port_feasibility_status: string;
  data_provenance: Record<string, any>;
  decision_confidence: DecisionConfidence;
  created_at: string;
}

export interface StrategyDetailRecordResponse {
  id: string;
  cargo_request_id?: string | null;
  strategy_type: ContractStrategyType;
  contract_duration: string;
  voyage_count: number;
  total_quantity: number;
  contracted_quantity: number;
  spot_quantity: number;
  reference_rate?: number | null;
  expected_rate: number;
  expected_cost: number;
  p10_cost: number;
  p50_cost: number;
  p90_cost: number;
  market_exposure: number;
  flexibility_measure: number;
  risk_adjusted_cost: number;
  break_even_rate?: number | null;
  decision_confidence: DecisionConfidence;
  data_status: DataStatusType;
  created_at: string;
  scenarios: StrategyScenarioItem[];
}

export const contractsApi = {
  analyze: (payload: ContractAnalysisRequest): Promise<StrategyComparisonResponse> => {
    return apiClient<StrategyComparisonResponse>('/contracts/analyze', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getById: (id: string): Promise<StrategyDetailRecordResponse> => {
    return apiClient<StrategyDetailRecordResponse>(`/contracts/${id}`);
  },

  getComparison: (id: string): Promise<StrategyComparisonResponse> => {
    return apiClient<StrategyComparisonResponse>(`/contracts/${id}/comparison`);
  },

  getScenarios: (id: string): Promise<StrategyScenarioItem[]> => {
    return apiClient<StrategyScenarioItem[]>(`/contracts/${id}/scenarios`);
  },

  getBreakEven: (id: string): Promise<BreakEvenAnalysisResult> => {
    return apiClient<BreakEvenAnalysisResult>(`/contracts/${id}/break-even`);
  },

  simulateCoverage: (payload: CoverageSimulationRequest): Promise<CoverageTierResult> => {
    return apiClient<CoverageTierResult>('/contracts/coverage', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
