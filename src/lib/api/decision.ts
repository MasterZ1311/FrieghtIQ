import { apiClient } from './client';

export type DecisionPipelineState =
  | 'DRAFT'
  | 'VALIDATING'
  | 'VESSEL_ANALYSIS'
  | 'PORT_ANALYSIS'
  | 'FREIGHT_ANALYSIS'
  | 'MARKET_ANALYSIS'
  | 'DECISION_ANALYSIS'
  | 'CONTRACT_ANALYSIS'
  | 'RISK_ANALYSIS'
  | 'ECONOMIC_ANALYSIS'
  | 'READY'
  | 'PARTIAL'
  | 'BLOCKED'
  | 'FAILED';

export type DecisionReadinessStatus = 'READY' | 'CONDITIONAL' | 'PARTIAL' | 'BLOCKED';

export interface DataQualitySummary {
  status: DecisionReadinessStatus;
  score: number;
  checks_performed: number;
  passed_checks: number;
  failed_checks: number;
  warnings_count: number;
  issues: Array<{
    field: string;
    severity: string;
    message: string;
    status: string;
  }>;
  explanation: string;
}

export interface DecisionReadiness {
  status: DecisionReadinessStatus;
  score: number;
  summary: string;
  evidence_matrix: Record<string, string>;
  gaps: Array<{
    module: string;
    description: string;
    impact: string;
  }>;
  commercial_caveats: string[];
}

export interface TimelineStage {
  stage: string;
  label: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'PARTIAL' | 'FAILED' | 'SKIPPED';
  duration_ms: number;
  completed_at: string;
  details?: Record<string, any>;
}

export interface VoyageDecisionContext {
  cargo_id: string;
  voyage_id: string;
  vessel_id?: string | null;
  origin_port_id: string;
  destination_port_id: string;
  analysis_run_id: string;
  decision_id: string;
  context_version: string;
  dataset_version: string;
  pipeline_state: DecisionPipelineState;
  is_partial: boolean;
  unavailable_modules: string[];
  cargo: {
    id: string;
    requirement_code: string;
    commodity: string;
    quantity_mt: number;
    laycan_start: string;
    laycan_end: string;
    load_port_name: string;
    discharge_port_name: string;
    data_status: string;
  };
  route: {
    origin_port_id: string;
    origin_port_name: string;
    destination_port_id: string;
    destination_port_name: string;
    distance_nm: number;
    corridor: string;
    data_status: string;
  };
  vessel?: {
    id: string;
    name: string;
    imo: string;
    vessel_class: string;
    dwt: number;
    draft_m: number;
    beam_m: number;
    loa_m: number;
    speed_laden_knots: number;
    speed_ballast_knots: number;
    consumption_laden_mtpd: number;
    match_score: number;
    match_status: string;
    match_summary: string;
    data_status: string;
  } | null;
  ports: {
    evaluated_berths: number;
    feasibility_status: string;
    summary: string;
    data_status: string;
  };
  forecast: {
    target_date: string;
    p10: number;
    p50: number;
    p90: number;
    volatility_score: number;
    model_version: string;
    data_status: string;
  };
  regime: {
    regime: string;
    probabilities: Record<string, number>;
    description: string;
    model_version: string;
    data_status: string;
  };
  wait_fix: {
    decision: string;
    recommendation: string;
    expected_savings_usd: number;
    confidence: string;
    rationale: string;
    data_status: string;
  };
  contract: {
    recommended_strategy: string;
    expected_total_expenditure_usd: number;
    risk_score: number;
    rationale: string;
    data_status: string;
  };
  idle: {
    recommendation: string;
    expected_wait_days: number;
    ballast_nm: number;
    cost_impact_usd: number;
    data_status: string;
  };
  risk: {
    overall_severity: string;
    active_risks_count: number;
    congestion_indicator: string;
    avg_queue_days: number;
    weather_severity: string;
    tidal_status: string;
    safe_ukc_m: number;
    financial_exposure_usd: number;
    data_status: string;
  };
  economics: {
    total_voyage_cost_usd: number;
    cost_per_mt_usd: number;
    distance_nm: number;
    freight_cost_usd: number;
    bunker_cost_usd: number;
    port_cost_usd: number;
    time_cost_usd: number;
    delay_cost_usd: number;
    repositioning_cost_usd: number;
    currency: string;
    data_status: string;
  };
  data_quality: DataQualitySummary;
  decision_readiness: DecisionReadiness;
  timeline: TimelineStage[];
  generated_at: string;
  completed_at: string;
  model_versions: Record<string, string>;
  dataset_versions: Record<string, string>;
}

export interface AnalysisRunSchema {
  id: string;
  decision_id: string;
  cargo_id: string;
  voyage_id: string;
  vessel_id?: string | null;
  status: DecisionPipelineState;
  stage: string;
  execution_time_ms: number;
  error?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface AnalysisRunDetailSchema extends AnalysisRunSchema {
  context_version: string;
  model_versions?: Record<string, string> | null;
  dataset_versions?: Record<string, string> | null;
  inputs?: Record<string, any> | null;
  outputs?: Record<string, any> | null;
  data_quality?: DataQualitySummary | null;
  readiness?: DecisionReadiness | null;
  timeline?: TimelineStage[] | null;
}

export interface ExecutiveDashboardSummarySchema {
  active_cargo_requests_count: number;
  pending_decisions_count: number;
  matched_vessels_count: number;
  high_risk_voyages_count: number;
  partial_analyses_count: number;
  primary_decision?: VoyageDecisionContext | null;
  market_overview: {
    regime: string;
    p50_rate: number;
    route: string;
    trend: string;
  };
  operations_overview: {
    congestion: string;
    queue_days: number;
    tidal_window: string;
    weather_status: string;
  };
  economics_overview: {
    cost_per_mt: number;
    total_cost: number;
    bunker_benchmark: string;
  };
  audit_events_recent: Array<{
    action: string;
    entity: string;
    user: string;
    timestamp: string;
  }>;
}

export interface VoyageDecisionReportSchema {
  report_id: string;
  decision_id: string;
  analysis_run_id: string;
  title: string;
  classification: string;
  generated_at: string;
  user_id: string;
  executive_summary: string;
  cargo_requirement: Record<string, any>;
  vessel_analysis: Record<string, any>;
  port_feasibility: Record<string, any>;
  freight_forecast: Record<string, any>;
  market_regime: Record<string, any>;
  wait_fix_analysis: Record<string, any>;
  contract_strategy: Record<string, any>;
  idle_repositioning: Record<string, any>;
  operational_risk: Record<string, any>;
  voyage_economics: Record<string, any>;
  data_quality_assessment: Record<string, any>;
  decision_readiness: Record<string, any>;
  assumptions: string[];
  sources: Array<{
    domain: string;
    source: string;
    status: string;
  }>;
  signoff_block: {
    prepared_by: string;
    commercial_directorate: string;
    cag_cvc_compliance_note: string;
  };
}

export interface AdminDataHealthSchema {
  total_adapters: number;
  online_count: number;
  adapters: Array<{
    name: string;
    category: string;
    status: string;
    source_type: string;
    last_ingestion: string;
    record_count: number;
    freshness: string;
    errors_count: number;
    version: string;
    description: string;
  }>;
}

export interface AdminModelHealthSchema {
  total_models: number;
  models: Array<{
    name: string;
    version: string;
    dataset: string;
    dataset_version: string;
    status: string;
    last_training: string;
    last_prediction: string;
    mae?: number;
    rmse?: number;
    mape?: string;
    pinball_loss?: number;
    coverage_90?: string;
    model_type: string;
    log_likelihood?: number;
    regime_states?: number;
    convergence?: string;
  }>;
}

export interface AuditLogSchema {
  id: string;
  user_id: string;
  action: string;
  entity_type: string;
  entity_id: string;
  details?: Record<string, any> | null;
  created_at: string;
}

// ==========================================
// API CLIENT CALLS
// ==========================================

export async function runDecisionAnalysis(params: {
  cargo_id: string;
  vessel_id?: string;
  voyage_id?: string;
  user_id?: string;
  origin_port_id?: string;
  destination_port_id?: string;
}): Promise<VoyageDecisionContext> {
  return apiClient<VoyageDecisionContext>('/decision/analyze', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function getDecisionContext(decisionIdOrCargoId: string): Promise<VoyageDecisionContext> {
  return apiClient<VoyageDecisionContext>(`/decision/${decisionIdOrCargoId}`);
}

export async function listAnalysisRuns(limit: number = 20, offset: number = 0): Promise<AnalysisRunSchema[]> {
  return apiClient<AnalysisRunSchema[]>(`/decision/runs?limit=${limit}&offset=${offset}`);
}

export async function getAnalysisRunDetail(runId: string): Promise<AnalysisRunDetailSchema> {
  return apiClient<AnalysisRunDetailSchema>(`/decision/runs/${runId}`);
}

export async function generateDecisionReport(
  decisionId: string,
  userId: string = 'SAIL-COMMERCIAL-OFFICER'
): Promise<VoyageDecisionReportSchema> {
  return apiClient<VoyageDecisionReportSchema>(
    `/decision/reports/generate?decision_id=${encodeURIComponent(decisionId)}&user_id=${encodeURIComponent(userId)}`,
    { method: 'POST' }
  );
}

export async function getDashboardSummary(): Promise<ExecutiveDashboardSummarySchema> {
  return apiClient<ExecutiveDashboardSummarySchema>('/decision/dashboard/summary');
}

export async function getDataHealth(): Promise<AdminDataHealthSchema> {
  return apiClient<AdminDataHealthSchema>('/decision/health/data');
}

export async function getModelHealth(): Promise<AdminModelHealthSchema> {
  return apiClient<AdminModelHealthSchema>('/decision/health/models');
}

export async function getAuditTrail(limit: number = 50): Promise<AuditLogSchema[]> {
  return apiClient<AuditLogSchema[]>(`/decision/audit?limit=${limit}`);
}

export function getReportExportUrl(decisionId: string, format: 'CSV' | 'JSON' | 'PDF'): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
  return `${baseUrl}/decision/reports/export?decision_id=${encodeURIComponent(decisionId)}&export_format=${format}`;
}
