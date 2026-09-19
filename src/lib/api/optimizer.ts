import { apiClient } from './client';
import { Port, Berth } from './ports';
import { Vessel } from './vessels';

export interface FeasibilityRuleEvaluation {
  rule_name: string;
  status: 'PASS' | 'CONDITIONAL' | 'FAIL' | 'UNKNOWN';
  limit_value?: number;
  vessel_value?: number;
  unit: string;
  margin?: number;
  is_blocking: boolean;
  narrative: string;
}

export interface BerthFeasibilityResult {
  id: string;
  berth_id: string;
  berth?: Berth;
  status: 'PASS' | 'CONDITIONAL' | 'FAIL' | 'UNKNOWN';
  draft_clearance_m?: number;
  loa_clearance_m?: number;
  beam_clearance_m?: number;
  estimated_turnaround_days?: number;
  summary_explanation: string;
  rule_evaluations: FeasibilityRuleEvaluation[];
}

export interface FeasibilityRun {
  id: string;
  vessel_id: string;
  port_id: string;
  vessel?: Vessel;
  port?: Port;
  run_timestamp: string;
  overall_status: 'PASS' | 'CONDITIONAL' | 'FAIL' | 'UNKNOWN';
  evaluated_berths_count: number;
  passing_berths_count: number;
  summary_narrative?: string;
  berth_results: BerthFeasibilityResult[];
}

export const optimizerApi = {
  evaluateFeasibility: (vesselId: string, portId: string, cargoQuantityMt?: number) =>
    apiClient<FeasibilityRun>('/optimizer/evaluate', {
      method: 'POST',
      body: JSON.stringify({
        vessel_id: vesselId,
        port_id: portId,
        cargo_quantity_mt: cargoQuantityMt,
      }),
    }),
  getLatestFeasibility: (vesselId: string, portId: string) =>
    apiClient<FeasibilityRun>(`/optimizer/vessels/${vesselId}/ports/${portId}/latest`),
};
