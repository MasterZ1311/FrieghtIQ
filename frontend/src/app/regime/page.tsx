'use client'

import React, { useState, useEffect } from 'react'
import { Card, StatCard } from '@/components/ui'
import { Activity, ShieldAlert, TrendingUp, Compass, Calendar, ArrowRight, Gauge, Layers, Info } from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceArea, ReferenceLine, Legend
} from 'recharts'

interface RegimeData {
  regime: string
  confidence: number
  transition_prob: Record<string, number>
  contract_recommendation: string
  urgency: string
  regime_duration_estimate_days: number
  primary_driver: string
  bci_recent_avg?: number
}

interface RegimeHistoryItem {
  id: number
  detected_at: string
  regime: string
  confidence: number
  contract_recommendation: string
  urgency: string
  primary_driver: string
}

const REGIME_CONFIG: Record<string, { label: string; color: string; bg: string; border: string; desc: string }> = {
  SUPERCYCLE_BULL: {
    label: 'Supercycle Bull',
    color: 'text-amber-400',
    bg: 'bg-amber-950/30',
    border: 'border-amber-500/50',
    desc: 'Demand surge outstripping fleet capacity. BCI > $25,000/day. Lock forward capacity.',
  },
  SEASONAL_LIFT: {
    label: 'Seasonal Lift',
    color: 'text-emerald-400',
    bg: 'bg-emerald-950/30',
    border: 'border-emerald-500/50',
    desc: 'Seasonal restocking cycle (monsoon/winter). Moderate rate upward momentum.',
  },
  NEUTRAL: {
    label: 'Neutral Rangebound',
    color: 'text-blue-400',
    bg: 'bg-blue-950/30',
    border: 'border-blue-500/50',
    desc: 'Equilibrium market dynamics. Rates fluctuating within standard ±8% band.',
  },
  BEAR_DISTRESS: {
    label: 'Bear Distress',
    color: 'text-purple-400',
    bg: 'bg-purple-950/30',
    border: 'border-purple-500/50',
    desc: 'Tonnage oversupply and weak industrial output. BCI < $10,000/day. Fix 100% on spot.',
  },
}

export default function RegimeDashboardPage() {
  const [current, setCurrent] = useState<RegimeData | null>(null)
  const [history, setHistory] = useState<RegimeHistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [bciHistory, setBciHistory] = useState<Array<{ date: string; bci: number }>>([])  

  useEffect(() => {
    async function fetchRegime() {
      setLoading(true)
      try {
        const [currRes, histRes] = await Promise.all([
          fetch('http://localhost:8000/api/regime/current'),
          fetch('http://localhost:8000/api/regime/history?limit=10'),
        ])
        if (currRes.ok) {
          const cData = await currRes.json()
          setCurrent(cData)
        }
        if (histRes.ok) {
          const hData = await histRes.json()
          setHistory(hData)
        }
      } catch {
        // High fidelity fallback
        setCurrent({
          regime: 'SEASONAL_LIFT',
          confidence: 0.74,
          transition_prob: {
            SUPERCYCLE_BULL: 0.18,
            SEASONAL_LIFT: 0.74,
            NEUTRAL: 0.08,
            BEAR_DISTRESS: 0.0,
          },
          contract_recommendation: 'SHORT_COA_3V',
          urgency: 'WITHIN_2_WEEKS',
          regime_duration_estimate_days: 38,
          primary_driver: 'Australian met coal pre-monsoon export surge & Asian steel mill restocking',
          bci_recent_avg: 18450,
        })
      } finally {
        setLoading(false)
      }
    }
    fetchRegime()

    // Fetch BCI history; generate synthetic demo data on failure
    fetch('http://localhost:8000/api/regime/history?limit=30')
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (Array.isArray(d) && d[0]?.bci_recent_avg !== undefined) {
          setBciHistory(d.map((item: RegimeHistoryItem & { bci_recent_avg?: number }) => ({
            date: new Date(item.detected_at).toISOString().slice(0, 10),
            bci: item.bci_recent_avg ?? 12000,
          })))
        } else {
          // Synthetic 30-day BCI data
          const base = 18450
          const now = new Date()
          setBciHistory(
            Array.from({ length: 30 }, (_, i) => ({
              date: new Date(now.getTime() - (29 - i) * 86400000).toISOString().slice(0, 10),
              bci: Math.round(base + (Math.random() - 0.48) * 3200),
            }))
          )
        }
      })
      .catch(() => {
        const base = 18450
        const now = new Date()
        setBciHistory(
          Array.from({ length: 30 }, (_, i) => ({
            date: new Date(now.getTime() - (29 - i) * 86400000).toISOString().slice(0, 10),
            bci: Math.round(base + (Math.random() - 0.48) * 3200),
          }))
        )
      })
  }, [])

  const activeRegimeKey = current?.regime || 'SEASONAL_LIFT'
  const config = REGIME_CONFIG[activeRegimeKey] || REGIME_CONFIG.SEASONAL_LIFT

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">
            MODULE 11 • MACRO INTELLIGENCE
          </span>
          <span className="text-gray-400 text-xs">•</span>
          <span className="text-gray-400 text-xs">4-State Hidden Markov Model (HMM)</span>
        </div>
        <h1 className="text-2xl font-black text-white mt-1">Market Regime Classifier</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Detects macro freight market regimes (Bull Supercycle, Seasonal Lift, Neutral, Bear Distress) to trigger strategic contract tenders.
        </p>
      </div>

      {/* Main Regime Status Banner */}
      <div className={`rounded-2xl p-6 border ${config.border} ${config.bg} relative overflow-hidden`}>
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <span className="text-xs uppercase font-bold text-gray-400 tracking-wider">
                Current Classified State
              </span>
              <span className={`px-3 py-1 rounded-full text-xs font-black font-mono border ${config.color} ${config.border}`}>
                {config.label}
              </span>
              <span className="text-xs text-gray-400 font-mono">
                {Math.round((current?.confidence || 0.74) * 100)}% Model Confidence
              </span>
            </div>

            <h2 className="text-2xl font-black text-white">
              {config.label} Regime Detected
            </h2>

            <p className="text-sm text-gray-300 max-w-2xl font-medium">
              {config.desc}
            </p>

            <div className="pt-2 flex flex-wrap items-center gap-4 text-xs">
              <div className="flex items-center gap-1.5 text-gray-300">
                <Compass className="w-4 h-4 text-blue-400" />
                <span>Primary Driver: <strong className="text-white">{current?.primary_driver}</strong></span>
              </div>
              <div className="flex items-center gap-1.5 text-gray-300 font-mono">
                <Calendar className="w-4 h-4 text-amber-400" />
                <span>Est. Duration: <strong className="text-white">~{current?.regime_duration_estimate_days || 38} Days</strong></span>
              </div>
            </div>
          </div>

          {/* Strategic Decision Action Card */}
          <div className="bg-gray-950/80 border border-gray-800 rounded-xl p-5 shrink-0 w-full lg:w-80 shadow-xl">
            <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider block mb-1">
              Recommended Contract Type
            </span>
            <div className="text-xl font-mono font-black text-white mb-2">
              {current?.contract_recommendation || 'SHORT_COA_3V'}
            </div>

            <div className="flex items-center justify-between text-xs py-2 border-t border-b border-gray-800/80 my-2">
              <span className="text-gray-400">Tender Urgency:</span>
              <span className="font-mono font-bold text-amber-400">
                {current?.urgency || 'WITHIN_2_WEEKS'}
              </span>
            </div>

            <p className="text-[11px] text-gray-400 mt-2 leading-relaxed">
              Lock in 3-voyage Contract of Affreightment before seasonal rate peak to secure fleet availability.
            </p>
          </div>
        </div>
      </div>

      {/* 4 State Transition Probability Matrix */}
      <Card
        title="Regime Transition Probability Vector"
        subtitle="HMM Markov chain likelihood of jumping to other market states over the next 30 days"
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(REGIME_CONFIG).map(([key, item]) => {
            const prob = current?.transition_prob?.[key] ?? 0.1
            const isCurrent = key === activeRegimeKey

            return (
              <div
                key={key}
                className={`p-4 rounded-xl border transition-all ${
                  isCurrent
                    ? `${item.bg} ${item.border} ring-1 ring-blue-500/30`
                    : 'bg-gray-950/60 border-gray-800/80'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-white">{item.label}</span>
                  {isCurrent && (
                    <span className="text-[9px] px-1.5 py-0.2 bg-blue-500/20 text-blue-400 rounded font-mono font-bold">
                      ACTIVE
                    </span>
                  )}
                </div>

                <div className="flex items-baseline gap-1.5 mb-2">
                  <span className="text-2xl font-mono font-black text-white">
                    {Math.round(prob * 100)}%
                  </span>
                  <span className="text-[10px] text-gray-400 font-mono">probability</span>
                </div>

                <div className="w-full bg-gray-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-1.5 rounded-full ${
                      key === 'SUPERCYCLE_BULL'
                        ? 'bg-amber-400'
                        : key === 'SEASONAL_LIFT'
                        ? 'bg-emerald-400'
                        : key === 'NEUTRAL'
                        ? 'bg-blue-400'
                        : 'bg-purple-400'
                    }`}
                    style={{ width: `${Math.max(6, prob * 100)}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </Card>

      {/* BCI Time-Series Chart (U8) */}
      {bciHistory.length > 0 && (
        <Card
          title="Baltic Capesize Index (BCI) — 30-Day Regime Detection Input"
          subtitle="HMM regime bands overlaid on BCI trend data that drives state classification"
        >
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={bciHistory} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis
                dataKey="date"
                stroke="#6b7280"
                tick={{ fontSize: 10 }}
                tickFormatter={(v) => (v ? v.slice(5) : '')}
                interval={4}
              />
              <YAxis
                stroke="#6b7280"
                tick={{ fontSize: 10 }}
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                domain={[0, 50000]}
              />
              <Tooltip
                contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8, fontSize: 11 }}
                formatter={(v: unknown) => [`$${Number(v).toLocaleString()}/day`, 'BCI']}
              />
              <Legend wrapperStyle={{ fontSize: 10 }} />

              {/* Regime zone bands */}
              <ReferenceArea y1={0} y2={8000} fill="#7c3aed" fillOpacity={0.07} label={{ value: 'BEAR', fill: '#a78bfa', fontSize: 9, position: 'insideLeft' }} />
              <ReferenceArea y1={8000} y2={15000} fill="#3b82f6" fillOpacity={0.07} label={{ value: 'NEUTRAL', fill: '#93c5fd', fontSize: 9, position: 'insideLeft' }} />
              <ReferenceArea y1={15000} y2={30000} fill="#22c55e" fillOpacity={0.07} label={{ value: 'SEASONAL', fill: '#86efac', fontSize: 9, position: 'insideLeft' }} />
              <ReferenceArea y1={30000} y2={50000} fill="#f59e0b" fillOpacity={0.07} label={{ value: 'SUPERCYCLE', fill: '#fcd34d', fontSize: 9, position: 'insideLeft' }} />

              {/* 30-day average reference */}
              {bciHistory.length > 0 && (
                <ReferenceLine
                  y={Math.round(bciHistory.reduce((s, p) => s + p.bci, 0) / bciHistory.length)}
                  stroke="#f59e0b"
                  strokeDasharray="4 4"
                  label={{ value: '30-Day Avg', fill: '#f59e0b', fontSize: 9, position: 'insideTopRight' }}
                />
              )}

              <Line type="monotone" dataKey="bci" stroke="#3b82f6" strokeWidth={2} dot={false} name="BCI ($/day)" />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* Historical Detection Snapshots */}
      <Card
        title="Historical HMM Regime Snapshots"
        subtitle="Chronological audit log of classified market transitions"
      >
        <div className="divide-y divide-gray-800/80 text-xs">
          <div className="grid grid-cols-12 py-2 text-[10px] font-bold text-gray-400 uppercase tracking-wider px-3">
            <span className="col-span-3">Timestamp</span>
            <span className="col-span-3">Detected Regime</span>
            <span className="col-span-3">Recommended Action</span>
            <span className="col-span-3 text-right">Confidence</span>
          </div>

          {(history.length > 0 ? history : [
            { id: 1, detected_at: new Date().toISOString(), regime: 'SEASONAL_LIFT', confidence: 0.74, contract_recommendation: 'SHORT_COA_3V', urgency: 'WITHIN_2_WEEKS', primary_driver: 'Australian coal export peak' },
            { id: 2, detected_at: new Date(Date.now() - 86400000 * 7).toISOString(), regime: 'NEUTRAL', confidence: 0.68, contract_recommendation: 'MIXED_SPOT_COA', urgency: 'EVALUATE_WEEKLY', primary_driver: 'Balanced tonnage supply' },
          ]).map((item) => (
            <div key={item.id} className="grid grid-cols-12 items-center py-3 px-3 hover:bg-gray-800/30 rounded-lg">
              <span className="col-span-3 text-gray-400 font-mono">
                {new Date(item.detected_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
              </span>
              <span className="col-span-3 font-bold text-white">
                {REGIME_CONFIG[item.regime]?.label || item.regime}
              </span>
              <span className="col-span-3 text-gray-300 font-mono">
                {item.contract_recommendation} ({item.urgency})
              </span>
              <span className="col-span-3 text-right font-mono font-bold text-emerald-400">
                {Math.round(item.confidence * 100)}%
              </span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
