'use client'
import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import {
  formatUSD,
  trendArrow,
  marketActionConfig,
} from '@/lib/utils'
import {
  Card,
  StatCard,
  MarketEntryCard,
  DataModeBadge,
  ErrorBox,
  Disclaimer,
  PageHeader,
  RiskBadge,
  SkeletonCard,
  SkeletonChart,
  SkeletonBanner,
} from '@/components/ui'
import type {
  DashboardSummary,
  HistoryDataPoint,
  VesselClass,
  MarketEntryAction,
} from '@/types'
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
  TrendingUp,
  Ship,
  ArrowRight,
  Calculator,
  CalendarCheck2,
  DollarSign,
  Layers,
  Anchor,
  ShieldAlert,
  GitCompare,
  Bot,
  Gauge,
  Clock,
  Sparkles,
  Droplets,
} from 'lucide-react'


const DASHBOARD_ROUTES = [
  {
    origin: 'Australia',
    destination: 'Thoothukudi',
    vessel_class: 'Panamax' as VesselClass,
    commodity: 'Coal',
    label: 'AUS → Thoothukudi / VOCPA (Panamax Coal)',
    currentRate: 13.80,
    predictedRate: 12.95,
    action: 'WAIT' as MarketEntryAction,
    savings: 63750,
    confidence: 89,
    vessel: 'Panamax' as VesselClass,
    totalCost: 1028238,
    contract: '6-Mo COA (Save $63.8k)',
    riskScore: 31,
  },
  {
    origin: 'Indonesia',
    destination: 'Chennai',
    vessel_class: 'Supramax' as VesselClass,
    commodity: 'Coal',
    label: 'IDN → Chennai Port (Supramax Pig Iron/Coal)',
    currentRate: 11.20,
    predictedRate: 12.40,
    action: 'CHARTER NOW' as MarketEntryAction,
    savings: 66000,
    confidence: 85,
    vessel: 'Supramax' as VesselClass,
    totalCost: 648000,
    contract: 'Spot Prompt Fixture',
    riskScore: 26,
  },
  {
    origin: 'Australia',
    destination: 'Kamarajar',
    vessel_class: 'Panamax' as VesselClass,
    commodity: 'Coal',
    label: 'AUS → Kamarajar / Ennore (Panamax Coal)',
    currentRate: 14.10,
    predictedRate: 13.20,
    action: 'WAIT' as MarketEntryAction,
    savings: 67500,
    confidence: 87,
    vessel: 'Panamax' as VesselClass,
    totalCost: 1057500,
    contract: 'Indexed 6-Mo COA',
    riskScore: 32,
  },
  {
    origin: 'Australia',
    destination: 'Paradip',
    vessel_class: 'Panamax' as VesselClass,
    commodity: 'Coal',
    label: 'AUS → Paradip (Panamax Coal)',
    currentRate: 14.85,
    predictedRate: 13.9,
    action: 'WAIT' as MarketEntryAction,
    savings: 66500,
    confidence: 86,
    vessel: 'Panamax' as VesselClass,
    totalCost: 1039500,
    contract: '6-Mo COA (Save $66.5k)',
    riskScore: 34,
  },
  {
    origin: 'Mozambique',
    destination: 'Gangavaram',
    vessel_class: 'Capesize' as VesselClass,
    commodity: 'Coal',
    label: 'MOZ → Gangavaram (Capesize Coal)',
    currentRate: 10.95,
    predictedRate: 10.8,
    action: 'MONITOR' as MarketEntryAction,
    savings: 22500,
    confidence: 79,
    vessel: 'Capesize' as VesselClass,
    totalCost: 1642500,
    contract: 'Indexed Collar Contract',
    riskScore: 41,
  },
  {
    origin: 'United States',
    destination: 'Paradip',
    vessel_class: 'Panamax' as VesselClass,
    commodity: 'Coal',
    label: 'USA → Paradip (Panamax Coal)',
    currentRate: 34.6,
    predictedRate: 36.2,
    action: 'CHARTER NOW' as MarketEntryAction,
    savings: 112000,
    confidence: 88,
    vessel: 'Panamax' as VesselClass,
    totalCost: 2595000,
    contract: 'Long-Term COA Volume',
    riskScore: 54,
  },
]

// Regime chip colours
const REGIME_CHIP: Record<string, { chip: string; dot: string; label: string }> = {
  BEAR_DISTRESS:   { chip: 'bg-red-500/20 text-red-300 border-red-500/40',     dot: 'bg-red-400',     label: 'Bear Market' },
  NEUTRAL:         { chip: 'bg-blue-500/20 text-blue-300 border-blue-500/40',   dot: 'bg-blue-400',   label: 'Neutral' },
  SEASONAL_LIFT:   { chip: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40', dot: 'bg-emerald-400', label: 'Seasonal Lift' },
  SUPERCYCLE_BULL: { chip: 'bg-amber-500/20 text-amber-300 border-amber-500/40', dot: 'bg-amber-400', label: 'Supercycle Bull' },
}

export default function ExecutiveDashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [history, setHistory] = useState<HistoryDataPoint[]>([])
  const [selectedRoute, setSelectedRoute] = useState(DASHBOARD_ROUTES[0])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isLiveApi, setIsLiveApi] = useState(false)

  // Live regime state
  const [regime, setRegime] = useState<{
    regime: string; confidence: number; urgency: string;
    contract_recommendation: string; primary_driver: string;
  } | null>(null)

  // Live congestion state (4 ports)
  type CongestionEntry = { congestion_score?: number; anchor_count?: number; estimated_wait_days?: number; virtual_arrival_saving_usd?: number }
  const [congestion, setCongestion] = useState<Record<string, CongestionEntry>>({})

  // Tidal windows
  const [tidalWindows, setTidalWindows] = useState<Array<{ window_start: string; available_draft_m: number; vessel_classes_feasible: string[] }>>([])  

  const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  const fetchRegime = useCallback(() => {
    fetch(`${BASE_URL}/api/regime/current`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setRegime(d) })
      .catch(() => {})
  }, [BASE_URL])

  const fetchCongestion = useCallback(() => {
    const ports = ['INTUT', 'INMAA', 'INPAV', 'INHZA']
    Promise.all(
      ports.map(p =>
        fetch(`${BASE_URL}/api/ports/congestion?port=${p}`)
          .then(r => r.ok ? r.json() : null)
          .catch(() => null)
      )
    ).then(([tut, maa, pav, hza]) => {
      setCongestion({
        INTUT: tut || { congestion_score: 18, anchor_count: 2, estimated_wait_days: 1.5, virtual_arrival_saving_usd: 12400 },
        INMAA: maa || { congestion_score: 42, anchor_count: 4, estimated_wait_days: 3.0, virtual_arrival_saving_usd: 28600 },
        INPAV: pav || { congestion_score: 74, anchor_count: 6, estimated_wait_days: 4.5, virtual_arrival_saving_usd: 41200 },
        INHZA: hza || { congestion_score: 55, anchor_count: 5, estimated_wait_days: 3.5, virtual_arrival_saving_usd: 32100 },
      })
    })
  }, [BASE_URL])

  const fetchTidal = useCallback(() => {
    fetch(`${BASE_URL}/api/ports/tidal-windows?port=haldia&days=3`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (Array.isArray(d)) setTidalWindows(d.slice(0, 3)) })
      .catch(() => {
        // Fallback demo tidal data
        const now = new Date()
        setTidalWindows([
          { window_start: new Date(now.getTime() + 6*3600000).toISOString(), available_draft_m: 8.4, vessel_classes_feasible: ['Handysize', 'Supramax'] },
          { window_start: new Date(now.getTime() + 18*3600000).toISOString(), available_draft_m: 9.1, vessel_classes_feasible: ['Handysize', 'Supramax'] },
          { window_start: new Date(now.getTime() + 30*3600000).toISOString(), available_draft_m: 8.7, vessel_classes_feasible: ['Handysize'] },
        ])
      })
  }, [BASE_URL])

  useEffect(() => {
    let active = true
    Promise.all([
      api.health(),
      api.dashboard.summary(),
      api.dashboard.chartData(
        selectedRoute.origin,
        selectedRoute.destination,
        selectedRoute.vessel_class
      ),
    ])
      .then(([health, s, h]) => {
        if (!active) return
        setIsLiveApi(health.isLive)
        setSummary(s)
        setHistory(h.data)
      })
      .catch((e: unknown) => {
        if (!active) return
        setError(e instanceof Error ? e.message : 'Dashboard load failed')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [selectedRoute.origin, selectedRoute.destination, selectedRoute.vessel_class])

  // Fetch regime, congestion, tidal on mount + poll regime every 60s
  useEffect(() => {
    fetchRegime()
    fetchCongestion()
    fetchTidal()
    const regimeInterval = setInterval(fetchRegime, 60000)
    return () => clearInterval(regimeInterval)
  }, [fetchRegime, fetchCongestion, fetchTidal])

  // Generate chart data combining historical points with forecast forward projection and confidence band
  const combinedChartData = (() => {
    if (!history || history.length === 0) return []

    // Take last 12 historical points
    const hist = history.slice(-12).map((h) => ({
      date: h.date,
      actualRate: h.rate,
      predictedRate: undefined as number | undefined,
      lowerBound: undefined as number | undefined,
      upperBound: undefined as number | undefined,
      tce: h.tce,
    }))

    // Connect the last historical point with the forecast point
    const lastPoint = hist[hist.length - 1]
    if (lastPoint) {
      lastPoint.predictedRate = lastPoint.actualRate
      lastPoint.lowerBound = lastPoint.actualRate
      lastPoint.upperBound = lastPoint.actualRate
    }

    // Add forecast milestones (+14d, +30d)
    const d14 = new Date(lastPoint ? lastPoint.date : '2026-09-14')
    d14.setDate(d14.getDate() + 14)

    const d30 = new Date(lastPoint ? lastPoint.date : '2026-09-14')
    d30.setDate(d30.getDate() + 30)

    const midPredicted = Number(
      ((selectedRoute.currentRate + selectedRoute.predictedRate) / 2).toFixed(2)
    )

    // P10 / P50 / P90 quantile bands
    const forecastPoints = [
      {
        date: d14.toISOString().slice(0, 10) + ' +14d',
        actualRate: undefined as number | undefined,
        p50: midPredicted,
        p90: Number((midPredicted * 1.13).toFixed(2)),
        p10: Number((midPredicted * 0.88).toFixed(2)),
        tce: Math.round(midPredicted * 1180),
      },
      {
        date: d30.toISOString().slice(0, 10) + ' +30d',
        actualRate: undefined as number | undefined,
        p50: selectedRoute.predictedRate,
        p90: Number((selectedRoute.predictedRate * 1.15).toFixed(2)),
        p10: Number((selectedRoute.predictedRate * 0.85).toFixed(2)),
        tce: Math.round(selectedRoute.predictedRate * 1200),
      },
    ]

    return [...hist, ...forecastPoints]
  })()

  const expectedMoveUsd = Number(
    (selectedRoute.predictedRate - selectedRoute.currentRate).toFixed(2)
  )

  return (
    <div className="p-8 max-w-[1700px] mx-auto">
      {/* Top Header & Context */}
      <PageHeader
        title="Executive Chartering Dashboard"
        subtitle="Real-time freight rate indications, predictive market timing, vessel suitability & financial risk intelligence for East Coast Indian dry bulk trade"
      >
        <DataModeBadge isLive={isLiveApi} />
        <Link
          href="/copilot"
          className="px-3.5 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-md shadow-purple-600/25"
        >
          <Bot size={14} />
          AI Copilot
        </Link>
        <Link
          href="/regime"
          className="px-3.5 py-2 bg-gray-900 hover:bg-gray-800 border border-gray-700 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow"
        >
          <Gauge size={14} />
          HMM Regime
        </Link>
        <Link
          href="/cargo-planning"
          className="px-3.5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow"
        >
          <CalendarCheck2 size={14} />
          New Cargo Plan
        </Link>
      </PageHeader>

      {/* ─── MACRO REGIME & REAL OPTIONS INTELLIGENCE BANNER ─── */}
      <div className="mb-6 p-4 rounded-2xl bg-gradient-to-r from-gray-900 via-blue-950/40 to-gray-900 border border-blue-600/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-lg">
        <div className="flex flex-wrap items-center gap-4 text-xs">
          {/* Live HMM Regime */}
          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full animate-pulse ${regime ? REGIME_CHIP[regime.regime]?.dot ?? 'bg-gray-400' : 'bg-gray-600'}`} />
            <span className="text-gray-400 font-medium">HMM Market Regime:</span>
            <Link
              href="/regime"
              title={regime?.primary_driver}
              className={`px-2 py-0.5 rounded-full text-xs font-mono font-bold border hover:underline ${
                regime ? REGIME_CHIP[regime.regime]?.chip ?? 'bg-gray-700 text-gray-300 border-gray-600' : 'bg-gray-800 text-gray-400 border-gray-700'
              }`}
            >
              {regime
                ? `${REGIME_CHIP[regime.regime]?.label ?? regime.regime} (${Math.round(regime.confidence * 100)}% Conf)`
                : 'Loading...'}
            </Link>
          </div>

          <div className="h-4 w-px bg-gray-800 hidden sm:block" />

          {/* Regime action / urgency */}
          <div className="flex items-center gap-2">
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-gray-400 font-medium">Strategy Signal:</span>
            <span className="font-mono font-bold text-amber-300">
              {regime ? `${regime.urgency} — ${regime.contract_recommendation}` : 'WAIT 12d (Option Value: $120,155)'}
            </span>
          </div>

          <div className="h-4 w-px bg-gray-800 hidden sm:block" />

          {/* Paradip congestion (live) */}
          <div className="flex items-center gap-2">
            <Anchor className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-gray-400 font-medium">East Coast AIS Queue:</span>
            <span className="font-mono font-bold text-white">
              {congestion.INPAV
                ? `Paradip (${congestion.INPAV.congestion_score ?? 74}/100, ${congestion.INPAV.anchor_count ?? 6} ships)`
                : 'Paradip (74/100 Congested, 6 ships)'}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Link
            href="/copilot"
            className="text-xs text-purple-300 hover:text-white flex items-center gap-1 font-semibold transition bg-purple-950/40 hover:bg-purple-900/60 px-3 py-1.5 rounded-lg border border-purple-500/40"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            Consult Copilot on this Route
            <ArrowRight className="w-3.5 h-3.5 ml-0.5" />
          </Link>
        </div>
      </div>

      {/* Trade Route Selector */}
      <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-1">
        <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider whitespace-nowrap mr-1">
          Active Trade Lane:
        </span>

        {DASHBOARD_ROUTES.map((route) => {
          const isSelected = selectedRoute.label === route.label
          const cfg = marketActionConfig(route.action)
          return (
            <button
              key={route.label}
              onClick={() => setSelectedRoute(route)}
              className={`px-3.5 py-2 rounded-xl text-xs font-medium border transition-all flex items-center gap-2 whitespace-nowrap ${
                isSelected
                  ? 'bg-gray-800 border-blue-500 text-white shadow-sm ring-1 ring-blue-500/30'
                  : 'bg-gray-900/60 border-gray-800 text-gray-400 hover:text-white hover:border-gray-700'
              }`}
            >
              <span>{route.label}</span>
              <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${cfg.badgeBg}`}>
                {route.action}
              </span>
            </button>
          )
        })}
      </div>

      {loading && (
        <div>
          <SkeletonBanner />
          <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-3 mb-6">
            {Array.from({ length: 8 }).map((_, i) => <SkeletonCard key={i} />)}
          </div>
          <SkeletonChart />
        </div>
      )}
      {error && <ErrorBox message={error} />}

      {/* ─── 8 PROMINENT EXECUTIVE KPIS ─── */}
      <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-3 mb-6">
        {/* KPI 1: Current Freight Indication */}
        <StatCard
          label="1. Current Rate"
          value={formatUSD(selectedRoute.currentRate, 2)}
          subValue="USD / Metric Ton"
          icon={<DollarSign size={15} />}
          badge={{ text: 'Prompt Index', color: 'bg-gray-800 text-gray-300' }}
        />

        {/* KPI 2: Forecast Freight */}
        <StatCard
          label="2. Forecast Rate"
          value={formatUSD(selectedRoute.predictedRate, 2)}
          subValue="30-Day Forward"
          icon={<TrendingUp size={15} />}
          badge={{
            text: `${trendArrow(expectedMoveUsd > 0 ? 'rising' : 'falling')} ${
              expectedMoveUsd > 0 ? 'RISING' : 'FALLING'
            }`,
            color:
              expectedMoveUsd > 0
                ? 'bg-red-500/20 text-red-400'
                : 'bg-emerald-500/20 text-emerald-400',
          }}
        />

        {/* KPI 3: Market Entry Recommendation */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col justify-between">
          <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
            3. Market Action
          </p>
          <div className="my-1">
            <span
              className={`inline-block px-3 py-1 rounded-lg text-xs font-black tracking-wide ${
                marketActionConfig(selectedRoute.action).badgeBg
              }`}
            >
              {selectedRoute.action}
            </span>
            <p className="text-[11px] text-gray-400 mt-1">Confidence {selectedRoute.confidence}%</p>
          </div>
          <span className="text-[10px] text-gray-400">AI Entry Directive</span>
        </div>

        {/* KPI 4: Recommended Vessel */}
        <StatCard
          label="4. Best Vessel"
          value={selectedRoute.vessel}
          subValue="Optimal parcel fit"
          icon={<Ship size={15} />}
          badge={{ text: 'Score: 95/100', color: 'bg-blue-500/20 text-blue-300' }}
        />

        {/* KPI 5: Estimated Voyage Cost */}
        <StatCard
          label="5. Voyage Cost"
          value={formatUSD(selectedRoute.totalCost, 0)}
          subValue="Bunker, Port, OPEX"
          icon={<Calculator size={15} />}
          badge={{ text: '70,000 MT Basis', color: 'bg-gray-800 text-gray-400' }}
        />

        {/* KPI 6: Contract Recommendation */}
        <StatCard
          label="6. Contract Type"
          value="Short-Term COA"
          subValue="3–6 Month Coverage"
          icon={<Layers size={15} />}
          badge={{ text: 'Hedge vs Spot', color: 'bg-emerald-500/20 text-emerald-300' }}
        />

        {/* KPI 7: Risk Score */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col justify-between">
          <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
            7. Risk Score
          </p>
          <div className="flex items-baseline gap-2 my-1">
            <p className="text-2xl font-black text-white">{selectedRoute.riskScore}</p>
            <span className="text-xs text-gray-400">/ 100</span>
            <RiskBadge level={selectedRoute.riskScore > 50 ? 'High' : selectedRoute.riskScore > 35 ? 'Medium' : 'Low'} />
          </div>
          <span className="text-[10px] text-gray-400">Multi-factor Index</span>
        </div>

        {/* KPI 8: Potential Savings */}
        <div className="bg-emerald-950/30 border border-emerald-800/60 rounded-xl p-4 flex flex-col justify-between">
          <p className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">
            8. Opportunity
          </p>
          <div className="my-1">
            <p className="text-xl font-black text-emerald-300">
              {formatUSD(selectedRoute.savings, 0)}
            </p>
            <p className="text-[11px] text-emerald-400/80 mt-0.5">Potential Savings</p>
          </div>
          <span className="text-[10px] text-emerald-400/60">vs. baseline spot</span>
        </div>
      </div>

      {/* ─── LIVE PORT CONGESTION CARDS (U5) ─── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {[
          { code: 'INTUT', name: 'Thoothukudi (VOCPA)', shortName: 'Thoothukudi' },
          { code: 'INMAA', name: 'Chennai Kamarajar', shortName: 'Chennai' },
          { code: 'INPAV', name: 'Paradip', shortName: 'Paradip' },
          { code: 'INHZA', name: 'Haldia (Tidal)', shortName: 'Haldia' },
        ].map(({ code, name, shortName }) => {
          const c = congestion[code]
          const score = c?.congestion_score ?? (code === 'INTUT' ? 18 : code === 'INMAA' ? 42 : code === 'INPAV' ? 74 : 55)
          const anchors = c?.anchor_count ?? (code === 'INTUT' ? 2 : code === 'INMAA' ? 4 : code === 'INPAV' ? 6 : 5)
          const waitDays = c?.estimated_wait_days ?? (code === 'INTUT' ? 1.5 : code === 'INMAA' ? 3.0 : code === 'INPAV' ? 4.5 : 3.5)
          const vaSaving = c?.virtual_arrival_saving_usd
          const barColor = score > 75 ? 'bg-red-500' : score > 40 ? 'bg-amber-500' : 'bg-emerald-500'
          const textColor = score > 75 ? 'text-red-400' : score > 40 ? 'text-amber-400' : 'text-emerald-400'
          return (
            <div key={code} className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-gray-700 transition-all">
              <div className="flex items-center justify-between mb-2">
                <p className="text-[11px] font-bold text-gray-400 uppercase tracking-wider truncate">{shortName}</p>
                <span className={`text-xs font-black font-mono ${textColor}`}>{score}/100</span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-1.5 mb-3">
                <div className={`h-1.5 rounded-full ${barColor} transition-all`} style={{ width: `${score}%` }} />
              </div>
              <p className="text-[11px] text-gray-400">{anchors} vessels anchored · ~{waitDays.toFixed(1)}d wait</p>
              {vaSaving && vaSaving > 5000 && (
                <p className="text-[10px] text-emerald-400 mt-1 font-semibold">VA Saving: {formatUSD(vaSaving, 0)}</p>
              )}
            </div>
          )
        })}
      </div>
      <p className="text-[11px] text-gray-500 -mt-4 mb-6 font-medium uppercase tracking-wider">⚓ East Coast AIS Port Queue — Live Snapshot</p>

      {/* ─── HIGH VISUAL MARKET ENTRY CARD ─── */}
      <div className="mb-6">
        <MarketEntryCard
          action={selectedRoute.action}
          currentRate={selectedRoute.currentRate}
          predictedRate={selectedRoute.predictedRate}
          expectedMovement={expectedMoveUsd}
          confidencePct={selectedRoute.confidence}
          potentialSavings={selectedRoute.savings}
          origin={selectedRoute.origin}
          destination={selectedRoute.destination}
          vesselClass={selectedRoute.vessel_class}
          horizonDays={30}
          recommendationText={
            selectedRoute.action === 'WAIT'
              ? `Model indicates supply overhang with 1.34x Pacific bulker ballast ratio. Delaying spot fixture 12–16 days captures an estimated $${selectedRoute.savings.toLocaleString()} in freight savings for 70k MT.`
              : selectedRoute.action === 'CHARTER NOW'
              ? `Immediate chartering strongly recommended. Regional vessel tightening and bunker fuel escalation will push rates higher within 10 days.`
              : `Monitor forward fixtures closely. Capesize supply remains balanced, but seasonal monsoon factors in Bay of Bengal require active queue surveillance.`
          }
          isDemoData={!isLiveApi}
        />
      </div>

      {/* ─── CHARTS: HISTORICAL FREIGHT + FORECAST + CONFIDENCE BAND ─── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6">
        {/* Main Chart */}
        <Card
          title="Freight Rate Trajectory & Confidence Band"
          subtitle="Weekly historical actuals transitioning into 30-day forecast with statistical upper/lower bounds"
          className="xl:col-span-2"
        >
          <div className="flex items-center justify-between gap-4 mb-4 text-xs">
            <div className="flex items-center gap-4 flex-wrap">
              <span className="flex items-center gap-1.5 text-gray-300">
                <span className="w-3 h-0.5 bg-blue-500 inline-block" /> Historical Rate
              </span>
              <span className="flex items-center gap-1.5 text-gray-300">
                <span className="w-3 h-0.5 bg-amber-400 inline-block" /> P50 Median
              </span>
              <span className="flex items-center gap-1.5 text-gray-300">
                <span className="w-3 h-0.5 bg-emerald-400 inline-block" style={{ borderTop: '2px dotted' }} /> P90 Optimistic
              </span>
              <span className="flex items-center gap-1.5 text-gray-300">
                <span className="w-3 h-0.5 bg-red-400 inline-block" style={{ borderTop: '2px dotted' }} /> P10 Pessimistic
              </span>
            </div>
            <span className="text-[11px] text-gray-400 font-mono">
              LightGBM + HMM Ensemble | P10/P50/P90 Quantile Forecast
            </span>
          </div>

          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={combinedChartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="quantileBand" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.18} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.03} />
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
                  name === 'actualRate' ? 'Historical Actual'
                    : name === 'p50' ? 'P50 Median Forecast'
                    : name === 'p90' ? 'P90 Optimistic'
                    : name === 'p10' ? 'P10 Pessimistic'
                    : String(name),
                ]}
              />
              <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />

              {/* P90→P10 quantile shaded band */}
              <Area type="monotone" dataKey="p90" stroke="#22c55e" strokeDasharray="3 3"
                strokeWidth={1.5} fill="url(#quantileBand)" strokeOpacity={0.7} name="p90" />
              <Area type="monotone" dataKey="p10" stroke="#f87171" strokeDasharray="3 3"
                strokeWidth={1.5} fill="#111827" strokeOpacity={0.7} name="p10" />

              {/* Historical actual */}
              <Area type="monotone" dataKey="actualRate" stroke="#3b82f6" fill="none"
                strokeWidth={2.5} dot={{ r: 3, fill: '#3b82f6' }} name="actualRate" />

              {/* P50 median forecast */}
              <Line type="monotone" dataKey="p50" stroke="#f59e0b" strokeWidth={2.5}
                strokeDasharray="4 4" dot={{ r: 4, fill: '#f59e0b' }} name="p50" />

              <ReferenceLine
                y={selectedRoute.predictedRate}
                stroke="#f59e0b"
                strokeDasharray="3 3"
                label={{
                  value: `P50: $${selectedRoute.predictedRate.toFixed(2)}`,
                  fill: '#f59e0b',
                  fontSize: 10,
                  position: 'insideTopRight',
                }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        {/* Side Panel: Decision Pillars & Quick Links */}
        <Card title="Operational Command Matrix" subtitle="Deep-dive access across core decision engines + tidal schedule">
          <div className="space-y-3">
            {/* Link 1: Cargo Planning */}
            <Link
              href="/cargo-planning"
              className="p-3 bg-gray-800/40 hover:bg-gray-800/90 border border-gray-800 hover:border-blue-500/50 rounded-xl transition flex items-center justify-between group"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 group-hover:bg-blue-500 group-hover:text-white transition">
                  <CalendarCheck2 size={16} />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">Cargo Planning Workflow</h4>
                  <p className="text-[11px] text-gray-400">Origin, Destination, Laycan & Volume</p>
                </div>
              </div>
              <ArrowRight size={14} className="text-gray-500 group-hover:text-blue-400 transition" />
            </Link>

            {/* Link 2: Vessel Optimization */}
            <Link
              href="/vessels"
              className="p-3 bg-gray-800/40 hover:bg-gray-800/90 border border-gray-800 hover:border-cyan-500/50 rounded-xl transition flex items-center justify-between group"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 group-hover:bg-cyan-500 group-hover:text-white transition">
                  <Ship size={16} />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">4-Class Vessel Comparison</h4>
                  <p className="text-[11px] text-gray-400">Handysize · Supramax · Panamax · Capesize</p>
                </div>
              </div>
              <ArrowRight size={14} className="text-gray-500 group-hover:text-cyan-400 transition" />
            </Link>

            {/* Link 3: Port Compatibility */}
            <Link
              href="/ports"
              className="p-3 bg-gray-800/40 hover:bg-gray-800/90 border border-gray-800 hover:border-amber-500/50 rounded-xl transition flex items-center justify-between group"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 group-hover:bg-amber-500 group-hover:text-white transition">
                  <Anchor size={16} />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">Port Compatibility Matrix</h4>
                  <p className="text-[11px] text-gray-400">Draft, LOA & tidal constraints (7 ports)</p>
                </div>
              </div>
              <ArrowRight size={14} className="text-gray-500 group-hover:text-amber-400 transition" />
            </Link>

            {/* Link 4: Risk & Alerts */}
            <Link
              href="/risk"
              className="p-3 bg-gray-800/40 hover:bg-gray-800/90 border border-gray-800 hover:border-red-500/50 rounded-xl transition flex items-center justify-between group"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-red-500/10 text-red-400 group-hover:bg-red-500 group-hover:text-white transition">
                  <ShieldAlert size={16} />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">Risk Dashboard & Alerts</h4>
                  <p className="text-[11px] text-gray-400">5 Active operational alerts</p>
                </div>
              </div>
              <ArrowRight size={14} className="text-gray-500 group-hover:text-red-400 transition" />
            </Link>

            {/* Link 5: Scenario Simulator */}
            <Link
              href="/scenarios"
              className="p-3 bg-gray-800/40 hover:bg-gray-800/90 border border-gray-800 hover:border-purple-500/50 rounded-xl transition flex items-center justify-between group"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 group-hover:bg-purple-500 group-hover:text-white transition">
                  <GitCompare size={16} />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">Scenario & Idle Optimizer</h4>
                  <p className="text-[11px] text-gray-400">Slow-steaming vs Demurrage P&L</p>
                </div>
              </div>
              <ArrowRight size={14} className="text-gray-500 group-hover:text-purple-400 transition" />
            </Link>

            {/* Tidal Windows (U6) */}
            {tidalWindows.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-800">
                <p className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Droplets size={12} className="text-cyan-400" />
                  Next Tidal Windows — Haldia
                </p>
                <div className="space-y-2">
                  {tidalWindows.map((w, i) => {
                    const dt = new Date(w.window_start)
                    const timeStr = dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                    const dateStr = dt.toLocaleDateString([], { month: 'short', day: 'numeric' })
                    return (
                      <div key={i} className="flex items-center justify-between p-2 bg-gray-800/40 rounded-lg text-[11px]">
                        <div className="flex items-center gap-2">
                          <span className="px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-400 font-mono font-bold">HW</span>
                          <span className="text-gray-300 font-medium">{timeStr} <span className="text-gray-500">{dateStr}</span></span>
                        </div>
                        <span className="font-mono text-blue-300">{w.available_draft_m?.toFixed(1)}m</span>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>

      <Disclaimer
        text={
          summary?.disclaimer ||
          'DEMO BENCHMARK DATA: Powered by FreightIQ maritime physics and East Coast India historical fixtures. All figures indicative.'
        }
      />
    </div>
  )
}
