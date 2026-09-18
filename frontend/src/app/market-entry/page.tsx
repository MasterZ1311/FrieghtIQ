'use client'
import { useState, useEffect, useCallback } from 'react'
import { api } from '@/lib/api'
import { formatUSD, ORIGINS, DESTINATIONS, VESSEL_CLASSES, COMMODITIES, signalConfig } from '@/lib/utils'
import { Card, Loading, ErrorBox, Disclaimer, Select, Input, PageHeader, StatCard, EmptyState, DemoBadge } from '@/components/ui'
import type { MarketEntryResponse, VesselClass, Commodity } from '@/types'
import { Sparkles, DollarSign, Clock, ShieldCheck } from 'lucide-react'
import OptionValueCard from '@/components/ui/OptionValueCard'


export default function MarketEntryPage() {
  const [origin, setOrigin] = useState('Australia')
  const [destination, setDestination] = useState('Paradip')
  const [vesselClass, setVesselClass] = useState<VesselClass>('Panamax')
  const [commodity, setCommodity] = useState<Commodity>('Coal')
  const [cargo, setCargo] = useState('70000')
  const [urgency, setUrgency] = useState('30')
  const [result, setResult] = useState<MarketEntryResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.marketEntry.signal({
        origin, destination, vessel_class: vesselClass,
        commodity, cargo_mt: Number(cargo), urgency_days: Number(urgency),
      })
      setResult(res)
    } catch (e: unknown) {
      const err = e instanceof Error ? e.message : 'Market entry signal generation failed'
      setError(err)
    } finally {
      setLoading(false)
    }
  }, [origin, destination, vesselClass, commodity, cargo, urgency])

  useEffect(() => {
    handleSubmit()
  }, [handleSubmit])

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <PageHeader
        title="Market Entry Timing & Arbitrage Signal"
        subtitle="Algorithmic chartering execution signal: BUY NOW vs. WAIT vs. HEDGE evaluating spot curve gradient, seasonal demand, and supply tightness"
        actions={<DemoBadge />}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card title="Shipment Urgency Parameters" subtitle="Specify timing tolerance and volume" className="col-span-1">
          <div className="space-y-4">
            <Select label="Origin Corridor" value={origin} onChange={setOrigin} options={ORIGINS} />
            <Select label="Destination Port" value={destination} onChange={setDestination} options={DESTINATIONS} />
            <Select label="Vessel Class" value={vesselClass} onChange={(v) => setVesselClass(v as VesselClass)} options={VESSEL_CLASSES} />
            <Select label="Commodity" value={commodity} onChange={(v) => setCommodity(v as Commodity)} options={COMMODITIES} />
            <Input label="Cargo Volume (MT)" value={cargo} onChange={setCargo} type="number" />
            <Input label="Urgency Window (days)" value={urgency} onChange={setUrgency} type="number" min={0} max={180} />
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 text-white font-bold text-xs rounded-lg transition shadow-md shadow-blue-600/30 flex items-center justify-center gap-2 mt-2"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <Sparkles size={14} className="text-cyan-300" />
                  <span>Compute Market Signal</span>
                </>
              )}
            </button>
          </div>
        </Card>

        <div className="col-span-1 lg:col-span-2 space-y-5">
          {loading && <Loading message="Evaluating forward curves, bunker correlation & entry timing arbitrage…" />}
          {error && <ErrorBox message={error} onRetry={handleSubmit} />}

          {result && (() => {
            const cfg = signalConfig(result.signal)
            return (
              <>
                {/* Prominent Signal Banner */}
                <div className={`p-6 border-2 rounded-2xl shadow-xl ${cfg.bg}`}>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                        <span className="text-xs font-black tracking-wider uppercase text-gray-300">
                          Recommended Action
                        </span>
                      </div>
                      <p className={`text-4xl font-black tracking-tight ${cfg.color}`}>{cfg.label}</p>
                      <p className="text-gray-200 mt-2 text-sm leading-relaxed max-w-xl">{result.recommendation}</p>
                    </div>
                    <div className="p-4 bg-gray-950/60 rounded-xl border border-gray-800 text-right flex-shrink-0">
                      <p className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Model Confidence</p>
                      <p className="text-3xl font-black text-white tabular-nums">{result.confidence_pct}%</p>
                      <p className="text-[10px] text-emerald-400 font-semibold mt-0.5">High Conviction</p>
                    </div>
                  </div>
                </div>

                {/* Savings and Metrics Highlight */}
                <div className="grid grid-cols-3 gap-3.5">
                  <StatCard
                    label="Optimal Entry Window"
                    value={result.best_entry_window}
                    subValue="Recommended execution"
                    icon={<Clock size={16} />}
                  />
                  <StatCard
                    label="Estimated Timing Savings"
                    value={formatUSD(result.estimated_savings_usd, 0)}
                    subValue="vs. deferring to later window"
                    badge={{ text: 'Cost Avoidance', color: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' }}
                    icon={<DollarSign size={16} />}
                  />
                  <StatCard
                    label="Signal Conviction"
                    value={`${result.confidence_pct}%`}
                    subValue="Multi-factor model"
                    badge={{ text: result.confidence_pct >= 75 ? 'Optimal Window' : 'Moderate', color: result.confidence_pct >= 75 ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30' : 'bg-amber-500/20 text-amber-300 border border-amber-500/30' }}
                    icon={<ShieldCheck size={16} />}
                  />
                </div>

                {/* Reasons & Warnings */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card title="Drivers Supporting Signal" subtitle="Market fundamentals favoring this timing">
                    <ul className="space-y-2.5">
                      {result.reasons.map((r, i) => (
                        <li key={i} className="flex gap-2.5 text-xs text-gray-300">
                          <span className="text-emerald-400 font-bold flex-shrink-0">→</span>
                          <span className="leading-relaxed">{r}</span>
                        </li>
                      ))}
                    </ul>
                  </Card>

                  {result.warnings.length > 0 && (
                    <Card title="Market Execution Warnings" subtitle="Risk variables to monitor during charter negotiation">
                      <ul className="space-y-2.5">
                        {result.warnings.map((w, i) => (
                          <li key={i} className="flex gap-2.5 text-xs text-amber-300/90">
                            <span className="text-amber-400 font-bold flex-shrink-0">⚠</span>
                            <span className="leading-relaxed">{w}</span>
                          </li>
                        ))}
                      </ul>
                    </Card>
                  )}
                </div>

                {/* Real Options Timing Card (Black-Scholes-Merton) */}
                <OptionValueCard
                  initialRate={result?.current_rate_usd_per_mt || 28.4}
                  initialTarget={result?.predicted_rate_usd_per_mt || 26.0}
                  initialCargoMt={Number(cargo) || 70000}
                  initialDays={Number(urgency) || 30}
                  route={`${origin}_${destination}`}
                />


                {/* Alternative Execution Strategies */}
                <Card title="Alternative Chartering Execution Strategies" subtitle="Trade-off evaluation of alternative procurement postures">

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                    {result.alternative_strategies.map((s, i) => (
                      <div key={i} className="p-3.5 bg-gray-950/60 border border-gray-800 rounded-xl space-y-2">
                        <p className="font-bold text-white text-xs">{s.strategy}</p>
                        <p className="text-[11px] text-gray-400 leading-relaxed">{s.description}</p>
                        <div className="grid grid-cols-2 gap-2 pt-2 border-t border-gray-800/80 text-[11px]">
                          <div>
                            <span className="text-[10px] font-bold text-gray-500 uppercase">Advantages:</span>
                            {s.pros.map((p, j) => <p key={j} className="text-emerald-400 mt-0.5">+ {p}</p>)}
                          </div>
                          <div>
                            <span className="text-[10px] font-bold text-gray-500 uppercase">Downsides:</span>
                            {s.cons.map((c, j) => <p key={j} className="text-red-400 mt-0.5">− {c}</p>)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <Disclaimer text={result.disclaimer} />
                </Card>
              </>
            )
          })()}

          {!result && !loading && (
            <EmptyState
              title="No Market Signal Generated"
              description="Configure corridor parameters to compute whether to buy now, wait, or hedge freight rates."
              actionLabel="Analyze Australia → Paradip Signal"
              onAction={handleSubmit}
            />
          )}
        </div>
      </div>
    </div>
  )
}

