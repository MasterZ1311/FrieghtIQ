import type {
  RiskLevel,
  Trend,
  ConstraintStatus,
  SignalType,
  MarketEntryAction,
  FeasibilityStatus,
  IdleRiskLevel,
} from '@/types'

export function formatUSD(value: number, decimals = 0): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

export function formatNumber(value: number, decimals = 0): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

export function formatPercent(value: number, decimals = 1): string {
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(decimals)}%`
}

export function riskColor(level: RiskLevel): string {
  const colors: Record<RiskLevel, string> = {
    Low: 'text-emerald-400',
    Medium: 'text-amber-400',
    High: 'text-orange-400',
    Critical: 'text-red-500',
  }
  return colors[level] || 'text-gray-400'
}

export function riskBg(level: RiskLevel): string {
  const colors: Record<RiskLevel, string> = {
    Low: 'bg-emerald-500/20 border-emerald-500/40',
    Medium: 'bg-amber-500/20 border-amber-500/40',
    High: 'bg-orange-500/20 border-orange-500/40',
    Critical: 'bg-red-500/20 border-red-500/40',
  }
  return colors[level] || 'bg-gray-700'
}

export function trendColor(trend: Trend): string {
  const colors: Record<Trend, string> = {
    rising: 'text-red-400',
    falling: 'text-emerald-400',
    stable: 'text-blue-400',
  }
  return colors[trend] || 'text-gray-400'
}

export function trendArrow(trend: Trend): string {
  return trend === 'rising' ? '↑' : trend === 'falling' ? '↓' : '→'
}

export function constraintColor(status: ConstraintStatus): string {
  return status === 'OK' ? 'text-emerald-400' : status === 'WARNING' ? 'text-amber-400' : 'text-red-400'
}

export function marketActionConfig(action: MarketEntryAction): {
  color: string
  bg: string
  border: string
  glow: string
  badgeBg: string
  label: string
  icon: string
} {
  switch (action) {
    case 'CHARTER NOW':
      return {
        color: 'text-emerald-400',
        bg: 'bg-emerald-950/40',
        border: 'border-emerald-500/60',
        glow: 'shadow-emerald-500/10',
        badgeBg: 'bg-emerald-500 text-slate-950 font-bold',
        label: 'CHARTER NOW',
        icon: '⚡',
      }
    case 'WAIT':
      return {
        color: 'text-amber-400',
        bg: 'bg-amber-950/40',
        border: 'border-amber-500/60',
        glow: 'shadow-amber-500/10',
        badgeBg: 'bg-amber-500 text-slate-950 font-bold',
        label: 'WAIT',
        icon: '⏳',
      }
    case 'MONITOR':
    default:
      return {
        color: 'text-cyan-400',
        bg: 'bg-cyan-950/40',
        border: 'border-cyan-500/60',
        glow: 'shadow-cyan-500/10',
        badgeBg: 'bg-cyan-500 text-slate-950 font-bold',
        label: 'MONITOR',
        icon: '👁',
      }
  }
}

export function signalConfig(signal: SignalType): { color: string; bg: string; label: string } {
  const map: Record<SignalType, { color: string; bg: string; label: string }> = {
    BUY_NOW: { color: 'text-emerald-400', bg: 'bg-emerald-500/20 border-emerald-500/40', label: '✓ BUY NOW' },
    WAIT: { color: 'text-amber-400', bg: 'bg-amber-500/20 border-amber-500/40', label: '⏳ WAIT' },
    CAUTIOUS_BUY: { color: 'text-yellow-400', bg: 'bg-yellow-500/20 border-yellow-500/40', label: '⚠ CAUTIOUS BUY' },
    HEDGE: { color: 'text-purple-400', bg: 'bg-purple-500/20 border-purple-500/40', label: '⇌ HEDGE' },
  }
  return map[signal] || { color: 'text-gray-400', bg: 'bg-gray-700', label: signal }
}

export function feasibilityConfig(status: FeasibilityStatus): { color: string; bg: string; border: string } {
  switch (status) {
    case 'Feasible':
      return { color: 'text-emerald-400', bg: 'bg-emerald-500/15', border: 'border-emerald-500/40' }
    case 'Restricted':
      return { color: 'text-red-400', bg: 'bg-red-500/15', border: 'border-red-500/40' }
    case 'Sub-optimal':
    default:
      return { color: 'text-amber-400', bg: 'bg-amber-500/15', border: 'border-amber-500/40' }
  }
}

export function idleRiskConfig(risk: IdleRiskLevel): { color: string; bg: string } {
  switch (risk) {
    case 'Low':
      return { color: 'text-emerald-400', bg: 'bg-emerald-500/20' }
    case 'Moderate':
      return { color: 'text-blue-400', bg: 'bg-blue-500/20' }
    case 'Elevated':
      return { color: 'text-amber-400', bg: 'bg-amber-500/20' }
    case 'High':
    default:
      return { color: 'text-red-400', bg: 'bg-red-500/20' }
  }
}

export const ORIGINS = [
  'Australia',
  'United States',
  'Mozambique',
  'Russia',
  'Indonesia',
  'South Africa',
] as const

export const DESTINATIONS = [
  'Thoothukudi',
  'Chennai',
  'Kamarajar',
  'Paradip',
  'Visakhapatnam',
  'Gangavaram',
  'Gopalpur',
  'Dhamra',
  'Sagar-Sandheads',
  'Haldia',
] as const

export const VESSEL_CLASSES = ['Handysize', 'Supramax', 'Panamax', 'Capesize'] as const

export const COMMODITIES = ['Coal', 'Iron Ore', 'Grain', 'Fertilizer', 'Bauxite'] as const

export const CONTRACT_TYPES = ['Spot', 'Short-Term', 'Medium-Term', 'Long-Term'] as const

export const CONTRACT_DURATIONS = [
  'Spot Single Voyage',
  '3-Month Short-Term COA',
  '6-Month Medium-Term COA',
  '12-Month Long-Term Volume',
] as const
