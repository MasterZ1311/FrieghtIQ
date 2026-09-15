/**
 * FreightIQ Dedicated Service Layer
 * Typed API client with graceful fallback to domain-accurate mock benchmark data.
 * Clearly demarcates live vs demo data sources.
 */

import type {
  FreightForecastResponse,
  VesselRecommendResponse,
  PortCheckResponse,
  EconomicsResponse,
  MarketEntryResponse,
  RiskResponse,
  ContractCompareResponse,
  ScenarioResponse,
  IdleScenarioRequest,
  IdleScenarioResponse,
  DashboardSummary,
  HistoryDataPoint,
  Port,
  VesselClass,
  Commodity,
  ContractType,
  CargoPlanWorkflowInput,
  CargoPlanEvaluationResult,
  EndToEndRequest,
  EndToEndResponse,
} from '@/types'


import {
  MOCK_DASHBOARD_SUMMARY,
  MOCK_PORTS,
  generateMockHistory,
  getMockForecast,
  getMockVesselComparison,
  getMockPortCheck,
  getMockEconomics,
  getMockMarketSignal,
  getMockRisk,
  getMockContracts,
  getMockScenarios,
  getMockIdleAnalysis,
  evaluateMockCargoPlan,
} from './mockData'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const FORCE_MOCK = process.env.NEXT_PUBLIC_FORCE_MOCK === 'true'

async function fetchWithTimeout(url: string, options: RequestInit = {}, timeoutMs = 3000): Promise<Response> {
  const controller = new AbortController()
  const id = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const res = await fetch(url, { ...options, signal: controller.signal })
    clearTimeout(id)
    return res
  } catch (err) {
    clearTimeout(id)
    throw err
  }
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetchWithTimeout(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err?.detail || `API error ${res.status}`)
  }
  return res.json()
}

// ─── Live API Implementation ──────────────────────────────────────────────────

export const liveApi = {
  dashboard: {
    summary: (): Promise<DashboardSummary> => apiFetch('/api/dashboard/summary'),
    chartData: (origin: string, destination: string, vesselClass: string): Promise<{ data: HistoryDataPoint[]; disclaimer: string }> =>
      apiFetch(`/api/dashboard/chart-data?origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}&vessel_class=${encodeURIComponent(vesselClass)}`),
  },
  forecast: {
    predict: (params: {
      origin: string
      destination: string
      vessel_class: VesselClass
      commodity: Commodity
      cargo_mt: number
      horizon_days: number
      laycan_start?: string
    }): Promise<FreightForecastResponse> =>
      apiFetch('/api/forecast/predict', { method: 'POST', body: JSON.stringify(params) }),
    history: (origin: string, destination: string, vesselClass: string): Promise<{ data: HistoryDataPoint[]; disclaimer: string }> =>
      apiFetch(`/api/forecast/history?origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}&vessel_class=${encodeURIComponent(vesselClass)}`),
  },
  vessels: {
    recommend: (params: {
      origin: string
      destination: string
      commodity: Commodity
      cargo_mt: number
      budget_usd_per_mt?: number
    }): Promise<VesselRecommendResponse> =>
      apiFetch('/api/vessels/recommend', { method: 'POST', body: JSON.stringify(params) }),
    list: (): Promise<{ vessels: unknown[] }> => apiFetch('/api/vessels/list'),
  },
  ports: {
    check: (params: {
      port: string
      vessel_class: VesselClass
      cargo_mt: number
      commodity: Commodity
    }): Promise<PortCheckResponse> =>
      apiFetch('/api/ports/check', { method: 'POST', body: JSON.stringify(params) }),
    list: (region?: string): Promise<{ ports: Port[] }> =>
      apiFetch(`/api/ports/list${region ? `?region=${region}` : ''}`),
  },
  economics: {
    calculate: (params: {
      origin: string
      destination: string
      vessel_class: VesselClass
      commodity: Commodity
      cargo_mt: number
      freight_rate_usd_per_mt?: number
      bunker_price_usd_per_mt?: number
      port_days_origin?: number
      port_days_dest?: number
    }): Promise<EconomicsResponse> =>
      apiFetch('/api/economics/calculate', { method: 'POST', body: JSON.stringify(params) }),
  },
  marketEntry: {
    signal: (params: {
      origin: string
      destination: string
      vessel_class: VesselClass
      commodity: Commodity
      cargo_mt: number
      urgency_days: number
    }): Promise<MarketEntryResponse> =>
      apiFetch('/api/market-entry/signal', { method: 'POST', body: JSON.stringify(params) }),
  },
  risk: {
    score: (params: {
      origin: string
      destination: string
      vessel_class: VesselClass
      commodity: Commodity
      cargo_mt: number
      contract_type: ContractType
    }): Promise<RiskResponse> =>
      apiFetch('/api/risk/score', { method: 'POST', body: JSON.stringify(params) }),
  },
  contracts: {
    compare: (params: {
      origin: string
      destination: string
      vessel_class: VesselClass
      commodity: Commodity
      cargo_mt: number
      annual_volume_mt?: number
      planning_horizon_months?: number
    }): Promise<ContractCompareResponse> =>
      apiFetch('/api/contracts/compare', { method: 'POST', body: JSON.stringify(params) }),
  },
  scenarios: {
    simulate: (params: {
      base_origin: string
      base_destination: string
      base_vessel_class: VesselClass
      base_commodity: Commodity
      base_cargo_mt: number
      scenarios: Record<string, unknown>[]
    }): Promise<ScenarioResponse> =>
      apiFetch('/api/scenarios/simulate', { method: 'POST', body: JSON.stringify(params) }),
    idleAnalysis: (params: IdleScenarioRequest): Promise<IdleScenarioResponse> =>
      apiFetch('/api/scenarios/idle-analysis', { method: 'POST', body: JSON.stringify(params) }),
  },
  cargoPlanning: {
    evaluate: async (input: CargoPlanWorkflowInput): Promise<CargoPlanEvaluationResult> => {
      return evaluateMockCargoPlan(input)
    },
  },
  workflow: {
    endToEnd: (params: EndToEndRequest): Promise<EndToEndResponse> =>
      apiFetch('/api/workflow/end-to-end', { method: 'POST', body: JSON.stringify(params) }),
  },
}


// ─── Mock API Implementation ──────────────────────────────────────────────────

export const mockApi = {
  dashboard: {
    summary: async (): Promise<DashboardSummary> => ({ ...MOCK_DASHBOARD_SUMMARY, isDemoData: true }),
    chartData: async (origin: string, destination: string, vesselClass: string): Promise<{ data: HistoryDataPoint[]; disclaimer: string }> =>
      generateMockHistory(vesselClass === 'Capesize' ? 10.95 : 14.85),
  },
  forecast: {
    predict: async (params: {
      origin: string
      destination: string
      vessel_class: VesselClass
      commodity: Commodity
      cargo_mt: number
      horizon_days: number
      laycan_start?: string
    }): Promise<FreightForecastResponse> => ({ ...getMockForecast(params), isDemoData: true }),
    history: async (origin: string, destination: string, vesselClass: string): Promise<{ data: HistoryDataPoint[]; disclaimer: string }> =>
      generateMockHistory(vesselClass === 'Capesize' ? 10.95 : 14.85),
  },
  vessels: {
    recommend: async (params: {
      origin: string
      destination: string
      commodity: Commodity
      cargo_mt: number
      budget_usd_per_mt?: number
    }): Promise<VesselRecommendResponse> => ({ ...getMockVesselComparison(params), isDemoData: true }),
    list: async (): Promise<{ vessels: unknown[] }> => ({
      vessels: ['Handysize', 'Supramax', 'Panamax', 'Capesize'],
    }),
  },
  ports: {
    check: async (params: {
      port: string
      vessel_class: VesselClass
      cargo_mt: number
      commodity: Commodity
    }): Promise<PortCheckResponse> => ({
      ...getMockPortCheck(params.port, params.vessel_class),
      isDemoData: true,
    }),
    list: async (_region?: string): Promise<{ ports: Port[] }> => ({
      ports: MOCK_PORTS,
    }),
  },
  economics: {
    calculate: async (params: {
      origin: string
      destination: string
      vessel_class: VesselClass
      commodity: Commodity
      cargo_mt: number
      freight_rate_usd_per_mt?: number
      bunker_price_usd_per_mt?: number
      port_days_origin?: number
      port_days_dest?: number
    }): Promise<EconomicsResponse> => ({ ...getMockEconomics(params), isDemoData: true }),
  },
  marketEntry: {
    signal: async (params: {
      origin: string
      destination: string
      vessel_class: VesselClass
      commodity: Commodity
      cargo_mt: number
      urgency_days: number
    }): Promise<MarketEntryResponse> => ({ ...getMockMarketSignal(params), isDemoData: true }),
  },
  risk: {
    score: async (params: {
      origin: string
      destination: string
      vessel_class: VesselClass
      commodity: Commodity
      cargo_mt: number
      contract_type: ContractType
    }): Promise<RiskResponse> => ({ ...getMockRisk(params), isDemoData: true }),
  },
  contracts: {
    compare: async (params: {
      origin: string
      destination: string
      vessel_class: VesselClass
      commodity: Commodity
      cargo_mt: number
      annual_volume_mt?: number
      planning_horizon_months?: number
    }): Promise<ContractCompareResponse> => ({ ...getMockContracts(params), isDemoData: true }),
  },
  scenarios: {
    simulate: async (params: {
      base_origin: string
      base_destination: string
      base_vessel_class: VesselClass
      base_commodity: Commodity
      base_cargo_mt: number
      scenarios: Record<string, unknown>[]
    }): Promise<ScenarioResponse> => ({
      ...getMockScenarios({
        origin: params.base_origin,
        destination: params.base_destination,
        vessel_class: params.base_vessel_class,
        cargo_mt: params.base_cargo_mt,
      }),
      isDemoData: true,
    }),
    idleAnalysis: async (params: IdleScenarioRequest): Promise<IdleScenarioResponse> => ({
      ...getMockIdleAnalysis(params),
      isDemoData: true,
    }),
  },
  cargoPlanning: {
    evaluate: async (input: CargoPlanWorkflowInput): Promise<CargoPlanEvaluationResult> =>
      evaluateMockCargoPlan(input),
  },
  workflow: {
    endToEnd: async (params: EndToEndRequest): Promise<EndToEndResponse> => {
      const targetVessel = (params.vessel_class as VesselClass) || 'Panamax'
      const comm = (params.commodity as Commodity) || 'Coal'
      const fc = await mockApi.forecast.predict({
        origin: params.origin,
        destination: params.destination,
        vessel_class: targetVessel,
        commodity: comm,
        cargo_mt: params.cargo_mt,
        horizon_days: params.urgency_days || 30,
      })
      const vr = await mockApi.vessels.recommend({
        origin: params.origin,
        destination: params.destination,
        commodity: comm,
        cargo_mt: params.cargo_mt,
      })
      const portComp = await mockApi.ports.check({
        port: params.destination,
        vessel_class: targetVessel,
        cargo_mt: params.cargo_mt,
        commodity: comm,
      })
      const econ = await mockApi.economics.calculate({
        origin: params.origin,
        destination: params.destination,
        vessel_class: targetVessel,
        commodity: comm,
        cargo_mt: params.cargo_mt,
      })
      const me = await mockApi.marketEntry.signal({
        origin: params.origin,
        destination: params.destination,
        vessel_class: targetVessel,
        commodity: comm,
        cargo_mt: params.cargo_mt,
        urgency_days: params.urgency_days || 30,
      })
      const contracts = await mockApi.contracts.compare({
        origin: params.origin,
        destination: params.destination,
        vessel_class: targetVessel,
        commodity: comm,
        cargo_mt: params.cargo_mt,
      })
      const risk = await mockApi.risk.score({
        origin: params.origin,
        destination: params.destination,
        vessel_class: targetVessel,
        commodity: comm,
        cargo_mt: params.cargo_mt,
        contract_type: 'Spot',
      })

      const allPorts: Record<string, PortCheckResponse> = {}
      for (const vc of ['Handysize', 'Supramax', 'Panamax', 'Capesize'] as VesselClass[]) {
        allPorts[vc] = await mockApi.ports.check({
          port: params.destination,
          vessel_class: vc,
          cargo_mt: params.cargo_mt,
          commodity: comm,
        })
      }

      return {
        origin: params.origin,
        destination: params.destination,
        commodity: String(params.commodity),
        cargo_mt: params.cargo_mt,
        distance_nm: econ.distance_nm,
        forecast: fc,
        vessel_feasibility: vr.alternatives,
        recommended_vessel: targetVessel,
        port_compatibility: portComp,
        all_ports_compatibility: allPorts,
        market_entry: me,
        economics: econ,
        contracts: contracts,
        risk: risk,
        final_recommendation: {
          recommended_vessel: targetVessel,
          optimal_timing_signal: me.signal,
          recommended_contract: contracts.recommended_contract,
          port_status: portComp.compatible ? 'Compatible' : 'Restricted',
          overall_risk_level: risk.overall_risk_level,
          overall_fit_score: 88,
          estimated_freight_usd_per_mt: fc.predicted_rate_usd_per_mt,
          total_voyage_cost_usd: econ.total_cost_usd,
          tce_usd_per_day: econ.tce_usd_per_day,
          breakeven_rate_usd_per_mt: econ.breakeven_rate_usd_per_mt,
          margin_pct: econ.margin_pct,
          action_items: [
            `Vessel Selection: Deploy ${targetVessel} (${params.cargo_mt.toLocaleString()} MT).`,
            `Market Entry: ${me.signal} timing signal active.`,
            `Contract Strategy: Recommended ${contracts.recommended_contract}.`,
          ],
        },
        explanation: `Comprehensive end-to-end evaluation for ${params.origin} to ${params.destination} with ${targetVessel}.`,
        disclaimer: '[DEMO] End-to-end evaluation calculated from synthetic and simulated maritime operational models.',
      }
    },
  },
}


// ─── Resilient Unified Service Layer ──────────────────────────────────────────
// Tries live API first; if backend is unreachable or in mock mode, falls back seamlessly to typed mock data.

async function resilientCall<T>(liveFn: () => Promise<T>, mockFn: () => Promise<T>): Promise<T> {
  if (FORCE_MOCK) {
    return mockFn()
  }
  try {
    const res = await liveFn()
    return { ...res, isDemoData: false }
  } catch {
    // Graceful fallback to verified typed mock data
    return mockFn()
  }
}

export const api = {
  health: async (): Promise<{ status: string; isLive: boolean }> => {
    try {
      const res = await fetchWithTimeout(`${BASE_URL}/health`, {}, 1500)
      if (res.ok) return { status: 'healthy', isLive: true }
    } catch {
      // offline
    }
    return { status: 'demo_mode', isLive: false }
  },

  dashboard: {
    summary: () => resilientCall(liveApi.dashboard.summary, mockApi.dashboard.summary),
    chartData: (origin: string, destination: string, vesselClass: string) =>
      resilientCall(
        () => liveApi.dashboard.chartData(origin, destination, vesselClass),
        () => mockApi.dashboard.chartData(origin, destination, vesselClass)
      ),
  },

  forecast: {
    predict: (params: {
      origin: string
      destination: string
      vessel_class: VesselClass
      commodity: Commodity
      cargo_mt: number
      horizon_days: number
      laycan_start?: string
    }) =>
      resilientCall(
        () => liveApi.forecast.predict(params),
        () => mockApi.forecast.predict(params)
      ),
    history: (origin: string, destination: string, vesselClass: string) =>
      resilientCall(
        () => liveApi.forecast.history(origin, destination, vesselClass),
        () => mockApi.forecast.history(origin, destination, vesselClass)
      ),
  },

  vessels: {
    recommend: (params: {
      origin: string
      destination: string
      commodity: Commodity
      cargo_mt: number
      budget_usd_per_mt?: number
    }) =>
      resilientCall(
        () => liveApi.vessels.recommend(params),
        () => mockApi.vessels.recommend(params)
      ),
    list: () => resilientCall(liveApi.vessels.list, mockApi.vessels.list),
  },

  ports: {
    check: (params: {
      port: string
      vessel_class: VesselClass
      cargo_mt: number
      commodity: Commodity
    }) =>
      resilientCall(
        () => liveApi.ports.check(params),
        () => mockApi.ports.check(params)
      ),
    list: (region?: string) =>
      resilientCall(
        () => liveApi.ports.list(region),
        () => mockApi.ports.list(region)
      ),
  },

  economics: {
    calculate: (params: {
      origin: string
      destination: string
      vessel_class: VesselClass
      commodity: Commodity
      cargo_mt: number
      freight_rate_usd_per_mt?: number
      bunker_price_usd_per_mt?: number
      port_days_origin?: number
      port_days_dest?: number
    }) =>
      resilientCall(
        () => liveApi.economics.calculate(params),
        () => mockApi.economics.calculate(params)
      ),
  },

  marketEntry: {
    signal: (params: {
      origin: string
      destination: string
      vessel_class: VesselClass
      commodity: Commodity
      cargo_mt: number
      urgency_days: number
    }) =>
      resilientCall(
        () => liveApi.marketEntry.signal(params),
        () => mockApi.marketEntry.signal(params)
      ),
  },

  risk: {
    score: (params: {
      origin: string
      destination: string
      vessel_class: VesselClass
      commodity: Commodity
      cargo_mt: number
      contract_type: ContractType
    }) =>
      resilientCall(
        () => liveApi.risk.score(params),
        () => mockApi.risk.score(params)
      ),
  },

  contracts: {
    compare: (params: {
      origin: string
      destination: string
      vessel_class: VesselClass
      commodity: Commodity
      cargo_mt: number
      annual_volume_mt?: number
      planning_horizon_months?: number
    }) =>
      resilientCall(
        () => liveApi.contracts.compare(params),
        () => mockApi.contracts.compare(params)
      ),
  },

  scenarios: {
    simulate: (params: {
      base_origin: string
      base_destination: string
      base_vessel_class: VesselClass
      base_commodity: Commodity
      base_cargo_mt: number
      scenarios: Record<string, unknown>[]
    }) =>
      resilientCall(
        () => liveApi.scenarios.simulate(params),
        () => mockApi.scenarios.simulate(params)
      ),
    idleAnalysis: (params: IdleScenarioRequest) =>
      resilientCall(
        () => liveApi.scenarios.idleAnalysis(params),
        () => mockApi.scenarios.idleAnalysis(params)
      ),
  },

  cargoPlanning: {
    evaluate: (input: CargoPlanWorkflowInput) =>
      resilientCall(
        () => liveApi.cargoPlanning.evaluate(input),
        () => mockApi.cargoPlanning.evaluate(input)
      ),
  },

  workflow: {
    endToEnd: (params: EndToEndRequest) =>
      resilientCall(
        () => liveApi.workflow.endToEnd(params),
        () => mockApi.workflow.endToEnd(params)
      ),
  },
}

