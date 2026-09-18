'use client'
import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import {
  formatUSD,
  DESTINATIONS,
  VESSEL_CLASSES,
  COMMODITIES,
  constraintColor,
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
import type { PortCheckResponse, Commodity, VesselClass, Port } from '@/types'
import {
  Anchor,
  Clock,
  DollarSign,
  Gauge,
} from 'lucide-react'
import CongestionHeatmap from '@/components/ui/CongestionHeatmap'
import TidalCalendar from '@/components/ui/TidalCalendar'


const STATUS_ICON: Record<string, string> = { OK: '✓', WARNING: '⚠', FAIL: '✗' }
const STATUS_BG: Record<string, string> = {
  OK: 'bg-emerald-500/10 border-emerald-500/30',
  WARNING: 'bg-amber-500/10 border-amber-500/30',
  FAIL: 'bg-red-500/10 border-red-500/30',
}

export default function PortsPage() {
  const [port, setPort] = useState('Thoothukudi')
  const [vesselClass, setVesselClass] = useState<VesselClass>('Panamax')
  const [cargo, setCargo] = useState('74510')
  const [commodity, setCommodity] = useState<Commodity>('Coal')

  const [result, setResult] = useState<PortCheckResponse | null>(null)
  const [ports, setPorts] = useState<Port[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isLiveApi, setIsLiveApi] = useState(false)

  const handleCheck = async () => {
    setLoading(true)
    setError(null)
    try {
      const [health, res, pList] = await Promise.all([
        api.health(),
        api.ports.check({
          port,
          vessel_class: vesselClass,
          cargo_mt: Number(cargo) || 70000,
          commodity,
        }),
        api.ports.list('East Coast'),
      ])
      setIsLiveApi(health.isLive)
      setResult(res)
      setPorts(pList.ports)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Port check failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    handleCheck()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Vessel draft lookup table for matrix
  const vesselDrafts: Record<VesselClass, number> = {
    Handysize: 9.8,
    Supramax: 12.8,
    Panamax: 14.2,
    Capesize: 18.2,
  }

  const getMatrixStatus = (portObj: Port, vClass: VesselClass): { label: string; color: string; icon: string } => {
    const draft = vesselDrafts[vClass]
    if (portObj.name === 'Haldia' && vClass !== 'Handysize') {
      return { label: 'FAIL', color: 'bg-red-500/20 text-red-400 border-red-500/40', icon: '✗' }
    }
    if (portObj.max_draft_m < draft) {
      return { label: 'FAIL', color: 'bg-red-500/20 text-red-400 border-red-500/40', icon: '✗' }
    }
    if (portObj.max_draft_m - draft < 1.0 || portObj.tide_restricted) {
      return { label: 'TIDE/WARN', color: 'bg-amber-500/20 text-amber-400 border-amber-500/40', icon: '⚠' }
    }
    return { label: 'CLEARED', color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40', icon: '✓' }
  }

  return (
    <div className="p-8 max-w-[1700px] mx-auto">
      <PageHeader
        title="Port Compatibility & Constraint Engine"
        subtitle="Vessel draft, LOA, beam, and tidal compatibility validation across all primary East Coast Indian commercial ports."
      >
        <DataModeBadge isLive={isLiveApi} />
      </PageHeader>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Input Parameters */}
        <div className="lg:col-span-4 space-y-5">
          <Card title="Port & Vessel Parameters" subtitle="Select port and vessel specifications to test clearance">
            <div className="space-y-4">
              <Select label="Destination Port" value={port} onChange={setPort} options={DESTINATIONS} />
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
              <Input label="Cargo Volume (MT)" value={cargo} onChange={setCargo} type="number" />
              <button
                onClick={handleCheck}
                disabled={loading}
                className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 text-white rounded-xl text-xs font-bold uppercase tracking-wider transition shadow flex items-center justify-center gap-1.5 mt-2"
              >
                {loading ? 'Validating Navigation Limits…' : 'Run Compatibility Verification'}
              </button>
            </div>
          </Card>

          {/* Quick Port Operational Rule */}
          <div className="p-4 bg-gray-900/60 border border-gray-800 rounded-xl text-xs space-y-2 text-gray-400">
            <h4 className="text-[11px] font-bold text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
              <Anchor size={14} className="text-amber-400" />
              East Coast Navigation Rule
            </h4>
            <p className="leading-relaxed">
              • <strong>Gangavaram & Dhamra:</strong> Deepwater non-riverine ports with natural draft
              supporting fully laden Capesize tonnage.
            </p>
            <p className="leading-relaxed">
              • <strong>Haldia Dock Complex:</strong> Critical Hooghly river sandbar restricts safe
              navigational draft to 8.5m HW. Large vessels require prior lighterage at Sandheads.
            </p>
          </div>
        </div>

        {/* Results & Verification Display */}
        <div className="lg:col-span-8 space-y-5">
          {error && <ErrorBox message={error} />}
          {loading && <Loading message="Checking channel depth, berth LOA and tidal constraints…" />}

          {result && (
            <>
              {/* Compatibility Banner */}
              <div
                className={`p-5 border rounded-2xl flex flex-wrap items-center justify-between gap-4 ${
                  result.compatible
                    ? 'bg-emerald-950/30 border-emerald-500/50'
                    : 'bg-red-950/30 border-red-500/50'
                }`}
              >
                <div className="flex items-center gap-4">
                  <div
                    className={`w-12 h-12 rounded-xl flex items-center justify-center font-bold text-2xl shadow-lg ${
                      result.compatible
                        ? 'bg-emerald-600 text-white shadow-emerald-600/30'
                        : 'bg-red-600 text-white shadow-red-600/30'
                    }`}
                  >
                    {result.compatible ? '✓' : '✗'}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-sm font-black uppercase tracking-wider ${
                          result.compatible ? 'text-emerald-400' : 'text-red-400'
                        }`}
                      >
                        {result.compatible ? 'FULLY CLEARED' : 'RESTRICTED / INCOMPATIBLE'}
                      </span>
                    </div>
                    <h3 className="text-xl font-bold text-white mt-0.5">
                      {result.vessel_class} Bulker at {result.port}
                    </h3>
                    <p className="text-xs text-gray-300 mt-0.5">
                      Vessel Laden Draft: <strong>{result.vessel_draft_m}m</strong> · Port Allowable Draft:{' '}
                      <strong>{result.max_draft_m}m</strong> (Draft Margin:{' '}
                      <span className={result.max_draft_m - result.vessel_draft_m >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                        {(result.max_draft_m - result.vessel_draft_m).toFixed(1)}m
                      </span>
                      )
                    </p>
                  </div>
                </div>

                <div className="text-right">
                  <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
                    Turnaround & Dues
                  </span>
                  <p className="text-lg font-black text-white mt-0.5">
                    {result.turnaround_days} Days Turnaround
                  </p>
                  <span className="text-xs text-blue-400 font-mono">
                    Port Dues: {formatUSD(result.port_dues_usd, 0)}
                  </span>
                </div>
              </div>

              {/* Numerical Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <StatCard
                  label="Average Turnaround"
                  value={`${result.turnaround_days} Days`}
                  subValue="Loading & discharge cycle"
                  icon={<Clock size={16} />}
                />
                <StatCard
                  label="Daily Handling Rate"
                  value={`${(result.handling_rate_mt_day / 1000).toFixed(0)}k MT/d`}
                  subValue="Mechanized grab capacity"
                  icon={<Gauge size={16} />}
                />
                <StatCard
                  label="Estimated Port Dues"
                  value={formatUSD(result.port_dues_usd, 0)}
                  subValue="Pilotage, berthage & towage"
                  icon={<DollarSign size={16} />}
                />
              </div>

              {/* ── GREEN HYDROGEN HUB BADGE (VOCPA / Kamarajar only) ── */}
              {(result.port.includes('Thoothukudi') ||
                result.port.includes('VOCPA') ||
                result.port.includes('Kamarajar')) && (
                <div className="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-500/40 shadow-lg shadow-emerald-500/10">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse flex-shrink-0" />
                        <span className="text-emerald-300 font-black text-sm tracking-wide">
                          MoPSW Green Hydrogen &amp; Green Ammonia Bunkering Hub
                        </span>
                      </div>
                      <p className="text-xs text-emerald-400/70 mb-3">
                        Designated at India Green Fuel Conclave 2026 · India&apos;s first integrated green bunkering gateway on the East Coast
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {['Green H₂', 'Green NH₃', 'Green MeOH', 'IMO Compliant'].map((fuel) => (
                          <span
                            key={fuel}
                            className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                          >
                            {fuel}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <div className="text-3xl mb-1">🌿</div>
                      <p className="text-[10px] text-emerald-400/60 font-semibold">Since 2026</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Constraint Checks Details */}
              <Card title="Detailed Constraint Verification Checklist">
                <div className="space-y-2.5">
                  {result.constraints.map((c, i) => (
                    <div
                      key={i}
                      className={`flex items-start gap-3 p-3 border rounded-xl ${STATUS_BG[c.status]}`}
                    >
                      <span className={`font-bold text-sm flex-shrink-0 mt-0.5 ${constraintColor(c.status)}`}>
                        {STATUS_ICON[c.status]}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <p className="text-xs font-bold text-white">{c.constraint}</p>
                          <span
                            className={`px-2 py-0.5 text-[10px] font-bold rounded uppercase ${constraintColor(
                              c.status
                            )}`}
                          >
                            {c.status}
                          </span>
                        </div>
                        <p className="text-xs text-gray-400 mt-0.5 leading-relaxed">{c.detail}</p>
                      </div>
                    </div>
                  ))}
                </div>

                {result.notes && (
                  <p className="mt-4 p-3 bg-gray-950/60 border border-gray-800 rounded-xl text-xs text-gray-400 italic">
                    <strong>Port Master Note: </strong>
                    {result.notes}
                  </p>
                )}
              </Card>
            </>
          )}

          {/* ─── EAST COAST INDIA 7-PORT COMPATIBILITY MATRIX ─── */}
          {ports.length > 0 && (
            <Card
              title="East Coast India 7-Port vs. 4-Vessel Master Compatibility Matrix"
              subtitle="Comprehensive draft and operational feasibility reference across Handysize, Supramax, Panamax, and Capesize"
            >
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="border-b border-gray-800 text-gray-400 text-[11px] uppercase tracking-wider">
                      <th className="py-2.5 pr-4">Port Name</th>
                      <th className="py-2.5 px-3">Max Draft</th>
                      <th className="py-2.5 px-3">Max DWT</th>
                      <th className="py-2.5 px-2 text-center">Handysize (9.8m)</th>
                      <th className="py-2.5 px-2 text-center">Supramax (12.8m)</th>
                      <th className="py-2.5 px-2 text-center">Panamax (14.2m)</th>
                      <th className="py-2.5 px-2 text-center">Capesize (18.2m)</th>
                      <th className="py-2.5 pl-3 text-right">Congestion</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800/60">
                    {ports.map((p) => (
                      <tr key={p.name} className="hover:bg-gray-800/40 transition">
                        <td className="py-3 pr-4">
                          <span className="font-bold text-white block">{p.name}</span>
                          <span className="text-[10px] text-gray-400">{p.berths} Berths</span>
                        </td>
                        <td className="py-3 px-3 font-mono font-semibold text-gray-200">
                          {p.max_draft_m}m
                        </td>
                        <td className="py-3 px-3 font-mono text-gray-300">
                          {(p.max_dwt / 1000).toFixed(0)}k DWT
                        </td>

                        {/* Handysize */}
                        <td className="py-3 px-2 text-center">
                          {(() => {
                            const st = getMatrixStatus(p, 'Handysize')
                            return (
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${st.color}`}>
                                {st.icon} {st.label}
                              </span>
                            )
                          })()}
                        </td>

                        {/* Supramax */}
                        <td className="py-3 px-2 text-center">
                          {(() => {
                            const st = getMatrixStatus(p, 'Supramax')
                            return (
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${st.color}`}>
                                {st.icon} {st.label}
                              </span>
                            )
                          })()}
                        </td>

                        {/* Panamax */}
                        <td className="py-3 px-2 text-center">
                          {(() => {
                            const st = getMatrixStatus(p, 'Panamax')
                            return (
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${st.color}`}>
                                {st.icon} {st.label}
                              </span>
                            )
                          })()}
                        </td>

                        {/* Capesize */}
                        <td className="py-3 px-2 text-center">
                          {(() => {
                            const st = getMatrixStatus(p, 'Capesize')
                            return (
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${st.color}`}>
                                {st.icon} {st.label}
                              </span>
                            )
                          })()}
                        </td>

                        <td className="py-3 pl-3 text-right">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              p.congestion_level === 'Low'
                                ? 'bg-emerald-500/20 text-emerald-400'
                                : p.congestion_level === 'Moderate'
                                ? 'bg-blue-500/20 text-blue-400'
                                : p.congestion_level === 'Heavy'
                                ? 'bg-amber-500/20 text-amber-400'
                                : 'bg-red-500/20 text-red-400'
                            }`}
                          >
                            {p.congestion_level}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* AIS Live Port Congestion & Virtual Arrival Engine */}
          <CongestionHeatmap />

          {/* INCOIS Semi-Diurnal Tidal Gate Scheduler */}
          <TidalCalendar />

          <Disclaimer text={result?.disclaimer || 'DEMO BENCHMARK DATA: East Coast India Port Specifications.'} />

        </div>
      </div>
    </div>
  )
}
