import { apiClient } from './client';

export interface BerthConstraint {
  id: string;
  constraint_type: string;
  parameter_name: string;
  limit_value: number;
  unit: string;
  severity: string;
  condition_description?: string;
}

export interface Berth {
  id: string;
  port_id: string;
  berth_code: string;
  berth_name: string;
  berth_type: string;
  max_loa_m?: number;
  max_beam_m?: number;
  max_draft_m?: number;
  max_air_draft_m?: number;
  max_dwt?: number;
  discharge_rate_tpd?: number;
  loading_rate_tpd?: number;
  equipment_summary?: string;
  night_berthing: boolean;
  constraints?: BerthConstraint[];
}

export interface PortConstraint {
  id: string;
  port_id: string;
  constraint_type: string;
  parameter_name: string;
  limit_value: number;
  unit: string;
  severity: string;
  condition_description?: string;
}

export interface PortDataSource {
  id: string;
  source_name: string;
  source_type: string;
  doc_reference?: string;
  publication_date?: string;
  verified: boolean;
  verified_by?: string;
}

export interface Port {
  id: string;
  unlocode: string;
  name: string;
  country: string;
  coast?: string;
  latitude: number;
  longitude: number;
  channel_max_draft_m?: number;
  channel_max_loa_m?: number;
  channel_max_beam_m?: number;
  tide_range_m?: number;
  night_navigation: boolean;
  tug_requirement_count: number;
  notes?: string;
}

export interface PortDetail extends Port {
  berths: Berth[];
  constraints: PortConstraint[];
  data_sources: PortDataSource[];
}

export const portsApi = {
  getPorts: () => apiClient<Port[]>('/ports'),
  getPortDetail: (portId: string) => apiClient<PortDetail>(`/ports/${portId}`),
  getPortBerths: (portId: string) => apiClient<Berth[]>(`/ports/${portId}/berths`),
};
