'use client'

import React from 'react'
import { Card } from '@/components/ui'
import { Leaf, Award, DollarSign, Wind, ShieldCheck } from 'lucide-react'

interface CarbonAnalysis {
  co2_emitted_mt: number
  co2_per_cargo_mt_kg: number
  cii_rating: 'A' | 'B' | 'C' | 'D' | 'E'
  eu_ets_cost_usd: number
  cii_charter_rate_impact_usd: number
  carbon_surcharge_total_usd: number
  carbon_adjusted_total_usd: number
  carbon_saving_if_slow_steam_usd: number
}

interface CarbonFootprintCardProps {
  carbonData?: CarbonAnalysis
  className?: string
}

const DEFAULT_CARBON: CarbonAnalysis = {
  co2_emitted_mt: 2140.0,
  co2_per_cargo_mt_kg: 30.57,
  cii_rating: 'B',
  eu_ets_cost_usd: 89400,
  cii_charter_rate_impact_usd: 0,
  carbon_surcharge_total_usd: 89400,
  carbon_adjusted_total_usd: 2936400,
  carbon_saving_if_slow_steam_usd: 22300,
}

export function CarbonFootprintCard({
  carbonData = DEFAULT_CARBON,
  className = '',
}: CarbonFootprintCardProps) {
  const data = carbonData || DEFAULT_CARBON

  const getCiiBadgeColor = (rating: string) => {
    switch (rating) {
      case 'A':
        return 'bg-emerald-500 text-black border-emerald-400'
      case 'B':
        return 'bg-emerald-600 text-white border-emerald-500'
      case 'C':
        return 'bg-amber-500 text-black border-amber-400'
      case 'D':
        return 'bg-orange-500 text-white border-orange-400'
      default:
        return 'bg-rose-600 text-white border-rose-500'
    }
  }

  return (
    <Card
      title="IMO Carbon Intensity & EU ETS Green Surcharge"
      subtitle="Scope 3 maritime emissions accounting, CII tier penalty modeling & carbon offsets"
      className={className}
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
        {/* Rating Card */}
        <div className="bg-gray-950/80 p-4 rounded-xl border border-gray-800 flex items-center justify-between">
          <div>
            <span className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider block">
              IMO CII Rating Tier
            </span>
            <span className="text-xs text-gray-400 mt-1 block">
              {data.cii_rating === 'A' || data.cii_rating === 'B'
                ? 'Superior efficiency • Zero rate penalty'
                : 'Sub-optimal rating • Surcharge applicable'}
            </span>
          </div>
          <div
            className={`w-12 h-12 rounded-xl flex items-center justify-center font-black text-2xl border shadow-lg ${getCiiBadgeColor(
              data.cii_rating
            )}`}
          >
            {data.cii_rating}
          </div>
        </div>

        {/* Total CO2 */}
        <div className="bg-gray-950/80 p-4 rounded-xl border border-gray-800">
          <div className="flex items-center justify-between text-gray-400 mb-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider">Voyage CO₂ Emitted</span>
            <Leaf className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-mono font-black text-white">
              {data.co2_emitted_mt.toLocaleString()}
            </span>
            <span className="text-xs font-mono text-gray-400">MT CO₂</span>
          </div>
          <span className="text-[11px] text-gray-400 font-mono mt-1 block">
            {data.co2_per_cargo_mt_kg} kg CO₂ / MT cargo delivered
          </span>
        </div>

        {/* EU ETS / Total Carbon Surcharge */}
        <div className="bg-gray-950/80 p-4 rounded-xl border border-gray-800">
          <div className="flex items-center justify-between text-gray-400 mb-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider">Carbon Cost Exposure</span>
            <DollarSign className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-mono font-black text-white">
              ${data.carbon_surcharge_total_usd.toLocaleString()}
            </span>
            <span className="text-xs font-mono text-gray-400">USD</span>
          </div>
          <span className="text-[11px] text-gray-400 font-mono mt-1 block">
            Includes EU ETS Allowance (€65/t)
          </span>
        </div>
      </div>

      {/* Virtual Arrival Green Savings Banner */}
      <div className="p-3.5 bg-emerald-950/20 border border-emerald-500/30 rounded-xl flex items-center justify-between gap-4 text-xs text-emerald-200">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center shrink-0 text-emerald-400 font-bold">
            <Wind className="w-4 h-4" />
          </div>
          <div>
            <span className="font-bold text-white block">
              Virtual Arrival Decarbonization Incentive
            </span>
            <span className="text-gray-300">
              Slow steaming by 1.8 knots reduces fuel consumption by 22% and avoids anchorage idling emissions.
            </span>
          </div>
        </div>

        <div className="text-right shrink-0">
          <span className="text-[10px] text-emerald-400 uppercase font-bold block">Carbon + Fuel Savings</span>
          <span className="text-base font-mono font-black text-white">
            +${data.carbon_saving_if_slow_steam_usd.toLocaleString()}
          </span>
        </div>
      </div>
    </Card>
  )
}
export default CarbonFootprintCard
