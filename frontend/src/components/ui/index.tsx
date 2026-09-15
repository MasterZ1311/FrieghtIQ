'use client'
import { type ReactNode } from 'react'
import { marketActionConfig, formatUSD, formatPercent } from '@/lib/utils'
import type { MarketEntryAction, RiskLevel } from '@/types'
import { TrendingUp, TrendingDown, Minus, Info, AlertTriangle, Database, Zap } from 'lucide-react'

interface CardProps {
  title?: string
  subtitle?: string
  badge?: ReactNode
  action?: ReactNode
  children: ReactNode
  className?: string
  accent?: boolean
}

export function Card({ title, subtitle, badge, action, children, className = '', accent = false }: CardProps) {
  return (
    <div
      className={`bg-gray-900 border border-gray-800 rounded-xl p-5 transition-all shadow-sm ${
        accent ? 'border-blue-700/50 bg-blue-950/20' : ''
      } ${className}`}
    >
      {(title || subtitle || badge || action) && (
        <div className="flex items-start justify-between gap-3 mb-4">
          <div>
            {title && <h3 className="text-xs font-bold text-gray-300 uppercase tracking-wider">{title}</h3>}
            {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
          </div>
          <div className="flex items-center gap-2">
            {badge}
            {action}
          </div>
        </div>
      )}
      {children}
    </div>
  )
}

interface StatCardProps {
  label: string
  value: string | number
  subValue?: string
  badge?: { text: string; color: string }
  icon?: ReactNode
  trend?: 'rising' | 'falling' | 'stable'
  highlight?: boolean
}

export function StatCard({ label, value, subValue, badge, icon, highlight = false }: StatCardProps) {
  return (
    <div
      className={`bg-gray-900 border rounded-xl p-4 flex flex-col justify-between transition-all ${
        highlight ? 'border-blue-600/60 bg-blue-950/25' : 'border-gray-800 hover:border-gray-700'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">{label}</p>
        {icon && <span className="text-gray-400 p-1 bg-gray-800/80 rounded-md">{icon}</span>}
      </div>
      <div className="my-1.5">
        <p className="text-2xl font-black text-white tracking-tight">{value}</p>
        {subValue && <p className="text-xs text-gray-400 mt-0.5">{subValue}</p>}
      </div>
      {badge && (
        <span className={`inline-block px-2 py-0.5 text-[11px] rounded-md font-semibold w-fit ${badge.color}`}>
          {badge.text}
        </span>
      )}
    </div>
  )
}

// ─── HIGH VISUAL MARKET ENTRY CARD ───────────────────────────────────────────

export interface MarketEntryCardProps {
  action: MarketEntryAction
  currentRate: number
  predictedRate: number
  expectedMovement: number
  confidencePct: number
  potentialSavings: number
  origin?: string
  destination?: string
  vesselClass?: string
  horizonDays?: number
  recommendationText?: string
  onActionClick?: () => void
  actionLabel?: string
  isDemoData?: boolean
}

export function MarketEntryCard({
  action,
  currentRate,
  predictedRate,
  expectedMovement,
  confidencePct,
  potentialSavings,
  origin = 'Australia',
  destination = 'Paradip',
  vesselClass = 'Panamax',
  horizonDays = 30,
  recommendationText,
  onActionClick,
  actionLabel,
  isDemoData = true,
}: MarketEntryCardProps) {
  const cfg = marketActionConfig(action)
  const movementPct = currentRate > 0 ? ((predictedRate - currentRate) / currentRate) * 100 : 0
  const isDrop = expectedMovement < 0

  return (
    <div
      className={`relative overflow-hidden rounded-2xl border ${cfg.border} ${cfg.bg} p-6 transition-all shadow-lg ${cfg.glow}`}
    >
      {/* Top Banner & Status */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-800/80 pb-4 mb-5">
        <div className="flex items-center gap-3">
          <div className={`px-3.5 py-1.5 rounded-lg text-sm tracking-wide ${cfg.badgeBg} flex items-center gap-2 shadow`}>
            <span>{cfg.icon}</span>
            <span>{cfg.label}</span>
          </div>
          <div>
            <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Market Entry Recommendation
            </h4>
            <p className="text-xs text-gray-400">
              {origin} → {destination} · <span className="text-gray-300 font-medium">{vesselClass}</span> · {horizonDays}-Day Horizon
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isDemoData && (
            <span className="px-2 py-0.5 text-[10px] font-mono bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded">
              DEMO BENCHMARK
            </span>
          )}
          <span className="px-2.5 py-1 text-xs bg-gray-800/90 border border-gray-700 rounded-md text-gray-300 font-medium">
            Confidence: <strong className="text-white">{confidencePct}%</strong>
          </span>
        </div>
      </div>

      {/* Grid of Key Numerical Indicators */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-5">
        {/* 1. Current Rate */}
        <div className="bg-gray-900/80 border border-gray-800 p-3.5 rounded-xl">
          <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Current Rate</span>
          <p className="text-xl font-black text-white mt-1">
            {formatUSD(currentRate, 2)}
            <span className="text-xs font-normal text-gray-400 ml-0.5">/MT</span>
          </p>
          <span className="text-[11px] text-gray-500">Prompt spot index</span>
        </div>

        {/* 2. Predicted Rate */}
        <div className="bg-gray-900/80 border border-gray-800 p-3.5 rounded-xl">
          <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Predicted Rate</span>
          <p className="text-xl font-black text-white mt-1">
            {formatUSD(predictedRate, 2)}
            <span className="text-xs font-normal text-gray-400 ml-0.5">/MT</span>
          </p>
          <span className="text-[11px] text-gray-500">Horizon: {horizonDays} days</span>
        </div>

        {/* 3. Expected Movement */}
        <div className="bg-gray-900/80 border border-gray-800 p-3.5 rounded-xl">
          <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Expected Shift</span>
          <div className="flex items-center gap-1 mt-1">
            {isDrop ? (
              <TrendingDown size={18} className="text-emerald-400" />
            ) : expectedMovement > 0 ? (
              <TrendingUp size={18} className="text-red-400" />
            ) : (
              <Minus size={18} className="text-blue-400" />
            )}
            <p className={`text-xl font-black ${isDrop ? 'text-emerald-400' : expectedMovement > 0 ? 'text-red-400' : 'text-blue-400'}`}>
              {expectedMovement > 0 ? `+${expectedMovement.toFixed(2)}` : expectedMovement.toFixed(2)}
            </p>
          </div>
          <span className={`text-[11px] font-semibold ${isDrop ? 'text-emerald-400' : expectedMovement > 0 ? 'text-red-400' : 'text-blue-400'}`}>
            {formatPercent(movementPct)} shift
          </span>
        </div>

        {/* 4. Confidence */}
        <div className="bg-gray-900/80 border border-gray-800 p-3.5 rounded-xl">
          <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Model Confidence</span>
          <p className="text-xl font-black text-white mt-1">{confidencePct}%</p>
          <div className="w-full bg-gray-800 h-1.5 rounded-full mt-2">
            <div
              className={`h-1.5 rounded-full ${confidencePct >= 80 ? 'bg-emerald-500' : 'bg-amber-500'}`}
              style={{ width: `${confidencePct}%` }}
            />
          </div>
        </div>

        {/* 5. Potential Savings */}
        <div className="bg-emerald-950/30 border border-emerald-800/50 p-3.5 rounded-xl">
          <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">Potential Savings</span>
          <p className="text-xl font-black text-emerald-300 mt-1">{formatUSD(potentialSavings, 0)}</p>
          <span className="text-[11px] text-emerald-400/80">vs. baseline spot fixture</span>
        </div>
      </div>

      {/* Decision Rationale & Immediate Action */}
      {recommendationText && (
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-3.5 bg-gray-950/70 border border-gray-800/80 rounded-xl">
          <div className="flex items-start gap-2.5">
            <Info size={16} className="text-blue-400 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-gray-300 leading-relaxed max-w-3xl">
              <strong className="text-white font-semibold">Strategic Directive: </strong>
              {recommendationText}
            </p>
          </div>
          {onActionClick && (
            <button
              onClick={onActionClick}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold whitespace-nowrap transition shadow flex items-center gap-1.5 self-end md:self-auto"
            >
              <Zap size={14} />
              {actionLabel || 'Execute Strategy'}
            </button>
          )}
        </div>
      )}
    </div>
  )
}

// ─── DATA MODE & STATUS INDICATORS ───────────────────────────────────────────

export function DataModeBadge({ isLive = false }: { isLive?: boolean }) {
  return (
    <div
      className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border ${
        isLive
          ? 'bg-emerald-950/40 border-emerald-800/60 text-emerald-400'
          : 'bg-amber-950/40 border-amber-800/60 text-amber-300'
      }`}
    >
      <span
        className={`w-2 h-2 rounded-full ${
          isLive ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'
        }`}
      />
      <span>{isLive ? 'Live Backend Connected' : 'DEMO MODE · Synthetic Data (SIH 2025)'}</span>
    </div>
  )
}

export function DemoBadge({ isLive = false }: { isLive?: boolean }) {
  return <DataModeBadge isLive={isLive} />
}

export function LiveTelemetryPill({ label = 'Decision Engine Ready' }: { label?: string }) {
  return (
    <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-950/40 border border-emerald-800/50 rounded-lg text-xs font-medium text-emerald-300">
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
        <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
      </span>
      {label}
    </div>
  )
}

interface BadgeProps {
  children: ReactNode
  color?: string
}

export function Badge({ children, color = 'bg-gray-800 text-gray-300 border border-gray-700' }: BadgeProps) {
  return (
    <span className={`px-2.5 py-0.5 text-xs rounded-md font-medium inline-flex items-center gap-1 ${color}`}>
      {children}
    </span>
  )
}

export function Disclaimer({ text }: { text: string }) {
  return (
    <div className="mt-6 px-4 py-2.5 bg-amber-500/5 border border-amber-500/20 rounded-lg text-amber-400/80 text-xs flex items-center gap-2">
      <AlertTriangle size={14} className="flex-shrink-0 text-amber-400" />
      <span>{text}</span>
    </div>
  )
}

export function Loading({ message = 'Computing maritime analytics…' }: { message?: string }) {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="flex flex-col items-center gap-3 text-gray-400">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-xs font-medium uppercase tracking-wider">{message}</span>
      </div>
    </div>
  )
}

export function ErrorBox({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="px-4 py-3 bg-red-950/30 border border-red-500/40 rounded-xl text-red-300 text-xs flex items-center justify-between gap-2.5 my-3">
      <div className="flex items-center gap-2.5">
        <AlertTriangle size={16} className="text-red-400 flex-shrink-0" />
        <div>
          <strong className="font-semibold text-red-200">Execution Error:</strong> {message}
        </div>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-2.5 py-1 bg-red-900/50 hover:bg-red-800/60 text-red-200 border border-red-700/50 rounded-lg text-[11px] font-semibold transition"
        >
          Retry
        </button>
      )}
    </div>
  )
}

export function EmptyState({
  title = 'No Data Available',
  description = 'Adjust input parameters and run analysis to populate metrics.',
  action,
  actionLabel,
  onAction,
}: {
  title?: string
  description?: string
  action?: ReactNode
  actionLabel?: string
  onAction?: () => void
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 border border-dashed border-gray-800 rounded-2xl text-center bg-gray-950/40">
      <Database size={32} className="text-gray-600 mb-3" />
      <h4 className="text-sm font-semibold text-gray-300">{title}</h4>
      <p className="text-xs text-gray-500 max-w-sm mt-1 mb-4">{description}</p>
      {action ||
        (actionLabel && onAction && (
          <button
            onClick={onAction}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition"
          >
            {actionLabel}
          </button>
        ))}
    </div>
  )
}

interface SelectProps {
  label: string
  value: string
  onChange: (v: string) => void
  options: readonly string[] | string[]
  className?: string
  disabled?: boolean
}

export function Select({ label, value, onChange, options, className = '', disabled = false }: SelectProps) {
  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      <label className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500 transition disabled:opacity-50"
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </div>
  )
}

interface InputProps {
  label: string
  value: string | number
  onChange: (v: string) => void
  type?: string
  placeholder?: string
  className?: string
  min?: number
  max?: number
  step?: number
  disabled?: boolean
}

export function Input({
  label,
  value,
  onChange,
  type = 'text',
  placeholder,
  className = '',
  min,
  max,
  step,
  disabled = false,
}: InputProps) {
  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      <label className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        min={min}
        max={max}
        step={step}
        disabled={disabled}
        className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500 transition placeholder:text-gray-600 disabled:opacity-50"
      />
    </div>
  )
}

export function PageHeader({
  title,
  subtitle,
  actions,
  children,
}: {
  title: string
  subtitle?: string
  actions?: ReactNode
  children?: ReactNode
}) {
  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
      <div>
        <h1 className="text-2xl font-black text-white tracking-tight">{title}</h1>
        {subtitle && <p className="text-gray-400 mt-1 text-xs leading-relaxed max-w-2xl">{subtitle}</p>}
      </div>
      {(actions || children) && (
        <div className="flex items-center gap-3">
          {actions}
          {children}
        </div>
      )}
    </div>
  )
}

export function SectionHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-3">
      <h2 className="text-xs font-bold text-gray-300 uppercase tracking-wider">{title}</h2>
      {subtitle && <p className="text-[11px] text-gray-500 mt-0.5">{subtitle}</p>}
    </div>
  )
}

export function RiskBadge({ level }: { level: RiskLevel | string }) {
  const colors: Record<string, string> = {
    Low: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30',
    Medium: 'bg-amber-500/15 text-amber-400 border border-amber-500/30',
    High: 'bg-orange-500/15 text-orange-400 border border-orange-500/30',
    Critical: 'bg-red-500/15 text-red-400 border border-red-500/30',
  }
  return (
    <span className={`px-2.5 py-0.5 text-xs rounded-full font-semibold ${colors[level] || 'bg-gray-800 text-gray-400'}`}>
      {level}
    </span>
  )
}

export function ProgressBar({ value, max = 100, color = 'bg-blue-500' }: { value: number; max?: number; color?: string }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100))
  return (
    <div className="w-full bg-gray-800 rounded-full h-1.5 overflow-hidden">
      <div className={`h-1.5 rounded-full ${color} transition-all duration-300`} style={{ width: `${pct}%` }} />
    </div>
  )
}
