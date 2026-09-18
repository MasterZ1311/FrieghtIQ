'use client'
import { useState, useEffect, useCallback } from 'react'
import { api } from '@/lib/api'
import { formatUSD, ORIGINS, DESTINATIONS, VESSEL_CLASSES, COMMODITIES } from '@/lib/utils'
import { Card, Loading, ErrorBox, Disclaimer, Select, Input, PageHeader, StatCard, EmptyState, DemoBadge } from '@/components/ui'
import type { EconomicsResponse, VesselClass, Commodity } from '@/types'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Sparkles, DollarSign, TrendingUp } from 'lucide-react'
import CarbonFootprintCard from '@/components/ui/CarbonFootprintCard'



export default function EconomicsPage() {
  const [origin, setOrigin] = useState('Australia')
  const [destination, setDestination] = useState('Gangavaram')
  const [vesselClass, setVesselClass] = useState<VesselClass>('Panamax')
  const [commodity, setCommodity] = useState<Commodity>('Coal')
  const [cargo, setCargo] = useState('70000')
  const [bunker, setBunker] = useState('650')
  const [portDaysOrigin, setPortDaysOrigin] = useState('2')
  const [portDaysDest, setPortDaysDest] = useState('3')
  const [manualRate, setManualRate] = useState('')
  const [result, setResult] = useState<EconomicsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.economics.calculate({
        origin, destination, vessel_class: vesselClass,
        commodity, cargo_mt: Number(cargo),
        bunker_price_usd_per_mt: Number(bunker),
        port_days_origin: Number(portDaysOrigin),
        port_days_dest: Number(portDaysDest),
        freight_rate_usd_per_mt: manualRate ? Number(manualRate) : undefined,
      })
      setResult(res)
    } catch (e: unknown) {
      const err = e instanceof Error ? e.message : 'Economics calculation failed'
      setError(err)
    } finally {
      setLoading(false)
    }
  }, [origin, destination, vesselClass, commodity, cargo, bunker, portDaysOrigin, portDaysDest, manualRate])

  useEffect(() => {
    handleSubmit()
  }, [handleSubmit])

  const costBreakdown = result ? [
    { name: 'Bunker', value: result.bunker_cost_usd, color: '#f59e0b' },
    { name: 'Port Dues', value: result.port_dues_usd, color: '#8b5cf6' },
    { name: 'Canal', value: result.canal_dues_usd, color: '#06b6d4' },
    { name: 'OPEX', value: result.opex_usd, color: '#6b7280' },
  ].filter((d) => d.value > 0) : []

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <PageHeader
        title="Voyage Economics & TCE Simulator"
        subtitle="Maritime Physics Engine computing nautical distance, bunker consumption, port disbursements, TCE returns, and breakeven rates"
        actions={<DemoBadge />}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card title="Voyage Parameters" subtitle="Specify operational cost drivers" className="col-span-1">
          <div className="space-y-4">
            <Select label="Origin Corridor" value={origin} onChange={setOrigin} options={ORIGINS} />
            <Select label="Destination Port" value={destination} onChange={setDestination} options={DESTINATIONS} />
            <Select label="Vessel Class" value={vesselClass} onChange={(v) => setVesselClass(v as VesselClass)} options={VESSEL_CLASSES} />
            <Select label="Commodity" value={commodity} onChange={(v) => setCommodity(v as Commodity)} options={COMMODITIES} />
            <Input label="Cargo Volume (MT)" value={cargo} onChange={setCargo} type="number" />
            <Input label="Bunker Fuel Price (VLSFO USD/MT)" value={bunker} onChange={setBunker} type="number" />
            <div className="grid grid-cols-2 gap-3">
              <Input label="Port Days Origin" value={portDaysOrigin} onChange={setPortDaysOrigin} type="number" />
              <Input label="Port Days Dest." value={portDaysDest} onChange={setPortDaysDest} type="number" />
            </div>
            <Input label="Manual Freight Rate (USD/MT, optional)" value={manualRate} onChange={setManualRate} type="number" placeholder="Auto from forecast model" />
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
                  <span>Calculate P&L</span>
                </>
              )}
            </button>
          </div>
        </Card>

        <div className="col-span-1 lg:col-span-2 space-y-5">
          {loading && <Loading message="Computing bunker consumption, port disbursements & TCE margins…" />}
          {error && <ErrorBox message={error} onRetry={handleSubmit} />}

          {result && (
            <>
              {/* P&L Key Summary Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
                <StatCard
                  label="Freight Revenue"
                  value={formatUSD(result.freight_revenue_usd, 0)}
                  subValue={`@ ${formatUSD(result.freight_rate_usd_per_mt, 2)}/MT`}
                  icon={<DollarSign size={16} />}
                />
                <StatCard
                  label="Total Voyage Cost"
                  value={formatUSD(result.total_cost_usd, 0)}
                  subValue="Bunker + Port + OPEX"
                />
                <StatCard
                  label="Gross Operating Profit"
                  value={formatUSD(result.gross_profit_usd, 0)}
                  subValue={`Margin: ${result.margin_pct.toFixed(1)}%`}
                  badge={{
                    text: result.gross_profit_usd >= 0 ? `+${result.margin_pct.toFixed(1)}% Margin` : 'Operating Loss',
                    color: result.gross_profit_usd >= 0 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-red-500/20 text-red-400 border border-red-500/30',
                  }}
                  icon={<TrendingUp size={16} />}
                />
                <StatCard
                  label="TCE Equivalence"
                  value={`${formatUSD(result.tce_usd_per_day, 0)}/d`}
                  subValue={`Breakeven: ${formatUSD(result.breakeven_rate_usd_per_mt, 2)}/MT`}
                />
              </div>

              {/* Timeline & Cost Breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card title="Voyage Timeline & Navigation Schedule" subtitle="Sea steaming days vs port turnaround">
                  <div className="space-y-3">
                    {[
                      { label: 'Corridor Distance', value: `${result.distance_nm.toLocaleString()} Nautical Miles` },
                      { label: 'Sea Transit Time', value: `${result.sea_days} days @ service speed` },
                      { label: 'Loading & Discharge Port Time', value: `${result.port_days} days combined` },
                      { label: 'Total Voyage Turnaround', value: `${result.total_voyage_days} days complete cycle` },
                    ].map((row) => (
                      <div key={row.label} className="flex justify-between text-xs border-b border-gray-800/80 pb-2.5">
                        <span className="text-gray-400">{row.label}</span>
                        <span className="text-white font-bold">{row.value}</span>
                      </div>
                    ))}
                  </div>
                </Card>

                <Card title="Disbursement Breakdown (USD)" subtitle="Cost distribution across voyage components">
                  <ResponsiveContainer width="100%" height={160}>
                    <BarChart data={costBreakdown} layout="vertical" margin={{ top: 0, right: 10, left: 10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
                      <XAxis type="number" stroke="#6b7280" tick={{ fontSize: 10, fill: '#9ca3af' }} tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`} />
                      <YAxis type="category" dataKey="name" stroke="#6b7280" tick={{ fontSize: 11, fill: '#9ca3af' }} width={65} />
                      <Tooltip
                        contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }}
                        formatter={(v: unknown) => [formatUSD(Number(v || 0), 0), 'Expense']}
                      />
                      <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                        {costBreakdown.map((entry, i) => (
                          <Cell key={i} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </Card>
              </div>

              {/* Full P&L Table */}
              <Card title="Executive Voyage Profit & Loss Statement" subtitle="Audited synthetic disbursement breakdown">
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-gray-800 text-gray-400">
                        <th className="text-left py-2.5 font-semibold uppercase tracking-wider">Accounting Line Item</th>
                        <th className="text-right py-2.5 font-semibold uppercase tracking-wider">Revenue / Expense (USD)</th>
                        <th className="text-right py-2.5 font-semibold uppercase tracking-wider">Cost / MT</th>
                        <th className="text-right py-2.5 font-semibold uppercase tracking-wider">% of Revenue</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-800/60">
                      {[
                        { label: 'Freight Revenue Gross', value: result.freight_revenue_usd, perMt: result.freight_rate_usd_per_mt, pct: '100.0%', isRevenue: true },
                        { label: 'Bunker Fuel Consumption (VLSFO + LSMGO)', value: -result.bunker_cost_usd, perMt: result.bunker_cost_usd / result.cargo_mt, pct: `${((result.bunker_cost_usd / result.freight_revenue_usd) * 100).toFixed(1)}%` },
                        { label: 'Port Disbursements & Berth Hire', value: -result.port_dues_usd, perMt: result.port_dues_usd / result.cargo_mt, pct: `${((result.port_dues_usd / result.freight_revenue_usd) * 100).toFixed(1)}%` },
                        { label: 'Canal & Transit Tolls', value: -result.canal_dues_usd, perMt: result.canal_dues_usd / result.cargo_mt, pct: `${((result.canal_dues_usd / result.freight_revenue_usd) * 100).toFixed(1)}%` },
                        { label: 'Vessel Daily OPEX & Crewing', value: -result.opex_usd, perMt: result.opex_usd / result.cargo_mt, pct: `${((result.opex_usd / result.freight_revenue_usd) * 100).toFixed(1)}%` },
                        { label: 'Net Gross Operating Profit', value: result.gross_profit_usd, perMt: result.gross_profit_usd / result.cargo_mt, pct: `${result.margin_pct.toFixed(1)}%`, isNet: true },
                      ].map((row) => (
                        <tr key={row.label} className={row.isNet ? 'bg-gray-800/40 font-bold' : ''}>
                          <td className={`py-2.5 ${row.isNet ? 'text-white font-bold' : 'text-gray-300'}`}>{row.label}</td>
                          <td className={`py-2.5 text-right tabular-nums ${row.isRevenue ? 'text-emerald-400 font-bold' : row.isNet ? (result.gross_profit_usd >= 0 ? 'text-emerald-400 font-black' : 'text-red-400 font-black') : 'text-gray-300'}`}>
                            {formatUSD(row.value, 0)}
                          </td>
                          <td className="py-2.5 text-right text-gray-400 tabular-nums">
                            {formatUSD(row.perMt, 2)}
                          </td>
                          <td className="py-2.5 text-right text-gray-400 tabular-nums">{row.pct}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <Disclaimer text={result.disclaimer} />
              </Card>

              {/* IMO CII Rating & EU ETS Scope 3 Carbon Surcharge */}
              <CarbonFootprintCard />
            </>
          )}


          {!result && !loading && (
            <EmptyState
              title="No Voyage Economics Computed"
              description="Configure voyage parameters to view full maritime P&L and TCE figures."
              actionLabel="Calculate Australia → Gangavaram Coal"
              onAction={handleSubmit}
            />
          )}
        </div>
      </div>
    </div>
  )
}

