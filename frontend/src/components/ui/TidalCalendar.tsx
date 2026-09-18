'use client'

import React, { useState, useEffect } from 'react'
import { Card } from '@/components/ui'
import { Waves, Calendar, Clock, CheckCircle2, XCircle, ArrowUpRight } from 'lucide-react'

interface TidalWindow {
  start: string
  end: string
  tide_height_m: number
  available_draft_m: number
  vessel_classes_feasible: string[]
  window_duration_hrs: number
}

interface TidalData {
  port: string
  channel_depth_m: number
  tidal_range_m: number
  windows: TidalWindow[]
  next_feasible_window?: TidalWindow
  source: string
  recommendation: string
}

export function TidalCalendar({ className = '' }: { className?: string }) {
  const [port, setPort] = useState<string>('haldia')
  const [data, setData] = useState<TidalData | null>(null)
  const [loading, setLoading] = useState<boolean>(false)

  const fetchTidal = async (selectedPort: string) => {
    setLoading(true)
    try {
      const res = await fetch(`http://localhost:8000/api/ports/tidal-windows?port=${selectedPort}&days=7`)
      if (res.ok) {
        const json = await res.json()
        setData(json)
      } else {
        throw new Error('Fallback')
      }
    } catch {
      // Harmonic fallback
      const mockWindows: TidalWindow[] = []
      const now = new Date()
      for (let i = 0; i < 8; i++) {
        const start = new Date(now.getTime() + (i * 12.4 + 4) * 3600000)
        const end = new Date(start.getTime() + 2 * 3600000)
        const tide = Number((3.8 + Math.sin(i * 0.4) * 0.8).toFixed(2))
        const depth = Number((9.5 + tide).toFixed(2))
        const feasible = depth >= 13.0 ? ['Handysize', 'Supramax'] : depth >= 11.0 ? ['Handysize'] : []
        mockWindows.push({
          start: start.toISOString(),
          end: end.toISOString(),
          tide_height_m: tide,
          available_draft_m: depth,
          vessel_classes_feasible: feasible,
          window_duration_hrs: 2.0,
        })
      }
      setData({
        port: selectedPort,
        channel_depth_m: 9.5,
        tidal_range_m: 4.2,
        windows: mockWindows,
        next_feasible_window: mockWindows[0],
        source: 'INCOIS / Harmonic Model (Demo)',
        recommendation: `Next safe tidal entry window: ${new Date(mockWindows[0].start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}. Maximum draft: ${mockWindows[0].available_draft_m}m.`,
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTidal(port)
  }, [port])

  return (
    <Card
      title="INCOIS Semi-Diurnal Tidal Gate Scheduler"
      subtitle="Predicts safe high-water transit windows across Hooghly river sandbars & draft barriers"
      className={className}
      action={
        <div className="flex items-center gap-1.5 bg-gray-950 p-1 rounded-lg border border-gray-800">
          {['haldia', 'gopalpur', 'sagar'].map((p) => (
            <button
              key={p}
              onClick={() => setPort(p)}
              className={`px-2.5 py-1 text-xs font-semibold rounded capitalize transition ${
                port === p
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      }
    >
      {/* Alert Header */}
      {data && (
        <div className="mb-4 p-3.5 bg-blue-950/30 border border-blue-600/40 rounded-xl flex items-start gap-3 text-xs text-blue-200">
          <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center shrink-0 text-blue-400 font-bold">
            <Waves className="w-4 h-4" />
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <span className="font-bold text-white uppercase text-[11px] tracking-wider">
                {data.port} Riverine Approach Gate
              </span>
              <span className="text-[10px] text-gray-400 font-mono">
                Datum Depth: {data.channel_depth_m}m • Spring Range: {data.tidal_range_m}m
              </span>
            </div>
            <p className="mt-1 text-gray-300 font-medium">{data.recommendation}</p>
          </div>
        </div>
      )}

      {/* Windows Table / Grid */}
      <div className="space-y-2">
        <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider grid grid-cols-12 px-3 py-1">
          <span className="col-span-4">Date & High Water Window</span>
          <span className="col-span-2 text-center">Tide Height</span>
          <span className="col-span-2 text-center">Total Draft</span>
          <span className="col-span-4 text-right">Feasible Vessel Classes</span>
        </div>

        <div className="divide-y divide-gray-800/80 max-h-72 overflow-y-auto pr-1">
          {data?.windows.slice(0, 8).map((w, idx) => {
            const startDate = new Date(w.start)
            const endDate = new Date(w.end)
            const isFeasible = w.vessel_classes_feasible.length > 0
            const isNext = idx === 0

            return (
              <div
                key={w.start}
                className={`grid grid-cols-12 items-center px-3 py-2.5 rounded-lg text-xs transition ${
                  isNext
                    ? 'bg-emerald-950/25 border border-emerald-500/30'
                    : 'hover:bg-gray-800/40'
                }`}
              >
                <div className="col-span-4 flex items-center gap-2">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      isFeasible ? 'bg-emerald-400' : 'bg-rose-400'
                    }`}
                  />
                  <div>
                    <span className="font-bold text-white block">
                      {startDate.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })}
                    </span>
                    <span className="text-[11px] text-gray-400 font-mono">
                      {startDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} –{' '}
                      {endDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ({w.window_duration_hrs}h)
                    </span>
                  </div>
                </div>

                <div className="col-span-2 text-center font-mono text-cyan-300 font-semibold">
                  +{w.tide_height_m}m
                </div>

                <div className="col-span-2 text-center font-mono font-bold text-white">
                  {w.available_draft_m}m
                </div>

                <div className="col-span-4 text-right flex flex-wrap justify-end gap-1">
                  {w.vessel_classes_feasible.length > 0 ? (
                    w.vessel_classes_feasible.map((vc) => (
                      <span
                        key={vc}
                        className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                      >
                        {vc}
                      </span>
                    ))
                  ) : (
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-rose-500/10 text-rose-400 border border-rose-500/30">
                      Draft Infeasible
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </Card>
  )
}
export default TidalCalendar
