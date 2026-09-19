import { apiClient } from './client';
import { DecisionConfidence } from './wait_fix';
import { DataStatusType } from './regime';

export type VesselEmploymentState =
  | 'EMPLOYED'
  | 'VOYAGE_COMPLETING'
  | 'AVAILABLE'
  | 'NEXT_EMPLOYMENT_PENDING'
  | 'IDLE_RISK'
  | 'IDLE'
  | 'REPOSITIONING'
  | 'ALTERNATIVE_EMPLOYMENT'
  | 'UNKNOWN';

export type EmploymentEventType =
  | 'VOYAGE_TRANSIT'
  | 'DISCHARGE'
  | 'LOAD'
  | 'ANCHORAGE_WAIT'
  | 'BALLAST_REPOSITION'
  | 'MAINTENANCE';

export type IdleScenarioType =
  | 'EARLY_ARRIVAL'
  | 'EMPLOYMENT_GAP'
  | 'PORT_DELAY'
  | 'REPOSITIONING_GAP'
  | 'DEMAND_GAP'
  | 'UNKNOWN';

export type RepositioningDecision =
  | 'REPOSITION'
  | 'DO_NOT_REPOSITION'
  | 'UNKNOWN';

export type DeadheadRiskLevel =
  | 'LOW'
  | 'MEDIUM'
  | 'HIGH'
  | 'UNKNOWN';

export interface FleetIdleOverview {
  dataset_coverage_count: number;
  active_vessels_count: number;
  idle_risk_count: number;
  currently_idle_count: number;
  repositioning_count: number;
  unknown_state_count: number;
  dataset_coverage_label: string;
  data_provenance: {
    source: string;
    disclaimer: string;
    integrity_policy: string;
  };
}

export interface VesselEmploymentSummary {
  vessel_id: string;
  vessel_name: string;
  vessel_class: string;
  current_location: string;
  current_voyage: string;
  current_status: string;
  employment_state: VesselEmploymentState;
  state_explanation: string;
  estimated_availability?: string | null;
  next_known_employment?: string | null;
  estimated_next_employment_at?: string | null;
  idle_days?: number | null;
  idle_exposure_label: string;
  idle_risk_level: string;
  idle_cost?: number | null;
  daily_cost_label: string;
  is_data_complete: boolean;
  data_confidence: DecisionConfidence;
  data_status: DataStatusType;
  last_updated?: string | null;
}

export interface FleetIdleStatusResponse {
  overview: FleetIdleOverview;
  vessels: VesselEmploymentSummary[];
}

export interface VesselEmploymentEvent {
  id: string;
  vessel_id: string;
  event_type: EmploymentEventType;
  voyage_id?: string | null;
  cargo_request_id?: string | null;
  origin_port_id?: string | null;
  origin_port_name?: string | null;
  destination_port_id?: string | null;
  destination_port_name?: string | null;
  event_start: string;
  event_end?: string | null;
  status: string;
  source_id?: string | null;
  data_status: DataStatusType;
}

export interface IdleScenario {
  id: string;
  vessel_id: string;
  vessel_name?: string | null;
  vessel_class?: string | null;
  voyage_id?: string | null;
  scenario_type: IdleScenarioType;
  current_location: string;
  next_known_employment?: string | null;
  estimated_available_at?: string | null;
  estimated_next_employment_at?: string | null;
  idle_days?: number | null;
  idle_cost?: number | null;
  confidence: DecisionConfidence;
  data_status: DataStatusType;
  created_at: string;
  updated_at: string;
}

export interface RepositioningOption {
  id: string;
  idle_scenario_id?: string | null;
  vessel_id: string;
  vessel_name?: string | null;
  target_port_id: string;
  target_port_name?: string | null;
  target_cargo_request_id?: string | null;
  cargo_name?: string | null;
  cargo_quantity_mt?: number | null;
  distance: number;
  distance_method: string;
  estimated_sailing_days: number;
  estimated_bunker_cost?: number | null;
  estimated_total_cost?: number | null;
  port_compatibility: string;
  timing_compatibility: string;
  status: RepositioningDecision;
  data_status: DataStatusType;
  created_at: string;
}

export interface AlternativeEmploymentCandidate {
  cargo_id: string;
  cargo_name: string;
  quantity_mt: number;
  origin_port_id: string;
  origin_port_name: string;
  destination_port_id: string;
  destination_port_name: string;
  laycan_start?: string | null;
  laycan_end?: string | null;
  compatibility_status: 'COMPATIBLE' | 'PARTIAL' | 'NOT_COMPATIBLE' | 'UNKNOWN';
  matching_status: string;
  origin_port_status: string;
  destination_port_status: string;
  repositioning_required: boolean;
  repositioning_distance_nm?: number | null;
  distance_method: string;
  matching_summary: string;
  port_validation_summary: string;
  is_data_complete: boolean;
  missing_fields?: string | null;
  data_status: string;
}

export interface RepositioningEconomicsComparison {
  vessel_name: string;
  comparison_status: string;
  data_confidence: string;
  revenue_status: string;
  wait_strategy: {
    strategy_name: string;
    idle_days?: number | null;
    repositioning_days: number;
    distance_nm: number;
    distance_method: string;
    bunker_cost: number;
    daily_cost?: number | null;
    estimated_total_cost?: number | null;
    cost_status: string;
    summary: string;
  };
  repositioning_strategies: Array<{
    strategy_name: string;
    idle_days: number;
    repositioning_days: number;
    distance_nm: number;
    distance_method: string;
    bunker_cost?: number | null;
    daily_cost?: number | null;
    estimated_total_cost?: number | null;
    cost_status: string;
    summary: string;
  }>;
  recommendation_note: string;
}

export interface IdleAnalysisResponse {
  vessel_id: string;
  vessel_name: string;
  vessel_class: string;
  current_location: string;
  estimated_availability?: string | null;
  next_known_employment?: string | null;
  estimated_next_employment_at?: string | null;
  idle_days?: number | null;
  idle_narrative: string;
  daily_vessel_cost?: number | null;
  daily_cost_status: string;
  idle_cost?: number | null;
  idle_cost_narrative: string;
  alternative_candidates: AlternativeEmploymentCandidate[];
  repositioning_options: Array<{
    vessel_id: string;
    target_port_id: string;
    target_port_name: string;
    target_cargo_request_id?: string | null;
    cargo_name: string;
    distance_nm?: number | null;
    distance_method: string;
    speed_knots?: number | null;
    speed_label: string;
    sailing_days?: number | null;
    estimated_eta?: string | null;
    port_compatibility: string;
    timing_compatibility: string;
    timing_narrative: string;
    estimated_bunker_cost?: number | null;
    bunker_narrative: string;
    estimated_total_cost?: number | null;
    decision: string;
    recommendation_reason: string;
    deadhead_risk: DeadheadRiskLevel;
    deadhead_narrative: string;
    candidate_compatibility: string;
    data_status: string;
  }>;
  economics_comparison: RepositioningEconomicsComparison;
  data_provenance: {
    vessel_data_complete: boolean;
    source: string;
    distance_methodology: string;
  };
}

export interface VesselEmploymentTimelineResponse {
  vessel_id: string;
  vessel_name: string;
  vessel_class: string;
  employment_state: VesselEmploymentState;
  current_location: string;
  current_status: string;
  is_verified_particulars: boolean;
  estimated_availability?: string | null;
  next_known_employment?: string | null;
  estimated_next_employment_at?: string | null;
  idle_days?: number | null;
  idle_cost?: number | null;
  data_status: DataStatusType;
  data_freshness_label: string;
  events: VesselEmploymentEvent[];
  active_scenario?: IdleScenario | null;
  repositioning_options: RepositioningOption[];
}

export const idleApi = {
  getFleetStatus: async (): Promise<FleetIdleStatusResponse> => {
    return apiClient<FleetIdleStatusResponse>('/idle/vessels');
  },

  getScenarios: async (): Promise<IdleScenario[]> => {
    return apiClient<IdleScenario[]>('/idle/scenarios');
  },

  getScenarioById: async (id: string): Promise<IdleScenario> => {
    return apiClient<IdleScenario>(`/idle/scenarios/${id}`);
  },

  analyzeVessel: async (payload: {
    vessel_id: string;
    daily_vessel_cost_assumption?: number;
    scenario_type?: IdleScenarioType;
  }): Promise<IdleAnalysisResponse> => {
    return apiClient<IdleAnalysisResponse>('/idle/analyze', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  analyzeRepositioningRoute: async (payload: {
    vessel_id: string;
    target_port_id: string;
    target_cargo_request_id?: string;
    speed_assumption_knots?: number;
    bunker_price_usd?: number;
    daily_vessel_cost_assumption?: number;
  }): Promise<Record<string, unknown>> => {
    return apiClient<Record<string, unknown>>('/repositioning/analyze', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getRepositioningOptions: async (vesselId: string): Promise<RepositioningOption[]> => {
    return apiClient<RepositioningOption[]>(`/repositioning/${vesselId}/options`);
  },

  getVesselTimeline: async (vesselId: string): Promise<VesselEmploymentTimelineResponse> => {
    return apiClient<VesselEmploymentTimelineResponse>(`/vessels/${vesselId}/employment-timeline`);
  },
};
