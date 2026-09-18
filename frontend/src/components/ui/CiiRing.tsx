'use client'

import React from 'react'

export interface CiiRingProps {
  grade: 'A' | 'B' | 'C' | 'D' | 'E'
  size?: number
  className?: string
}

const GRADE_CONFIG: Record<
  'A' | 'B' | 'C' | 'D' | 'E',
  { color: string; pct: number; label: string; glow: string }
> = {
  A: { color: '#22c55e', pct: 1.0, label: 'Superior', glow: 'rgba(34, 197, 94, 0.35)' },
  B: { color: '#86efac', pct: 0.8, label: 'High Efficiency', glow: 'rgba(134, 239, 172, 0.3)' },
  C: { color: '#eab308', pct: 0.6, label: 'Moderate', glow: 'rgba(234, 179, 8, 0.3)' },
  D: { color: '#f97316', pct: 0.4, label: 'Sub-Standard', glow: 'rgba(249, 115, 22, 0.3)' },
  E: { color: '#ef4444', pct: 0.2, label: 'Critical Tier', glow: 'rgba(239, 68, 68, 0.35)' },
}

export function CiiRing({ grade, size = 96, className = '' }: CiiRingProps) {
  const config = GRADE_CONFIG[grade] || GRADE_CONFIG['C']
  const radius = 38
  const strokeWidth = 8
  const circumference = 2 * Math.PI * radius // ≈ 238.76
  const strokeDashoffset = circumference * (1 - config.pct)

  return (
    <div className={`relative inline-flex flex-col items-center justify-center ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        className="transform -rotate-90 transition-all duration-700"
      >
        {/* Background track circle */}
        <circle
          cx="50"
          cy="50"
          r={radius}
          stroke="#1f2937"
          strokeWidth={strokeWidth}
          fill="none"
        />
        {/* Animated Progress Arc */}
        <circle
          cx="50"
          cy="50"
          r={radius}
          stroke={config.color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          fill="none"
          style={{
            transition: 'stroke-dashoffset 1s ease-out, stroke 0.5s ease',
            filter: `drop-shadow(0 0 6px ${config.glow})`,
          }}
        />
      </svg>
      {/* Centered Grade Label */}
      <div className="absolute inset-0 flex flex-col items-center justify-center select-none pointer-events-none">
        <span
          className="text-2xl font-black tracking-tight"
          style={{ color: config.color }}
        >
          {grade}
        </span>
        <span className="text-[9px] uppercase font-bold text-gray-400 tracking-wider -mt-0.5">
          CII
        </span>
      </div>
    </div>
  )
}

export default CiiRing
