/**
 * FreightIQ Realistic Domain Mock Data & Benchmark Sets
 * Marked explicitly as synthetic benchmark data for testing and offline command-center operation.
 */

import type {
  DashboardSummary,
  FreightForecastResponse,
  VesselRecommendResponse,
  PortCheckResponse,
  EconomicsResponse,
  MarketEntryResponse,
  RiskResponse,
  ContractCompareResponse,
  ScenarioResponse,
  IdleScenarioResponse,
  HistoryDataPoint,
  Port,
  VesselClass,
  VesselClassComparison,
  AlertItem,
  CargoPlanWorkflowInput,
  CargoPlanEvaluationResult,
} from '@/types'

export const DEMO_DISCLAIMER =
  'DEMO BENCHMARK DATA: Generated from FreightIQ maritime physics models and East Coast India historical fixtures. Not an active commercial quote.'

export const MOCK_PORTS: Port[] = [
  {
    name: 'Paradip',
    country: 'India',
    region: 'East Coast',
    max_dwt: 125000,
    max_draft_m: 14.5,
    max_loa_m: 260,
    max_beam_m: 43,
    berths: 16,
    tide_restricted: true,
    congestion_level: 'Heavy',
    avg_turnaround_days: 4.8,
    handling_rate_mt_day: 28000,
    suitable_commodities: ['Coal', 'Iron Ore', 'Fertilizer', 'Bauxite'],
    latitude: 20.2644,
    longitude: 86.6698,
    notes: 'Primary coking & thermal coal hub for Odisha & Central steel corridor. Capesize requires offshore transshipment / lighterage.',
  },
  {
    name: 'Visakhapatnam',
    country: 'India',
    region: 'East Coast',
    max_dwt: 150000,
    max_draft_m: 16.5,
    max_loa_m: 290,
    max_beam_m: 45,
    berths: 24,
    tide_restricted: false,
    congestion_level: 'Moderate',
    avg_turnaround_days: 3.6,
    handling_rate_mt_day: 35000,
    suitable_commodities: ['Coal', 'Iron Ore', 'Fertilizer', 'Bauxite', 'Grain'],
    latitude: 17.6868,
    longitude: 83.2185,
    notes: 'Deepwater outer harbour accommodates baby-Capesize. Inner harbour restricted to Panamax (14.5m draft).',
  },
  {
    name: 'Gangavaram',
    country: 'India',
    region: 'East Coast',
    max_dwt: 200000,
    max_draft_m: 19.5,
    max_loa_m: 330,
    max_beam_m: 55,
    berths: 9,
    tide_restricted: false,
    congestion_level: 'Low',
    avg_turnaround_days: 2.7,
    handling_rate_mt_day: 48000,
    suitable_commodities: ['Coal', 'Iron Ore', 'Bauxite'],
    latitude: 17.6258,
    longitude: 83.2384,
    notes: 'Premier deepwater terminal with mechanized discharge. Fully cleared for laden Capesize up to 200,000 DWT.',
  },
  {
    name: 'Gopalpur',
    country: 'India',
    region: 'East Coast',
    max_dwt: 105000,
    max_draft_m: 13.5,
    max_loa_m: 235,
    max_beam_m: 36,
    berths: 5,
    tide_restricted: true,
    congestion_level: 'Moderate',
    avg_turnaround_days: 3.9,
    handling_rate_mt_day: 22000,
    suitable_commodities: ['Coal', 'Fertilizer', 'Iron Ore'],
    latitude: 19.3094,
    longitude: 84.9664,
    notes: 'Direct conveyor integration with southern Odisha industrial clusters. Subject to high ocean swell during monsoon.',
  },
  {
    name: 'Dhamra',
    country: 'India',
    region: 'East Coast',
    max_dwt: 180000,
    max_draft_m: 17.5,
    max_loa_m: 310,
    max_beam_m: 48,
    berths: 6,
    tide_restricted: false,
    congestion_level: 'Low',
    avg_turnaround_days: 2.9,
    handling_rate_mt_day: 42000,
    suitable_commodities: ['Coal', 'Iron Ore', 'Bauxite'],
    latitude: 20.8038,
    longitude: 86.9744,
    notes: 'All-weather, deep-draft port serving Jamshedpur and Kalinganagar steel complexes.',
  },
  {
    name: 'Sagar-Sandheads',
    country: 'India',
    region: 'East Coast',
    max_dwt: 120000,
    max_draft_m: 12.0,
    max_loa_m: 240,
    max_beam_m: 38,
    berths: 4,
    tide_restricted: true,
    congestion_level: 'Moderate',
    avg_turnaround_days: 5.2,
    handling_rate_mt_day: 18000,
    suitable_commodities: ['Coal', 'Fertilizer'],
    latitude: 21.6500,
    longitude: 88.0800,
    notes: 'Anchorage lighterage point for upstream Hooghly navigation. Strong tidal currents require pilotage assistance.',
  },
  {
    name: 'Haldia',
    country: 'India',
    region: 'East Coast',
    max_dwt: 45000,
    max_draft_m: 8.5,
    max_loa_m: 195,
    max_beam_m: 32,
    berths: 14,
    tide_restricted: true,
    congestion_level: 'Severe',
    avg_turnaround_days: 6.8,
    handling_rate_mt_day: 14000,
    suitable_commodities: ['Coal', 'Grain', 'Fertilizer', 'Bauxite'],
    latitude: 22.0232,
    longitude: 88.0645,
    notes: 'Riverine port with critical sandbar draft limit (8.5m). Large vessels must discharge parcel at Sandheads or Paradip before entry.',
  },
]

export const MOCK_ALERTS: AlertItem[] = [
  {
    id: 'alt-01',
    title: 'Paradip Anchorage Waiting Time Elevated to 5.8 Days',
    severity: 'High',
    category: 'Port Congestion',
    location: 'Paradip (East Coast India)',
    timestamp: '28 mins ago',
    description:
      '7 bulkers waiting at anchorage due to scheduled conveyor maintenance at Central Coal Berth. Queue expected to normalize by Thursday.',
    recommended_action: 'Initiate slow-steaming at 11.2 knots to absorb 1.8 days of delay and save ~$18,400 in voyage bunker.',
    impact_indicator: '+$24,000/day Demurrage Risk',
  },
  {
    id: 'alt-02',
    title: 'Singapore VLSFO Bunker Spike +$34/MT',
    severity: 'Medium',
    category: 'Bunker Fuel',
    location: 'Singapore Hub (SGP)',
    timestamp: '1 hour ago',
    description:
      'Crude rally and refinery turnaround in Fujairah driving bunkering spot prices to $684/MT. Colombo and Visakhapatnam spreads widening.',
    recommended_action: 'Stem fuel at bunkering alternative Port Louis or fix index-linked bunker adjustment factor (BAF).',
    impact_indicator: '+$1.40/MT Voyage Cost Impact',
  },
  {
    id: 'alt-03',
    title: 'Monsoon South-Easterly Swell Warning — Gopalpur Outer Berth',
    severity: 'Critical',
    category: 'Weather & Monsoon',
    location: 'Bay of Bengal (Gopalpur Approach)',
    timestamp: '3 hours ago',
    description:
      'IMD cyclone tracking indicates wave swell 3.8m–4.4m over the next 72 hours. Outer berth berthing suspended for vessels LOA > 220m.',
    recommended_action: 'Consider immediate diversion of Panamax parcel to Dhamra or Visakhapatnam Outer Harbor.',
    impact_indicator: 'Berthing Stoppage Expected',
  },
  {
    id: 'alt-04',
    title: 'Australia Newcastle Port Queues Clearing — Capesize Ballast Fleet Ample',
    severity: 'Info',
    category: 'Market Volatility',
    location: 'Hay Point / Newcastle (AUS)',
    timestamp: '5 hours ago',
    description:
      'Vessel queue at DBCT and Newcastle fell below 14-day average. Spot tonnage supply in Indo-Pacific is loose, softening C5 rates.',
    recommended_action: 'Favorable timing for charterers. Negotiate below broker prompt indication or float 3-voyage tender.',
    impact_indicator: '-4.2% Spot Freight Softening',
  },
  {
    id: 'alt-05',
    title: 'Haldia Riverine Draft Restrictions Downgraded to 8.2m HW',
    severity: 'Critical',
    category: 'Port Congestion',
    location: 'Haldia Dock Complex',
    timestamp: '8 hours ago',
    description:
      'Eden Channel silting after tidal bore reduced safe allowable sailing draft. Vessels over 32,000 MT must lighter at Sandheads.',
    recommended_action: 'Do not commit Supramax or Panamax directly to Haldia. Book Gangavaram/Paradip with rake dispatch.',
    impact_indicator: 'Mandatory Lighterage Required',
  },
]

export const MOCK_DASHBOARD_SUMMARY: DashboardSummary = {
  rate_snapshots: [
    {
      route: 'AUS → Paradip (Panamax)',
      origin: 'Australia',
      destination: 'Paradip',
      vessel_class: 'Panamax',
      current_rate: 14.85,
      predicted_rate: 13.9,
      trend: 'falling',
      confidence_pct: 86,
      tce: 18450,
      market_action: 'WAIT',
      savings_usd: 66500,
    },
    {
      route: 'IDN → Visakhapatnam (Supramax)',
      origin: 'Indonesia',
      destination: 'Visakhapatnam',
      vessel_class: 'Supramax',
      current_rate: 11.2,
      predicted_rate: 12.4,
      trend: 'rising',
      confidence_pct: 82,
      tce: 16200,
      market_action: 'CHARTER NOW',
      savings_usd: 66000,
    },
    {
      route: 'MOZ → Gangavaram (Capesize)',
      origin: 'Mozambique',
      destination: 'Gangavaram',
      vessel_class: 'Capesize',
      current_rate: 10.95,
      predicted_rate: 10.8,
      trend: 'stable',
      confidence_pct: 79,
      tce: 22800,
      market_action: 'MONITOR',
      savings_usd: 22500,
    },
    {
      route: 'USA → Paradip (Panamax)',
      origin: 'United States',
      destination: 'Paradip',
      vessel_class: 'Panamax',
      current_rate: 34.6,
      predicted_rate: 36.2,
      trend: 'rising',
      confidence_pct: 88,
      tce: 24100,
      market_action: 'CHARTER NOW',
      savings_usd: 112000,
    },
  ],
  executive_kpis: {
    current_freight_indication: 14.85,
    forecast_freight: 13.9,
    forecast_trend: 'falling',
    market_entry_action: 'WAIT',
    recommended_vessel: 'Panamax',
    estimated_voyage_cost: 1039500,
    contract_recommendation: '6-Month COA + Spot Hedge',
    risk_score: 34,
    risk_level: 'Low',
    potential_savings: 66500,
  },
  market_entry_highlight: {
    action: 'WAIT',
    signal: 'WAIT',
    current_rate_usd_per_mt: 14.85,
    predicted_rate_usd_per_mt: 13.9,
    expected_movement_usd: -0.95,
    expected_movement_pct: -6.4,
    confidence_pct: 86,
    potential_savings_usd: 66500,
    recommendation:
      'Delay spot fixture by 12–18 days. Newcastle Capesize/Panamax fleet overhang is expanding and Indian domestic port inventories are at 22 days.',
    reasons: [
      'Pacific ballast fleet ratio rose from 1.12 to 1.34 over past 14 days',
      'Port stock in Paradip & Dhamra above seasonal average, dampening prompt buyer urgency',
      'Singapore VLSFO futures indicating flat-to-lower bunker cost in next delivery cycle',
      'Iron ore export quotas in Australia maintaining normal flow with no weather disruption',
    ],
    warnings: [
      'Monsoon onset late in Bay of Bengal could increase port turnaround variance',
      'Sudden Chinese steel stimulus may absorb Pacific spot tonnage in late Laycan',
    ],
    best_entry_window: 'Target fixture window: 14–22 Oct (Save ~$66,500 on 70k MT parcel)',
    estimated_savings_usd: 66500,
    alternative_strategies: [
      {
        strategy: 'Tender 3-Month COA at Index Minus $0.40',
        description: 'Secure volume baseline while retaining floating discount on physical index.',
        pros: ['Guaranteed tonnage availability', 'No counterparty default risk'],
        cons: ['Requires firm cargo volume schedule'],
      },
      {
        strategy: 'Prompt Spot Charter',
        description: 'Fix vessel immediately at current market indication of $14.85/MT.',
        pros: ['Complete schedule certainty', 'Zero commodity stockout risk'],
        cons: ['Leaves an estimated $66,500 in market savings on the table'],
      },
    ],
    disclaimer: DEMO_DISCLAIMER,
    isDemoData: true,
  },
  disclaimer: DEMO_DISCLAIMER,
  isDemoData: true,
}

export function generateMockHistory(
  baseRate = 14.85,
  points = 26
): { data: HistoryDataPoint[]; disclaimer: string } {
  const result: HistoryDataPoint[] = []
  const now = new Date('2026-09-01')

  for (let i = points; i >= 0; i--) {
    const d = new Date(now)
    d.setDate(d.getDate() - i * 7)
    const noise = Math.sin(i * 0.45) * 1.6 + Math.cos(i * 0.2) * 0.8
    const r = Math.max(9.0, Number((baseRate + noise).toFixed(2)))
    const tce = Math.round(r * 1150 + 1200 + noise * 400)
    const bunker = Math.round(620 + Math.sin(i * 0.3) * 45)
    result.push({
      date: d.toISOString().slice(0, 10),
      rate: r,
      tce,
      bunker,
      congestion: Number((3.2 + Math.cos(i * 0.5) * 1.4).toFixed(1)),
      demand: Math.round(75 + noise * 8),
    })
  }

  return { data: result, disclaimer: DEMO_DISCLAIMER }
}

export function getMockForecast(params: {
  origin?: string
  destination?: string
  vessel_class?: VesselClass
  commodity?: string
  cargo_mt?: number
  horizon_days?: number
}): FreightForecastResponse {
  const baseRate =
    params.vessel_class === 'Capesize'
      ? 10.8
      : params.vessel_class === 'Panamax'
      ? 14.85
      : params.vessel_class === 'Supramax'
      ? 16.4
      : 19.2

  const horizon = params.horizon_days || 30
  const trend = horizon > 45 ? 'rising' : 'falling'
  const delta = trend === 'falling' ? -0.95 : 1.35
  const predicted = Number((baseRate + delta).toFixed(2))

  return {
    origin: params.origin || 'Australia',
    destination: params.destination || 'Paradip',
    vessel_class: params.vessel_class || 'Panamax',
    commodity: params.commodity || 'Coal',
    current_rate_usd_per_mt: baseRate,
    predicted_rate_usd_per_mt: predicted,
    lower_bound: Number((predicted - 0.85).toFixed(2)),
    upper_bound: Number((predicted + 1.15).toFixed(2)),
    confidence_pct: 86,
    horizon_days: horizon,
    tce_estimate_usd_per_day: Math.round(predicted * 1200 + 1500),
    trend,
    influencing_factors: [
      {
        factor: 'Pacific Bulker Tonnage Supply',
        direction: 'bearish',
        magnitude: 'high',
        description: 'Vessel ballast availability from China/Japan to Australian ports up 14% week-on-week.',
      },
      {
        factor: 'Singapore VLSFO Bunker Cost',
        direction: 'neutral',
        magnitude: 'medium',
        description: 'Crude Brent rangebound $74–$78/bbl keeping bunker prices around $640–$660/MT.',
      },
      {
        factor: 'Indian Steel Mill Coking Coal Demand',
        direction: 'bullish',
        magnitude: 'medium',
        description: 'East coast domestic crude steel runs at 89% capacity with restocking planned for Q4.',
      },
      {
        factor: 'Paradip Port Turnaround Congestion',
        direction: 'bearish',
        magnitude: 'low',
        description: 'Waiting times declining from 5.4 days to 3.8 days as modernized coal unloading berth ramps up.',
      },
    ],
    disclaimer: DEMO_DISCLAIMER,
    generated_at: new Date().toISOString(),
    isDemoData: true,
  }
}

export function getMockVesselComparison(params: {
  origin?: string
  destination?: string
  commodity?: string
  cargo_mt?: number
}): VesselRecommendResponse {
  const dest = params.destination || 'Visakhapatnam'
  const cargoMt = params.cargo_mt || 70000

  const detailed_comparison: VesselClassComparison[] = [
    {
      vessel_class: 'Handysize',
      dwt_range: '28,000 – 39,999 DWT',
      feasibility: cargoMt > 42000 ? 'Sub-optimal' : 'Feasible',
      estimated_freight_usd_per_mt: 22.4,
      cargo_capacity_mt: '35,000 MT max parcel',
      optimal_parcel_mt: 34000,
      port_compatibility: 'Unrestricted at all berths (Draft 9.8m, Geared with 4x30t cranes)',
      port_compatible: true,
      estimated_turnaround_days: 3.2,
      idle_risk: 'Low',
      idle_cost_risk_usd: 14500,
      overall_score: cargoMt > 42000 ? 54 : 88,
      fuel_burn_sea_mt_day: 18.5,
      daily_hire_usd: 14200,
      reasons: [
        'Geared self-discharging capability allows discharge at any shallow or river berth',
        'Minimal draft constraints; no tide delay',
      ],
      warnings: ['Significantly higher freight $/MT due to lack of cargo scale on bulk mineral runs'],
    },
    {
      vessel_class: 'Supramax',
      dwt_range: '50,000 – 64,999 DWT',
      feasibility: 'Feasible',
      estimated_freight_usd_per_mt: 16.85,
      cargo_capacity_mt: '55,000 MT max parcel',
      optimal_parcel_mt: 54000,
      port_compatibility: 'Cleared across all major East Coast berths (Draft 12.8m)',
      port_compatible: true,
      estimated_turnaround_days: 3.9,
      idle_risk: 'Low',
      idle_cost_risk_usd: 18200,
      overall_score: cargoMt <= 60000 ? 94 : 76,
      fuel_burn_sea_mt_day: 26.2,
      daily_hire_usd: 16800,
      reasons: [
        'Excellent balance between cargo volume economics and port draft flexibility',
        'Standard workhorse vessel with high prompt availability across Indo-Pacific',
      ],
      warnings: ['Requires split parcel if total procurement volume is 70,000+ MT'],
    },
    {
      vessel_class: 'Panamax',
      dwt_range: '65,000 – 84,999 DWT',
      feasibility: dest === 'Haldia' ? 'Restricted' : 'Feasible',
      estimated_freight_usd_per_mt: 14.85,
      cargo_capacity_mt: '75,000 MT max parcel',
      optimal_parcel_mt: 72000,
      port_compatibility:
        dest === 'Haldia'
          ? 'Draft restricted (Requires 14.2m vs 8.5m channel limit)'
          : 'Fully compatible at mechanized coal berths (Paradip, Vizag, Gangavaram, Dhamra)',
      port_compatible: dest !== 'Haldia',
      estimated_turnaround_days: 4.4,
      idle_risk: 'Moderate',
      idle_cost_risk_usd: 24500,
      overall_score: dest === 'Haldia' ? 42 : 95,
      fuel_burn_sea_mt_day: 31.0,
      daily_hire_usd: 18500,
      reasons: [
        'Optimal economies of scale for standard 70k MT dry bulk shipments',
        'Direct fit for deepwater East Coast steel plant receiving conveyors',
        'Competitive TCE and broad charter market liquidity',
      ],
      warnings: [
        dest === 'Haldia' ? 'Cannot discharge directly at Haldia without prior lighterage' : 'Subject to 3-5 day anchorage queue during peak import season',
      ],
    },
    {
      vessel_class: 'Capesize',
      dwt_range: '120,000 – 205,000 DWT',
      feasibility: dest === 'Gangavaram' || dest === 'Dhamra' ? 'Feasible' : 'Restricted',
      estimated_freight_usd_per_mt: 10.95,
      cargo_capacity_mt: '150,000 – 180,000 MT parcel',
      optimal_parcel_mt: 160000,
      port_compatibility:
        dest === 'Gangavaram' || dest === 'Dhamra'
          ? 'Cleared at deepwater berths (18m+ draft available)'
          : `Restricted at ${dest} (Laden draft 18.2m exceeds port safe limit)`,
      port_compatible: dest === 'Gangavaram' || dest === 'Dhamra',
      estimated_turnaround_days: 5.6,
      idle_risk: 'Elevated',
      idle_cost_risk_usd: 48000,
      overall_score: dest === 'Gangavaram' || dest === 'Dhamra' ? 92 : 38,
      fuel_burn_sea_mt_day: 48.0,
      daily_hire_usd: 24200,
      reasons: [
        'Lowest freight cost per MT ($10.95/MT vs $14.85 for Panamax)',
        'Unmatched economies of scale for large utility or integrated steel mill inventory',
      ],
      warnings: [
        'Strictly limited to deepwater ports (Gangavaram, Dhamra) or offshore lightering',
        'High daily demurrage exposure ($28k–$34k/day) if congestion spikes',
      ],
    },
  ]

  const recommended =
    cargoMt >= 120000 && (dest === 'Gangavaram' || dest === 'Dhamra')
      ? 'Capesize'
      : cargoMt <= 45000 || dest === 'Haldia'
      ? 'Supramax'
      : 'Panamax'

  return {
    recommended_class: recommended,
    alternatives: detailed_comparison.map((c) => ({
      vessel_class: c.vessel_class,
      dwt_range: c.dwt_range,
      recommended: c.vessel_class === recommended,
      fit_score: c.overall_score,
      estimated_freight_usd_per_mt: c.estimated_freight_usd_per_mt,
      voyage_days: Math.round(18 + (c.vessel_class === 'Capesize' ? 2 : 0)),
      tce_usd_per_day: Math.round(c.daily_hire_usd * 1.05),
      port_compatible: c.port_compatible,
      reasons: c.reasons,
      warnings: c.warnings,
    })),
    detailed_comparison,
    reasoning:
      recommended === 'Panamax'
        ? `Panamax delivers optimal logistics economics for ${cargoMt.toLocaleString()} MT at ${dest}. Maximizes cargo intake while avoiding Capesize berth draft penalties.`
        : recommended === 'Supramax'
        ? `Supramax chosen due to parcel size (${cargoMt.toLocaleString()} MT) and draft flexibility at destination port ${dest}.`
        : `Capesize chosen for large-scale economies of scale into deepwater terminal ${dest}.`,
    disclaimer: DEMO_DISCLAIMER,
    isDemoData: true,
  }
}

export function getMockPortCheck(portName = 'Paradip', vesselClass: VesselClass = 'Panamax'): PortCheckResponse {
  const p = MOCK_PORTS.find((item) => item.name.toLowerCase() === portName.toLowerCase()) || MOCK_PORTS[0]

  const draftMap: Record<VesselClass, number> = {
    Handysize: 9.8,
    Supramax: 12.8,
    Panamax: 14.2,
    Capesize: 18.2,
  }

  const vesselDraft = draftMap[vesselClass] || 14.2
  const compatible = p.max_draft_m >= vesselDraft

  return {
    port: p.name,
    vessel_class: vesselClass,
    compatible,
    constraints: [
      {
        constraint: 'Channel & Berth Draft Limit',
        status: p.max_draft_m >= vesselDraft ? 'OK' : 'FAIL',
        detail: `Port allowable draft is ${p.max_draft_m}m vs vessel laden draft of ${vesselDraft}m (Margin: ${(
          p.max_draft_m - vesselDraft
        ).toFixed(1)}m).`,
      },
      {
        constraint: 'Length Overall (LOA) Berth Clearance',
        status: 'OK',
        detail: `Berth LOA limit ${p.max_loa_m}m accommodates standard ${vesselClass} design specs.`,
      },
      {
        constraint: 'Tidal Navigational Windows',
        status: p.tide_restricted ? 'WARNING' : 'OK',
        detail: p.tide_restricted
          ? 'Berthing/unberthing restricted to high-water tidal windows (+2.8m HW spring tide).'
          : 'Non-tidal deepwater approach allows 24/7 unassisted vessel navigation.',
      },
      {
        constraint: 'Unloader Shore Crane Outreach',
        status: vesselClass === 'Capesize' && p.name !== 'Gangavaram' && p.name !== 'Dhamra' ? 'WARNING' : 'OK',
        detail:
          vesselClass === 'Capesize'
            ? 'Capesize 45m+ beam requires long-reach gantry grab unloaders (1,800 MT/hr capacity).'
            : 'Standard harbor portal cranes and conveyor hoppers fully compatible.',
      },
    ],
    turnaround_days: p.avg_turnaround_days,
    port_dues_usd:
      vesselClass === 'Capesize' ? 95000 : vesselClass === 'Panamax' ? 62000 : vesselClass === 'Supramax' ? 48000 : 34000,
    handling_rate_mt_day: p.handling_rate_mt_day,
    max_draft_m: p.max_draft_m,
    vessel_draft_m: vesselDraft,
    notes: p.notes,
    disclaimer: DEMO_DISCLAIMER,
    isDemoData: true,
  }
}

export function getMockEconomics(params: {
  origin?: string
  destination?: string
  vessel_class?: VesselClass
  cargo_mt?: number
  freight_rate_usd_per_mt?: number
  bunker_price_usd_per_mt?: number
}): EconomicsResponse {
  const cargoMt = params.cargo_mt || 70000
  const ratePerMt = params.freight_rate_usd_per_mt || 14.85
  const bunkerPrice = params.bunker_price_usd_per_mt || 650

  const distanceNm = 4920
  const seaDays = 14.5
  const portDays = 4.2
  const totalDays = seaDays + portDays

  const freightRevenue = cargoMt * ratePerMt
  const bunkerCost = Math.round(seaDays * 31.0 * bunkerPrice + portDays * 3.5 * bunkerPrice)
  const portDues = 62000
  const canalDues = 0
  const opex = Math.round(totalDays * 7200)
  const totalCost = bunkerCost + portDues + canalDues + opex
  const grossProfit = freightRevenue - totalCost
  const tce = Math.round(grossProfit / totalDays)
  const breakeven = Number((totalCost / cargoMt).toFixed(2))
  const marginPct = Number(((grossProfit / freightRevenue) * 100).toFixed(1))

  return {
    origin: params.origin || 'Australia',
    destination: params.destination || 'Paradip',
    vessel_class: params.vessel_class || 'Panamax',
    cargo_mt: cargoMt,
    distance_nm: distanceNm,
    sea_days: seaDays,
    port_days: portDays,
    total_voyage_days: totalDays,
    freight_revenue_usd: freightRevenue,
    freight_rate_usd_per_mt: ratePerMt,
    bunker_cost_usd: bunkerCost,
    port_dues_usd: portDues,
    canal_dues_usd: canalDues,
    opex_usd: opex,
    total_cost_usd: totalCost,
    gross_profit_usd: grossProfit,
    tce_usd_per_day: tce,
    breakeven_rate_usd_per_mt: breakeven,
    margin_pct: marginPct,
    disclaimer: DEMO_DISCLAIMER,
    isDemoData: true,
  }
}

export function getMockMarketSignal(params: {
  origin?: string
  destination?: string
  vessel_class?: VesselClass
  commodity?: string
  cargo_mt?: number
  urgency_days?: number
}): MarketEntryResponse {
  const origin = params.origin || 'Australia'
  const dest = params.destination || 'Paradip'
  const isAustralia = origin.includes('Aus')

  const action = isAustralia ? 'WAIT' : 'CHARTER NOW'
  const currentRate = isAustralia ? 14.85 : 12.4
  const predictedRate = isAustralia ? 13.9 : 13.6
  const savings = isAustralia ? 66500 : 84000

  return {
    action,
    signal: isAustralia ? 'WAIT' : 'BUY_NOW',
    current_rate_usd_per_mt: currentRate,
    predicted_rate_usd_per_mt: predictedRate,
    expected_movement_usd: Number((predictedRate - currentRate).toFixed(2)),
    expected_movement_pct: Number((((predictedRate - currentRate) / currentRate) * 100).toFixed(1)),
    confidence_pct: 86,
    potential_savings_usd: savings,
    recommendation:
      action === 'WAIT'
        ? `Model recommends delaying spot fixture by 12–16 days for ${origin} → ${dest}. Pacific ballast tonnage supply is loose, providing downward pricing leverage.`
        : `Model recommends immediate fixture for ${origin} → ${dest}. Upward freight pressure identified across regional bunkering and prompt laycan slots.`,
    reasons: [
      'Pacific bulker ballast ratio increased to 1.34x (above 12-month historical mean)',
      'East Coast Indian power plant stockpiles stand healthy at 21 days of consumption',
      'Refined marine bunker fuel price trends project flat-to-softening into next week',
    ],
    warnings: [
      'Watch for sudden Chinese iron ore tender activity which could absorb Capesize tonnage quickly',
      'Late-monsoon Bay of Bengal depressions can cause port queue variability',
    ],
    best_entry_window:
      action === 'WAIT' ? 'Optimal charter window: 14–22 Oct (Estimated savings: $66,500)' : 'Immediate 72-hour execution window',
    estimated_savings_usd: savings,
    alternative_strategies: [
      {
        strategy: '3-Month Short-Term COA',
        description: 'Lock in 3 consecutive quarterly liftings at fixed discount to Baltic Dry Index.',
        pros: ['Guarantees laycan reliability', 'Mitigates spot freight spikes'],
        cons: ['Slightly lower spot upside if rates drop further'],
      },
      {
        strategy: 'Index-Linked Floating Contract with Cap',
        description: 'Contract at spot index with a guaranteed $15.50/MT ceiling.',
        pros: ['Full downside capture if market falls', 'Protected against runaway rate inflation'],
        cons: ['Modest premium charged by shipowner for option cap'],
      },
    ],
    disclaimer: DEMO_DISCLAIMER,
    isDemoData: true,
  }
}

export function getMockRisk(_params: {
  origin?: string
  destination?: string
  vessel_class?: VesselClass
}): RiskResponse {
  return {
    overall_risk_score: 34,
    overall_risk_level: 'Low',
    risk_factors: [
      {
        category: 'Market & Rate Volatility',
        name: 'Spot Freight Swing Exposure',
        level: 'Low',
        score: 28,
        description: 'Dry bulk FFA futures indicating moderate forward volatility (+/- 4.5% 30-day band).',
        mitigation: 'Utilize 30-day forward freight indications and index-linked contracts with rate collars.',
      },
      {
        category: 'Port Operations',
        name: 'Turnaround & Anchorage Demurrage',
        level: 'Medium',
        score: 52,
        description: 'Paradip coal berth maintenance causing 4.8-day average pre-berthing wait.',
        mitigation: 'Incorporate slow-steaming voyage clauses and negotiate 5 weather-working days laytime.',
      },
      {
        category: 'Bunker Price',
        name: 'VLSFO Bunkering Volatility',
        level: 'Low',
        score: 24,
        description: 'Singapore VLSFO stable within $630–$660/MT band.',
        mitigation: 'Stem bunkers at Port Louis or Visakhapatnam to capture price arbitrage.',
      },
      {
        category: 'Weather & Seasonality',
        name: 'Bay of Bengal Monsoon Swell',
        level: 'Medium',
        score: 48,
        description: 'Late monsoon tropical lows can impede pilot boarding and lighterage at Sandheads.',
        mitigation: 'Target deepwater non-tidal berths (Gangavaram, Dhamra) during monsoon months.',
      },
      {
        category: 'Vessel Supply',
        name: 'Regional Tonnage Availability',
        level: 'Low',
        score: 18,
        description: 'Over 45 Panamax bulkers currently ballasting into Indo-Pacific basin.',
        mitigation: 'Tender open cargo quote across multiple brokers to provoke competitive owner bidding.',
      },
    ],
    alerts: MOCK_ALERTS,
    top_risks: [
      'Berth congestion delays at Paradip (demurrage risk)',
      'Monsoon swell restrictions on coastal lightering operations',
    ],
    recommended_actions: [
      'Request virtual arrival clause to slow steam during known anchorage delays',
      'Fix COA coverage for 60% of volume and float 40% on spot market',
      'Designate Gangavaram or Dhamra as named contractual alternative discharge ports',
    ],
    disclaimer: DEMO_DISCLAIMER,
    isDemoData: true,
  }
}

export function getMockContracts(params: {
  annual_volume_mt?: number
  planning_horizon_months?: number
}): ContractCompareResponse {
  const annualMt = params.annual_volume_mt || 500000
  const spotRate = 14.85
  const shortRate = 13.9
  const medRate = 13.2

  const spotTotal = annualMt * spotRate
  const shortTotal = annualMt * shortRate
  const medTotal = annualMt * medRate

  return {
    options: [
      {
        contract_type: 'Spot Market (Voyage Charter)',
        duration: 'Single Voyage',
        rate_usd_per_mt: spotRate,
        total_cost_usd: spotTotal,
        cost_per_month_usd: Math.round(spotTotal / 12),
        flexibility_score: 95,
        risk_score: 72,
        recommended: false,
        breakeven_freight_usd: spotRate,
        pros: ['Maximum flexibility to abandon or scale volume', 'Zero financial commitment if production stalls'],
        cons: ['Complete exposure to seasonal freight spikes', 'No guaranteed tonnage during tight markets'],
      },
      {
        contract_type: 'Short-Term COA (3–6 Months)',
        duration: '3–6 Months',
        rate_usd_per_mt: shortRate,
        total_cost_usd: shortTotal,
        cost_per_month_usd: Math.round(shortTotal / 12),
        flexibility_score: 78,
        risk_score: 38,
        recommended: true,
        breakeven_freight_usd: shortRate,
        pros: [
          'Guaranteed vessel laycan windows every 25–30 days',
          'Saves ~$475,000 annually compared to unhedged spot',
          'Retains flexibility to renegotiate after monsoon season',
        ],
        cons: ['Fixed lifting penalties if cargo is delayed at mine'],
      },
      {
        contract_type: 'Medium-Term Time Charter (12 Months)',
        duration: '12 Months',
        rate_usd_per_mt: medRate,
        total_cost_usd: medTotal,
        cost_per_month_usd: Math.round(medTotal / 12),
        flexibility_score: 55,
        risk_score: 44,
        recommended: false,
        breakeven_freight_usd: medRate,
        pros: [
          'Lowest freight cost ($13.20/MT saves ~$825,000/yr)',
          'Complete dedicated vessel schedule control and operational dispatch',
        ],
        cons: ['Bunker fuel price risk shifts entirely to charterer', 'Vessel idle costs during supply disruptions'],
      },
    ],
    recommended_contract: 'Short-Term COA (3–6 Months)',
    blended_strategy: '65% Volume on 6-Month COA + 35% Floating Spot Market',
    expected_saving_vs_spot: spotTotal - shortTotal,
    reasoning:
      'A short-term COA captures significant volume discounts while preserving flexibility against expected Q1 freight dips. Blended approach protects against plant production disruptions.',
    annual_volume_mt: annualMt,
    monthly_cashflow: [
      { month: 'Oct', spot_cost: Math.round(spotTotal / 12 * 1.04), short_term_cost: Math.round(shortTotal / 12), medium_term_cost: Math.round(medTotal / 12) },
      { month: 'Nov', spot_cost: Math.round(spotTotal / 12 * 1.08), short_term_cost: Math.round(shortTotal / 12), medium_term_cost: Math.round(medTotal / 12) },
      { month: 'Dec', spot_cost: Math.round(spotTotal / 12 * 1.06), short_term_cost: Math.round(shortTotal / 12), medium_term_cost: Math.round(medTotal / 12) },
      { month: 'Jan', spot_cost: Math.round(spotTotal / 12 * 0.96), short_term_cost: Math.round(shortTotal / 12), medium_term_cost: Math.round(medTotal / 12) },
      { month: 'Feb', spot_cost: Math.round(spotTotal / 12 * 0.92), short_term_cost: Math.round(shortTotal / 12), medium_term_cost: Math.round(medTotal / 12) },
      { month: 'Mar', spot_cost: Math.round(spotTotal / 12 * 0.95), short_term_cost: Math.round(shortTotal / 12), medium_term_cost: Math.round(medTotal / 12) },
      { month: 'Apr', spot_cost: Math.round(spotTotal / 12 * 1.01), short_term_cost: Math.round(shortTotal / 12), medium_term_cost: Math.round(medTotal / 12) },
      { month: 'May', spot_cost: Math.round(spotTotal / 12 * 1.05), short_term_cost: Math.round(shortTotal / 12), medium_term_cost: Math.round(medTotal / 12) },
      { month: 'Jun', spot_cost: Math.round(spotTotal / 12 * 0.98), short_term_cost: Math.round(shortTotal / 12), medium_term_cost: Math.round(medTotal / 12) },
      { month: 'Jul', spot_cost: Math.round(spotTotal / 12 * 0.94), short_term_cost: Math.round(shortTotal / 12), medium_term_cost: Math.round(medTotal / 12) },
      { month: 'Aug', spot_cost: Math.round(spotTotal / 12 * 0.97), short_term_cost: Math.round(shortTotal / 12), medium_term_cost: Math.round(medTotal / 12) },
      { month: 'Sep', spot_cost: Math.round(spotTotal / 12 * 1.03), short_term_cost: Math.round(shortTotal / 12), medium_term_cost: Math.round(medTotal / 12) },
    ],
    disclaimer: DEMO_DISCLAIMER,
    isDemoData: true,
  }
}

export function getMockScenarios(params: {
  origin?: string
  destination?: string
  vessel_class?: VesselClass
  cargo_mt?: number
}): ScenarioResponse {
  const origin = params.origin || 'Australia'
  const dest = params.destination || 'Paradip'
  const vessel = params.vessel_class || 'Panamax'
  const cargoMt = params.cargo_mt || 70000

  const baseRate = 14.85
  const baseCost = cargoMt * baseRate

  return {
    base_scenario: {
      scenario_name: 'Base Case (Standard Route)',
      vessel_class: vessel,
      origin,
      destination: dest,
      freight_rate_usd_per_mt: baseRate,
      tce_usd_per_day: 18450,
      total_cost_usd: baseCost,
      voyage_days: 18.7,
      bunker_cost_usd: 312000,
      risk_score: 34,
      delta_vs_base_pct: 0,
    },
    alternatives: [
      {
        scenario_name: 'Capesize Consolidation (Dhamra Port)',
        vessel_class: 'Capesize',
        origin,
        destination: 'Dhamra',
        freight_rate_usd_per_mt: 10.95,
        tce_usd_per_day: 22800,
        total_cost_usd: Math.round(cargoMt * 10.95),
        voyage_days: 20.2,
        bunker_cost_usd: 485000,
        risk_score: 41,
        delta_vs_base_pct: -26.3,
      },
      {
        scenario_name: 'Indonesia Short-Haul Alternate (Supramax)',
        vessel_class: 'Supramax',
        origin: 'Indonesia',
        destination: 'Visakhapatnam',
        freight_rate_usd_per_mt: 11.2,
        tce_usd_per_day: 16200,
        total_cost_usd: Math.round(cargoMt * 11.2),
        voyage_days: 9.4,
        bunker_cost_usd: 148000,
        risk_score: 22,
        delta_vs_base_pct: -24.6,
      },
      {
        scenario_name: 'High Bunker Shock (+30% Fuel Spike)',
        vessel_class: vessel,
        origin,
        destination: dest,
        freight_rate_usd_per_mt: 16.9,
        tce_usd_per_day: 15100,
        total_cost_usd: Math.round(cargoMt * 16.9),
        voyage_days: 18.7,
        bunker_cost_usd: 405600,
        risk_score: 58,
        delta_vs_base_pct: 13.8,
      },
      {
        scenario_name: 'US Gulf Long-Haul via Cape of Good Hope',
        vessel_class: 'Panamax',
        origin: 'United States',
        destination: dest,
        freight_rate_usd_per_mt: 34.6,
        tce_usd_per_day: 24100,
        total_cost_usd: Math.round(cargoMt * 34.6),
        voyage_days: 38.5,
        bunker_cost_usd: 780000,
        risk_score: 64,
        delta_vs_base_pct: 133.0,
      },
    ],
    best_scenario: 'Capesize Consolidation (Dhamra Port)',
    worst_scenario: 'US Gulf Long-Haul via Cape of Good Hope',
    disclaimer: DEMO_DISCLAIMER,
    isDemoData: true,
  }
}

export function getMockIdleAnalysis(params: {
  destination?: string
  vessel_class?: VesselClass
  waiting_days?: number
  demurrage_rate_usd_day?: number
  bunker_price_usd_per_mt?: number
  slow_steaming_knots?: number
}): IdleScenarioResponse {
  const dest = params.destination || 'Paradip'
  const vessel = params.vessel_class || 'Panamax'
  const waitingDays = params.waiting_days ?? 5.5
  const demurrageRate = params.demurrage_rate_usd_day || 24000
  const bunkerPrice = params.bunker_price_usd_per_mt || 650
  const slowKnots = params.slow_steaming_knots || 11.5

  const normalSpeed = 14.0
  const normalSeaDays = 14.5
  const normalBunker = Math.round(normalSeaDays * 31.0 * bunkerPrice)

  const slowSeaDays = Number((normalSeaDays * (normalSpeed / slowKnots)).toFixed(1))
  const slowDailyBurn = 31.0 * Math.pow(slowKnots / normalSpeed, 3)
  const slowBunker = Math.round(slowSeaDays * slowDailyBurn * bunkerPrice)
  const bunkerSavings = normalBunker - slowBunker

  const absorbedWaitingDays = Number((slowSeaDays - normalSeaDays).toFixed(1))
  const remainingWaitingDays = Math.max(0, Number((waitingDays - absorbedWaitingDays).toFixed(1)))
  const demurrageIncurred = Math.round(remainingWaitingDays * demurrageRate)
  const netBenefit = bunkerSavings + Math.round(absorbedWaitingDays * demurrageRate)

  return {
    destination: dest,
    vessel_class: vessel,
    waiting_days: waitingDays,
    demurrage_rate_usd_day: demurrageRate,
    laytime_allowed_days: 3.5,
    actual_port_days: Number((waitingDays + 2.5).toFixed(1)),
    anchorage_idle_bunker_usd: Math.round(waitingDays * 3.5 * bunkerPrice),
    anchorage_vessel_cost_usd: Math.round(waitingDays * 18500),
    total_waiting_cost_usd: Math.round(waitingDays * 18500 + waitingDays * 3.5 * bunkerPrice),
    demurrage_incurred_usd: demurrageIncurred,
    dispatch_earned_usd: 0,
    total_congestion_exposure_usd: Math.round(waitingDays * demurrageRate),
    slow_steaming: {
      normal_speed_kn: normalSpeed,
      normal_sea_days: normalSeaDays,
      normal_sea_bunker_cost_usd: normalBunker,
      slow_speed_kn: slowKnots,
      slow_sea_days: slowSeaDays,
      slow_sea_bunker_cost_usd: slowBunker,
      bunker_savings_usd: bunkerSavings,
      absorbed_waiting_days: absorbedWaitingDays,
      remaining_waiting_days: remainingWaitingDays,
      net_economic_benefit_usd: netBenefit,
    },
    diversion_options: [
      {
        alternative_port: 'Dhamra Port',
        distance_delta_nm: 68,
        turnaround_days: 2.8,
        congestion_level: 'Low (0.8 days wait)',
        port_dues_delta_usd: 8500,
        net_savings_usd: 48200,
        recommendation: 'Highly Recommended: Avoids 4+ days anchorage queue with direct rail connectivity to Odisha plants.',
      },
      {
        alternative_port: 'Gangavaram Port',
        distance_delta_nm: 185,
        turnaround_days: 2.7,
        congestion_level: 'Low (1.1 days wait)',
        port_dues_delta_usd: -6200,
        net_savings_usd: 36400,
        recommendation: 'Feasible: Deepwater mechanized berth absorbs parcel rapidly, offsets extra steaming fuel.',
      },
    ],
    optimal_strategy: `Slow-steam at ${slowKnots} knots on transit leg. Absorbs ${absorbedWaitingDays} waiting days, cuts fuel cost by $${bunkerSavings.toLocaleString()}, and reduces net demurrage exposure by $${netBenefit.toLocaleString()}.`,
    actionable_recommendations: [
      `Transmit revised Notice of Readiness (NOR) instructions to master for ${slowKnots} knots Virtual Arrival.`,
      `Request shipper/charterer virtual arrival laytime credit under BIMCO Slow Steaming Clause 2020.`,
      `Monitor Dhamra coal berth queue as backup diversion if Paradip waiting days exceed 6.0 days.`,
    ],
    disclaimer: DEMO_DISCLAIMER,
    isDemoData: true,
  }
}

export function evaluateMockCargoPlan(input: CargoPlanWorkflowInput): CargoPlanEvaluationResult {
  const cargoMt = input.cargo_mt || 70000
  const dest = input.destination || 'Paradip'
  const origin = input.origin || 'Australia'

  let recommendedClass: VesselClass = 'Panamax'
  if (cargoMt >= 120000 && (dest === 'Gangavaram' || dest === 'Dhamra')) {
    recommendedClass = 'Capesize'
  } else if (cargoMt <= 45000 || dest === 'Haldia') {
    recommendedClass = 'Supramax'
  }

  const ratePerMt =
    recommendedClass === 'Capesize' ? 10.95 : recommendedClass === 'Panamax' ? 14.85 : 16.85
  const totalVoyageCost = Math.round(cargoMt * ratePerMt)
  const bunkerCost = Math.round(totalVoyageCost * 0.38)
  const portDues = recommendedClass === 'Capesize' ? 95000 : 62000
  const voyageDays = origin.includes('USA') ? 38 : origin.includes('Moz') ? 16 : origin.includes('Indo') ? 9 : 19

  return {
    plan_id: `CP-${Math.floor(100000 + Math.random() * 900000)}`,
    input,
    feasibility: dest === 'Haldia' && cargoMt > 45000 ? 'Restricted' : 'Feasible',
    recommended_vessel: recommendedClass,
    estimated_freight_usd_per_mt: ratePerMt,
    total_voyage_cost_usd: totalVoyageCost,
    bunker_cost_usd: bunkerCost,
    port_dues_usd: portDues,
    voyage_days: voyageDays,
    tce_estimate_usd_per_day: Math.round(ratePerMt * 1220),
    port_compatibility: {
      status: dest === 'Haldia' && cargoMt > 45000 ? 'FAIL' : 'OK',
      max_draft_m: dest === 'Haldia' ? 8.5 : dest === 'Gangavaram' ? 19.5 : 14.5,
      vessel_draft_m: recommendedClass === 'Capesize' ? 18.2 : recommendedClass === 'Panamax' ? 14.2 : 12.8,
      notes:
        dest === 'Haldia' && cargoMt > 45000
          ? 'Haldia river draft (8.5m) cannot accommodate laden vessel without prior lightering at Sandheads.'
          : 'Berth draft and LOA clearances confirmed compatible.',
    },
    market_signal: origin.includes('Aus') ? 'WAIT' : 'CHARTER NOW',
    laycan_risk: {
      congestion_score: dest === 'Paradip' ? 68 : dest === 'Haldia' ? 88 : 28,
      turnaround_days: dest === 'Paradip' ? 4.8 : dest === 'Gangavaram' ? 2.7 : 3.6,
      weather_risk: 'Low-to-moderate swell risk in current laycan window',
    },
    contract_recommendation: {
      strategy: input.contract_duration.includes('Spot')
        ? 'Spot Market Single Voyage with Laytime Collar'
        : 'Short-Term Volume Commitment (COA)',
      potential_savings_usd: Math.round(cargoMt * 0.95),
      reason:
        'Forward curves indicate freight softening over next 2–3 weeks. Fixing a floating index with cap captures market downside.',
    },
    created_at: new Date().toISOString(),
  }
}
