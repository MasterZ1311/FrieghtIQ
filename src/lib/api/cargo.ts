import { apiClient } from './client';
import { Port } from './ports';

export interface CargoHandlingLog {
  id: string;
  requirement_id: string;
  vessel_id?: string;
  port_id: string;
  berth_id?: string;
  start_time: string;
  end_time?: string;
  quantity_handled_mt: number;
  average_rate_tpd?: number;
  remarks?: string;
}

export interface CargoRequirement {
  id: string;
  requirement_code: string;
  title: string;
  cargo_type: string;
  quantity_mt: number;
  tolerance_pct: number;
  load_port_id: string;
  discharge_port_id: string;
  load_port?: Port;
  discharge_port?: Port;
  laycan_start: string;
  laycan_end: string;
  target_freight_usd_pmt?: number;
  max_vessel_age_years: number;
  preferred_vessel_classes: string;
  gear_requirement: string;
  status: string;
  created_by: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface CargoRequirementDetail extends CargoRequirement {
  handling_logs: CargoHandlingLog[];
}

export interface CreateCargoRequirementInput {
  title: string;
  cargo_type: string;
  quantity_mt: number;
  tolerance_pct?: number;
  load_port_id: string;
  discharge_port_id: string;
  laycan_start: string;
  laycan_end: string;
  target_freight_usd_pmt?: number;
  max_vessel_age_years?: number;
  preferred_vessel_classes?: string;
  gear_requirement?: string;
  notes?: string;
}

export const cargoApi = {
  getRequirements: () => apiClient<CargoRequirement[]>('/cargo/requirements'),
  getRequirementDetail: (id: string) => apiClient<CargoRequirementDetail>(`/cargo/requirements/${id}`),
  createRequirement: (input: CreateCargoRequirementInput) =>
    apiClient<CargoRequirement>('/cargo/requirements', {
      method: 'POST',
      body: JSON.stringify(input),
    }),
};
