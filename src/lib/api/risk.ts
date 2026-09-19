import { apiClient } from './client';
import { DataStatusType } from './regime';

export type RiskType =
  | 'PORT_CONGESTION'
  | 'WEATHER'
  | 'TIDAL'
  | 'VESSEL'
  | 'PORT_OPERATION'
  | 'TIMING'
  | 'IDLE'
  | 'REPOSITIONING'
  | 'DATA_QUALITY';

export type RiskSeverity =
  | 'LOW'
  | 'MEDIUM'
  | 'HIGH'
  | 'CRITICAL'
  | 'UNKNOWN';

export type RiskStatus =
  | 'ACTIVE'
  | 'MONITORED'
  | 'MITIGATED'
  | 'RESOLVED'
  | 'EXPIRED'
  | 'SIMULATED';

export type TidalWindowStatus =
  | 'PASS'
  | 'CONDITIONAL'
  | 'FAIL'
  | 'UNKNOWN';

export type CongestionIndicator =
  | 'LOW'
  | 'MODERATE'
  | 'SEVERE'
  | 'CRITICAL'
  | 'UNKNOWN';

export interface WeatherObservation {
  id: string;
  port_id: string;
  port_name?: string;
  observed_at: string;
  temperature_c?: number;
  wind_speed_knots?: number;
  wind_direction_deg?: number;
  gust_speed_knots?: number;
  wave_height_m?: number;
  swell_height_m?: number;
  precipitation_mm?: number;
  visibility_km?: number;
  pressure_hpa?: number;
  cyclone_alert: boolean;
  cargo_handling_stoppage: boolean;
  data_source: string;
  is_synthetic: boolean;
  created_at?: string;
}

export interface WeatherForecastItem {
  port_id: string;
  port_name?: string;
  forecast_date: string;
  forecast_time: string;
  wind_speed_knots: number;
  gust_speed_knots?: number;
  wave_height_m: number;
  swell_height_m?: number;
  precipitation_mm: number;
  cyclone_alert: boolean;
  cargo_handling_stoppage: boolean;
  data_source: string;
  is_synthetic: boolean;
}

export interface WeatherEvaluationResponse {
  port_id: string;
  port_name?: string;
  severity: RiskSeverity;
  current_weather?: WeatherObservation;
  forecast: WeatherForecastItem[];
  handling_stoppage_risk: RiskSeverity;
  navigation_risk: RiskSeverity;
  estimated_weather_delay_hours: number;
  explanations: string[];
  mitigations: string[];
  data_source: string;
  is_synthetic: boolean;
}

export interface TidalWindow {
  id: string;
  port_id: string;
  port_name?: string;
  berth_id?: string;
  berth_name?: string;
  window_start: string;
  window_end: string;
  peak_water_time?: string;
  predicted_tide_height_m?: number;
  berth_depth_cd_m?: number;
  total_available_depth_m?: number;
  required_ukc_m: number;
  status: TidalWindowStatus;
  explanation?: string;
  data_source: string;
  created_at?: string;
}

export interface TidalEvaluationRequest {
  port_id: string;
  port_name?: string;
  berth_id?: string;
  vessel_draft_m?: number;
  berth_draft_m?: number;
  channel_draft_m?: number;
  required_ukc_m?: number;
  arrival_time?: string;
}

export interface TidalEvaluationResponse {
  status: TidalWindowStatus;
  vessel_draft_m?: number;
  berth_draft_m?: number;
  required_ukc_m?: number;
  required_depth_m?: number;
  available_depth_m?: number;
  ukc_margin_m?: number;
  high_water_slots: any[];
  recommended_window?: any;
  explanation: string;
  mitigation: string;
}

export interface PortCongestion {
  id: string;
  port_id: string;
  port_name?: string;
  snapshot_time: string;
  waiting_vessels_count: number;
  working_vessels_count: number;
  anchorage_vessels_count: number;
  berth_occupancy_pct: number;
  avg_waiting_hours: number;
  avg_turnaround_hours: number;
  congestion_indicator: CongestionIndicator;
  capesize_waiting_count: number;
  panamax_waiting_count: number;
  supramax_waiting_count: number;
  data_source: string;
  data_status: DataStatusType;
  created_at?: string;
}

export interface CongestionEvaluationResponse {
  port_id: string;
  port_name?: string;
  severity: RiskSeverity;
  indicator: CongestionIndicator;
  congestion_data?: PortCongestion;
  history: Array<{
    date: string;
    avg_waiting_hours: number;
    berth_occupancy_pct: number;
    waiting_vessels_count: number;
    data_source: string;
  }>;
  vessel_class: string;
  avg_wait_hours: number;
  laytime_allowed_hours: number;
  demurrage_exposure_usd?: number;
  demurrage_hours: number;
  explanations: string[];
  mitigations: string[];
  data_source: string;
  is_synthetic: boolean;
}

export interface RiskEvent {
  id: string;
  risk_type: RiskType;
  severity: RiskSeverity;
  status: RiskStatus;
  port_id?: string;
  port_name?: string;
  berth_id?: string;
  vessel_id?: string;
  vessel_name?: string;
  voyage_id?: string;
  title: string;
  description: string;
  trigger_source: string;
  occurred_at: string;
  expires_at?: string;
  financial_exposure_usd?: number;
  delay_hours_estimate?: number;
  mitigation_action?: string;
  data_status: DataStatusType;
  created_at?: string;
}

export interface UnifiedRiskSummaryResponse {
  total_active_events: number;
  critical_events_count: number;
  high_events_count: number;
  medium_events_count: number;
  low_events_count: number;
  overall_operational_severity: RiskSeverity;
  total_financial_exposure_usd: number;
  total_delay_hours: number;
  events: RiskEvent[];
  top_risk_ports: Array<{
    port_name: string;
    port_id?: string;
    count: number;
    max_severity: string;
  }>;
  provenance_breakdown: Record<string, number>;
}

export interface PortRiskEvaluationResponse {
  port_id: string;
  port_name?: string;
  overall_severity: RiskSeverity;
  primary_drivers: Array<{
    risk_type: string;
    severity: string;
    summary: string;
    mitigation: string;
  }>;
  financial_exposure: {
    total_exposure_usd: number;
    demurrage_exposure_usd: number;
    weather_delay_cost_usd: number;
    weather_delay_hours: number;
    idle_cost_usd: number;
  };
  total_delay_hours: number;
  components: {
    congestion: any;
    weather: any;
    tidal: any;
    operations: any;
  };
  explanations: string[];
  mitigations: string[];
}

export interface VoyageRiskEvaluationRequest {
  origin_port_id: string;
  origin_port_name?: string;
  destination_port_id: string;
  destination_port_name?: string;
  vessel_id?: string;
  vessel_name?: string;
  vessel_class?: string;
  vessel_draft_m?: number;
  origin_berth_draft_m?: number;
  destination_berth_draft_m?: number;
  cargo_type?: string;
  eta_origin?: string;
  laycan_from?: string;
  laycan_to?: string;
  charter_hire_usd_per_day?: number;
}

export interface VoyageRiskEvaluationResponse {
  origin_port: {
    id: string;
    name?: string;
    risk: PortRiskEvaluationResponse;
  };
  destination_port: {
    id: string;
    name?: string;
    risk: PortRiskEvaluationResponse;
  };
  timing_risk: any;
  data_quality: any;
  overall_severity: RiskSeverity;
  primary_drivers: Array<{
    risk_type: string;
    severity: string;
    summary: string;
    mitigation: string;
  }>;
  financial_exposure: {
    total_exposure_usd: number;
    demurrage_exposure_usd: number;
    weather_delay_cost_usd: number;
    weather_delay_hours: number;
    idle_cost_usd: number;
  };
  total_delay_hours: number;
  explanations: string[];
  mitigations: string[];
}

// ----------------------------------------------------
// API Client Calls
// ----------------------------------------------------

export const riskApi = {
  // Unified Risk Center
  getRiskSummary: async (): Promise<UnifiedRiskSummaryResponse> => {
    return apiClient<UnifiedRiskSummaryResponse>('/api/v1/risk');
  },

  getRiskEvents: async (params?: {
    severity?: string;
    risk_type?: string;
    status?: string;
    port_id?: string;
    vessel_id?: string;
    voyage_id?: string;
    limit?: number;
  }): Promise<RiskEvent[]> => {
    const query = new URLSearchParams();
    if (params?.severity) query.append('severity', params.severity);
    if (params?.risk_type) query.append('risk_type', params.risk_type);
    if (params?.status) query.append('status', params.status);
    if (params?.port_id) query.append('port_id', params.port_id);
    if (params?.vessel_id) query.append('vessel_id', params.vessel_id);
    if (params?.voyage_id) query.append('voyage_id', params.voyage_id);
    if (params?.limit) query.append('limit', params.limit.toString());
    const qs = query.toString();
    return apiClient<RiskEvent[]>(`/api/v1/risk/events${qs ? `?${qs}` : ''}`);
  },

  getRiskEventDetail: async (eventId: string): Promise<RiskEvent> => {
    return apiClient<RiskEvent>(`/api/v1/risk/events/${eventId}`);
  },

  updateRiskEventStatus: async (eventId: string, newStatus: RiskStatus): Promise<RiskEvent> => {
    return apiClient<RiskEvent>(`/api/v1/risk/events/${eventId}/status?new_status=${newStatus}`, {
      method: 'PATCH'
    });
  },

  analyzePortRisk: async (params: {
    port_id: string;
    port_name?: string;
    vessel_draft_m?: number;
    berth_draft_m?: number;
    cargo_type?: string;
    vessel_class?: string;
  }): Promise<PortRiskEvaluationResponse> => {
    const query = new URLSearchParams();
    query.append('port_id', params.port_id);
    if (params.port_name) query.append('port_name', params.port_name);
    if (params.vessel_draft_m !== undefined) query.append('vessel_draft_m', params.vessel_draft_m.toString());
    if (params.berth_draft_m !== undefined) query.append('berth_draft_m', params.berth_draft_m.toString());
    if (params.cargo_type) query.append('cargo_type', params.cargo_type);
    if (params.vessel_class) query.append('vessel_class', params.vessel_class);
    return apiClient<PortRiskEvaluationResponse>(`/api/v1/risk/analyze/port?${query.toString()}`, {
      method: 'POST'
    });
  },

  analyzeVoyageRisk: async (payload: VoyageRiskEvaluationRequest): Promise<VoyageRiskEvaluationResponse> => {
    return apiClient<VoyageRiskEvaluationResponse>('/api/v1/risk/analyze/voyage', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  // Port Congestion
  getAllPortCongestions: async (): Promise<PortCongestion[]> => {
    return apiClient<PortCongestion[]>('/api/v1/congestion/ports');
  },

  getPortCongestionDetail: async (
    portId: string,
    params?: {
      vessel_class?: string;
      laytime_hours?: number;
      demurrage_rate?: number;
    }
  ): Promise<CongestionEvaluationResponse> => {
    const query = new URLSearchParams();
    if (params?.vessel_class) query.append('vessel_class', params.vessel_class);
    if (params?.laytime_hours !== undefined) query.append('laytime_hours', params.laytime_hours.toString());
    if (params?.demurrage_rate !== undefined) query.append('demurrage_rate', params.demurrage_rate.toString());
    const qs = query.toString();
    return apiClient<CongestionEvaluationResponse>(`/api/v1/congestion/ports/${portId}${qs ? `?${qs}` : ''}`);
  },

  analyzeCongestion: async (params: {
    port_id: string;
    port_name?: string;
    vessel_class?: string;
    laytime_allowed_hours?: number;
    demurrage_rate_usd_per_day?: number;
  }): Promise<CongestionEvaluationResponse> => {
    const query = new URLSearchParams();
    query.append('port_id', params.port_id);
    if (params.port_name) query.append('port_name', params.port_name);
    if (params.vessel_class) query.append('vessel_class', params.vessel_class);
    if (params.laytime_allowed_hours !== undefined) query.append('laytime_allowed_hours', params.laytime_allowed_hours.toString());
    if (params.demurrage_rate_usd_per_day !== undefined) query.append('demurrage_rate_usd_per_day', params.demurrage_rate_usd_per_day.toString());
    return apiClient<CongestionEvaluationResponse>(`/api/v1/congestion/analyze?${query.toString()}`, {
      method: 'POST'
    });
  },

  // Weather Risk
  getPortWeather: async (portId: string, cargoType?: string): Promise<WeatherEvaluationResponse> => {
    const query = new URLSearchParams();
    if (cargoType) query.append('cargo_type', cargoType);
    const qs = query.toString();
    return apiClient<WeatherEvaluationResponse>(`/api/v1/weather/ports/${portId}${qs ? `?${qs}` : ''}`);
  },

  analyzeWeather: async (params: {
    port_id: string;
    port_name?: string;
    cargo_type?: string;
  }): Promise<WeatherEvaluationResponse> => {
    const query = new URLSearchParams();
    query.append('port_id', params.port_id);
    if (params.port_name) query.append('port_name', params.port_name);
    if (params.cargo_type) query.append('cargo_type', params.cargo_type);
    return apiClient<WeatherEvaluationResponse>(`/api/v1/weather/analyze?${query.toString()}`, {
      method: 'POST'
    });
  },

  // Tidal Gate Scheduler
  getPortTidalWindows: async (portId: string): Promise<TidalWindow[]> => {
    return apiClient<TidalWindow[]>(`/api/v1/tidal/ports/${portId}`);
  },

  getBerthTidalWindows: async (berthId: string): Promise<TidalWindow[]> => {
    return apiClient<TidalWindow[]>(`/api/v1/tidal/berths/${berthId}`);
  },

  evaluateTidalGate: async (payload: TidalEvaluationRequest): Promise<TidalEvaluationResponse> => {
    return apiClient<TidalEvaluationResponse>('/api/v1/tidal/evaluate', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }
};
