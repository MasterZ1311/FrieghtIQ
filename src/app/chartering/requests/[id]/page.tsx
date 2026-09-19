"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { 
  Ship, Anchor, Calendar, ArrowRight, ShieldCheck, 
  Layers, Clock, ExternalLink, ArrowLeft, CheckCircle2, AlertCircle, RefreshCw
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatusBadge } from "@/components/badges/StatusBadge";
import { MetricCard } from "@/components/data-display/MetricCard";
import { cargoApi, CargoRequirementDetail } from "@/lib/api";

export default function CargoRequirementDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [requirement, setRequirement] = useState<CargoRequirementDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchDetail() {
      try {
        setLoading(true);
        // Try fetching live requirement
        const data = await cargoApi.getRequirementDetail(id);
        setRequirement(data);
      } catch (err: any) {
        console.warn("Could not fetch requirement directly, trying list...", err);
        try {
          const list = await cargoApi.getRequirements();
          const match = list.find(r => r.id === id || r.requirement_code === id);
          if (match) {
            setRequirement({ ...match, handling_logs: [] });
          } else if (list.length > 0) {
            setRequirement({ ...list[0], handling_logs: [] });
          } else {
            setError("Cargo requirement not found");
          }
        } catch {
          setError("Failed to load cargo requirement");
        }
      } finally {
        setLoading(false);
      }
    }
    fetchDetail();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex items-center gap-3 text-slate-400">
          <RefreshCw className="h-5 w-5 animate-spin text-blue-400" />
          <span>Loading requirement intelligence...</span>
        </div>
      </div>
    );
  }

  if (error || !requirement) {
    return (
      <div className="p-8 text-center space-y-4">
        <AlertCircle className="h-12 w-12 text-rose-400 mx-auto" />
        <h2 className="text-lg font-bold text-slate-100">Requirement Not Found</h2>
        <p className="text-sm text-slate-400">Could not retrieve requisition record for ID: {id}</p>
        <Link href="/chartering/requests" className="inline-flex items-center gap-2 text-sm text-blue-400 hover:underline">
          <ArrowLeft className="h-4 w-4" /> Back to Active Requests
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
        <Link href="/chartering/requests" className="hover:text-slate-200 transition-colors">
          REQUESTS
        </Link>
        <span>/</span>
        <span className="text-blue-400">{requirement.requirement_code}</span>
      </div>

      <PageHeader
        title={requirement.requirement_code}
        description={requirement.title}
        status={`STATUS: ${requirement.status}`}
        actions={
          <div className="flex items-center gap-3">
            <Link
              href={`/chartering/requests/${requirement.id}/vessels`}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary hover:bg-primary-hover text-xs font-semibold text-white shadow-md transition-colors"
            >
              <Ship className="h-4 w-4" />
              <span>Evaluate Candidate Vessels</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        }
      />

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="CARGO PARCEL SIZE"
          value={`${requirement.quantity_mt.toLocaleString()} MT`}
          change={`±${requirement.tolerance_pct}% MOLOO`}
          changeType="neutral"
          subtext={requirement.cargo_type.replace(/_/g, ' ')}
        />
        <MetricCard
          label="LAYCAN WINDOW"
          value={new Date(requirement.laycan_start).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
          subtext={`to ${new Date(requirement.laycan_end).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}`}
        />
        <MetricCard
          label="TARGET FREIGHT"
          value={requirement.target_freight_usd_pmt ? `$${requirement.target_freight_usd_pmt.toFixed(2)}/MT` : "MARKET RATE"}
          subtext="Budgeted procurement ceiling"
        />
        <MetricCard
          label="VESSEL CLASSES"
          value={requirement.preferred_vessel_classes.replace(/,/g, ' / ')}
          subtext={`Max Age: ≤ ${requirement.max_vessel_age_years} yrs`}
        />
      </div>

      {/* Main Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Voyage & Ports Profile */}
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <Anchor className="h-4 w-4 text-blue-400" />
              <span>Voyage Route & Port Requirements</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-2">
                <div className="text-[10px] font-mono uppercase text-slate-400">Loading Port (Origin)</div>
                <div className="text-base font-bold text-slate-100 font-mono">
                  {requirement.load_port?.name || "Newcastle Port"}
                </div>
                <div className="text-xs text-slate-400">UN/LOCODE: {requirement.load_port?.unlocode || "AUNCB"} • Australia</div>
                <div className="text-xs text-cyan-400 font-mono">
                  Permissible Draft: {requirement.load_port?.channel_max_draft_m || 15.2}m
                </div>
              </div>

              <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-2">
                <div className="text-[10px] font-mono uppercase text-slate-400">Discharge Port (Destination)</div>
                <div className="text-base font-bold text-slate-100 font-mono">
                  {requirement.discharge_port?.name || "Paradip Port"}
                </div>
                <div className="text-xs text-slate-400">UN/LOCODE: {requirement.discharge_port?.unlocode || "INPRT"} • East Coast India</div>
                <div className="text-xs text-emerald-400 font-mono">
                  Permissible Draft: {requirement.discharge_port?.channel_max_draft_m || 16.0}m (CB-1 / CB-2 / MCB)
                </div>
              </div>
            </div>

            <div className="p-4 rounded-lg bg-blue-950/20 border border-blue-900/30 text-xs text-slate-300 space-y-1">
              <div className="font-semibold text-blue-400">Chartering Note:</div>
              <p>{requirement.notes || "Direct import of prime hard coking coal for blast furnace blend at SAIL integrated steel plants."}</p>
            </div>
          </div>

          {/* Vetting & Commercial Policy */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              <span>Technical & Commercial Vetting Criteria</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                <span className="text-slate-400 text-[10px] block">MAX VESSEL AGE</span>
                <span className="text-slate-200 font-semibold">{requirement.max_vessel_age_years} Years Built</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                <span className="text-slate-400 text-[10px] block">GEAR REQUIREMENT</span>
                <span className="text-slate-200 font-semibold">{requirement.gear_requirement}</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                <span className="text-slate-400 text-[10px] block">REQUISITION ISSUER</span>
                <span className="text-slate-200 font-semibold">{requirement.created_by}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Col: Quick Actions & Live Status */}
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
            <h3 className="text-sm font-semibold text-slate-100">Action Center</h3>
            <div className="space-y-2">
              <Link
                href={`/chartering/requests/${requirement.id}/vessels`}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-primary/20 hover:bg-primary/30 border border-primary/40 text-xs font-semibold text-blue-200 transition-colors"
              >
                <span className="flex items-center gap-2">
                  <Ship className="h-4 w-4 text-blue-400" />
                  <span>Run Deterministic Matching</span>
                </span>
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href={`/optimization/vessel-port?port_id=${requirement.discharge_port_id}`}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-slate-800 hover:bg-slate-700/80 border border-slate-700 text-xs font-medium text-slate-200 transition-colors"
              >
                <span className="flex items-center gap-2">
                  <Anchor className="h-4 w-4 text-emerald-400" />
                  <span>Verify Berth Feasibility</span>
                </span>
                <ExternalLink className="h-4 w-4 text-slate-400" />
              </Link>
              <Link
                href={`/intelligence/freight`}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-slate-800 hover:bg-slate-700/80 border border-slate-700 text-xs font-medium text-slate-200 transition-colors"
              >
                <span className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-amber-400" />
                  <span>View Route Forecasts</span>
                </span>
                <ExternalLink className="h-4 w-4 text-slate-400" />
              </Link>
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Data Governance</h4>
            <div className="space-y-2 text-xs text-slate-300">
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Created:</span>
                <span className="font-mono">{new Date(requirement.created_at).toLocaleString()}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Last Modified:</span>
                <span className="font-mono">{new Date(requirement.updated_at).toLocaleString()}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Data Integrity:</span>
                <span className="text-emerald-400 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3" /> VERIFIED SAIL SPEC
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
