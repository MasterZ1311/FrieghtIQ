import { apiClient } from './client';

export type MarketRegimeType = 'BULL' | 'BEAR' | 'NEUTRAL' | 'SEASONAL';
export type DataStatusType = 'LIVE' | 'RECENT' | 'STALE' | 'PUBLIC' | 'LICENSED' | 'DEMO' | 'SYNTHETIC' | 'UNAVAILABLE' | 'UNKNOWN';
export type ForecastRegimeAlignment = 'ALIGNED' | 'DIVERGENT' | 'NEUTRAL' | 'INSUFFICIENT_DATA';

export interface RegimeProbabilities {
  BULL: number;
  BEAR: number;
  NEUTRAL: number;
  SEASONAL: number;
}

export interface RegimeEvidenceItem {
  signal_name: string;
  current_value: number;
  baseline_value?: number;
  signal_direction: 'POSITIVE' | 'NEGATIVE' | 'FLAT' | 'CYCLIC' | 'VOLATILE' | string;
  relative_weight: number;
  interpretation: string;
}

export interface RegimeModelInfo {
  model_name: string;
  model_type: string;
  version: string;
  number_of_states: number;
  training_period: string;
  dataset_version: string;
  validation_method: string;
  status: string;
  features?: string[];
}

export interface RegimeDatasetInfo {
  source: string;
  dataset_name: string;
  dataset_version: string;
  observation_count: number;
  last_updated: string;
  data_status: DataStatusType;
  disclaimer: string;
}

export interface RegimeTransition {
  id: string;
  market_regime_id: string;
  previous_regime: MarketRegimeType;
  new_regime: MarketRegimeType;
  current_regime?: MarketRegimeType;
  transition_date: string;
  confidence: number;
  trigger_features?: string;
  model_version_id: string;
  created_at: string;
}

export interface CurrentRegimeResponse {
  route_code: string;
  trade_lane: string;
  origin_port_id?: string;
  destination_port_id?: string;
  cargo_type: string;
  vessel_class: string;
  regime: MarketRegimeType;
  probabilities: RegimeProbabilities;
  confidence: number;
  current_duration_days: number;
  historical_avg_duration_days?: number | null;
  historical_median_duration_days?: number | null;
  transition_frequency_per_year?: number | null;
  forecast_alignment: ForecastRegimeAlignment;
  forecast_alignment_rationale: string;
  evidence: RegimeEvidenceItem[];
  model: RegimeModelInfo;
  dataset: RegimeDatasetInfo;
  data_status: DataStatusType;
  detected_at: string;
  route?: {
    route_code?: string;
    trade_lane?: string;
    origin_port_id?: string;
    destination_port_id?: string;
    vessel_class?: string;
    cargo_type?: string;
  };
}

export interface RegimeHistoryPoint {
  date: string;
  regime: MarketRegimeType;
  probabilities: RegimeProbabilities;
  freight_rate: number;
}

export interface RegimeAnalysisRequest {
  origin_port_id: string;
  destination_port_id: string;
  cargo_type?: string;
  vessel_class?: string;
}

export const regimeApi = {
  getCurrent: (params?: {
    origin?: string;
    destination?: string;
    cargo?: string;
    vessel_class?: string;
  }): Promise<CurrentRegimeResponse> => {
    const q = new URLSearchParams();
    if (params?.origin) q.append('origin', params.origin);
    if (params?.destination) q.append('destination', params.destination);
    if (params?.cargo) q.append('cargo', params.cargo);
    if (params?.vessel_class) q.append('vessel_class', params.vessel_class);
    const qs = q.toString() ? `?${q.toString()}` : '';
    return apiClient<CurrentRegimeResponse>(`/regime/current${qs}`);
  },

  getHistory: (params?: {
    origin?: string;
    destination?: string;
    vessel_class?: string;
    days?: number;
  }): Promise<RegimeHistoryPoint[]> => {
    const q = new URLSearchParams();
    if (params?.origin) q.append('origin', params.origin);
    if (params?.destination) q.append('destination', params.destination);
    if (params?.vessel_class) q.append('vessel_class', params.vessel_class);
    if (params?.days) q.append('days', params.days.toString());
    const qs = q.toString() ? `?${q.toString()}` : '';
    return apiClient<RegimeHistoryPoint[]>(`/regime/history${qs}`);
  },

  analyze: (payload: RegimeAnalysisRequest): Promise<CurrentRegimeResponse> => {
    return apiClient<CurrentRegimeResponse>('/regime/analyze', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getTransitions: (params?: {
    trade_lane?: string;
    limit?: number;
  }): Promise<RegimeTransition[]> => {
    const q = new URLSearchParams();
    if (params?.trade_lane) q.append('trade_lane', params.trade_lane);
    if (params?.limit) q.append('limit', params.limit.toString());
    const qs = q.toString() ? `?${q.toString()}` : '';
    return apiClient<RegimeTransition[]>(`/regime/transitions${qs}`);
  },

  getModels: (): Promise<RegimeModelInfo[]> => {
    return apiClient<RegimeModelInfo[]>('/regime/models');
  },
};
