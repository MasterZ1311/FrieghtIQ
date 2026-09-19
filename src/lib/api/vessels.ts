import { apiClient } from './client';

export interface VesselParticulars {
  summer_dwt?: number;
  summer_draft_m?: number;
  loa_m?: number;
  beam_m?: number;
  depth_m?: number;
  gross_tonnage?: number;
  net_tonnage?: number;
  grain_capacity_cbm?: number;
  bale_capacity_cbm?: number;
  holds_hatches_count?: string;
  gear_summary?: string;
  speed_ballast_knots?: number;
  speed_laden_knots?: number;
  consumption_laden_mtpd?: number;
  is_verified: boolean;
  unverified_fields?: string;
}

export interface VesselAvailability {
  current_status: string;
  current_latitude?: number;
  current_longitude?: number;
  current_port_name?: string;
  destination_port_name?: string;
  open_port_name?: string;
  open_date_start?: string;
  open_date_end?: string;
  eta_open_port?: string;
  data_confidence: string;
  source_evidence: string;
}

export interface OperationalSnapshotRecord {
  snapshot_vessel_name: string;
  observed_handled_cargo_mt: number;
  cargo_type: string;
  discharge_port_code: string;
  discharge_berth_code?: string;
  observation_date: string;
  data_integrity_note: string;
}

export interface Vessel {
  id: string;
  imo_number: string;
  vessel_name: string;
  vessel_class: string;
  flag?: string;
  year_built?: number;
  call_sign?: string;
  classification_society?: string;
  is_snapshot_vessel: boolean;
  particulars?: VesselParticulars;
  availability?: VesselAvailability;
}

export interface VesselDetail extends Vessel {
  snapshot_records: OperationalSnapshotRecord[];
}

export interface VesselFilterQuery {
  vessel_class?: string;
  status?: string;
  is_snapshot?: boolean;
}

export const vesselsApi = {
  getVessels: (params?: VesselFilterQuery) => {
    const query = new URLSearchParams();
    if (params?.vessel_class) query.append('vessel_class', params.vessel_class);
    if (params?.status) query.append('status', params.status);
    if (params?.is_snapshot !== undefined) query.append('is_snapshot', String(params.is_snapshot));
    const qs = query.toString();
    return apiClient<Vessel[]>(`/vessels${qs ? `?${qs}` : ''}`);
  },
  getVesselDetail: (vesselId: string) => apiClient<VesselDetail>(`/vessels/${vesselId}`),
};
