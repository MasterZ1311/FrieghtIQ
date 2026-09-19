import { apiClient } from './client';
import { MarketRegimeType, DataStatusType, ForecastRegimeAlignment } from './regime';

export type WaitFixDecision = 'FIX_NOW' | 'WAIT' | 'MONITOR' | 'DECISION_WINDOW_EXPIRED' | 'NOT_EVALUABLE';
export type DecisionConfidence = 'HIGH' | 'MEDIUM' | 'LOW';

export interface ScenarioItem {
  scenario_name: string;
  rate: number;
  probability: number;
  freight_cost: number;
  difference_vs_fix: number;
}

export interface OptionValueResult {
  option_value_usd?: number | null;
  option_value_pmt?: number | null;
  methodology: string;
  parameters: Record<string, any>;
  status: 'AVAILABLE' | 'OPTION_VALUE_UNAVAILABLE' | string;
  rationale: string;
}

export interface WaitFixAssumptions {
  current_freight_rate: number;
  reference_fix_rate: number;
  cargo_quantity_mt: number;
  decision_horizon_days: number;
  remaining_days: number;
  historical_volatility_annualized: number;
  discount_rate_annual: number;
  forecast_model: string;
  regime_model: string;
  dataset_version: string;
  data_status: DataStatusType;
}

export interface WaitFixEvidenceItem {
  factor_name: string;
  observed_value: string;
  impact_on_decision: 'FAVORS_WAIT' | 'FAVORS_FIX' | 'NEUTRAL' | string;
  weight: number;
  description: string;
}

export interface DataQualityReport {
  forecast_data: string;
  regime_data: string;
  port_feasibility: string;
  vessel_feasibility: string;
  reference_fix_rate: string;
  overall_quality: 'HIGH' | 'MEDIUM' | 'LOW' | string;
}

export interface WaitFixAnalysisResponse {
  id: string;
  cargo_request_id?: string | null;
  origin_port_id: string;
  destination_port_id: string;
  trade_lane: string;
  cargo_type: string;
  cargo_quantity: number;
  vessel_class: string;
  decision: WaitFixDecision;
  decision_confidence: DecisionConfidence;
  current_freight_rate: number;
  expected_wait_rate: number;
  expected_fix_cost: number;
  expected_wait_cost: number;
  expected_modeled_difference: number;
  decision_deadline?: string | null;
  remaining_days: number;
  p10_rate: number;
  p50_rate: number;
  p90_rate: number;
  scenarios: ScenarioItem[];
  option_analysis: OptionValueResult;
  assumptions: WaitFixAssumptions;
  why_this_result: string[];
  what_could_change_this: string[];
  evidence: WaitFixEvidenceItem[];
  forecast_regime_alignment: ForecastRegimeAlignment;
  data_quality: DataQualityReport;
  data_status: DataStatusType;
  created_at: string;
}

export interface WaitFixAnalysisRequest {
  cargo_request_id?: string;
  origin_port_id?: string;
  destination_port_id?: string;
  cargo_type?: string;
  cargo_quantity?: number;
  vessel_class?: string;
  decision_horizon_days?: number;
  reference_fix_rate?: number;
}

export interface OptionValueRequest {
  current_freight_rate: number;
  reference_fix_rate: number;
  cargo_quantity: number;
  remaining_days: number;
  volatility_annualized?: number;
  discount_rate?: number;
}

export const waitFixApi = {
  analyze: (payload: WaitFixAnalysisRequest): Promise<WaitFixAnalysisResponse> => {
    return apiClient<WaitFixAnalysisResponse>('/wait-fix/analyze', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getLatest: (params?: {
    cargo_request_id?: string;
    origin?: string;
    destination?: string;
    vessel_class?: string;
  }): Promise<WaitFixAnalysisResponse> => {
    const q = new URLSearchParams();
    if (params?.cargo_request_id) q.append('cargo_request_id', params.cargo_request_id);
    if (params?.origin) q.append('origin', params.origin);
    if (params?.destination) q.append('destination', params.destination);
    if (params?.vessel_class) q.append('vessel_class', params.vessel_class);
    const qs = q.toString() ? `?${q.toString()}` : '';
    return apiClient<WaitFixAnalysisResponse>(`/wait-fix/latest${qs}`);
  },

  getById: (id: string): Promise<WaitFixAnalysisResponse> => {
    return apiClient<WaitFixAnalysisResponse>(`/wait-fix/${id}`);
  },

  getHistory: (params?: {
    cargo_request_id?: string;
    limit?: number;
  }): Promise<WaitFixAnalysisResponse[]> => {
    const q = new URLSearchParams();
    if (params?.cargo_request_id) q.append('cargo_request_id', params.cargo_request_id);
    if (params?.limit) q.append('limit', params.limit.toString());
    const qs = q.toString() ? `?${q.toString()}` : '';
    return apiClient<WaitFixAnalysisResponse[]>(`/wait-fix/history${qs}`);
  },

  getScenarios: (id: string): Promise<ScenarioItem[]> => {
    return apiClient<ScenarioItem[]>(`/wait-fix/${id}/scenarios`);
  },

  calculateOptionValue: (payload: OptionValueRequest): Promise<OptionValueResult> => {
    return apiClient<OptionValueResult>('/wait-fix/option-value', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
