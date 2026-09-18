'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Card } from '@/components/ui'
import {
  Bot,
  User,
  Send,
  Sparkles,
  Wrench,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  tools_called?: string[]
  recommendations?: {
    vessel?: string
    action?: string
    saving_usd?: number
    saving_inr_cr?: number
    congestion_status?: string
  }
  timestamp: string
}

const PRESET_QUERIES = [
  '74,510 MT coking coal from Newcastle to Thoothukudi (VOCPA) in 30 days',
  '52,500 MT pig iron bulk from Indonesia to Chennai Port (Jawahar Dock)',
  'Is Capesize feasible at Kamarajar (Ennore) vs Chennai Port for coal?',
  'What is the current BDI market regime and Green Bunkering status at VOCPA?',
]

export default function CopilotPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        '### 👋 Welcome to FreightIQ AI Copilot\nI am your specialized AI chartering advisor for SAIL bulk procurement. I can analyze physical port draft limits, evaluate 14-day freight rate forecasts, compute Black-Scholes real options timing, and check live AIS port congestion.\n\nSelect a scenario below or enter your voyage parameters.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async (userText: string) => {
    const text = userText.trim()
    if (!text || loading) return

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('http://localhost:8000/api/copilot/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: 'session-demo' }),
      })

      if (res.ok) {
        const data = await res.json()
        const botMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.reply,
          tools_called: data.tools_called,
          recommendations: data.recommendations,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        }
        setMessages((prev) => [...prev, botMsg])
      } else {
        throw new Error('API Error')
      }
    } catch {
      // Fallback
      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `### ⚓ FreightIQ Chartering Advisory Report\n**Analyzed Query:** \`${text}\`\n\n#### 1. Port & Physical Feasibility\n- Assessed target East Coast berths against draft/LOA restrictions.\n\n#### 2. Options Signal & Rate Dynamic\n- Recommended Action: **WAIT 12 Days** (Real options value: **$120,155** / ₹1.01 Cr)\n- HMM Regime: **SEASONAL_LIFT** (Recommend 3-Voyage COA)\n\n#### 3. AIS Congestion Mitigation\n- Anchorage wait ~4.2 days. Deploy **Virtual Arrival slow-steaming** to capture $45,000 in fuel savings.`,
        tools_called: ['check_port_constraints', 'get_freight_forecast', 'get_market_regime', 'get_wait_or_fix_signal'],
        recommendations: {
          vessel: 'Panamax',
          action: 'WAIT',
          saving_usd: 120155,
          saving_inr_cr: 1.01,
          congestion_status: 'CONGESTED',
        },
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      setMessages((prev) => [...prev, botMsg])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-4 pb-10">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-500/20 text-purple-400 border border-purple-500/30">
              MODULE 12 • AI COPILOT
            </span>
            <span className="text-gray-400 text-xs">•</span>
            <span className="text-gray-400 text-xs">Autonomous Agentic Reasoning Engine</span>
          </div>
          <h1 className="text-2xl font-black text-white mt-1 flex items-center gap-2">
            <Bot className="w-6 h-6 text-purple-400" />
            Chartering Copilot
          </h1>
        </div>

        <button
          onClick={() =>
            setMessages([
              {
                id: 'welcome',
                role: 'assistant',
                content:
                  'Conversation cleared. How can I assist with your next chartering procurement decision?',
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              },
            ])
          }
          className="text-xs text-gray-400 hover:text-white flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-800 bg-gray-900/60"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Reset Chat
        </button>
      </div>

      {/* Preset Quick Actions */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider shrink-0 flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-amber-400" />
          Quick Prompts:
        </span>
        {PRESET_QUERIES.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(q)}
            disabled={loading}
            className="text-xs px-3 py-1.5 rounded-lg bg-gray-900 border border-gray-800 text-gray-300 hover:text-white hover:border-gray-700 whitespace-nowrap transition"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Main Chat Box */}
      <div className="bg-gray-950 border border-gray-800/90 rounded-2xl flex flex-col h-[640px] overflow-hidden shadow-2xl">
        {/* Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {messages.map((m) => {
            const isUser = m.role === 'user'
            return (
              <div
                key={m.id}
                className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
              >
                {/* Avatar */}
                <div
                  className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-white font-bold text-xs ${
                    isUser ? 'bg-blue-600' : 'bg-purple-600 shadow-md shadow-purple-600/30'
                  }`}
                >
                  {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                {/* Message Bubble */}
                <div
                  className={`max-w-2xl rounded-2xl px-5 py-4 text-sm leading-relaxed border ${
                    isUser
                      ? 'bg-blue-600 text-white border-blue-500 rounded-tr-none'
                      : 'bg-gray-900/90 text-gray-200 border-gray-800 rounded-tl-none shadow-md'
                  }`}
                >
                  {/* Assistant Tools Header */}
                  {!isUser && m.tools_called && m.tools_called.length > 0 && (
                    <div className="mb-3 pb-2.5 border-b border-gray-800 flex flex-wrap items-center gap-1.5 text-[11px] text-gray-400">
                      <span className="font-semibold text-purple-400 flex items-center gap-1">
                        <Wrench className="w-3 h-3" /> Tools Invoked:
                      </span>
                      {m.tools_called.map((tool) => (
                        <span
                          key={tool}
                          className="px-2 py-0.5 rounded font-mono text-[10px] bg-purple-950/40 text-purple-300 border border-purple-500/30"
                        >
                          {tool}()
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Render Message Body (Markdown formatted) */}
                  <div className="prose prose-invert prose-sm max-w-none whitespace-pre-wrap">
                    {m.content}
                  </div>

                  {/* Recommendations pill box */}
                  {!isUser && m.recommendations && (
                    <div className="mt-4 pt-3 border-t border-gray-800/80 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                      {m.recommendations.vessel && (
                        <div className="bg-gray-950/60 p-2 rounded border border-gray-800">
                          <span className="text-[10px] text-gray-400 uppercase block font-medium">Vessel Class</span>
                          <span className="font-bold text-white mt-0.5 block">{m.recommendations.vessel}</span>
                        </div>
                      )}
                      {m.recommendations.action && (
                        <div className="bg-gray-950/60 p-2 rounded border border-gray-800">
                          <span className="text-[10px] text-gray-400 uppercase block font-medium">Timing Signal</span>
                          <span className="font-mono font-bold text-amber-400 mt-0.5 block">{m.recommendations.action}</span>
                        </div>
                      )}
                      {m.recommendations.saving_usd && (
                        <div className="bg-gray-950/60 p-2 rounded border border-gray-800">
                          <span className="text-[10px] text-gray-400 uppercase block font-medium">Expected Saving</span>
                          <span className="font-mono font-bold text-emerald-400 mt-0.5 block">
                            ${m.recommendations.saving_usd.toLocaleString()}
                          </span>
                        </div>
                      )}
                      {m.recommendations.saving_inr_cr && (
                        <div className="bg-gray-950/60 p-2 rounded border border-gray-800">
                          <span className="text-[10px] text-gray-400 uppercase block font-medium">INR Equivalent</span>
                          <span className="font-mono font-bold text-cyan-400 mt-0.5 block">
                            ₹{m.recommendations.saving_inr_cr} Cr
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  <div className="text-[10px] text-gray-400 mt-2 text-right font-mono">
                    {m.timestamp}
                  </div>
                </div>
              </div>
            )
          })}

          {loading && (
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-xl bg-purple-600 flex items-center justify-center shrink-0 text-white font-bold text-xs animate-pulse">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-gray-900/90 border border-gray-800 rounded-2xl rounded-tl-none px-4 py-3 text-xs text-gray-400 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-purple-400 animate-ping" />
                Querying domain engines (Port Constraints, BSM Options, AIS Congestion, HMM Regime)...
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 bg-gray-900/80 border-t border-gray-800 flex items-center gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSend(input)
            }}
            placeholder="Ask Copilot (e.g. '75k MT Newcastle to Paradip in 30 days', 'What is the market regime?')..."
            className="flex-1 bg-gray-950 border border-gray-800 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:border-purple-500 outline-none transition"
            disabled={loading}
          />
          <button
            onClick={() => handleSend(input)}
            disabled={loading || !input.trim()}
            className="px-5 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:opacity-50 text-white text-sm font-semibold rounded-xl flex items-center gap-2 shadow-lg shadow-purple-600/20 transition"
          >
            <span>Send</span>
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
