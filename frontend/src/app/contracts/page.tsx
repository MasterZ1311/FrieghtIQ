'use client'
import { useState, useEffect, useCallback } from 'react'
import { api } from '@/lib/api'
import {
  formatUSD,
  formatNumber,
  ORIGINS,
  DESTINATIONS,
  VESSEL_CLASSES,
  COMMODITIES,
} from '@/lib/utils'
import {
  Card,
  Loading,
  ErrorBox,
  Disclaimer,
  Select,
  Input,
  PageHeader,
  ProgressBar,
  DataModeBadge,
} from '@/components/ui'
import type { ContractCompareResponse, VesselClass, Commodity } from '@/types'
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
  AreaChart,
  Area,
  Line,
} from 'recharts'
import { ShieldCheck } from 'lucide-react'

const CONTRACT_COLORS: Record<string, string> = {
  'Spot Market (Voyage Charter)': '#f59e0b',
  'Short-Term COA (3–6 Months)': '#3b82f6',
  'Medium-Term Time Charter (12 Months)': '#10b981',
  Spot: '#f59e0b',
  'Short-Term': '#3b82f6',
  'Medium-Term': '#10b981',
}

export default function ContractsPage() {
  const [origin, setOrigin] = useState('Australia')
  const [destination, setDestination] = useState('Paradip')
  const [vesselClass, setVesselClass] = useState<VesselClass>('Panamax')
  const [commodity, setCommodity] = useState<Commodity>('Coal')
  const [cargo, setCargo] = useState('70000')
  const [annualVolume, setAnnualVolume] = useState('500000')
  const [horizon, setHorizon] = useState('12')

  const [result, setResult] = useState<ContractCompareResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isLiveApi, setIsLiveApi] = useState(false)

  const handleCompare = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [health, res] = await Promise.all([
        api.health(),
        api.contracts.compare({
          origin,
          destination,
          vessel_class: vesselClass,
          commodity,
          cargo_mt: Number(cargo) || 70000,
          annual_volume_mt: Number(annualVolume) || 500000,
          planning_horizon_months: Number(horizon) || 12,
        }),
      ])
      setIsLiveApi(health.isLive)
      setResult(res)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Contract comparison failed')
    } finally {
      setLoading(false)
    }
  }, [origin, destination, vesselClass, commodity, cargo, annualVolume, horizon])

  useEffect(() => {
    handleCompare()
  }, [handleCompare])

  return (
    <div className="p-8 max-w-[1700px] mx-auto">
      <PageHeader
        title="Contract Simulator & Economics Engine"
        subtitle="Compare Spot, Short-Term COA, and Medium-Term Time Charter economics with cashflow risk modeling."
      >
        <DataModeBadge isLive={isLiveApi} />
      </PageHeader>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Parameters */}
        <div className="lg:col-span-4 space-y-5">
          <Card title="Contract Parameters" subtitle="Configure annual commitment and volume target">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <Select label="Origin" value={origin} onChange={setOrigin} options={ORIGINS} />
                <Select label="Destination" value={destination} onChange={setDestination} options={DESTINATIONS} />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <Select
                  label="Vessel Class"
                  value={vesselClass}
                  onChange={(v) => setVesselClass(v as VesselClass)}
                  options={VESSEL_CLASSES}
                />
                <Select
                  label="Commodity"
                  value={commodity}
                  onChange={(v) => setCommodity(v as Commodity)}
                  options={COMMODITIES}
                />
              </div>

              <Input label="Single Parcel Size (MT)" value={cargo} onChange={setCargo} type="number" />
              <Input
                label="Annual Procurement Volume (MT)"
                value={annualVolume}
                onChange={setAnnualVolume}
                type="number"
              />
              <Input
                label="Planning Horizon (months)"
                value={horizon}
                onChange={setHorizon}
                type="number"
                min={1}
                max={24}
              />

              <button
                onClick={handleCompare}
                disabled={loading}
                className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 text-white rounded-xl text-xs font-bold uppercase tracking-wider transition shadow flex items-center justify-center gap-1.5 mt-2"
              >
                {loading ? 'Simulating Economics…' : 'Simulate Contract Economics'}
              </button>
            </div>
          </Card>

          {/* Strategy Tip */}
          <div className="p-4 bg-gray-900/60 border border-gray-800 rounded-xl text-xs space-y-2 text-gray-400">
            <h4 className="text-[11px] font-bold text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldCheck size={14} className="text-emerald-400" />
              Chartering Portfolio Best Practice
            </h4>
            <p className="leading-relaxed">
              For annual volumes exceeding 500,000 MT into East Coast India, an unhedged 100% spot
              strategy risks severe margin erosion during Q3/Q4 pre-winter restocking.
            </p>
          </div>
        </div>

        {/* Results & Contract Economics Visuals */}
        <div className="lg:col-span-8 space-y-5">
          {error && <ErrorBox message={error} />}
          {loading && <Loading message="Computing 12-month contract economics and cashflow distributions…" />}

          {result && (
            <>
              {/* Recommendation Banner */}
              <div className="p-5 bg-gradient-to-r from-emerald-950/40 via-gray-900 to-gray-900 border border-emerald-600/50 rounded-2xl flex flex-wrap items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider">
                      Recommended Procurement Strategy
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500 text-slate-950">
                      ★ HIGHEST VALUE
                    </span>
                  </div>
                  <h3 className="text-2xl font-black text-white mt-0.5">
                    {result.recommended_contract}
                  </h3>
                  <p className="text-xs text-gray-300 max-w-2xl mt-1 leading-relaxed">
                    {result.reasoning}
                  </p>
                  {result.blended_strategy && (
                    <div className="mt-2 text-xs text-blue-400 font-medium">
                      Optimal Blended Strategy: <strong>{result.blended_strategy}</strong>
                    </div>
                  )}
                </div>

                <div className="text-right">
                  <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">
                    Expected Savings vs. Spot
                  </span>
                  <p className="text-2xl font-black text-emerald-300 mt-0.5">
                    +{formatUSD(result.expected_saving_vs_spot, 0)}
                  </p>
                  <span className="text-xs text-gray-400">Annualized Dollar Benefit</span>
                </div>
              </div>

              {/* ─── CONTRACT ECONOMICS CHART 1: TOTAL EXPENDITURE COMPARISON ─── */}
              <Card
                title="Total Annual Expenditure by Contract Structure"
                subtitle={`Projected total logistics expenditure for ${formatNumber(
                  result.annual_volume_mt
                )} MT commitment`}
              >
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={result.options} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                    <XAxis
                      dataKey="contract_type"
                      stroke="#6b7280"
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v) => (v ? v.split(' ')[0] : '')}
                    />
                    <YAxis
                      stroke="#6b7280"
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v) => `$${(v / 1e6).toFixed(1)}M`}
                    />
                    <Tooltip
                      contentStyle={{
                        background: '#111827',
                        border: '1px solid #374151',
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                      formatter={(v: unknown, name: unknown) => [formatUSD(Number(v || 0), 0), String(name)]}
                    />
                    <Bar dataKey="total_cost_usd" name="Total Expenditure" radius={[4, 4, 0, 0]}>
                      {result.options.map((opt, i) => (
                        <Cell
                          key={i}
                          fill={CONTRACT_COLORS[opt.contract_type] || '#3b82f6'}
                          opacity={opt.recommended ? 1 : 0.65}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Card>

              {/* ─── CONTRACT ECONOMICS CHART 2: MONTHLY CASHFLOW PROJECTION ─── */}
              {result.monthly_cashflow && result.monthly_cashflow.length > 0 && (
                <Card
                  title="Monthly Cashflow Volatility Profile (Spot vs. COA vs. Time Charter)"
                  subtitle="Spot procurement suffers from freight rate swings; COA and Time Charter offer stable, predictable monthly outlays"
                >
                  <ResponsiveContainer width="100%" height={240}>
                    <AreaChart data={result.monthly_cashflow} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
                      <defs>
                        <linearGradient id="spotGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                      <XAxis dataKey="month" stroke="#6b7280" tick={{ fontSize: 11 }} />
                      <YAxis
                        stroke="#6b7280"
                        tick={{ fontSize: 11 }}
                        tickFormatter={(v) => `$${(v / 1e3).toFixed(0)}k`}
                      />
                      <Tooltip
                        contentStyle={{
                          background: '#111827',
                          border: '1px solid #374151',
                          borderRadius: 8,
                          fontSize: 12,
                        }}
                        formatter={(v: unknown, name: unknown) => [
                          formatUSD(Number(v || 0), 0),
                          name === 'spot_cost'
                            ? 'Spot Market'
                            : name === 'short_term_cost'
                            ? 'Short-Term COA'
                            : 'Medium-Term Time Charter',
                        ]}
                      />
                      <Legend wrapperStyle={{ fontSize: 11, paddingTop: 6 }} />
                      <Area
                        type="monotone"
                        dataKey="spot_cost"
                        stroke="#f59e0b"
                        strokeWidth={2}
                        fill="url(#spotGrad)"
                        name="spot_cost"
                      />
                      <Line
                        type="monotone"
                        dataKey="short_term_cost"
                        stroke="#3b82f6"
                        strokeWidth={2.5}
                        dot={false}
                        name="short_term_cost"
                      />
                      <Line
                        type="monotone"
                        dataKey="medium_term_cost"
                        stroke="#10b981"
                        strokeWidth={2}
                        strokeDasharray="4 4"
                        dot={false}
                        name="medium_term_cost"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </Card>
              )}

              {/* 3 Contract Options Detail Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {result.options.map((opt) => (
                  <div
                    key={opt.contract_type}
                    className={`p-4 rounded-2xl border flex flex-col justify-between ${
                      opt.recommended
                        ? 'bg-emerald-950/20 border-emerald-500 shadow ring-1 ring-emerald-500/30'
                        : 'bg-gray-900 border-gray-800'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-white line-clamp-1">
                          {opt.contract_type}
                        </span>
                        {opt.recommended && (
                          <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-emerald-500 text-slate-950 whitespace-nowrap">
                            Recommended
                          </span>
                        )}
                      </div>

                      <p className="text-2xl font-black text-white mt-1">
                        {formatUSD(opt.rate_usd_per_mt, 2)}
                        <span className="text-xs font-normal text-gray-400">/MT</span>
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        Total: {formatUSD(opt.total_cost_usd, 0)}
                      </p>

                      {/* Trade-off Meters */}
                      <div className="mt-4 space-y-2 text-xs">
                        <div>
                          <div className="flex justify-between text-[11px] text-gray-400 mb-1">
                            <span>Flexibility Score</span>
                            <span className="font-bold text-gray-200">{opt.flexibility_score}%</span>
                          </div>
                          <ProgressBar value={opt.flexibility_score} color="bg-blue-500" />
                        </div>
                        <div>
                          <div className="flex justify-between text-[11px] text-gray-400 mb-1">
                            <span>Risk Exposure</span>
                            <span className="font-bold text-gray-200">{opt.risk_score}%</span>
                          </div>
                          <ProgressBar
                            value={opt.risk_score}
                            color={opt.risk_score > 60 ? 'bg-red-500' : 'bg-emerald-500'}
                          />
                        </div>
                      </div>

                      {/* Pros & Cons */}
                      <div className="mt-4 pt-3 border-t border-gray-800 text-xs space-y-2">
                        <div>
                          <p className="text-[11px] font-semibold text-emerald-400 mb-1">✓ Pros</p>
                          {opt.pros.map((p, i) => (
                            <p key={i} className="text-gray-300 text-[11px] leading-tight mb-1">
                              • {p}
                            </p>
                          ))}
                        </div>
                        <div>
                          <p className="text-[11px] font-semibold text-amber-400 mb-1">⚠ Cons</p>
                          {opt.cons.map((c, i) => (
                            <p key={i} className="text-gray-400 text-[11px] leading-tight mb-1">
                              • {c}
                            </p>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          <Disclaimer text={result?.disclaimer || 'DEMO BENCHMARK DATA: FreightIQ Contract Economics.'} />
        </div>
      </div>
    </div>
  )
}
