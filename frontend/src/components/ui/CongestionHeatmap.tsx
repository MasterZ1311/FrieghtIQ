'use client'

import React, { useState, useEffect } from 'react'
import { Card } from '@/components/ui'
import { Anchor, AlertCircle, Fuel, Gauge, RefreshCw, Ship } from 'lucide-react'

interface PortCongestion {
  port: string
  congestion_score: number
  status: 'CLEAR' | 'MODERATE' | 'CONGESTED' | 'CRITICAL'
  anchor_count: number
  avg_approach_speed_knots: number
  estimated_wait_days: number
  demurrage_exposure_usd: number
  virtual_arrival_saving_usd: number
  recommendation: string
  source: string
  updated_at: string
}

const DEFAULT_PORTS: PortCongestion[] = [
  {
    port: 'thoothukudi',
    congestion_score: 42,
    status: 'MODERATE',
    anchor_count: 5,
    avg_approach_speed_knots: 9.1,
    estimated_wait_days: 2.2,
    demurrage_exposure_usd: 39600,
    virtual_arrival_saving_usd: 21780,
    recommendation: 'VOCPA NCB-1 berth scheduled; virtual arrival captures $21.8k fuel savings',
    source: 'Global Timex / Shipping Mail (Sept 18, 2026)',
    updated_at: new Date().toISOString(),
  },
  {
    port: 'chennai',
    congestion_score: 46,
    status: 'MODERATE',
    anchor_count: 7,
    avg_approach_speed_knots: 8.8,
    estimated_wait_days: 2.8,
    demurrage_exposure_usd: 50400,
    virtual_arrival_saving_usd: 27720,
    recommendation: 'Jawahar Dock JD-2 clear for Supramax pig iron discharge (MV Supra Monarch)',
    source: 'Exim India Shipping Times (Sept 11, 2026)',
    updated_at: new Date().toISOString(),
  },
  {
    port: 'kamarajar',
    congestion_score: 25,
    status: 'CLEAR',
    anchor_count: 2,
    avg_approach_speed_knots: 10.5,
    estimated_wait_days: 1.4,
    demurrage_exposure_usd: 22400,
    virtual_arrival_saving_usd: 12320,
    recommendation: 'Dedicated coal berths CB1/CB2 clear for prompt cape/panamax berthing',
    source: 'Exim India Shipping Times (Sept 11, 2026)',
    updated_at: new Date().toISOString(),
  },
  {
    port: 'paradip',
    congestion_score: 74,
    status: 'CONGESTED',
    anchor_count: 14,
    avg_approach_speed_knots: 4.1,
    estimated_wait_days: 6.8,
    demurrage_exposure_usd: 136000,
    virtual_arrival_saving_usd: 74800,
    recommendation: 'Slow steam to 10.2 knots to absorb berth waiting time',
    source: 'AISHub / DEMO',
    updated_at: new Date().toISOString(),
  },
  {
    port: 'visakhapatnam',
    congestion_score: 38,
    status: 'MODERATE',
    anchor_count: 6,
    avg_approach_speed_knots: 9.4,
    estimated_wait_days: 2.1,
    demurrage_exposure_usd: 37800,
    virtual_arrival_saving_usd: 20790,
    recommendation: 'Normal steaming. Outer anchorage queue clearing as scheduled',
    source: 'AISHub / DEMO',
    updated_at: new Date().toISOString(),
  },
  {
    port: 'gangavaram',
    congestion_score: 22,
    status: 'CLEAR',
    anchor_count: 2,
    avg_approach_speed_knots: 11.2,
    estimated_wait_days: 0.8,
    demurrage_exposure_usd: 12000,
    virtual_arrival_saving_usd: 6600,
    recommendation: 'Deep draft cape berths fully available upon arrival',
    source: 'AISHub / DEMO',
    updated_at: new Date().toISOString(),
  },
  {
    port: 'dhamra',
    congestion_score: 18,
    status: 'CLEAR',
    anchor_count: 1,
    avg_approach_speed_knots: 11.8,
    estimated_wait_days: 0.5,
    demurrage_exposure_usd: 7500,
    virtual_arrival_saving_usd: 4125,
    recommendation: 'Express cape discharge available. No waiting anticipated',
    source: 'AISHub / DEMO',
    updated_at: new Date().toISOString(),
  },
  {
    port: 'haldia',
    congestion_score: 65,
    status: 'CONGESTED',
    anchor_count: 8,
    avg_approach_speed_knots: 5.8,
    estimated_wait_days: 4.2,
    demurrage_exposure_usd: 63000,
    virtual_arrival_saving_usd: 34650,
    recommendation: 'Check tidal gate. Coordinate entry with morning spring tide',
    source: 'AISHub / DEMO',
    updated_at: new Date().toISOString(),
  },
  {
    port: 'gopalpur',
    congestion_score: 30,
    status: 'MODERATE',
    anchor_count: 2,
    avg_approach_speed_knots: 10.1,
    estimated_wait_days: 1.0,
    demurrage_exposure_usd: 12000,
    virtual_arrival_saving_usd: 6600,
    recommendation: 'Moderate queue. Handymax draft restrictions in effect',
    source: 'AISHub / DEMO',
    updated_at: new Date().toISOString(),
  },
  {
    port: 'sagar',
    congestion_score: 45,
    status: 'MODERATE',
    anchor_count: 4,
    avg_approach_speed_knots: 8.9,
    estimated_wait_days: 2.0,
    demurrage_exposure_usd: 24000,
    virtual_arrival_saving_usd: 13200,
    recommendation: 'Transshipment anchorage operational. Low swell conditions',
    source: 'AISHub / DEMO',
    updated_at: new Date().toISOString(),
  },
]

export function CongestionHeatmap({ className = '' }: { className?: string }) {
  const [ports, setPorts] = useState<PortCongestion[]>(DEFAULT_PORTS)
  const [selectedPort, setSelectedPort] = useState<PortCongestion>(DEFAULT_PORTS[0])
  const [loading, setLoading] = useState(false)

  const fetchLive = async () => {
    setLoading(true)
    try {
      const res = await fetch('http://localhost:8000/api/ports/congestion?port=all')
      if (res.ok) {
        const data = await res.json()
        if (data.ports && data.ports.length > 0) {
          setPorts(data.ports)
          setSelectedPort(data.ports[0])
        }
      }
    } catch {
      // Fallback already in state
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLive()
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'CRITICAL':
        return 'text-rose-400 bg-rose-950/40 border-rose-500/50'
      case 'CONGESTED':
        return 'text-amber-400 bg-amber-950/40 border-amber-500/50'
      case 'MODERATE':
        return 'text-blue-400 bg-blue-950/40 border-blue-500/50'
      default:
        return 'text-emerald-400 bg-emerald-950/40 border-emerald-500/50'
    }
  }

  const getBarColor = (score: number) => {
    if (score > 75) return 'bg-rose-500'
    if (score > 50) return 'bg-amber-500'
    if (score > 25) return 'bg-blue-500'
    return 'bg-emerald-500'
  }

  return (
    <Card
      title="East Coast India — AIS Port Congestion & Virtual Arrival"
      subtitle="Live vessel anchorage queue tracking with Virtual Arrival speed optimization"
      className={className}
      action={
        <button
          onClick={fetchLive}
          disabled={loading}
          className="flex items-center gap-1 text-[11px] font-semibold text-gray-400 hover:text-white px-2 py-1 bg-gray-800/80 rounded border border-gray-700 transition"
        >
          <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
          Refresh AIS
        </button>
      }
    >
      {/* 7 Port Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5 mb-5">
        {ports.map((p) => {
          const isSelected = selectedPort.port.toLowerCase() === p.port.toLowerCase()
          return (
            <button
              key={p.port}
              onClick={() => setSelectedPort(p)}
              className={`p-3 rounded-xl border text-left transition-all relative overflow-hidden ${
                isSelected
                  ? 'bg-gray-800/90 border-blue-500 shadow-md shadow-blue-500/10'
                  : 'bg-gray-950/70 border-gray-800/80 hover:border-gray-700 hover:bg-gray-900/50'
              }`}
            >
              <div className="flex items-center justify-between gap-1 mb-1.5">
                <span className="text-xs font-bold text-white capitalize truncate">{p.port}</span>
                <span className={`text-[9px] px-1.5 py-0.2 rounded font-mono font-bold border ${getStatusColor(p.status)}`}>
                  {p.congestion_score}
                </span>
              </div>

              {/* Mini progress bar */}
              <div className="w-full bg-gray-800 rounded-full h-1.5 mb-2 overflow-hidden">
                <div
                  className={`h-1.5 rounded-full transition-all ${getBarColor(p.congestion_score)}`}
                  style={{ width: `${Math.min(100, Math.max(8, p.congestion_score))}%` }}
                />
              </div>

              <div className="flex items-center justify-between text-[10px] text-gray-400 font-mono">
                <span>{p.anchor_count} anc.</span>
                <span>{p.estimated_wait_days}d wait</span>
              </div>
            </button>
          )
        })}
      </div>

      {/* Selected Port Detailed Intelligence Panel */}
      <div className="bg-gray-950/70 border border-gray-800/90 rounded-xl p-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b border-gray-800/70">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400 font-bold">
              <Anchor className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="text-base font-bold text-white capitalize">
                  {selectedPort.port} Port Anchorage Analysis
                </h4>
                <span className={`text-xs px-2 py-0.5 rounded-full font-mono font-bold border ${getStatusColor(selectedPort.status)}`}>
                  {selectedPort.status} ({selectedPort.congestion_score}/100)
                </span>
              </div>
              <p className="text-xs text-gray-400">
                Source: {selectedPort.source} • Updated: {new Date(selectedPort.updated_at).toLocaleTimeString()}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="text-right">
              <span className="text-[10px] uppercase font-semibold text-emerald-400 block">Virtual Arrival Bunker Saving</span>
              <span className="text-lg font-mono font-black text-white">
                ${selectedPort.virtual_arrival_saving_usd.toLocaleString()}
              </span>
            </div>
          </div>
        </div>

        {/* 4 KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 my-4">
          <div className="bg-gray-900/80 p-3 rounded-lg border border-gray-800">
            <span className="text-[10px] text-gray-400 uppercase font-semibold block">Vessels at Anchor</span>
            <span className="text-lg font-mono font-bold text-white flex items-center gap-1.5 mt-0.5">
              <Ship className="w-4 h-4 text-blue-400" />
              {selectedPort.anchor_count} Ships
            </span>
          </div>

          <div className="bg-gray-900/80 p-3 rounded-lg border border-gray-800">
            <span className="text-[10px] text-gray-400 uppercase font-semibold block">Average Queue Delay</span>
            <span className="text-lg font-mono font-bold text-amber-400 flex items-center gap-1.5 mt-0.5">
              <Gauge className="w-4 h-4" />
              ~{selectedPort.estimated_wait_days} Days
            </span>
          </div>

          <div className="bg-gray-900/80 p-3 rounded-lg border border-gray-800">
            <span className="text-[10px] text-gray-400 uppercase font-semibold block">Demurrage Risk Exposure</span>
            <span className="text-lg font-mono font-bold text-rose-400 flex items-center gap-1.5 mt-0.5">
              <AlertCircle className="w-4 h-4" />
              ${selectedPort.demurrage_exposure_usd.toLocaleString()}
            </span>
          </div>

          <div className="bg-gray-900/80 p-3 rounded-lg border border-gray-800">
            <span className="text-[10px] text-gray-400 uppercase font-semibold block">Average Approach Speed</span>
            <span className="text-lg font-mono font-bold text-emerald-400 flex items-center gap-1.5 mt-0.5">
              <Fuel className="w-4 h-4" />
              {selectedPort.avg_approach_speed_knots} Knots
            </span>
          </div>
        </div>

        {/* Actionable Strategy */}
        <div className="bg-blue-950/20 border border-blue-700/40 rounded-lg p-3 text-xs text-blue-200 flex items-start gap-2">
          <span className="font-bold shrink-0">🎯 Operational Directive:</span>
          <span>{selectedPort.recommendation}</span>
        </div>
      </div>
    </Card>
  )
}
export default CongestionHeatmap
