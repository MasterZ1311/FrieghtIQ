'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { api } from '@/lib/api'
import {
  LayoutDashboard,
  CalendarCheck2,
  TrendingUp,
  Ship,
  Anchor,
  FileText,
  ShieldAlert,
  GitCompare,
  Calculator,
  Gauge,
  Bot,
} from 'lucide-react'

const navItems = [
  { href: '/', label: 'Executive Dashboard', icon: LayoutDashboard, badge: null },
  { href: '/copilot', label: 'AI Copilot Advisor', icon: Bot, badge: 'Agentic' },
  { href: '/regime', label: 'Market Regime', icon: Gauge, badge: 'HMM' },
  { href: '/workflow', label: 'End-to-End Decision', icon: CalendarCheck2, badge: 'Flow' },
  { href: '/forecast', label: 'Freight Forecast', icon: TrendingUp, badge: null },
  { href: '/vessels', label: 'Vessel Optimization', icon: Ship, badge: '4-Class' },
  { href: '/ports', label: 'Port Compatibility', icon: Anchor, badge: '7 Ports' },
  { href: '/contracts', label: 'Contract Simulator', icon: FileText, badge: null },
  { href: '/risk', label: 'Risk & Alerts', icon: ShieldAlert, badge: 'Live Feed' },
  { href: '/scenarios', label: 'Scenario Simulator', icon: GitCompare, badge: 'What-If' },
]



export default function Sidebar() {
  const pathname = usePathname()
  const [isLive, setIsLive] = useState(false)

  useEffect(() => {
    api.health().then((h) => setIsLive(h.isLive))
  }, [])

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-gray-950 border-r border-gray-800/80 flex flex-col z-30 select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-gray-800/80">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-700 flex items-center justify-center text-white font-black text-sm shadow-md shadow-blue-500/20">
            FQ
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <h1 className="text-white font-black text-base tracking-tight leading-none">FreightIQ</h1>
              <span className="px-1.5 py-0.2 bg-blue-500/20 text-blue-400 text-[10px] font-mono rounded">PRO</span>
            </div>
            <p className="text-gray-400 text-[11px] mt-0.5 font-medium">Chartering Command Center</p>
          </div>
        </div>

        {/* Backend Connection Indicator */}
        <div className="mt-3.5 px-2.5 py-1.5 rounded-lg border text-[11px] flex items-center justify-between transition-all bg-gray-900/90 border-gray-800">
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                isLive ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'
              }`}
            />
            <span className="text-gray-300 font-medium">
              {isLive ? 'API Engine Active' : 'Demo Benchmark'}
            </span>
          </div>
          <span className="text-[10px] text-gray-400 font-mono">v1.0</span>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1 scrollbar-thin scrollbar-thumb-gray-800">
        <p className="px-3 text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-2">
          Operations & Intelligence
        </p>

        <ul className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const active = pathname === item.href
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all group ${
                    active
                      ? 'bg-blue-600 text-white shadow-sm shadow-blue-600/30'
                      : 'text-gray-400 hover:text-white hover:bg-gray-900/80'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <Icon
                      size={16}
                      className={active ? 'text-white' : 'text-gray-500 group-hover:text-gray-300'}
                    />
                    <span className="truncate">{item.label}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                        active
                          ? 'bg-blue-700/80 text-blue-100'
                          : 'bg-gray-800 text-gray-400 group-hover:text-gray-300'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </Link>
              </li>
            )
          })}
        </ul>

        <div className="pt-4 mt-4 border-t border-gray-900">
          <p className="px-3 text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-2">
            Supplemental Tools
          </p>
          <Link
            href="/economics"
            className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
              pathname === '/economics'
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-900/80'
            }`}
          >
            <Calculator size={16} className="text-gray-500" />
            <span>Voyage Economics P&L</span>
          </Link>
        </div>
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-gray-800/80 bg-gray-950/60 text-[11px] text-gray-400">
        <div className="flex items-center justify-between text-gray-400 mb-1">
          <span>Target Ports</span>
          <span className="text-gray-300 font-medium">East Coast India</span>
        </div>
        <p className="text-[10px] leading-relaxed text-gray-400">
          Paradip · Vizag · Gangavaram · Gopalpur · Dhamra · Haldia
        </p>
      </div>
    </aside>
  )
}
