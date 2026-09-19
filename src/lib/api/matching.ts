import { apiClient } from './client';
import { Vessel } from './vessels';

export interface MatchingRuleResult {
  rule_name: string;
  rule_category: string;
  status: 'RELEVANT' | 'PARTIAL' | 'NOT_RELEVANT' | 'UNKNOWN';
  evaluated_value?: string;
  required_value?: string;
  explanation: string;
  is_blocking: boolean;
}

export interface MatchingCandidate {
  id: string;
  vessel_id: string;
  vessel?: Vessel;
  overall_status: 'RELEVANT' | 'PARTIAL' | 'NOT_RELEVANT' | 'UNKNOWN';
  summary_explanation: string;
  is_data_complete: boolean;
  missing_fields?: string;
  rule_results: MatchingRuleResult[];
}

export interface MatchingRun {
  id: string;
  requirement_id: string;
  run_timestamp: string;
  total_evaluated: number;
  relevant_count: number;
  partial_count: number;
  not_relevant_count: number;
  unknown_count: number;
  candidates: MatchingCandidate[];
}

export const matchingApi = {
  evaluate: (requirementId: string, candidateVesselIds?: string[]) =>
    apiClient<MatchingRun>('/matching/evaluate', {
      method: 'POST',
      body: JSON.stringify({
        requirement_id: requirementId,
        candidate_vessel_ids: candidateVesselIds,
      }),
    }),
  getLatestForRequirement: (requirementId: string) =>
    apiClient<MatchingRun>(`/matching/requirements/${requirementId}/latest`),
};
