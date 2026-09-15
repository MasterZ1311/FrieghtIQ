'use client'
import { useState, useEffect, useCallback } from 'react'
import { api } from '@/lib/api'
import {
  formatUSD,
  formatNumber,
  ORIGINS,
  DESTINATIONS,
  COMMODITIES,
  feasibilityConfig,
  idleRiskConfig,
} from '@/lib/utils'
import {
  Card,
  Loading,
  ErrorBox,
  Disclaimer,
  Select,
  Input,
  PageHeader,
  StatCard,
  ProgressBar,
  DataModeBadge,
} from '@/components/ui'
import type { VesselRecommendResponse, Commodity, VesselClass } from '@/types'
import {
  Ship,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Sparkles,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
} from 'recharts'

export default function VesselsPage() {
  const [origin, setOrigin] = useState('Australia')
  const [destination, setDestination] = useState('Visakhapatnam')
  const [commodity, setCommodity] = useState<Commodity>('Coal')
  const [cargo, setCargo] = useState('70000')
  const [budget, setBudget] = useState('')

  const [result, setResult] = useState<VesselRecommendResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isLiveApi, setIsLiveApi] = useState(false)
  const [selectedVessel, setSelectedVessel] = useState<VesselClass>('Panamax')

  const handleRecommend = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [health, res] = await Promise.all([
        api.health(),
        api.vessels.recommend({
          origin,
          destination,
          commodity,
          cargo_mt: Number(cargo) || 70000,
          budget_usd_per_mt: budget ? Number(budget) : undefined,
        }),
      ])
      setIsLiveApi(health.isLive)
      setResult(res)
      if (res.recommended_class) {
        setSelectedVessel(res.recommended_class)
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Vessel analysis failed')
    } finally {
      setLoading(false)
    }
  }, [origin, destination, commodity, cargo, budget])

  useEffect(() => {
    handleRecommend()
  }, [handleRecommend])

  const fitScoreColor = (score: number) =>
    score >= 85 ? 'bg-emerald-500' : score >= 65 ? 'bg-blue-500' : score >= 45 ? 'bg-amber-500' : 'bg-red-500'

  // Prepare chart comparison data
  const comparisonChartData = result?.detailed_comparison.map((v) => ({
    name: v.vessel_class,
    score: v.overall_score,
    rate: v.estimated_freight_usd_per_mt,
    turnaround: v.estimated_turnaround_days,
    isRecommended: v.vessel_class === result.recommended_class,
  })) || []

  return (
    <div className="p-8 max-w-[1700px] mx-auto">
      <PageHeader
        title="Vessel Optimization & 4-Class Comparison"
        subtitle="Algorithmic vessel class selection and multi-dimensional benchmark comparing Handysize, Supramax, Panamax, and Capesize bulkers."
      >
        <DataModeBadge isLive={isLiveApi} />
      </PageHeader>

      {/* Input Parameters Bar */}
      <Card className="mb-6 border-blue-900/40 bg-gray-900/90">
        <div className="grid grid-cols-1 md:grid-cols-6 gap-3 items-end">
          <Select label="Origin" value={origin} onChange={setOrigin} options={ORIGINS} />
          <Select label="Destination" value={destination} onChange={setDestination} options={DESTINATIONS} />
          <Select
            label="Commodity"
            value={commodity}
            onChange={(v) => setCommodity(v as Commodity)}
            options={COMMODITIES}
          />
          <Input label="Cargo Volume (MT)" value={cargo} onChange={setCargo} type="number" />
          <Input
            label="Budget Cap ($/MT, opt)"
            value={budget}
            onChange={setBudget}
            type="number"
            placeholder="e.g. 16.50"
          />
          <button
            onClick={handleRecommend}
            disabled={loading}
            className="w-full h-9 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 text-white font-bold text-xs uppercase tracking-wider rounded-lg transition shadow flex items-center justify-center gap-1.5"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <Sparkles size={14} />
                Optimize Fleet
              </>
            )}
          </button>
        </div>
      </Card>

      {error && <ErrorBox message={error} />}
      {loading && <Loading message="Evaluating vessel economics, draft clearances and port delays…" />}

      {result && (
        <div className="space-y-6">
          {/* Winner Banner */}
          <div className="p-5 bg-gradient-to-r from-blue-950/70 via-gray-900 to-gray-900 border border-blue-700/60 rounded-2xl flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/30 flex-shrink-0">
                <Ship size={24} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-bold text-blue-400 uppercase tracking-wider">
                    Recommended Vessel Class
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500 text-slate-950">
                    ★ OPTIMAL FIT
                  </span>
                </div>
                <h2 className="text-2xl font-black text-white mt-0.5">
                  {result.recommended_class}
                </h2>
                <p className="text-xs text-gray-300 max-w-2xl mt-1 leading-relaxed">
                  {result.reasoning}
                </p>
              </div>
            </div>

            <div className="text-right">
              <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
                Target Route
              </span>
              <p className="text-sm font-bold text-white mt-0.5">
                {origin} → {destination}
              </p>
              <span className="text-xs text-blue-400 font-mono">
                {formatNumber(Number(cargo))} MT {commodity}
              </span>
            </div>
          </div>

          {/* ─── 4-CLASS SIDE-BY-SIDE COMPARISON CARDS ─── */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-bold text-gray-300 uppercase tracking-wider flex items-center gap-2">
                <Ship size={15} className="text-blue-400" />
                Vessel Class Comparison Matrix (Handysize · Supramax · Panamax · Capesize)
              </h3>
              <span className="text-[11px] text-gray-400">
                Click any vessel card to inspect deep-dive
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
              {result.detailed_comparison.map((v) => {
                const isSelected = selectedVessel === v.vessel_class
                const isWinner = v.vessel_class === result.recommended_class
                const feasCfg = feasibilityConfig(v.feasibility)
                const idleCfg = idleRiskConfig(v.idle_risk)

                return (
                  <div
                    key={v.vessel_class}
                    onClick={() => setSelectedVessel(v.vessel_class)}
                    className={`cursor-pointer rounded-2xl border p-5 transition-all flex flex-col justify-between ${
                      isWinner
                        ? 'bg-blue-950/25 border-blue-500 shadow-md ring-1 ring-blue-500/40'
                        : isSelected
                        ? 'bg-gray-850 border-gray-600'
                        : 'bg-gray-900 border-gray-800 hover:border-gray-700'
                    }`}
                  >
                    <div>
                      {/* Top Vessel Header */}
                      <div className="flex items-start justify-between gap-2 mb-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="text-lg font-black text-white">{v.vessel_class}</h4>
                            {isWinner && (
                              <span className="px-1.5 py-0.2 bg-blue-600 text-white rounded text-[10px] font-bold">
                                ★ BEST
                              </span>
                            )}
                          </div>
                          <p className="text-[11px] text-gray-400 font-mono mt-0.5">{v.dwt_range}</p>
                        </div>

                        {/* Overall Score Badge */}
                        <div className="text-right">
                          <span className="text-[10px] text-gray-400 uppercase font-semibold">Score</span>
                          <p className="text-lg font-black text-white leading-none mt-0.5">
                            {v.overall_score}
                            <span className="text-[10px] font-normal text-gray-500">/100</span>
                          </p>
                        </div>
                      </div>

                      {/* Score Bar */}
                      <div className="mb-4">
                        <ProgressBar value={v.overall_score} color={fitScoreColor(v.overall_score)} />
                      </div>

                      {/* 7 Required Metrics */}
                      <div className="space-y-2.5 text-xs">
                        {/* 1. Feasibility */}
                        <div className="flex items-center justify-between p-2 bg-gray-950/60 rounded-lg">
                          <span className="text-gray-400">1. Feasibility:</span>
                          <span
                            className={`px-2 py-0.5 rounded text-[11px] font-bold border ${feasCfg.bg} ${feasCfg.color} ${feasCfg.border}`}
                          >
                            {v.feasibility}
                          </span>
                        </div>

                        {/* 2. Estimated Freight */}
                        <div className="flex items-center justify-between p-2 bg-gray-950/60 rounded-lg">
                          <span className="text-gray-400">2. Est. Freight:</span>
                          <span className="font-black text-white text-sm">
                            {formatUSD(v.estimated_freight_usd_per_mt, 2)}
                            <span className="text-[10px] font-normal text-gray-400">/MT</span>
                          </span>
                        </div>

                        {/* 3. Cargo Capacity */}
                        <div className="flex items-center justify-between p-2 bg-gray-950/60 rounded-lg">
                          <span className="text-gray-400">3. Cargo Capacity:</span>
                          <span className="font-semibold text-gray-200 text-right font-mono text-[11px]">
                            {v.cargo_capacity_mt}
                          </span>
                        </div>

                        {/* 4. Port Compatibility */}
                        <div className="p-2 bg-gray-950/60 rounded-lg">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-gray-400">4. Port Clearances:</span>
                            <span
                              className={`font-bold text-[11px] flex items-center gap-1 ${
                                v.port_compatible ? 'text-emerald-400' : 'text-red-400'
                              }`}
                            >
                              {v.port_compatible ? (
                                <>
                                  <CheckCircle2 size={12} /> Cleared
                                </>
                              ) : (
                                <>
                                  <XCircle size={12} /> Restricted
                                </>
                              )}
                            </span>
                          </div>
                          <p className="text-[10px] text-gray-400 leading-tight line-clamp-2">
                            {v.port_compatibility}
                          </p>
                        </div>

                        {/* 5. Estimated Turnaround */}
                        <div className="flex items-center justify-between p-2 bg-gray-950/60 rounded-lg">
                          <span className="text-gray-400">5. Turnaround:</span>
                          <span className="font-semibold text-gray-200">
                            {v.estimated_turnaround_days} Days
                          </span>
                        </div>

                        {/* 6. Idle Risk */}
                        <div className="flex items-center justify-between p-2 bg-gray-950/60 rounded-lg">
                          <span className="text-gray-400">6. Idle Risk:</span>
                          <div className="text-right">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${idleCfg.bg} ${idleCfg.color}`}
                            >
                              {v.idle_risk}
                            </span>
                            <p className="text-[10px] text-gray-400 mt-0.5 font-mono">
                              Exp: {formatUSD(v.idle_cost_risk_usd, 0)}
                            </p>
                          </div>
                        </div>

                        {/* 7. Overall Score Summary */}
                        <div className="flex items-center justify-between p-2 bg-gray-950/60 rounded-lg">
                          <span className="text-gray-400">7. Overall Fit:</span>
                          <span className="font-black text-blue-400">
                            {v.overall_score} / 100
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Reasons preview */}
                    <div className="mt-4 pt-3 border-t border-gray-800 text-[11px]">
                      <p className="text-gray-400 font-semibold mb-1">Key Match Factor:</p>
                      <p className="text-gray-300 leading-tight line-clamp-2">
                        • {v.reasons[0] || 'Standard trade fit'}
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* ─── CHARTS & DETAILED BREAKDOWN ─── */}
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
            {/* Fit Score & Freight Comparison Chart */}
            <Card
              title="Vessel Score & Freight Rate Trade-Off"
              subtitle="Comparison of benchmarked Fit Score (0-100) and Freight $/MT across all 4 vessel classes"
              className="xl:col-span-6"
            >
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={comparisonChartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="name" stroke="#6b7280" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#6b7280" tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      background: '#111827',
                      border: '1px solid #374151',
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                    formatter={(v: unknown, name: unknown) => [
                      name === 'score' ? `${v}/100` : `$${Number(v || 0).toFixed(2)}/MT`,
                      name === 'score' ? 'Overall Fit Score' : 'Freight Rate',
                    ]}
                  />
                  <Legend wrapperStyle={{ fontSize: 11, paddingTop: 6 }} />
                  <Bar dataKey="score" name="Fit Score" radius={[4, 4, 0, 0]}>
                    {comparisonChartData.map((entry, idx) => (
                      <Cell
                        key={`cell-${idx}`}
                        fill={entry.isRecommended ? '#3b82f6' : '#4b5563'}
                      />
                    ))}
                  </Bar>
                  <Bar dataKey="rate" name="Freight $/MT" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>

            {/* Selected Vessel Deep Dive Details */}
            {(() => {
              const current =
                result.detailed_comparison.find((v) => v.vessel_class === selectedVessel) ||
                result.detailed_comparison[0]
              return (
                <Card
                  title={`Deep Dive: ${current.vessel_class} Bulker Profile`}
                  subtitle="Detailed operational parameters, fuel consumption and reasons"
                  className="xl:col-span-6"
                >
                  <div className="grid grid-cols-3 gap-3 mb-4">
                    <StatCard
                      label="Daily Time Charter"
                      value={formatUSD(current.daily_hire_usd, 0) + '/d'}
                      subValue="Market Daily Hire"
                    />
                    <StatCard
                      label="Fuel Consumption"
                      value={`${current.fuel_burn_sea_mt_day} MT/d`}
                      subValue="Sea Speed at 14 kn"
                    />
                    <StatCard
                      label="Optimal Parcel"
                      value={`${(current.optimal_parcel_mt / 1000).toFixed(0)}k MT`}
                      subValue="Intake Capacity"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div className="p-3 bg-gray-950/60 rounded-xl border border-gray-800">
                      <h5 className="font-semibold text-emerald-400 mb-2 flex items-center gap-1">
                        <CheckCircle2 size={14} /> Advantages & Reasons
                      </h5>
                      <ul className="space-y-1.5 text-gray-300">
                        {current.reasons.map((r, i) => (
                          <li key={i} className="flex items-start gap-1.5">
                            <span className="text-emerald-400">•</span>
                            <span>{r}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="p-3 bg-gray-950/60 rounded-xl border border-gray-800">
                      <h5 className="font-semibold text-amber-400 mb-2 flex items-center gap-1">
                        <AlertTriangle size={14} /> Constraints & Warnings
                      </h5>
                      <ul className="space-y-1.5 text-gray-300">
                        {current.warnings.map((w, i) => (
                          <li key={i} className="flex items-start gap-1.5">
                            <span className="text-amber-400">•</span>
                            <span>{w}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </Card>
              )
            })()}
          </div>

          <Disclaimer text={result.disclaimer} />
        </div>
      )}
    </div>
  )
}
