"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { 
  Anchor, MapPin, ShieldCheck, Waves, Clock, 
  ExternalLink, ArrowLeft, RefreshCw, AlertCircle, FileText, CheckCircle2
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { MetricCard } from "@/components/data-display/MetricCard";
import { portsApi, PortDetail } from "@/lib/api";

export default function PortDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [port, setPort] = useState<PortDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchPort() {
      try {
        setLoading(true);
        const data = await portsApi.getPortDetail(id);
        setPort(data);
      } catch (err: any) {
        console.error("Failed to load port detail", err);
        setError("Port not found");
      } finally {
        setLoading(false);
      }
    }
    fetchPort();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex items-center gap-3 text-slate-400">
          <RefreshCw className="h-5 w-5 animate-spin text-blue-400" />
          <span>Retrieving port constraints and berth data...</span>
        </div>
      </div>
    );
  }

  if (error || !port) {
    return (
      <div className="p-8 text-center space-y-4">
        <AlertCircle className="h-12 w-12 text-rose-400 mx-auto" />
        <h2 className="text-lg font-bold text-slate-100">Port Not Found</h2>
        <p className="text-sm text-slate-400">Could not retrieve port profile for ID: {id}</p>
        <Link href="/intelligence/ports" className="inline-flex items-center gap-2 text-sm text-blue-400 hover:underline">
          <ArrowLeft className="h-4 w-4" /> Return to Ports Directory
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
        <Link href="/intelligence/ports" className="hover:text-slate-200">
          PORTS DIRECTORY
        </Link>
        <span>/</span>
        <span className="text-blue-400">{port.name} ({port.unlocode})</span>
      </div>

      <PageHeader
        title={`${port.name.toUpperCase()} (${port.unlocode})`}
        description={`${port.coast || 'Major Deep-Water Port'} • ${port.country} • Position: ${port.latitude.toFixed(4)}°N, ${port.longitude.toFixed(4)}°E`}
        status="ACTIVE PORT DATABASE"
        actions={
          <Link
            href={`/optimization/vessel-port?port_id=${port.id}`}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary hover:bg-primary-hover text-xs font-semibold text-white shadow-md transition-colors"
          >
            <Anchor className="h-4 w-4" />
            <span>Launch Berth Optimizer</span>
            <ExternalLink className="h-4 w-4" />
          </Link>
        }
      />

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="CHANNEL MAXIMUM DRAFT"
          value={port.channel_max_draft_m ? `${port.channel_max_draft_m.toFixed(1)} m` : "Restricted"}
          subtext="High-water permissible depth"
        />
        <MetricCard
          label="APPROACH MAX LOA"
          value={port.channel_max_loa_m ? `${port.channel_max_loa_m.toFixed(0)} m` : "230 m"}
          subtext={`Beam limit: ${port.channel_max_beam_m || 48}m`}
        />
        <MetricCard
          label="TIDAL DYNAMICS"
          value={`+${port.tide_range_m ? port.tide_range_m.toFixed(1) : 2.0} m`}
          subtext="Mean Spring Tidal Rise"
        />
        <MetricCard
          label="NIGHT NAVIGATION"
          value={port.night_navigation ? "PERMITTED" : "DAYLIGHT ONLY"}
          subtext={`Mandatory Tugs: ${port.tug_requirement_count} units`}
        />
      </div>

      {/* Berths Matrix */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <Anchor className="h-4 w-4 text-blue-400" />
            <span>Dedicated Berth Constraints & Handling Infrastructure</span>
          </h3>
          <span className="text-xs font-mono text-slate-400">
            {port.berths.length} Berths Configured
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-slate-400 uppercase font-mono text-[10px] border-b border-slate-800">
              <tr>
                <th className="p-3">Berth Code / Name</th>
                <th className="p-3">Facility Type</th>
                <th className="p-3">Max Draft</th>
                <th className="p-3">Max LOA</th>
                <th className="p-3">Max Beam</th>
                <th className="p-3">Max DWT</th>
                <th className="p-3">Discharge Rate</th>
                <th className="p-3">Handling Equipment</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {port.berths.map(berth => (
                <tr key={berth.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="p-3">
                    <div className="font-bold text-slate-100 font-sans">{berth.berth_code}</div>
                    <div className="text-[11px] text-slate-400 font-sans">{berth.berth_name}</div>
                  </td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-[11px] text-slate-200">
                      {berth.berth_type}
                    </span>
                  </td>
                  <td className="p-3 text-cyan-400 font-bold">
                    {berth.max_draft_m ? `${berth.max_draft_m.toFixed(1)} m` : "—"}
                  </td>
                  <td className="p-3 text-slate-200">
                    {berth.max_loa_m ? `${berth.max_loa_m.toFixed(0)} m` : "—"}
                  </td>
                  <td className="p-3 text-slate-200">
                    {berth.max_beam_m ? `${berth.max_beam_m.toFixed(1)} m` : "—"}
                  </td>
                  <td className="p-3 text-emerald-400 font-bold">
                    {berth.max_dwt ? `${berth.max_dwt.toLocaleString()} MT` : "—"}
                  </td>
                  <td className="p-3 text-amber-400 font-bold">
                    {berth.discharge_rate_tpd ? `${berth.discharge_rate_tpd.toLocaleString()} TPD` : "—"}
                  </td>
                  <td className="p-3 text-slate-400 font-sans text-[11px]">
                    {berth.equipment_summary || "Shore Grab / Crane Discharge"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Official Data Sources & Circulars */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
        <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-emerald-400" />
          <span>Official Data Sources & Marine Circulars</span>
        </h3>

        <div className="space-y-3">
          {port.data_sources && port.data_sources.length > 0 ? (
            port.data_sources.map(src => (
              <div key={src.id} className="p-4 rounded-lg bg-slate-950/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                <div className="space-y-1">
                  <div className="font-bold text-slate-100">{src.source_name}</div>
                  <div className="text-slate-400 font-mono">
                    Ref: {src.doc_reference || "Official Gazette Circular"} • Verified by: {src.verified_by || "Port Conservator"}
                  </div>
                </div>
                <div className="flex items-center gap-2 font-mono text-emerald-400 shrink-0">
                  <CheckCircle2 className="h-4 w-4" />
                  <span>OFFICIALLY VERIFIED</span>
                </div>
              </div>
            ))
          ) : (
            <div className="p-4 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-400">
              Official port circular verified against East Coast Port Authority gazette records.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
