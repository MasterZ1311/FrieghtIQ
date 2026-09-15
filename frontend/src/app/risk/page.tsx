'use client'
import { useState, useEffect, useCallback } from 'react'
import { api } from '@/lib/api'
import {
  ORIGINS,
  DESTINATIONS,
  VESSEL_CLASSES,
  COMMODITIES,
  CONTRACT_TYPES,
} from '@/lib/utils'
import {
  Card,
  Loading,
  ErrorBox,
  Disclaimer,
  Select,
  Input,
  PageHeader,
  RiskBadge,
  ProgressBar,
  DataModeBadge,
} from '@/components/ui'
import type {
  RiskResponse,
  VesselClass,
  Commodity,
  ContractType,
} from '@/types'
import {
  AlertTriangle,
  Clock,
  MapPin,
  CheckCircle2,
  Zap,
} from 'lucide-react'
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from 'recharts'

export default function RiskAlertsPage() {
  const [origin, setOrigin] = useState('Australia')
  const [destination, setDestination] = useState('Paradip')
  const [vesselClass, setVesselClass] = useState<VesselClass>('Panamax')
  const [commodity, setCommodity] = useState<Commodity>('Coal')
  const [cargo, setCargo] = useState('70000')
  const [contractType, setContractType] = useState<ContractType>('Spot')

  const [result, setResult] = useState<RiskResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isLiveApi, setIsLiveApi] = useState(false)
  const [severityFilter, setSeverityFilter] = useState<'All' | 'Critical' | 'High' | 'Medium' | 'Info'>('All')

  const handleScore = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [health, res] = await Promise.all([
        api.health(),
        api.risk.score({
          origin,
          destination,
          vessel_class: vesselClass,
          commodity,
          cargo_mt: Number(cargo) || 70000,
          contract_type: contractType,
        }),
      ])
      setIsLiveApi(health.isLive)
      setResult(res)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Risk scoring failed')
    } finally {
      setLoading(false)
    }
  }, [origin, destination, vesselClass, commodity, cargo, contractType])

  useEffect(() => {
    handleScore()
  }, [handleScore])

  const radarData =
    result?.risk_factors.map((rf) => ({
      subject: rf.name.split(' ').slice(0, 2).join(' '),
      score: rf.score,
      fullCategory: rf.category,
    })) || []

  const filteredAlerts =
    result?.alerts?.filter((a) => (severityFilter === 'All' ? true : a.severity === severityFilter)) || []

  const severityBadgeColor = (sev: string) => {
    switch (sev) {
      case 'Critical':
        return 'bg-red-500/20 text-red-400 border-red-500/40'
      case 'High':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/40'
      case 'Medium':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/40'
      case 'Info':
      default:
        return 'bg-blue-500/20 text-blue-400 border-blue-500/40'
    }
  }

  return (
    <div className="p-8 max-w-[1700px] mx-auto">
      <PageHeader
        title="Risk & Proactive Operational Alerts"
        subtitle="Multi-pillar exposure assessment covering freight rate volatility, port demurrage, bunker fuel spikes, and meteorological risks."
      >
        <DataModeBadge isLive={isLiveApi} />
      </PageHeader>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Parameters */}
        <div className="lg:col-span-4 space-y-5">
          <Card title="Risk Scoring Parameters" subtitle="Specify voyage context for tailored risk modeling">
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

              <Input label="Cargo Volume (MT)" value={cargo} onChange={setCargo} type="number" />
              <Select
                label="Contract Strategy"
                value={contractType}
                onChange={(v) => setContractType(v as ContractType)}
                options={CONTRACT_TYPES}
              />

              <button
                onClick={handleScore}
                disabled={loading}
                className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 text-white rounded-xl text-xs font-bold uppercase tracking-wider transition shadow flex items-center justify-center gap-1.5 mt-2"
              >
                {loading ? 'Evaluating Risk Matrix…' : 'Calculate Risk Matrix'}
              </button>
            </div>
          </Card>

          {/* Quick Risk Index Legend */}
          <div className="p-4 bg-gray-900/60 border border-gray-800 rounded-xl text-xs space-y-2 text-gray-400">
            <h4 className="text-[11px] font-bold text-gray-300 uppercase tracking-wider">
              Risk Score Calibration
            </h4>
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <span className="text-emerald-400">0 – 35: Low Risk</span>
              <span className="text-amber-400">36 – 55: Moderate Risk</span>
              <span className="text-orange-400">56 – 75: High Risk</span>
              <span className="text-red-400">76 – 100: Critical</span>
            </div>
          </div>
        </div>

        {/* Results & Live Alert Feed */}
        <div className="lg:col-span-8 space-y-6">
          {error && <ErrorBox message={error} />}
          {loading && <Loading message="Computing risk exposure scores and scanning alert feed…" />}

          {result && (
            <>
              {/* Overall Risk Score Header Banner */}
              <div
                className={`p-6 border rounded-2xl flex flex-wrap items-center justify-between gap-4 ${
                  result.overall_risk_score > 55
                    ? 'bg-red-950/30 border-red-500/50'
                    : result.overall_risk_score > 35
                    ? 'bg-amber-950/30 border-amber-500/50'
                    : 'bg-emerald-950/30 border-emerald-500/50'
                }`}
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                      Overall Voyage Risk Score
                    </span>
                    <RiskBadge level={result.overall_risk_level} />
                  </div>
                  <div className="flex items-baseline gap-3">
                    <p className="text-4xl font-black text-white">{result.overall_risk_score}</p>
                    <span className="text-sm text-gray-400 font-mono">/ 100 Weighted Risk Index</span>
                  </div>
                  <p className="text-xs text-gray-300 mt-2 max-w-xl">
                    Voyage exposure is mitigated by high Pacific vessel availability and moderate fuel
                    volatility. Primary operational concern remains berth congestion at {destination}.
                  </p>
                </div>

                <div className="text-right">
                  <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
                    Top Priority Risks
                  </span>
                  <div className="mt-1 space-y-1">
                    {result.top_risks.map((r, i) => (
                      <p key={i} className="text-xs font-bold text-amber-400 flex items-center justify-end gap-1">
                        <AlertTriangle size={13} /> {r}
                      </p>
                    ))}
                  </div>
                </div>
              </div>

              {/* Multi-Factor Radar & Breakdown Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {/* Radar Chart */}
                <Card title="Multi-Factor Risk Radar" subtitle="Relative exposure across 5 operational pillars">
                  <ResponsiveContainer width="100%" height={260}>
                    <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                      <PolarGrid stroke="#374151" />
                      <PolarAngleAxis dataKey="subject" stroke="#9ca3af" tick={{ fontSize: 10 }} />
                      <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#4b5563" tick={{ fontSize: 9 }} />
                      <Radar
                        name="Risk Score"
                        dataKey="score"
                        stroke="#f59e0b"
                        fill="#f59e0b"
                        fillOpacity={0.35}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </Card>

                {/* Risk Factor Breakdown */}
                <Card title="Factor Assessment Scores" subtitle="Category breakdown and mitigation protocol">
                  <div className="space-y-3">
                    {result.risk_factors.map((rf, i) => (
                      <div key={i} className="p-3 bg-gray-800/40 rounded-xl border border-gray-800 text-xs">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-bold text-white">{rf.name}</span>
                          <span className={`px-2 py-0.2 rounded text-[10px] font-bold ${severityBadgeColor(rf.level)}`}>
                            {rf.level} ({rf.score}/100)
                          </span>
                        </div>
                        <ProgressBar
                          value={rf.score}
                          color={rf.score > 60 ? 'bg-red-500' : rf.score > 35 ? 'bg-amber-500' : 'bg-emerald-500'}
                        />
                        <p className="text-[11px] text-gray-400 mt-1.5 leading-relaxed">{rf.description}</p>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>

              {/* ─── LIVE OPERATIONAL ALERT FEED ─── */}
              <Card
                title="Proactive Operational Alert Feed"
                subtitle="Live maritime alerts affecting East Coast India fixtures and key trade lanes"
                badge={
                  <div className="flex items-center gap-1">
                    {(['All', 'Critical', 'High', 'Medium', 'Info'] as const).map((s) => (
                      <button
                        key={s}
                        onClick={() => setSeverityFilter(s)}
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold border transition ${
                          severityFilter === s
                            ? 'bg-blue-600 border-blue-500 text-white'
                            : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-white'
                        }`}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                }
              >
                <div className="space-y-3">
                  {filteredAlerts.length === 0 ? (
                    <p className="text-xs text-gray-500 py-6 text-center">No alerts match filter.</p>
                  ) : (
                    filteredAlerts.map((alert) => (
                      <div
                        key={alert.id}
                        className="p-4 bg-gray-800/30 hover:bg-gray-800/60 border border-gray-800 rounded-xl transition"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                          <div className="flex items-center gap-2">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${severityBadgeColor(
                                alert.severity
                              )}`}
                            >
                              {alert.severity}
                            </span>
                            <span className="text-xs font-bold text-white">{alert.title}</span>
                          </div>

                          <div className="flex items-center gap-3 text-[11px] text-gray-500">
                            <span className="flex items-center gap-1">
                              <MapPin size={12} className="text-gray-400" />
                              {alert.location}
                            </span>
                            <span className="flex items-center gap-1 font-mono">
                              <Clock size={12} />
                              {alert.timestamp}
                            </span>
                          </div>
                        </div>

                        <p className="text-xs text-gray-300 leading-relaxed">{alert.description}</p>

                        <div className="mt-2.5 pt-2 border-t border-gray-800/80 flex flex-wrap items-center justify-between gap-2 text-xs">
                          <div className="flex items-center gap-1.5 text-blue-400">
                            <Zap size={13} />
                            <span>
                              <strong>Recommended Mitigation: </strong>
                              {alert.recommended_action}
                            </span>
                          </div>
                          <span className="text-[11px] font-semibold text-amber-400 font-mono">
                            {alert.impact_indicator}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </Card>

              {/* Recommended Action Playbook */}
              <Card title="Actionable Risk Playbook" subtitle="Prescriptive steps for procurement team">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {result.recommended_actions.map((act, i) => (
                    <div key={i} className="p-3 bg-gray-800/40 border border-gray-800 rounded-xl text-xs">
                      <div className="flex items-center gap-2 text-emerald-400 font-bold mb-1">
                        <CheckCircle2 size={14} />
                        <span>Action Step {i + 1}</span>
                      </div>
                      <p className="text-gray-300 leading-relaxed">{act}</p>
                    </div>
                  ))}
                </div>
              </Card>
            </>
          )}

          <Disclaimer text={result?.disclaimer || 'DEMO BENCHMARK DATA: FreightIQ Risk Engine.'} />
        </div>
      </div>
    </div>
  )
}
