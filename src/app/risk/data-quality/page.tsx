import React from "react";
import { CheckCircle2, ShieldCheck, Database, Info } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { DataStatusBadge } from "@/components/badges/DataStatusBadge";
import { ConfidenceBadge } from "@/components/badges/ConfidenceBadge";

interface TelemetryStream {
  name: string;
  source: string;
  status: "DEMO" | "LIVE" | "UNAVAILABLE" | "STALE";
  confidence: "HIGH" | "MEDIUM" | "LOW";
  lastSync: string;
  freshnessHz: string;
  integrityScore: string;
}

const TELEMETRY_STREAMS: TelemetryStream[] = [
  {
    name: "Baltic Freight Indices (C5/C3)",
    source: "Synthetic Baltic Exchange Proxy",
    status: "DEMO",
    confidence: "MEDIUM",
    lastSync: "2026-09-18 12:00 UTC",
    freshnessHz: "Daily Fix",
    integrityScore: "94.2%",
  },
  {
    name: "Vessel AIS Tracking Feed",
    source: "Mock Terrestrial + Satellite AIS",
    status: "DEMO",
    confidence: "MEDIUM",
    lastSync: "2026-09-18 11:30 UTC",
    freshnessHz: "15 min interval",
    integrityScore: "88.0%",
  },
  {
    name: "East Coast India Port Telemetry",
    source: "Static Port Authority Archetypes",
    status: "DEMO",
    confidence: "LOW",
    lastSync: "2026-09-18 00:00 UTC",
    freshnessHz: "Static baseline",
    integrityScore: "76.5%",
  },
  {
    name: "Marine Weather & Wave Height",
    source: "Simulated ECMWF / IMD Feed",
    status: "DEMO",
    confidence: "MEDIUM",
    lastSync: "2026-09-18 06:00 UTC",
    freshnessHz: "6-hour forecast",
    integrityScore: "91.0%",
  },
  {
    name: "Tidal Height Constituent Tables",
    source: "Hydrographic Office Baseline",
    status: "DEMO",
    confidence: "LOW",
    lastSync: "Pending Verification",
    freshnessHz: "Static calendar",
    integrityScore: "68.0%",
  },
];

export default function DataQualityPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="DATA QUALITY & PROVENANCE AUDIT"
        description="Comprehensive telemetry integrity verification, API freshness tracking, and data honesty validation across all freight intelligence pipelines."
        status="DEMO ENVIRONMENT"
      />

      <div className="p-3.5 rounded-xl bg-blue-950/40 border border-blue-900/50 text-xs text-blue-200 flex items-center gap-2.5">
        <Info className="h-4 w-4 text-blue-400 shrink-0" />
        <span>
          <strong>Data Honesty Standard:</strong> FREIGHT IQ maintains full provenance transparency. No synthetic dataset is ever disguised as live streaming telemetry.
        </span>
      </div>

      {/* Telemetry Streams Table */}
      <div className="rounded-xl border border-border bg-surface overflow-hidden">
        <div className="p-4 border-b border-border-subtle bg-surface-elevated/40">
          <h3 className="font-bold text-sm text-slate-100 flex items-center gap-2">
            <Database className="h-4 w-4 text-blue-400" />
            <span>Active Intelligence Ingestion Streams</span>
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-surface-elevated/60 text-[11px] uppercase tracking-wider text-slate-400 border-b border-border-subtle font-mono">
              <tr>
                <th className="py-3 px-4">Telemetry Pipeline</th>
                <th className="py-3 px-4">Source Provenance</th>
                <th className="py-3 px-4">Stream Status</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4">Cadence</th>
                <th className="py-3 px-4">Last Sync</th>
                <th className="py-3 px-4 text-right">Integrity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle/50 font-sans">
              {TELEMETRY_STREAMS.map((s, idx) => (
                <tr key={idx} className="hover:bg-surface-elevated/50 transition-colors">
                  <td className="py-3 px-4 font-bold text-slate-100">{s.name}</td>
                  <td className="py-3 px-4 font-mono text-xs text-slate-400">{s.source}</td>
                  <td className="py-3 px-4">
                    <DataStatusBadge status={s.status} size="xs" />
                  </td>
                  <td className="py-3 px-4">
                    <ConfidenceBadge level={s.confidence} />
                  </td>
                  <td className="py-3 px-4 font-mono text-xs text-slate-400">{s.freshnessHz}</td>
                  <td className="py-3 px-4 font-mono text-xs text-slate-400">{s.lastSync}</td>
                  <td className="py-3 px-4 font-mono font-bold text-emerald-400 text-right">
                    {s.integrityScore}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
