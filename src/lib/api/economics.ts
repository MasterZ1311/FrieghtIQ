import { apiClient } from './client';
import { DataStatusType } from './regime';

export type CostComponentType =
  | 'FREIGHT'
  | 'BUNKER'
  | 'PORT_DUES'
  | 'BERTH_CHARGES'
  | 'CARGO_HANDLING'
  | 'PILOTAGE_TOWAGE'
  | 'AGENCY_SUNDRIES'
  | 'TIME_CHARTER'
  | 'TIME_OPPORTUNITY'
  | 'DELAY_DEMURRAGE'
  | 'REPOSITIONING_BUNKER'
  | 'OTHER';

export type VoyageScenarioType =
  | 'BASE'
  | 'LOW_COST'
  | 'HIGH_COST'
  | 'DELAY'
  | 'SLOW_STEAM'
  | 'FAST_TRANSIT';

export type SpeedScenarioStatus =
  | 'ECONOMICALLY_PREFERRED'
  | 'EVALUATED'
  | 'SUBOPTIMAL'
  | 'SPEED_EXCEEDS_RATING'
  | 'INSUFFICIENT_DATA';

export interface CostComponentItem {
  id?: string;
  component_type: CostComponentType;
  amount: number;
  currency: string;
  unit: string;
  quantity?: number;
  rate?: number;
  source_id?: string;
  data_status: DataStatusType;
  assumption?: string;
}

export interface SpeedScenarioItem {
  id?: string;
  speed_knots: number;
  sailing_hours: number;
  sailing_days: number;
  fuel_consumption?: number;
  fuel_consumed?: number;
  bunker_price?: number;
  bunker_cost?: number;
  time_cost?: number;
  delay_exposure?: number;
  total_cost?: number;
  cost_per_mt?: number;
  status: SpeedScenarioStatus;
  assumptions?: string;
}

export interface VoyageScenarioItem {
  id?: string;
  scenario_name: VoyageScenarioType;
  description?: string;
  freight_rate?: number;
  bunker_price?: number;
  speed?: number;
  sailing_days?: number;
  port_delay_hours?: number;
  idle_days?: number;
  cost_breakdown?: {
    freight: number;
    bunker: number;
    port: number;
    time: number;
    delay: number;
    repositioning: number;
    other: number;
  };
  total_cost: number;
  cost_per_mt: number;
  assumptions?: string;
  data_status: DataStatusType;
}

export interface EconomicDataQualityItem {
  field: string;
  value: string;
  status: string;
  source: string;
  confidence_impact: string;
}

export interface EconomicDataQualityReport {
  overall_confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  items: EconomicDataQualityItem[];
  limitations_explanation: string;
}

export interface BunkerPriceResponse {
  port_name: string;
  fuel_grade: string;
  price_usd_per_mt: number;
  description: string;
  source: string;
  observed_at: string;
  data_status: string;
}

export interface BunkerCalculationResponse {
  distance_nm?: number;
  speed_knots?: number;
  sailing_hours: number;
  sailing_days: number;
  sea_consumption_mtpd?: number;
  port_days: number;
  port_consumption_mtpd?: number;
  fuel_consumed_mt?: number;
  bunker_price_usd_per_mt?: number;
  bunker_cost_usd?: number;
  fuel_grade: string;
  hub_location: string;
  source?: string;
  data_status: DataStatusType;
  is_calculable: boolean;
  explanation: string;
}

export interface SpeedBreakEvenStep {
  from_speed_knots: number;
  to_speed_knots: number;
  time_saved_hours: number;
  time_saved_days: number;
  time_value_saved_usd: number;
  delta_fuel_consumed_mt: number;
  delta_bunker_cost_usd: number;
  net_marginal_gain_usd: number;
  recommendation: string;
}

export interface SpeedBreakEvenResponse {
  is_evaluable: boolean;
  break_even_speed_knots?: number;
  economic_speed_range_min?: number;
  economic_speed_range_max?: number;
  marginal_steps: SpeedBreakEvenStep[];
  daily_charter_rate_usd?: number;
  bunker_price_usd_per_mt?: number;
  data_status: DataStatusType;
  verdict: string;
  explanation: string;
}

export interface SensitivityAnalysisResponse {
  baseline: Record<string, any>;
  bunker_sensitivity: Array<{
    delta_pct: string;
    bunker_price_usd: number;
    total_cost_usd: number;
    cost_per_mt: number;
    bunker_cost_usd: number;
    delta_total_usd: number;
  }>;
  freight_sensitivity: Array<{
    freight_rate_usd_per_mt: number;
    total_cost_usd: number;
    cost_per_mt: number;
    freight_cost_usd: number;
    delta_total_usd: number;
  }>;
  speed_sensitivity: Array<{
    speed_knots: number;
    sailing_days: number;
    bunker_cost_usd: number;
    time_cost_usd: number;
    total_cost_usd: number;
    cost_per_mt: number;
    delta_total_usd: number;
  }>;
  delay_sensitivity: Array<{
    delay_hours: number;
    delay_cost_usd: number;
    time_cost_usd: number;
    total_cost_usd: number;
    cost_per_mt: number;
    delta_total_usd: number;
  }>;
  cargo_sensitivity: Array<{
    cargo_quantity_mt: number;
    total_cost_usd: number;
    cost_per_mt: number;
    freight_cost_usd: number;
    delta_cost_per_mt: number;
  }>;
  hire_rate_sensitivity: Array<{
    daily_charter_rate_usd: number;
    time_cost_usd: number;
    total_cost_usd: number;
    cost_per_mt: number;
    delta_total_usd: number;
  }>;
  data_status: DataStatusType;
}

export interface VoyageEconomicsAnalysisResponse {
  id: string;
  origin_port_id: string;
  origin_port_name: string;
  origin_unlocode: string;
  destination_port_id: string;
  destination_port_name: string;
  destination_unlocode: string;
  distance_nm: number;
  cargo_quantity_mt: number;
  cargo_type: string;
  vessel_id?: string;
  vessel_name: string;
  vessel_class: string;
  operating_speed_knots: number;
  sailing_days: number;
  total_voyage_days: number;

  freight_cost_usd: number;
  freight_rate_usd_per_mt: number;
  bunker_cost_usd: number;
  bunker_price_usd_per_mt: number;
  port_cost_usd: number;
  time_cost_usd: number;
  daily_charter_rate_usd: number;
  delay_cost_usd: number;
  demurrage_hours: number;
  repositioning_cost_usd: number;
  other_cost_usd: number;
  total_voyage_cost_usd: number;
  cost_per_mt_usd: number;
  currency: string;
  data_status: DataStatusType;

  components: CostComponentItem[];
  scenarios: VoyageScenarioItem[];
  speed_analysis: {
    distance_nm: number;
    cargo_quantity_mt: number;
    baseline_speed_knots?: number;
    baseline_consumption_mtpd?: number;
    bunker_price_usd_per_mt?: number;
    daily_charter_rate_usd?: number;
    scenarios: SpeedScenarioItem[];
    can_determine_optimum: boolean;
    economically_preferred_speed_knots?: number;
    min_total_cost_usd?: number;
    verdict_label: string;
    data_status: DataStatusType;
    explanation: string;
  };
  break_even: SpeedBreakEvenResponse;
  sensitivity: SensitivityAnalysisResponse;
  data_quality_report: EconomicDataQualityReport;
  explanation: string;
}

export interface VoyageEconomicsAnalysisRequest {
  origin_port_id?: string;
  destination_port_id?: string;
  cargo_quantity_mt?: number;
  cargo_type?: string;
  vessel_id?: string;
  cargo_request_id?: string;
  voyage_id?: string;
  custom_speed_knots?: number;
  custom_freight_rate_usd_per_mt?: number;
  custom_bunker_price_usd_per_mt?: number;
  custom_daily_hire_usd?: number;
  congestion_delay_hours?: number;
  weather_delay_hours?: number;
  tidal_delay_hours?: number;
  laytime_allowed_hours?: number;
  demurrage_rate_usd_per_day?: number;
  ballast_distance_nm?: number;
  idle_days?: number;
}

// ----------------------------------------------------
// API Client
// ----------------------------------------------------

export const economicsApi = {
  // Master Voyage Economics
  analyzeVoyage: async (payload: VoyageEconomicsAnalysisRequest): Promise<VoyageEconomicsAnalysisResponse> => {
    return apiClient<VoyageEconomicsAnalysisResponse>('/api/v1/voyage-economics/analyze', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  getLatestAnalysis: async (): Promise<VoyageEconomicsAnalysisResponse> => {
    return apiClient<VoyageEconomicsAnalysisResponse>('/api/v1/voyage-economics/latest');
  },

  getAnalysisById: async (analysisId: string): Promise<VoyageEconomicsAnalysisResponse> => {
    return apiClient<VoyageEconomicsAnalysisResponse>(`/api/v1/voyage-economics/${analysisId}`);
  },

  getComponents: async (analysisId: string): Promise<CostComponentItem[]> => {
    return apiClient<CostComponentItem[]>(`/api/v1/voyage-economics/${analysisId}/components`);
  },

  getScenarios: async (analysisId: string): Promise<VoyageScenarioItem[]> => {
    return apiClient<VoyageScenarioItem[]>(`/api/v1/voyage-economics/${analysisId}/scenarios`);
  },

  getSpeedScenarios: async (analysisId: string): Promise<SpeedScenarioItem[]> => {
    return apiClient<SpeedScenarioItem[]>(`/api/v1/voyage-economics/${analysisId}/speed-scenarios`);
  },

  calculateSensitivity: async (params: {
    distance_nm: number;
    base_cargo_quantity_mt?: number;
    base_freight_rate_usd_per_mt?: number;
    base_bunker_price_usd_per_mt?: number;
    base_speed_knots?: number;
    base_daily_charter_rate_usd?: number;
    base_port_cost_usd?: number;
    base_port_delay_hours?: number;
    baseline_consumption_mtpd?: number;
    baseline_speed_knots?: number;
    laytime_allowed_hours?: number;
    demurrage_rate_usd_per_day?: number;
  }): Promise<SensitivityAnalysisResponse> => {
    return apiClient<SensitivityAnalysisResponse>('/api/v1/voyage-economics/sensitivity', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  },

  // Bunker Fuel
  calculateBunker: async (params: {
    distance_nm: number;
    speed_knots: number;
    consumption_mtpd?: number;
    bunker_price_usd_per_mt?: number;
    port_days?: number;
    port_consumption_mtpd?: number;
    fuel_grade?: string;
    hub_location?: string;
  }): Promise<BunkerCalculationResponse> => {
    return apiClient<BunkerCalculationResponse>('/api/v1/bunker/calculate', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  },

  getBunkerPrices: async (): Promise<BunkerPriceResponse[]> => {
    return apiClient<BunkerPriceResponse[]>('/api/v1/bunker/prices');
  },

  // Speed Optimization
  analyzeSpeed: async (params: {
    distance_nm: number;
    cargo_quantity_mt?: number;
    baseline_speed_knots?: number;
    baseline_consumption_mtpd?: number;
    bunker_price_usd_per_mt?: number;
    daily_charter_rate_usd?: number;
    port_cost_usd?: number;
    candidate_speeds?: number[];
  }): Promise<any> => {
    return apiClient<any>('/api/v1/speed/analyze', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  },

  calculateBreakEven: async (params: {
    distance_nm: number;
    cargo_quantity_mt?: number;
    baseline_speed_knots?: number;
    baseline_consumption_mtpd?: number;
    bunker_price_usd_per_mt?: number;
    daily_charter_rate_usd?: number;
  }): Promise<SpeedBreakEvenResponse> => {
    return apiClient<SpeedBreakEvenResponse>('/api/v1/speed/break-even', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  }
};
