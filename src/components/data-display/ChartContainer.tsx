"use client";

import React, { useState } from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";
import { DEMO_FREIGHT_RATES, DEMO_ALTERNATIVE_ROUTES } from "@/data/demo/freightRates";
import { DataStatusBadge } from "@/components/badges/DataStatusBadge";
import { ConfidenceBadge, SourceBadge } from "@/components/badges/ConfidenceBadge";
import { Info, Layers } from "lucide-react";

export const ChartContainer: React.FC = () => {
  const [showEnvelopes, setShowEnvelopes] = useState(true);
  const [selectedRoute, setSelectedRoute] = useState(DEMO_FREIGHT_RATES.route);

  // Prepare chart dataset
  const chartData = DEMO_FREIGHT_RATES.history.map((pt) => ({
    date: pt.date,
    historical: pt.historical ?? null,
    forecast: pt.forecast ?? null,
    p10: pt.p10 ?? null,
    p90: pt.p90 ?? null,
    // Band width for confidence area
    confidenceRange: pt.p10 && pt.p90 ? [pt.p10, pt.p90] : null,
  }));

  return (
    <div className="rounded-xl border border-border bg-surface p-5 sm:p-6">
      {/* Header & Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-border-subtle">
        <div>
          <div className="flex items-center gap-2.5 flex-wrap">
            <h3 className="text-base sm:text-lg font-bold text-slate-100 tracking-tight">
              Freight Market Overview & Forecast Envelope
            </h3>
            <DataStatusBadge status="DEMO DATA" size="xs" />
            <ConfidenceBadge level={DEMO_FREIGHT_RATES.confidence} />
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Simulated Capesize / Panamax spot & forward rates to East Coast India (USD / MT)
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <button
            onClick={() => setShowEnvelopes(!showEnvelopes)}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              showEnvelopes
                ? "bg-blue-950/70 border-blue-600 text-blue-300"
                : "bg-surface-elevated border-border text-slate-400 hover:text-slate-200"
            }`}
          >
            <Layers className="h-3.5 w-3.5" />
            <span>{showEnvelopes ? "Hide P10/P90 Band" : "Show P10/P90 Band"}</span>
          </button>

          <select
            value={selectedRoute}
            onChange={(e) => setSelectedRoute(e.target.value)}
            className="bg-surface-elevated border border-border text-xs text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-blue-500"
          >
            <option value={DEMO_FREIGHT_RATES.route}>
              {DEMO_FREIGHT_RATES.route} (Primary)
            </option>
            {DEMO_ALTERNATIVE_ROUTES.map((r) => (
              <option key={r.id} value={r.name}>
                {r.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Synthetic Data Disclaimer Banner */}
      <div className="my-3.5 flex items-center justify-between gap-3 px-3 py-2 rounded-lg bg-blue-950/40 border border-blue-900/50 text-[11px] text-blue-200">
        <div className="flex items-center gap-2">
          <Info className="h-4 w-4 text-blue-400 shrink-0" />
          <span>
            <strong>Data Honesty Notice:</strong> Values shown are synthetic benchmarks for Phase 01 architecture testing. Actual model integration (TFT & HMM) will connect in Phase 02.
          </span>
        </div>
        <SourceBadge source={DEMO_FREIGHT_RATES.source} className="hidden sm:inline-flex" />
      </div>

      {/* Chart Canvas */}
      <div className="h-72 sm:h-80 w-full mt-4">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={chartData}
            margin={{ top: 10, right: 20, left: -10, bottom: 0 }}
          >
            <defs>
              <linearGradient id="confidenceArea" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#818cf8" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#818cf8" stopOpacity={0.02} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" opacity={0.5} />
            
            <XAxis
              dataKey="date"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: "#1e3a5f" }}
            />
            
            <YAxis
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: "#1e3a5f" }}
              domain={[10, 18]}
              tickFormatter={(v) => `$${v}`}
            />

            <Tooltip
              content={({ active, payload, label }) => {
                if (!active || !payload || !payload.length) return null;
                return (
                  <div className="rounded-lg border border-border bg-slate-950/95 p-3 shadow-xl backdrop-blur-md text-xs font-mono">
                    <p className="font-bold text-slate-200 mb-1.5">{label}</p>
                    {payload.map((entry, idx) => (
                      <div key={idx} className="flex items-center justify-between gap-4 py-0.5">
                        <span style={{ color: entry.color }} className="text-[11px] capitalize">
                          {entry.name}:
                        </span>
                        <span className="font-bold text-slate-100">
                          ${Number(entry.value).toFixed(2)}/MT
                        </span>
                      </div>
                    ))}
                    <div className="mt-2 pt-1.5 border-t border-slate-800 text-[10px] text-sky-300">
                      Phase 01 Synthetic Point
                    </div>
                  </div>
                );
              }}
            />

            <Legend
              wrapperStyle={{ paddingTop: "12px", fontSize: "11px" }}
              formatter={(value) => <span className="text-slate-300 capitalize">{value}</span>}
            />

            {/* P10 - P90 Upper Confidence Area */}
            {showEnvelopes && (
              <Area
                name="P90 Pessimistic (Upper)"
                type="monotone"
                dataKey="p90"
                stroke="#a78bfa"
                strokeDasharray="4 4"
                fill="url(#confidenceArea)"
                fillOpacity={0.15}
              />
            )}

            {/* Historical Observation Line */}
            <Line
              name="Historical Spot ($/MT)"
              type="monotone"
              dataKey="historical"
              stroke="#38bdf8"
              strokeWidth={2.5}
              dot={{ r: 3, fill: "#38bdf8" }}
              activeDot={{ r: 5 }}
            />

            {/* Projected Median Forecast Line (P50) */}
            <Line
              name="Forecast P50 Projection"
              type="monotone"
              dataKey="forecast"
              stroke="#60a5fa"
              strokeWidth={2.5}
              strokeDasharray="5 5"
              dot={{ r: 4, fill: "#60a5fa" }}
            />

            {/* P10 Lower Bound */}
            {showEnvelopes && (
              <Line
                name="P10 Optimistic (Lower)"
                type="monotone"
                dataKey="p10"
                stroke="#34d399"
                strokeWidth={1.5}
                strokeDasharray="3 3"
                dot={false}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Footer provenance details */}
      <div className="mt-4 pt-3 border-t border-border-subtle flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400">
        <div>
          <span>Route: </span>
          <span className="text-slate-300 font-medium">{selectedRoute}</span>
          <span className="mx-2">•</span>
          <span>Last Updated: {DEMO_FREIGHT_RATES.lastUpdated.split("T")[0]}</span>
        </div>
        <div className="font-mono text-[10px] text-slate-400">
          Envelopes: P10 (Optimistic) | P50 (Expected) | P90 (Pessimistic)
        </div>
      </div>
    </div>
  );
};
