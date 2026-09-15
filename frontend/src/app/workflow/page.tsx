'use client'
import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import {
  formatUSD,
  formatNumber,
  trendArrow,
  riskBg,
  ORIGINS,
  DESTINATIONS,
  COMMODITIES,
} from '@/lib/utils'
import { Card, StatCard, Loading, ErrorBox, Disclaimer, PageHeader, Select, Input } from '@/components/ui'
import type {
  EndToEndResponse,
  Commodity,
  RiskLevel,
  Trend,
} from '@/types'
import {
  TrendingUp,
  Ship,
  Anchor,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Sparkles,
  DollarSign,
  FileText,
  Layers,
  ChevronRight,
} from 'lucide-react'

interface RoutePreset {
  name: string
  origin: string
  destination: string
  commodity: Commodity
  cargo_mt: number
  urgency_days: number
  badge: string
}

const ROUTE_PRESETS: RoutePreset[] = [
  {
    name: 'Australia → Paradip',
    origin: 'Australia',
    destination: 'Paradip',
    commodity: 'Coal',
    cargo_mt: 70000,
    urgency_days: 30,
    badge: 'Mandatory Scenario',
  },
  {
    name: 'Indonesia → Vizag',
    origin: 'Indonesia',
    destination: 'Visakhapatnam',
    commodity: 'Coal',
    cargo_mt: 55000,
    urgency_days: 21,
    badge: 'Route 2',
  },
  {
    name: 'Mozambique → Gangavaram',
    origin: 'Mozambique',
    destination: 'Gangavaram',
    commodity: 'Coal',
    cargo_mt: 150000,
    urgency_days: 45,
    badge: 'Route 3 (Capesize Deepwater)',
  },
  {
    name: 'United States → Paradip',
    origin: 'United States',
    destination: 'Paradip',
    commodity: 'Coal',
    cargo_mt: 70000,
    urgency_days: 30,
    badge: 'Route 4 (Suez Long-Haul)',
  },
]


export default function WorkflowPage() {
  const [origin, setOrigin] = useState('Australia')
  const [destination, setDestination] = useState('Paradip')
  const [commodity, setCommodity] = useState<Commodity>('Coal')
  const [cargo, setCargo] = useState('70000')
  const [urgencyDays, setUrgencyDays] = useState('30')
  const [annualVolume] = useState('500000')
  const [horizonMonths] = useState('12')


  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<EndToEndResponse | null>(null)

  const handleRunWorkflow = async (overrideParams?: {
    origin: string
    destination: string
    commodity: Commodity
    cargo_mt: number
    urgency_days: number
  }) => {
    setLoading(true)
    setError(null)
    const o = overrideParams ? overrideParams.origin : origin
    const d = overrideParams ? overrideParams.destination : destination
    const c = overrideParams ? overrideParams.commodity : commodity
    const mt = overrideParams ? overrideParams.cargo_mt : Number(cargo) || 70000
    const urg = overrideParams ? overrideParams.urgency_days : Number(urgencyDays) || 30

    if (overrideParams) {
      setOrigin(o)
      setDestination(d)
      setCommodity(c)
      setCargo(String(mt))
      setUrgencyDays(String(urg))
    }

    try {
      const res = await api.workflow.endToEnd({
        origin: o,
        destination: d,
        commodity: c,
        cargo_mt: mt,
        urgency_days: urg,
        annual_volume_mt: Number(annualVolume) || 500000,
        planning_horizon_months: Number(horizonMonths) || 12,
        bunker_price_usd_per_mt: 650,
      })
      setData(res)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Workflow execution failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    handleRunWorkflow()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <PageHeader
          title="Single End-to-End Decision Flow"
          subtitle="Cargo Input → Forecast → Vessel Feasibility → Vessel Ranking → Economics → Contract Comparison → Risk → Final Recommendation"
        />
        <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-950/40 border border-blue-800/60 rounded-lg text-xs text-blue-400 self-start">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          End-to-End Decision Engine Active
        </div>
      </div>

      {/* Preset Route Fast-Selectors */}
      <div className="space-y-2">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Fast Presets</span>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {ROUTE_PRESETS.map((p) => (
            <button
              key={p.name}
              onClick={() => handleRunWorkflow(p)}
              className={`p-3 text-left rounded-xl border transition flex flex-col justify-between ${
                origin === p.origin && destination === p.destination
                  ? 'bg-blue-600/20 border-blue-500 text-white'
                  : 'bg-gray-900/60 border-gray-800 text-gray-300 hover:border-gray-700'
              }`}
            >
              <div>
                <span className="text-[10px] font-bold text-blue-400 uppercase">{p.badge}</span>
                <p className="text-sm font-bold mt-1 text-white">{p.name}</p>
              </div>
              <p className="text-xs text-gray-400 mt-2">{formatNumber(p.cargo_mt)} MT · {p.commodity}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Flow Stage 1: Cargo Input */}
      <Card title="Stage 1: Cargo Input & Voyage Parameters" subtitle="Configure origin, destination, commodity, and volume parameters" className="border-blue-900/40">
        <div className="grid grid-cols-1 md:grid-cols-6 gap-3 p-4 bg-gray-950/60 rounded-xl border border-gray-800">
          <Select label="Origin" value={origin} onChange={setOrigin} options={ORIGINS} />
          <Select label="Destination Port" value={destination} onChange={setDestination} options={DESTINATIONS} />
          <Select label="Commodity" value={commodity} onChange={(v) => setCommodity(v as Commodity)} options={COMMODITIES} />
          <Input label="Cargo Volume (MT)" value={cargo} onChange={setCargo} type="number" />
          <Input label="Urgency Window (Days)" value={urgencyDays} onChange={setUrgencyDays} type="number" />
          <div className="flex flex-col justify-end">
            <button
              onClick={() => handleRunWorkflow()}
              disabled={loading}
              className="w-full h-10 px-4 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 text-white font-medium text-xs rounded-lg transition flex items-center justify-center gap-2 shadow-md shadow-blue-600/20"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <Sparkles size={14} />
                  Run Pipeline
                </>
              )}
            </button>
          </div>
        </div>
      </Card>

      {loading && <Loading />}
      {error && <ErrorBox message={error} />}

      {data && (
        <div className="space-y-8">
          {/* Flow Stepper Bar */}
          <div className="p-4 bg-gray-900/80 border border-gray-800 rounded-xl overflow-x-auto">
            <div className="flex items-center min-w-[750px] justify-between text-xs font-semibold">
              <span className="text-blue-400 flex items-center gap-1.5"><Layers size={14} /> 1. Input</span>
              <ChevronRight size={14} className="text-gray-600" />
              <span className="text-blue-400 flex items-center gap-1.5"><TrendingUp size={14} /> 2. Forecast</span>
              <ChevronRight size={14} className="text-gray-600" />
              <span className="text-cyan-400 flex items-center gap-1.5"><Anchor size={14} /> 3. Feasibility</span>
              <ChevronRight size={14} className="text-gray-600" />
              <span className="text-emerald-400 flex items-center gap-1.5"><Ship size={14} /> 4. Ranking</span>
              <ChevronRight size={14} className="text-gray-600" />
              <span className="text-amber-400 flex items-center gap-1.5"><DollarSign size={14} /> 5. Economics</span>
              <ChevronRight size={14} className="text-gray-600" />

              <span className="text-purple-400 flex items-center gap-1.5"><FileText size={14} /> 6. Contracts</span>
              <ChevronRight size={14} className="text-gray-600" />
              <span className="text-red-400 flex items-center gap-1.5"><ShieldAlert size={14} /> 7. Risk</span>
              <ChevronRight size={14} className="text-gray-600" />
              <span className="text-white bg-blue-600 px-2.5 py-1 rounded-lg flex items-center gap-1.5">8. Final Decision</span>
            </div>
          </div>

          {/* Flow Stage 2: Forecast */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard
              label="Stage 2: Freight Forecast"
              value={formatUSD(data.forecast.predicted_rate_usd_per_mt, 2) + '/MT'}
              subValue={`Current: ${formatUSD(data.forecast.current_rate_usd_per_mt, 2)}/MT · Range: $${data.forecast.lower_bound.toFixed(1)}–$${data.forecast.upper_bound.toFixed(1)}`}
              badge={{
                text: `${trendArrow(data.forecast.trend as Trend)} ${data.forecast.trend.toUpperCase()} · ${data.forecast.confidence_pct}% conf.`,
                color: data.forecast.trend === 'rising' ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400',
              }}
              icon={<TrendingUp size={16} />}
            />

            <StatCard
              label="Stage 4: Recommended Vessel"
              value={data.recommended_vessel}
              subValue={`Fit Score: ${data.final_recommendation.overall_fit_score}/100 · Port: ${data.final_recommendation.port_status}`}
              badge={{
                text: 'OPTIMAL FIT',
                color: 'bg-emerald-500/20 text-emerald-400',
              }}
              icon={<Ship size={16} />}
            />

            <StatCard
              label="Stage 5: Voyage Economics"
              value={formatUSD(data.economics.tce_usd_per_day, 0) + '/day'}
              subValue={`Total Cost: ${formatUSD(data.economics.total_cost_usd, 0)} · Margin: ${data.economics.margin_pct.toFixed(1)}%`}
              badge={{
                text: `Breakeven: $${data.economics.breakeven_rate_usd_per_mt.toFixed(2)}/MT`,
                color: 'bg-blue-500/20 text-blue-400',
              }}
              icon={<DollarSign size={16} />}
            />

            <StatCard
              label="Stage 7: Overall Risk"
              value={`${data.risk.overall_risk_score.toFixed(1)} / 100`}
              subValue={`Level: ${data.risk.overall_risk_level} · Signal: ${data.market_entry.signal}`}
              badge={{
                text: data.risk.overall_risk_level.toUpperCase(),
                color: riskBg(data.risk.overall_risk_level as RiskLevel),
              }}
              icon={<ShieldAlert size={16} />}
            />
          </div>

          {/* Flow Stage 3 & 4: Vessel Feasibility & Ranking Table */}
          <Card
            title="Stage 3 & 4: Vessel Feasibility Check & Multi-Class Ranking"
            subtitle={`Evaluation across Handysize, Supramax, Panamax, and Capesize for ${data.destination}`}
          >
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-gray-800/60 text-gray-400 uppercase text-[10px] tracking-wider border-b border-gray-800">
                  <tr>
                    <th className="py-3 px-4">Rank</th>
                    <th className="py-3 px-4">Vessel Class</th>
                    <th className="py-3 px-4">DWT Range</th>
                    <th className="py-3 px-4">Port Feasibility ({data.destination})</th>
                    <th className="py-3 px-4">Fit Score</th>
                    <th className="py-3 px-4">Est. Rate</th>
                    <th className="py-3 px-4">Voyage Days</th>
                    <th className="py-3 px-4">Estimated TCE</th>
                    <th className="py-3 px-4">Recommendation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {data.vessel_feasibility.map((v, idx) => {
                    const comp = data.all_ports_compatibility[v.vessel_class]
                    const isFeasible = comp ? comp.compatible : v.port_compatible
                    return (
                      <tr
                        key={v.vessel_class}
                        className={`transition ${v.vessel_class === data.recommended_vessel ? 'bg-blue-950/30 font-semibold' : 'hover:bg-gray-800/30'}`}
                      >
                        <td className="py-3 px-4">
                          <span className={`w-5 h-5 rounded-full inline-flex items-center justify-center text-[10px] font-bold ${
                            idx === 0 ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400'
                          }`}>
                            {idx + 1}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-white font-medium flex items-center gap-2">
                          <Ship size={14} className={idx === 0 ? 'text-blue-400' : 'text-gray-500'} />
                          {v.vessel_class}
                          {v.vessel_class === data.recommended_vessel && (
                            <span className="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 text-[10px] rounded font-bold">Selected</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-gray-300">{v.dwt_range}</td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-1.5">
                            {isFeasible ? (
                              <CheckCircle2 size={14} className="text-emerald-400" />
                            ) : (
                              <XCircle size={14} className="text-red-400" />
                            )}
                            <span className={isFeasible ? 'text-emerald-400 font-medium' : 'text-red-400 font-medium'}>
                              {isFeasible ? 'Feasible' : 'Infeasible (Draft / Port Limit)'}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-gray-200">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-2 bg-gray-800 rounded-full overflow-hidden">
                              <div
                                className={`h-full ${v.fit_score >= 75 ? 'bg-emerald-500' : v.fit_score >= 50 ? 'bg-amber-500' : 'bg-red-500'}`}
                                style={{ width: `${v.fit_score}%` }}
                              />
                            </div>
                            <span>{v.fit_score}/100</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-gray-300">{formatUSD(v.estimated_freight_usd_per_mt, 2)}/MT</td>
                        <td className="py-3 px-4 text-gray-400">{v.voyage_days}d</td>
                        <td className="py-3 px-4 text-gray-300">{formatUSD(v.tce_usd_per_day, 0)}/day</td>
                        <td className="py-3 px-4">
                          {v.vessel_class === data.recommended_vessel ? (
                            <span className="text-emerald-400 font-bold">★ Recommended</span>
                          ) : isFeasible ? (
                            <span className="text-gray-400">Alternative</span>
                          ) : (
                            <span className="text-red-400">Restricted</span>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Flow Stage 5 & 6: Economics & Contract Comparison */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Stage 5: Voyage Economics P&L */}
            <Card title="Stage 5: Voyage Economics & Cost Breakdown" subtitle={`Operational P&L for ${data.recommended_vessel} (${formatNumber(data.cargo_mt)} MT)`}>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between py-1.5 border-b border-gray-800 text-gray-400">
                  <span>Route Distance</span>
                  <span className="text-white font-medium">{formatNumber(data.economics.distance_nm)} Nautical Miles</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-gray-800 text-gray-400">
                  <span>Sea Days / Port Days</span>
                  <span className="text-white font-medium">{data.economics.sea_days.toFixed(1)}d sea + {data.economics.port_days.toFixed(1)}d port = {data.economics.total_voyage_days.toFixed(1)}d total</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-gray-800 text-gray-400">
                  <span>Freight Revenue</span>
                  <span className="text-emerald-400 font-bold">{formatUSD(data.economics.freight_revenue_usd, 0)}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-gray-800 text-gray-400">
                  <span>Bunker Fuel Cost (Sea + Aux)</span>
                  <span className="text-amber-400 font-medium">-{formatUSD(data.economics.bunker_cost_usd, 0)}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-gray-800 text-gray-400">
                  <span>Port Dues ({data.origin} + {data.destination})</span>
                  <span className="text-gray-300 font-medium">-{formatUSD(data.economics.port_dues_usd, 0)}</span>
                </div>
                {data.economics.canal_dues_usd > 0 && (
                  <div className="flex justify-between py-1.5 border-b border-gray-800 text-gray-400">
                    <span>Canal Transit Dues (Suez)</span>
                    <span className="text-gray-300 font-medium">-{formatUSD(data.economics.canal_dues_usd, 0)}</span>
                  </div>
                )}
                <div className="flex justify-between py-1.5 border-b border-gray-800 text-gray-400">
                  <span>Vessel OPEX</span>
                  <span className="text-gray-300 font-medium">-{formatUSD(data.economics.opex_usd, 0)}</span>
                </div>
                <div className="flex justify-between py-2 border-t-2 border-gray-700 font-bold text-sm">
                  <span className="text-white">Total Voyage Cost</span>
                  <span className="text-red-400">{formatUSD(data.economics.total_cost_usd, 0)}</span>
                </div>
                <div className="flex justify-between py-1 text-xs">
                  <span className="text-gray-400">Breakeven Rate</span>
                  <span className="text-white font-medium">${data.economics.breakeven_rate_usd_per_mt.toFixed(2)}/MT</span>
                </div>
                <div className="flex justify-between py-1 text-xs">
                  <span className="text-gray-400">Estimated Owner TCE</span>
                  <span className="text-blue-400 font-bold">{formatUSD(data.economics.tce_usd_per_day, 0)}/day</span>
                </div>
              </div>
            </Card>

            {/* Stage 6: Contract Comparison */}
            <Card title="Stage 6: Contract Comparison (Spot vs Period)" subtitle={`Optimal structure for annual procurement (${formatNumber(Number(annualVolume))} MT)`}>
              <div className="space-y-3">
                {data.contracts.options.map((opt) => (
                  <div
                    key={opt.contract_type}
                    className={`p-3 rounded-xl border transition ${
                      opt.contract_type === data.contracts.recommended_contract
                        ? 'bg-blue-950/40 border-blue-500/80'
                        : 'bg-gray-800/30 border-gray-800'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-white">{opt.contract_type}</span>
                        {opt.contract_type === data.contracts.recommended_contract && (
                          <span className="px-2 py-0.5 bg-blue-600 text-white text-[10px] font-bold rounded">Recommended</span>
                        )}
                      </div>
                      <span className="text-sm font-bold text-emerald-400">{formatUSD(opt.rate_usd_per_mt, 2)}/MT</span>
                    </div>
                    <div className="mt-2 grid grid-cols-2 text-xs text-gray-400 gap-2">
                      <div>Total Cost: <span className="text-white font-medium">{formatUSD(opt.total_cost_usd, 0)}</span></div>
                      <div>Flexibility: <span className="text-white font-medium">{opt.flexibility_score}/100</span></div>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">{opt.duration}</p>
                  </div>
                ))}

                <div className="p-3 bg-gray-950/60 rounded-xl border border-gray-800 text-xs text-gray-300">
                  <span className="font-bold text-blue-400">Contract Analysis: </span>
                  {data.contracts.reasoning}
                </div>
              </div>
            </Card>
          </div>

          {/* Flow Stage 7: Risk Factors */}
          <Card title="Stage 7: Multi-Factor Risk Assessment" subtitle="8-pillar operational, geopolitical, and freight volatility scoring">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {data.risk.risk_factors.map((rf) => (
                <div key={rf.name} className="p-3 bg-gray-800/40 border border-gray-800 rounded-xl flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] font-bold uppercase text-gray-400">{rf.category}</span>
                      <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold ${riskBg(rf.level as RiskLevel)}`}>
                        {rf.level}
                      </span>
                    </div>
                    <p className="text-xs font-bold text-white">{rf.name}</p>
                    <p className="text-[11px] text-gray-400 mt-1 line-clamp-2">{rf.description}</p>
                  </div>
                  <div className="mt-2 pt-2 border-t border-gray-800 text-[11px] text-blue-300">
                    <span className="font-semibold text-gray-400">Mitigation: </span>{rf.mitigation}
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Flow Stage 8: Final Recommendation & Explanation */}
          <Card title="Stage 8: Final Integrated Recommendation & Executive Briefing" className="border-emerald-500/40 bg-gradient-to-br from-gray-900 via-blue-950/20 to-gray-900">
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl mb-4">
              <div className="flex items-center gap-3">
                <CheckCircle2 size={24} className="text-emerald-400 flex-shrink-0" />
                <div>
                  <h3 className="text-base font-bold text-white">
                    Executive Chartering Decision: Fix {data.recommended_vessel} on {data.final_recommendation.recommended_contract} Contract
                  </h3>
                  <p className="text-xs text-emerald-300 mt-0.5">
                    Timing Signal: {data.market_entry.signal} · {data.market_entry.best_entry_window} · Port Status: {data.final_recommendation.port_status}
                  </p>
                </div>
              </div>
            </div>

            {/* Explanation Narrative */}
            <div className="p-4 bg-gray-950/60 rounded-xl border border-gray-800 text-sm leading-relaxed text-gray-200">
              <p className="font-medium text-white mb-2 flex items-center gap-1.5">
                <FileText size={16} className="text-blue-400" />
                Analytical Explanation & Justification
              </p>
              <p className="text-xs md:text-sm text-gray-300">{data.explanation}</p>
            </div>

            {/* Step-by-Step Action Items */}
            <div className="mt-4 space-y-2">
              <p className="text-xs font-bold uppercase text-gray-400 tracking-wider">Immediate Action Items</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {data.final_recommendation.action_items.map((act, idx) => (
                  <div key={idx} className="p-2.5 bg-gray-800/40 border border-gray-800 rounded-lg text-xs text-gray-300 flex items-start gap-2">
                    <span className="w-4 h-4 rounded-full bg-blue-500/20 text-blue-400 font-bold flex items-center justify-center text-[10px] flex-shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <span>{act}</span>
                  </div>
                ))}
              </div>
            </div>
          </Card>

          <Disclaimer text={data.disclaimer} />
        </div>
      )}
    </div>
  )
}
