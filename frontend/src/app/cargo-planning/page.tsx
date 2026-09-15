'use client'
import { useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import {
  formatUSD,
  formatNumber,
  ORIGINS,
  DESTINATIONS,
  COMMODITIES,
  CONTRACT_DURATIONS,
  marketActionConfig,
  feasibilityConfig,
} from '@/lib/utils'
import {
  Card,
  StatCard,
  Loading,
  ErrorBox,
  Disclaimer,
  Select,
  Input,
  PageHeader,
  EmptyState,
} from '@/components/ui'
import type {
  Origin,
  Destination,
  Commodity,
  ContractDurationOption,
  CargoPlanWorkflowInput,
  CargoPlanEvaluationResult,
} from '@/types'
import {
  Ship,
  Anchor,
  Fuel,
  Clock,
  ShieldCheck,
  ArrowRight,
  Download,
  Sparkles,
} from 'lucide-react'

export default function CargoPlanningPage() {
  const [origin, setOrigin] = useState<Origin>('Australia')
  const [destination, setDestination] = useState<Destination>('Paradip')
  const [commodity, setCommodity] = useState<Commodity>('Coal')
  const [cargoMt, setCargoMt] = useState('70000')
  const [laycanStart, setLaycanStart] = useState('2026-10-10')
  const [laycanEnd, setLaycanEnd] = useState('2026-10-20')
  const [duration, setDuration] = useState<ContractDurationOption>('Spot Single Voyage')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<CargoPlanEvaluationResult | null>(null)
  const [planSaved, setPlanSaved] = useState(false)

  const handlePresetCargo = (mt: number) => {
    setCargoMt(String(mt))
  }

  const handleEvaluate = async () => {
    setLoading(true)
    setError(null)
    setPlanSaved(false)
    try {
      const input: CargoPlanWorkflowInput = {
        origin,
        destination,
        commodity,
        cargo_mt: Number(cargoMt) || 70000,
        laycan_start: laycanStart,
        laycan_end: laycanEnd,
        contract_duration: duration,
      }
      const res = await api.cargoPlanning.evaluate(input)
      setResult(res)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Evaluation failed')
    } finally {
      setLoading(false)
    }
  }

  const handleExportPlan = () => {
    if (!result) return
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `FreightIQ-CargoPlan-${result.plan_id}.json`
    a.click()
    setPlanSaved(true)
    setTimeout(() => setPlanSaved(false), 3000)
  }

  return (
    <div className="p-8 max-w-[1700px] mx-auto">
      <PageHeader
        title="Cargo Planning Workflow"
        subtitle="End-to-end procurement and chartering planning: define cargo parameters, laycan schedule, and contract structure with instant multi-pillar feasibility validation."
      >
        {result && (
          <button
            onClick={handleExportPlan}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 rounded-xl text-xs font-semibold transition flex items-center gap-1.5"
          >
            <Download size={14} />
            {planSaved ? 'Plan Exported!' : 'Export Specification'}
          </button>
        )}
      </PageHeader>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* ─── WORKFLOW INPUT FORM ─── */}
        <div className="lg:col-span-5 space-y-5">
          <Card
            title="Step 1: Cargo & Route Specification"
            subtitle="Configure voyage parameters, parcel weight, and laycan timeline"
            className="border-blue-900/40"
          >
            <div className="space-y-4">
              {/* Origin & Destination */}
              <div className="grid grid-cols-2 gap-3">
                <Select
                  label="1. Origin"
                  value={origin}
                  onChange={(v) => setOrigin(v as Origin)}
                  options={ORIGINS}
                />
                <Select
                  label="2. Destination Port"
                  value={destination}
                  onChange={(v) => setDestination(v as Destination)}
                  options={DESTINATIONS}
                />
              </div>

              {/* Commodity */}
              <Select
                label="3. Commodity"
                value={commodity}
                onChange={(v) => setCommodity(v as Commodity)}
                options={COMMODITIES}
              />

              {/* Cargo Quantity with Presets */}
              <div>
                <Input
                  label="4. Cargo Quantity (Metric Tons)"
                  value={cargoMt}
                  onChange={setCargoMt}
                  type="number"
                  placeholder="70000"
                />
                <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                  <span className="text-[10px] text-gray-400 font-medium mr-1">Batch Presets:</span>
                  {[
                    { label: '35k MT (Handy)', val: 35000 },
                    { label: '55k MT (Supra)', val: 55000 },
                    { label: '75k MT (Panamax)', val: 75000 },
                    { label: '150k MT (Cape)', val: 150000 },
                  ].map((preset) => (
                    <button
                      key={preset.label}
                      type="button"
                      onClick={() => handlePresetCargo(preset.val)}
                      className={`px-2 py-0.5 rounded text-[11px] font-mono border transition ${
                        Number(cargoMt) === preset.val
                          ? 'bg-blue-600 border-blue-500 text-white'
                          : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-white'
                      }`}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Laycan Window */}
              <div className="grid grid-cols-2 gap-3 pt-1 border-t border-gray-800">
                <Input
                  label="5. Laycan Start Date"
                  value={laycanStart}
                  onChange={setLaycanStart}
                  type="date"
                />
                <Input
                  label="Laycan End / Cancelling"
                  value={laycanEnd}
                  onChange={setLaycanEnd}
                  type="date"
                />
              </div>

              {/* Contract Duration */}
              <Select
                label="6. Contract Duration"
                value={duration}
                onChange={(v) => setDuration(v as ContractDurationOption)}
                options={CONTRACT_DURATIONS}
              />

              {/* Action Button */}
              <button
                onClick={handleEvaluate}
                disabled={loading}
                className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 text-white font-bold text-xs uppercase tracking-wider rounded-xl transition shadow flex items-center justify-center gap-2 mt-4"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Computing Evaluation Engine…
                  </>
                ) : (
                  <>
                    <Sparkles size={16} />
                    Evaluate Cargo Plan
                  </>
                )}
              </button>
            </div>
          </Card>

          {/* Quick Guidance Info Box */}
          <div className="p-4 bg-gray-900/60 border border-gray-800 rounded-xl text-xs space-y-2 text-gray-400">
            <h4 className="text-[11px] font-bold text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldCheck size={14} className="text-blue-400" />
              Chartering Planning Rule of Thumb
            </h4>
            <p className="leading-relaxed">
              • East Coast Indian coal receivers require strict draft margin verification before
              contracting Capesize tonnage.
            </p>
            <p className="leading-relaxed">
              • Laycan windows under 10 days risk demurrage penalties if anchorage queues exceed 4.5
              days at Paradip or Haldia.
            </p>
          </div>
        </div>

        {/* ─── EVALUATION RESULTS & DECISION SCORECARD ─── */}
        <div className="lg:col-span-7 space-y-5">
          {error && <ErrorBox message={error} />}

          {!result && !loading && (
            <EmptyState
              title="Ready for Cargo Evaluation"
              description="Specify origin, destination, parcel volume, laycan dates, and contract type on the left, then click 'Evaluate Cargo Plan' to generate a full operational scorecard."
              action={
                <button
                  onClick={handleEvaluate}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition"
                >
                  Run Sample Evaluation (AUS → Paradip 70k MT)
                </button>
              }
            />
          )}

          {loading && <Loading message="Evaluating vessel compatibility, freight & port constraints…" />}

          {result && (
            <div className="space-y-5">
              {/* Header Status Bar */}
              <div className="p-5 bg-gray-900 border border-gray-800 rounded-2xl flex flex-wrap items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-gray-500">{result.plan_id}</span>
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                        feasibilityConfig(result.feasibility).bg
                      } ${feasibilityConfig(result.feasibility).color}`}
                    >
                      {result.feasibility.toUpperCase()}
                    </span>
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                        marketActionConfig(result.market_signal).badgeBg
                      }`}
                    >
                      {result.market_signal}
                    </span>
                  </div>
                  <h3 className="text-lg font-black text-white mt-1">
                    {result.input.origin} → {result.input.destination} ({formatNumber(result.input.cargo_mt)} MT {result.input.commodity})
                  </h3>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Laycan: {result.input.laycan_start} to {result.input.laycan_end} · {result.input.contract_duration}
                  </p>
                </div>

                <div className="text-right">
                  <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
                    Total Estimated Voyage Cost
                  </span>
                  <p className="text-2xl font-black text-white">
                    {formatUSD(result.total_voyage_cost_usd, 0)}
                  </p>
                  <span className="text-xs text-emerald-400 font-semibold">
                    {formatUSD(result.estimated_freight_usd_per_mt, 2)}/MT Freight
                  </span>
                </div>
              </div>

              {/* 4 Key Evaluation Pillars */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <StatCard
                  label="Recommended Vessel"
                  value={result.recommended_vessel}
                  subValue="Optimal intake & draft"
                  icon={<Ship size={16} />}
                  badge={{ text: '★ Optimal Class', color: 'bg-blue-500/20 text-blue-300' }}
                />
                <StatCard
                  label="Voyage Duration"
                  value={`${result.voyage_days} Days`}
                  subValue="Sea transit + port days"
                  icon={<Clock size={16} />}
                />
                <StatCard
                  label="Estimated Bunker"
                  value={formatUSD(result.bunker_cost_usd, 0)}
                  subValue="VLSFO marine fuel"
                  icon={<Fuel size={16} />}
                />
                <StatCard
                  label="Port Dues"
                  value={formatUSD(result.port_dues_usd, 0)}
                  subValue={`Berth & pilotage dues`}
                  icon={<Anchor size={16} />}
                />
              </div>

              {/* Detailed Technical Validation Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Port Compatibility Pre-Check */}
                <Card title="Port Clearance Pre-Check">
                  <div className="space-y-3 text-xs">
                    <div className="flex items-center justify-between p-2.5 bg-gray-800/50 rounded-lg">
                      <span className="text-gray-400">Berth Draft Clearance:</span>
                      <span
                        className={`font-semibold ${
                          result.port_compatibility.status === 'OK'
                            ? 'text-emerald-400'
                            : 'text-red-400'
                        }`}
                      >
                        {result.port_compatibility.vessel_draft_m}m Vessel vs {result.port_compatibility.max_draft_m}m Max
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-2.5 bg-gray-800/50 rounded-lg">
                      <span className="text-gray-400">Est. Port Turnaround:</span>
                      <span className="text-white font-semibold">
                        {result.laycan_risk.turnaround_days} Days
                      </span>
                    </div>
                    <p className="text-gray-400 italic text-[11px] leading-relaxed">
                      {result.port_compatibility.notes}
                    </p>
                  </div>
                </Card>

                {/* Contract Strategy Alignment */}
                <Card title="Chartering Strategy Alignment">
                  <div className="space-y-3 text-xs">
                    <div className="p-2.5 bg-gray-800/50 rounded-lg">
                      <span className="text-gray-400 block mb-1">Recommended Structure:</span>
                      <span className="text-white font-bold text-sm">
                        {result.contract_recommendation.strategy}
                      </span>
                    </div>
                    <div className="p-2.5 bg-emerald-950/30 border border-emerald-800/40 rounded-lg flex items-center justify-between">
                      <span className="text-emerald-400 font-medium">Projected Cost Benefit:</span>
                      <span className="text-emerald-300 font-black">
                        +{formatUSD(result.contract_recommendation.potential_savings_usd, 0)}
                      </span>
                    </div>
                    <p className="text-gray-400 text-[11px] leading-relaxed">
                      {result.contract_recommendation.reason}
                    </p>
                  </div>
                </Card>
              </div>

              {/* Next Action Directives */}
              <div className="p-4 bg-gray-900 border border-gray-800 rounded-xl flex items-center justify-between gap-4">
                <div className="text-xs text-gray-300">
                  <strong className="text-white">Next Step: </strong> Compare vessel options or
                  simulate delay risks for this cargo parcel.
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <Link
                    href="/vessels"
                    className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition flex items-center gap-1"
                  >
                    Compare Vessels <ArrowRight size={12} />
                  </Link>
                  <Link
                    href="/scenarios"
                    className="px-3.5 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg text-xs font-semibold transition"
                  >
                    Simulate Delays
                  </Link>
                </div>
              </div>
            </div>
          )}

          <Disclaimer text="DEMO BENCHMARK DATA: Cargo planning evaluation computed via FreightIQ synthetic algorithms. Does not bind shipowner or cargo receiver." />
        </div>
      </div>
    </div>
  )
}
