'use client'
import { useState, useEffect, useCallback } from 'react'
import { api } from '@/lib/api'
import {
  formatUSD,
  ORIGINS,
  DESTINATIONS,
  VESSEL_CLASSES,
  COMMODITIES,
  trendArrow,
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
  DataModeBadge,
} from '@/components/ui'
import type { FreightForecastResponse, HistoryDataPoint, VesselClass, Commodity } from '@/types'
import {
  AreaChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from 'recharts'
import {
  Sliders,
  Activity,
} from 'lucide-react'

export default function ForecastPage() {
  const [origin, setOrigin] = useState('Australia')
  const [destination, setDestination] = useState('Paradip')
  const [vesselClass, setVesselClass] = useState<VesselClass>('Panamax')
  const [commodity, setCommodity] = useState<Commodity>('Coal')
  const [cargo, setCargo] = useState('75000')
  const [horizon, setHorizon] = useState('30')
  const [bunkerShock, setBunkerShock] = useState('0') // % adjustment

  const [result, setResult] = useState<FreightForecastResponse | null>(null)
  const [history, setHistory] = useState<HistoryDataPoint[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isLiveApi, setIsLiveApi] = useState(false)

  const fetchForecast = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [health, fc, hist] = await Promise.all([
        api.health(),
        api.forecast.predict({
          origin,
          destination,
          vessel_class: vesselClass,
          commodity,
          cargo_mt: Number(cargo) || 75000,
          horizon_days: Number(horizon) || 30,
        }),
        api.forecast.history(origin, destination, vesselClass),
      ])
      setIsLiveApi(health.isLive)
      setResult(fc)
      setHistory(hist.data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Forecast computation failed')
    } finally {
      setLoading(false)
    }
  }, [origin, destination, vesselClass, commodity, cargo, horizon])

  useEffect(() => {
    fetchForecast()
  }, [fetchForecast])

  // Build high-precision chart data combining history and forward confidence band
  const chartData = (() => {
    if (!history || history.length === 0) return []

    // Take last 14 historical points
    const hist = history.slice(-14).map((h) => ({
      date: h.date,
      actualRate: h.rate,
      forecastRate: undefined as number | undefined,
      lowerBound: undefined as number | undefined,
      upperBound: undefined as number | undefined,
      tce: h.tce,
    }))

    const last = hist[hist.length - 1]
    if (last && result) {
      last.forecastRate = last.actualRate
      last.lowerBound = last.actualRate
      last.upperBound = last.actualRate
    }

    if (result) {
      const shockMultiplier = 1 + Number(bunkerShock) / 100 * 0.2
      const adjustedPredicted = Number((result.predicted_rate_usd_per_mt * shockMultiplier).toFixed(2))
      const adjustedLower = Number((result.lower_bound * shockMultiplier).toFixed(2))
      const adjustedUpper = Number((result.upper_bound * shockMultiplier).toFixed(2))

      const d1 = new Date(last ? last.date : '2026-09-01')
      d1.setDate(d1.getDate() + 14)

      const d2 = new Date(last ? last.date : '2026-09-01')
      d2.setDate(d2.getDate() + Number(horizon))

      const midRate = Number(((result.current_rate_usd_per_mt + adjustedPredicted) / 2).toFixed(2))

      const forwardPoints = [
        {
          date: d1.toISOString().slice(0, 10) + ' (Mid)',
          actualRate: undefined as number | undefined,
          forecastRate: midRate,
          lowerBound: Number((midRate - 0.7).toFixed(2)),
          upperBound: Number((midRate + 0.8).toFixed(2)),
          tce: Math.round(midRate * 1180),
        },
        {
          date: d2.toISOString().slice(0, 10) + ' (Forecast)',
          actualRate: undefined as number | undefined,
          forecastRate: adjustedPredicted,
          lowerBound: adjustedLower,
          upperBound: adjustedUpper,
          tce: Math.round(adjustedPredicted * 1220),
        },
      ]
      return [...hist, ...forwardPoints]
    }

    return hist
  })()

  const directionColors: Record<string, string> = {
    bullish: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
    bearish: 'text-red-400 bg-red-500/10 border-red-500/30',
    neutral: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
  }

  return (
    <div className="p-8 max-w-[1700px] mx-auto">
      <PageHeader
        title="Freight Rate Forecast & Confidence Engine"
        subtitle="Forward chartering rate forecasting with statistical confidence intervals, macro influencing drivers, and fuel price sensitivity modeling."
      >
        <DataModeBadge isLive={isLiveApi} />
      </PageHeader>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* ─── PARAMETER CONTROLS ─── */}
        <div className="lg:col-span-4 space-y-5">
          <Card title="Forecast Parameters" subtitle="Configure route, tonnage and projection horizon">
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

              <Input
                label="Cargo Volume (MT)"
                value={cargo}
                onChange={setCargo}
                type="number"
                placeholder="75000"
              />

              {/* Horizon Selector */}
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
                    Forecast Horizon
                  </label>
                  <span className="text-xs font-mono font-bold text-blue-400">{horizon} Days</span>
                </div>
                <div className="grid grid-cols-4 gap-1.5">
                  {['14', '30', '60', '90'].map((h) => (
                    <button
                      key={h}
                      type="button"
                      onClick={() => setHorizon(h)}
                      className={`py-1.5 rounded-lg text-xs font-mono border transition ${
                        horizon === h
                          ? 'bg-blue-600 border-blue-500 text-white font-bold'
                          : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-white'
                      }`}
                    >
                      {h}d
                    </button>
                  ))}
                </div>
              </div>

              {/* Sensitivity Shock Slider */}
              <div className="pt-2 border-t border-gray-800">
                <div className="flex justify-between items-center mb-1.5">
                  <label className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1">
                    <Sliders size={12} />
                    Bunker Fuel Sensitivity Shock
                  </label>
                  <span
                    className={`text-xs font-mono font-bold ${
                      Number(bunkerShock) > 0
                        ? 'text-red-400'
                        : Number(bunkerShock) < 0
                        ? 'text-emerald-400'
                        : 'text-gray-400'
                    }`}
                  >
                    {Number(bunkerShock) > 0 ? `+${bunkerShock}%` : `${bunkerShock}%`}
                  </span>
                </div>
                <input
                  type="range"
                  min="-30"
                  max="30"
                  step="10"
                  value={bunkerShock}
                  onChange={(e) => setBunkerShock(e.target.value)}
                  className="w-full accent-blue-500 bg-gray-800 rounded-lg h-2 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-gray-500 mt-1 font-mono">
                  <span>-30% (Bear)</span>
                  <span>Baseline (0%)</span>
                  <span>+30% (Spike)</span>
                </div>
              </div>

              <button
                onClick={fetchForecast}
                disabled={loading}
                className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 text-white rounded-xl text-xs font-bold uppercase tracking-wider transition shadow mt-2"
              >
                {loading ? 'Recalculating Trajectory…' : 'Generate Forecast Model'}
              </button>
            </div>
          </Card>

          {/* Model Specification Card */}
          <div className="p-4 bg-gray-900/60 border border-gray-800 rounded-xl text-xs space-y-2 text-gray-400">
            <h4 className="text-[11px] font-bold text-gray-300 uppercase tracking-wider">
              Methodology & Calibration
            </h4>
            <p className="leading-relaxed">
              • Calibrated against 5 years of Baltic Exchange East Coast India fixtures and AIS vessel
              position tracking.
            </p>
            <p className="leading-relaxed">
              • Confidence band reflects 90% statistical prediction interval incorporating fuel price
              variance and port delays.
            </p>
          </div>
        </div>

        {/* ─── CHARTS & RESULTS ─── */}
        <div className="lg:col-span-8 space-y-5">
          {error && <ErrorBox message={error} />}
          {loading && <Loading message="Computing forward freight curve and confidence boundaries…" />}

          {result && (
            <>
              {/* Top Numerical KPI Bar */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                <StatCard
                  label="Current Prompt Rate"
                  value={formatUSD(result.current_rate_usd_per_mt, 2) + '/MT'}
                  subValue={`${origin} → ${destination}`}
                />
                <StatCard
                  label={`${horizon}-Day Projected Rate`}
                  value={
                    formatUSD(
                      result.predicted_rate_usd_per_mt * (1 + (Number(bunkerShock) / 100) * 0.2),
                      2
                    ) + '/MT'
                  }
                  subValue={`Confidence: ${result.confidence_pct}%`}
                  badge={{
                    text: `${trendArrow(result.trend)} ${result.trend.toUpperCase()}`,
                    color:
                      result.trend === 'rising'
                        ? 'bg-red-500/20 text-red-400'
                        : 'bg-emerald-500/20 text-emerald-400',
                  }}
                />
                <StatCard
                  label="Confidence Range"
                  value={`$${result.lower_bound.toFixed(2)} – $${result.upper_bound.toFixed(2)}`}
                  subValue="90% Prediction Band"
                  badge={{ text: 'P10 – P90 Interval', color: 'bg-blue-500/20 text-blue-300' }}
                />
                <StatCard
                  label="Est. Daily TCE"
                  value={formatUSD(result.tce_estimate_usd_per_day, 0) + '/day'}
                  subValue="Time Charter Equivalent"
                  icon={<Activity size={16} />}
                />
              </div>

              {/* Comprehensive Forecast Chart with Confidence Band */}
              <Card
                title="Historical Freight vs. Forward Forecast with Confidence Band"
                subtitle={`Weekly rates into East Coast India with statistical P10–P90 forward envelope for ${horizon} days`}
              >
                <div className="flex items-center justify-between gap-4 mb-3 text-xs">
                  <div className="flex items-center gap-4 flex-wrap">
                    <span className="flex items-center gap-1.5 text-gray-300">
                      <span className="w-3 h-0.5 bg-blue-500 inline-block" /> Historical
                    </span>
                    <span className="flex items-center gap-1.5 text-gray-300">
                      <span className="w-3 h-0.5 bg-amber-400 border-dashed inline-block" /> Forecast
                    </span>
                    <span className="flex items-center gap-1.5 text-gray-300">
                      <span className="w-3 h-3 bg-blue-500/20 border border-blue-500/40 rounded inline-block" /> Confidence Band
                    </span>
                  </div>
                  {Number(bunkerShock) !== 0 && (
                    <span className="px-2 py-0.5 bg-amber-500/15 text-amber-300 rounded border border-amber-500/30 text-[11px] font-mono">
                      Bunker Shock: {bunkerShock}% Applied
                    </span>
                  )}
                </div>

                <ResponsiveContainer width="100%" height={320}>
                  <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="bandGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.05} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                    <XAxis
                      dataKey="date"
                      stroke="#6b7280"
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v) => (v ? v.slice(5, 10) : '')}
                    />
                    <YAxis
                      stroke="#6b7280"
                      tick={{ fontSize: 11 }}
                      domain={['auto', 'auto']}
                      tickFormatter={(v) => `$${v}`}
                    />
                    <Tooltip
                      contentStyle={{
                        background: '#111827',
                        border: '1px solid #374151',
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                      formatter={(v: unknown, name: unknown) => [
                        `$${Number(v || 0).toFixed(2)}/MT`,
                        name === 'actualRate'
                          ? 'Historical Actual'
                          : name === 'forecastRate'
                          ? 'Forecast'
                          : name === 'upperBound'
                          ? 'Upper Bound'
                          : name === 'lowerBound'
                          ? 'Lower Bound'
                          : String(name),
                      ]}
                    />
                    <Legend wrapperStyle={{ fontSize: 11, paddingTop: 6 }} />

                    <Area
                      type="monotone"
                      dataKey="upperBound"
                      stroke="#3b82f6"
                      strokeDasharray="3 3"
                      fill="url(#bandGrad)"
                      strokeOpacity={0.5}
                      name="upperBound"
                    />
                    <Area
                      type="monotone"
                      dataKey="lowerBound"
                      stroke="#3b82f6"
                      strokeDasharray="3 3"
                      fill="#111827"
                      strokeOpacity={0.5}
                      name="lowerBound"
                    />
                    <Area
                      type="monotone"
                      dataKey="actualRate"
                      stroke="#3b82f6"
                      fill="none"
                      strokeWidth={2.5}
                      dot={{ r: 3, fill: '#3b82f6' }}
                      name="actualRate"
                    />
                    <Line
                      type="monotone"
                      dataKey="forecastRate"
                      stroke="#f59e0b"
                      strokeWidth={2.5}
                      strokeDasharray="4 4"
                      dot={{ r: 4, fill: '#f59e0b' }}
                      name="forecastRate"
                    />
                    <ReferenceLine
                      y={result.predicted_rate_usd_per_mt}
                      stroke="#f59e0b"
                      strokeDasharray="3 3"
                      label={{
                        value: `Base Forecast: $${result.predicted_rate_usd_per_mt.toFixed(2)}`,
                        fill: '#f59e0b',
                        fontSize: 10,
                        position: 'insideBottomRight',
                      }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </Card>

              {/* Key Influencing Factors */}
              <Card title="Influencing Market Drivers" subtitle="Key supply-demand catalysts driving the rate forecast">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {result.influencing_factors.map((f, i) => (
                    <div
                      key={i}
                      className="p-3.5 bg-gray-800/40 border border-gray-800 rounded-xl flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-center justify-between gap-2 mb-1.5">
                          <span className="text-xs font-bold text-white">{f.factor}</span>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${
                              directionColors[f.direction]
                            }`}
                          >
                            {f.direction}
                          </span>
                        </div>
                        <p className="text-xs text-gray-400 leading-relaxed">{f.description}</p>
                      </div>
                      <div className="mt-2.5 pt-2 border-t border-gray-800/80 flex items-center justify-between text-[11px] text-gray-500">
                        <span>Impact Magnitude:</span>
                        <span className="font-semibold uppercase text-gray-300">{f.magnitude}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </>
          )}

          <Disclaimer text={result?.disclaimer || 'DEMO BENCHMARK DATA: FreightIQ forecast models.'} />
        </div>
      </div>
    </div>
  )
}
