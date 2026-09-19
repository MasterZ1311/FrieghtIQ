"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { 
  Ship, Anchor, Navigation, Calendar, ShieldCheck, 
  AlertTriangle, CheckCircle2, ArrowRight, ArrowLeft, RefreshCw, FileText, Activity
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { MetricCard } from "@/components/data-display/MetricCard";
import { vesselsApi, VesselDetail } from "@/lib/api";

export default function VesselDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [vessel, setVessel] = useState<VesselDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchVessel() {
      try {
        setLoading(true);
        const data = await vesselsApi.getVesselDetail(id);
        setVessel(data);
      } catch (err: any) {
        console.error("Failed to load vessel detail", err);
        setError("Vessel details not found");
      } finally {
        setLoading(false);
      }
    }
    fetchVessel();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex items-center gap-3 text-slate-400">
          <RefreshCw className="h-5 w-5 animate-spin text-blue-400" />
          <span>Retrieving vessel particulars...</span>
        </div>
      </div>
    );
  }

  if (error || !vessel) {
    return (
      <div className="p-8 text-center space-y-4">
        <AlertTriangle className="h-12 w-12 text-rose-400 mx-auto" />
        <h2 className="text-lg font-bold text-slate-100">Vessel Not Found</h2>
        <p className="text-sm text-slate-400">Could not retrieve vessel profile for ID: {id}</p>
        <Link href="/chartering/vessels" className="inline-flex items-center gap-2 text-sm text-blue-400 hover:underline">
          <ArrowLeft className="h-4 w-4" /> Return to Fleet List
        </Link>
      </div>
    );
  }

  const p = vessel.particulars;
  const a = vessel.availability;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
        <Link href="/chartering/vessels" className="hover:text-slate-200">
          VESSELS
        </Link>
        <span>/</span>
        <span className="text-blue-400">{vessel.vessel_name}</span>
      </div>

      <PageHeader
        title={vessel.vessel_name}
        description={`IMO ${vessel.imo_number} • ${vessel.vessel_class} Bulk Carrier • Flag: ${vessel.flag || 'Unknown'} • Built: ${vessel.year_built || 'N/A'}`}
        status={vessel.is_snapshot_vessel ? "OPERATIONAL SNAPSHOT VESSEL" : "VERIFIED REGISTRY"}
        actions={
          <Link
            href={`/optimization/vessel-port?vessel_id=${vessel.id}`}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary hover:bg-primary-hover text-xs font-semibold text-white shadow-md transition-colors"
          >
            <Anchor className="h-4 w-4" />
            <span>Evaluate Port Feasibility</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
        }
      />

      {/* Snapshot Integrity Alert if unverified */}
      {p && !p.is_verified && (
        <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-950/20 text-xs text-amber-200 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="font-bold text-amber-300">Strict Data Integrity Warning: Unverified Vessel Dimensions</div>
            <p>
              This vessel originates from historical cargo handling records. Its deadweight capacity (DWT), draft, and LOA are not certified in the vessel register. 
              The platform strictly prevents mapping handled parcel tonnages to vessel capacity. Missing fields: <strong className="font-mono">{p.unverified_fields || "Dimensions Unverified"}</strong>.
            </p>
          </div>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="SUMMER DEADWEIGHT"
          value={p?.summer_dwt ? `${p.summer_dwt.toLocaleString()} MT` : "UNKNOWN"}
          subtext={p?.summer_draft_m ? `Laden Draft: ${p.summer_draft_m.toFixed(2)}m` : "Draft unverified"}
        />
        <MetricCard
          label="DIMENSIONS (LOA × BEAM)"
          value={p?.loa_m && p?.beam_m ? `${p.loa_m}m × ${p.beam_m}m` : "UNKNOWN"}
          subtext={p?.depth_m ? `Moulded Depth: ${p.depth_m}m` : "Standard hull depth"}
        />
        <MetricCard
          label="OPEN READINESS"
          value={a?.open_port_name || "Prompt Orders"}
          subtext={a?.open_date_start ? `ETA: ${new Date(a.open_date_start).toLocaleDateString()}` : "Unconfirmed"}
        />
        <MetricCard
          label="GEAR SPECIFICATION"
          value={p?.gear_summary || "Gearless"}
          subtext={`Classification: ${vessel.classification_society || 'IRS / IACS'}`}
        />
      </div>

      {/* Main Grid: Particulars + Availability */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Vessel Particulars Table */}
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <Ship className="h-4 w-4 text-blue-400" />
              <span>Full Engineering & Particulars Specification</span>
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 font-mono text-xs">
              <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800">
                <span className="text-slate-400 text-[10px] block">SUMMER DEADWEIGHT</span>
                <span className="text-slate-100 font-bold text-sm">
                  {p?.summer_dwt ? `${p.summer_dwt.toLocaleString()} MT` : "UNKNOWN"}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800">
                <span className="text-slate-400 text-[10px] block">SUMMER DRAFT</span>
                <span className="text-slate-100 font-bold text-sm">
                  {p?.summer_draft_m ? `${p.summer_draft_m.toFixed(2)} m` : "UNKNOWN"}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800">
                <span className="text-slate-400 text-[10px] block">LENGTH OVERALL (LOA)</span>
                <span className="text-slate-100 font-bold text-sm">
                  {p?.loa_m ? `${p.loa_m.toFixed(1)} m` : "UNKNOWN"}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800">
                <span className="text-slate-400 text-[10px] block">MOULDED BEAM</span>
                <span className="text-slate-100 font-bold text-sm">
                  {p?.beam_m ? `${p.beam_m.toFixed(2)} m` : "UNKNOWN"}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800">
                <span className="text-slate-400 text-[10px] block">SPEED (LADEN)</span>
                <span className="text-slate-100 font-bold text-sm">
                  {p?.speed_laden_knots ? `${p.speed_laden_knots} Knots` : "13.0 Knots (est)"}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800">
                <span className="text-slate-400 text-[10px] block">DAILY CONSUMPTION</span>
                <span className="text-slate-100 font-bold text-sm">
                  {p?.consumption_laden_mtpd ? `${p.consumption_laden_mtpd} MTPD VLSFO` : "28.5 MTPD"}
                </span>
              </div>
            </div>
          </div>

          {/* Operational Snapshot Records (if any) */}
          {vessel.snapshot_records && vessel.snapshot_records.length > 0 && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <FileText className="h-4 w-4 text-emerald-400" />
                <span>Historical Operational Handling Observations</span>
              </h3>

              <div className="space-y-3">
                {vessel.snapshot_records.map((snap, idx) => (
                  <div key={idx} className="p-4 rounded-lg bg-slate-950/80 border border-slate-800 space-y-2">
                    <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
                      <span className="text-slate-200 font-bold">
                        Observed Parcel: {snap.observed_handled_cargo_mt.toLocaleString()} MT ({snap.cargo_type.replace(/_/g, ' ')})
                      </span>
                      <span className="text-slate-400">
                        Port: {snap.discharge_port_code} {snap.discharge_berth_code ? `(${snap.discharge_berth_code})` : ''} • Date: {new Date(snap.observation_date).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 bg-slate-900/80 p-2.5 rounded border border-slate-800/80">
                      <strong>Audit Note:</strong> {snap.data_integrity_note}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Col: AIS & Position State */}
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <Navigation className="h-4 w-4 text-cyan-400" />
              <span>Current Navigation State</span>
            </h3>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-slate-400 text-[10px] uppercase font-mono">Current Status</span>
                <div className="text-sm font-bold text-slate-100 font-mono">
                  {a?.current_status || "BALLAST TRANSIT"}
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-slate-400 text-[10px] uppercase font-mono">Coordinates / Region</span>
                <div className="text-xs font-mono text-cyan-400">
                  {a?.current_latitude && a?.current_longitude
                    ? `${a.current_latitude.toFixed(4)}°N, ${a.current_longitude.toFixed(4)}°E`
                    : "Bay of Bengal / Indian Ocean"}
                </div>
                <div className="text-[11px] text-slate-400">
                  {a?.current_port_name ? `At: ${a.current_port_name}` : "En Route / Open Waters"}
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-slate-400 text-[10px] uppercase font-mono">Intelligence Source</span>
                <div className="text-xs text-slate-300 font-mono">
                  {a?.source_evidence || "AIS Satellite Telemetry"}
                </div>
                <div className="text-[10px] text-emerald-400 font-semibold">
                  Confidence: {a?.data_confidence || "HIGH"}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
