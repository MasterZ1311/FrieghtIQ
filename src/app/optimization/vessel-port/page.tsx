"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { 
  Anchor, Ship, Cpu, CheckCircle2, AlertTriangle, XCircle, 
  HelpCircle, RefreshCw, ArrowRight, Gauge, Clock, ShieldAlert, ChevronDown, ChevronUp
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { 
  vesselsApi, portsApi, optimizerApi, 
  Vessel, Port, FeasibilityRun, BerthFeasibilityResult 
} from "@/lib/api";

export default function VesselPortOptimizerPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex items-center gap-3 text-slate-400">
          <RefreshCw className="h-5 w-5 animate-spin text-blue-400" />
          <span>Loading Vessel-Port Optimizer...</span>
        </div>
      </div>
    }>
      <VesselPortOptimizerContent />
    </Suspense>
  );
}

function VesselPortOptimizerContent() {
  const searchParams = useSearchParams();
  const initialVesselId = searchParams.get("vessel_id") || "";
  const initialPortId = searchParams.get("port_id") || "";

  const [vessels, setVessels] = useState<Vessel[]>([]);
  const [ports, setPorts] = useState<Port[]>([]);
  
  const [selectedVesselId, setSelectedVesselId] = useState<string>(initialVesselId);
  const [selectedPortId, setSelectedPortId] = useState<string>(initialPortId);
  const [cargoQty, setCargoQty] = useState<number>(75000);

  const [evaluation, setEvaluation] = useState<FeasibilityRun | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [expandedBerths, setExpandedBerths] = useState<Record<string, boolean>>({});

  const runEvaluation = async (vId: string, pId: string, qty: number) => {
    if (!vId || !pId) return;
    setLoading(true);
    try {
      const res = await optimizerApi.evaluateFeasibility(vId, pId, qty);
      setEvaluation(res);
      // Auto expand first berth
      if (res.berth_results.length > 0) {
        setExpandedBerths({ [res.berth_results[0].berth_id]: true });
      }
    } catch (err) {
      console.error("Feasibility evaluation failed", err);
    } finally {
      setLoading(false);
    }
  };

  // Initial load of vessels and ports
  useEffect(() => {
    async function loadOptions() {
      try {
        const [vList, pList] = await Promise.all([
          vesselsApi.getVessels(),
          portsApi.getPorts(),
        ]);
        setVessels(vList);
        setPorts(pList);

        const vId = initialVesselId || (vList.length > 0 ? vList[0].id : "");
        const pId = initialPortId || (pList.length > 0 ? pList[0].id : "");
        
        setSelectedVesselId(vId);
        setSelectedPortId(pId);

        if (vId && pId) {
          runEvaluation(vId, pId, 75000);
        }
      } catch (err) {
        console.error("Failed to load options", err);
      }
    }
    loadOptions();
  }, []);

  const selectedVessel = vessels.find(v => v.id === selectedVesselId);
  const selectedPort = ports.find(p => p.id === selectedPortId);

  const toggleBerth = (berthId: string) => {
    setExpandedBerths(prev => ({ ...prev, [berthId]: !prev[berthId] }));
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "PASS":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-950/90 text-emerald-300 border border-emerald-500/50">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" /> COMPATIBLE (PASS)
          </span>
        );
      case "CONDITIONAL":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-950/90 text-amber-300 border border-amber-500/50">
            <AlertTriangle className="h-4 w-4 text-amber-400" /> CONDITIONAL (TIDAL / LIGHTERAGE)
          </span>
        );
      case "UNKNOWN":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-indigo-950/90 text-indigo-300 border border-indigo-500/50">
            <HelpCircle className="h-4 w-4 text-indigo-400" /> UNVERIFIED DIMENSIONS
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-950/90 text-rose-300 border border-rose-500/50">
            <XCircle className="h-4 w-4 text-rose-400" /> RESTRICTED (FAIL)
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="VESSEL-PORT FEASIBILITY OPTIMIZER"
        description="Physical dimension validation engine evaluating draft clearance, LOA pockets, beam outreach, and handling turnaround times across East Coast Indian ports."
        status="BERTH CONSTRAINT ENGINE"
      />

      {/* 3-Column Configuration Header */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Column 1: Vessel Selection */}
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/80 space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase font-mono">
              <Ship className="h-4 w-4 text-blue-400" />
              <span>Select Vessel</span>
            </label>
            {selectedVessel?.is_snapshot_vessel && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                SNAPSHOT VESSEL
              </span>
            )}
          </div>

          <select
            value={selectedVesselId}
            onChange={(e) => {
              setSelectedVesselId(e.target.value);
              runEvaluation(e.target.value, selectedPortId, cargoQty);
            }}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 font-mono focus:outline-none focus:border-blue-500"
          >
            {vessels.map(v => (
              <option key={v.id} value={v.id}>
                {v.vessel_name} ({v.vessel_class} • {v.particulars?.summer_dwt ? `${v.particulars.summer_dwt.toLocaleString()} DWT` : 'Unverified DWT'})
              </option>
            ))}
          </select>

          {selectedVessel && (
            <div className="text-[11px] font-mono text-slate-400 space-y-1 bg-slate-950/60 p-2.5 rounded border border-slate-800">
              <div className="flex justify-between">
                <span>Laden Draft:</span>
                <span className="text-cyan-400 font-bold">
                  {selectedVessel.particulars?.summer_draft_m ? `${selectedVessel.particulars.summer_draft_m.toFixed(2)} m` : 'UNKNOWN'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>LOA × Beam:</span>
                <span className="text-slate-200">
                  {selectedVessel.particulars?.loa_m ? `${selectedVessel.particulars.loa_m}m × ${selectedVessel.particulars.beam_m}m` : 'UNKNOWN'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Gear:</span>
                <span className="text-slate-200">{selectedVessel.particulars?.gear_summary || 'Gearless'}</span>
              </div>
            </div>
          )}
        </div>

        {/* Column 2: Port Selection */}
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/80 space-y-3">
          <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase font-mono">
            <Anchor className="h-4 w-4 text-emerald-400" />
            <span>Select Destination Port</span>
          </label>

          <select
            value={selectedPortId}
            onChange={(e) => {
              setSelectedPortId(e.target.value);
              runEvaluation(selectedVesselId, e.target.value, cargoQty);
            }}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 font-mono focus:outline-none focus:border-emerald-500"
          >
            {ports.map(p => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.unlocode}) — {p.coast || p.country}
              </option>
            ))}
          </select>

          {selectedPort && (
            <div className="text-[11px] font-mono text-slate-400 space-y-1 bg-slate-950/60 p-2.5 rounded border border-slate-800">
              <div className="flex justify-between">
                <span>Channel Max Draft:</span>
                <span className="text-emerald-400 font-bold">
                  {selectedPort.channel_max_draft_m ? `${selectedPort.channel_max_draft_m.toFixed(1)} m` : 'Restricted'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Tidal Range (Rise):</span>
                <span className="text-slate-200">+{selectedPort.tide_range_m ? selectedPort.tide_range_m.toFixed(1) : 2.0} m</span>
              </div>
              <div className="flex justify-between">
                <span>Approach Max LOA:</span>
                <span className="text-slate-200">{selectedPort.channel_max_loa_m || 300} m</span>
              </div>
            </div>
          )}
        </div>

        {/* Column 3: Cargo Parcel & Trigger */}
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/80 space-y-3 flex flex-col justify-between">
          <div>
            <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase font-mono">
              <Gauge className="h-4 w-4 text-amber-400" />
              <span>Cargo Parcel Quantity (MT)</span>
            </label>
            <input
              type="number"
              step="1000"
              value={cargoQty}
              onChange={(e) => setCargoQty(Number(e.target.value))}
              className="mt-2 w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 font-mono focus:outline-none focus:border-amber-500"
            />
            <span className="text-[10px] text-slate-400 font-mono block mt-1">
              Used to calculate berth discharge turnaround duration.
            </span>
          </div>

          <button
            onClick={() => runEvaluation(selectedVesselId, selectedPortId, cargoQty)}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-primary hover:bg-primary-hover text-xs font-bold text-white shadow-md transition-colors font-mono"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? "Evaluating Clearances..." : "RUN FEASIBILITY OPTIMIZER"}</span>
          </button>
        </div>
      </div>

      {/* Overall Compatibility Banner */}
      {evaluation && (
        <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/90 space-y-2">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono uppercase text-slate-400">OVERALL PORT FEASIBILITY:</span>
              {getStatusBadge(evaluation.overall_status)}
            </div>
            <div className="text-xs font-mono text-slate-400">
              Compatible Berths: <strong className="text-emerald-400">{evaluation.passing_berths_count}</strong> of {evaluation.evaluated_berths_count}
            </div>
          </div>
          <p className="text-sm text-slate-200">
            {evaluation.summary_narrative}
          </p>
        </div>
      )}

      {/* Berth Evaluation Matrix */}
      {evaluation && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2 font-mono">
            <Anchor className="h-4 w-4 text-blue-400" />
            <span>BERTH-BY-BERTH FEASIBILITY BREAKDOWN ({evaluation.berth_results.length} BERTHS)</span>
          </h3>

          <div className="space-y-3">
            {evaluation.berth_results.map((bRes) => {
              const isExpanded = !!expandedBerths[bRes.berth_id];
              const berth = bRes.berth;

              return (
                <div
                  key={bRes.id}
                  className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden hover:border-slate-700 transition-all"
                >
                  {/* Berth Card Header */}
                  <div className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-3">
                        <span className="text-base font-bold font-mono text-slate-100">
                          {berth?.berth_code || bRes.berth_id}
                        </span>
                        <span className="text-xs text-slate-300 font-sans">
                          {berth?.berth_name}
                        </span>
                        <span className="px-2 py-0.5 rounded bg-slate-800 font-mono text-[10px] text-slate-400">
                          {berth?.berth_type}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 flex flex-wrap gap-x-5 gap-y-1 font-mono">
                        <span>
                          Draft Clearance:{" "}
                          <strong className={
                            (bRes.draft_clearance_m ?? -1) >= 0.5 ? "text-emerald-400" :
                            (bRes.draft_clearance_m ?? -1) >= 0 ? "text-amber-400" : "text-rose-400"
                          }>
                            {bRes.draft_clearance_m !== null && bRes.draft_clearance_m !== undefined
                              ? `${bRes.draft_clearance_m > 0 ? '+' : ''}${bRes.draft_clearance_m.toFixed(2)} m`
                              : "UNKNOWN"}
                          </strong>
                        </span>
                        <span>
                          LOA Clearance:{" "}
                          <strong className={(bRes.loa_clearance_m ?? -1) >= 0 ? "text-emerald-400" : "text-rose-400"}>
                            {bRes.loa_clearance_m !== null && bRes.loa_clearance_m !== undefined
                              ? `${bRes.loa_clearance_m > 0 ? '+' : ''}${bRes.loa_clearance_m.toFixed(1)} m`
                              : "UNKNOWN"}
                          </strong>
                        </span>
                        <span>
                          Est. Turnaround:{" "}
                          <strong className="text-amber-400">
                            {bRes.estimated_turnaround_days ? `${bRes.estimated_turnaround_days} Days` : "—"}
                          </strong>
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      {getStatusBadge(bRes.status)}
                      <button
                        onClick={() => toggleBerth(bRes.berth_id)}
                        className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 transition-colors"
                        title={isExpanded ? "Collapse details" : "Expand details"}
                      >
                        {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                      </button>
                    </div>
                  </div>

                  {/* Berth Narrative */}
                  <div className="px-4 py-2 bg-slate-950/40 border-t border-slate-800/80 text-xs text-slate-300">
                    <span className="font-semibold text-slate-400 font-mono">ASSESSMENT: </span>
                    <span>{bRes.summary_explanation}</span>
                  </div>

                  {/* Expanded Rule Evaluation Cards */}
                  {isExpanded && (
                    <div className="p-4 bg-slate-950/80 border-t border-slate-800 space-y-3">
                      <div className="text-[11px] font-mono text-slate-400 uppercase">
                        Physical Clearance Checks:
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-xs">
                        {bRes.rule_evaluations.map((rule) => (
                          <div
                            key={rule.rule_name}
                            className="p-3 rounded-lg border border-slate-800 bg-slate-900/60 space-y-1"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-slate-200">
                                {rule.rule_name.replace(/_/g, ' ')}
                              </span>
                              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                                rule.status === "PASS" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" :
                                rule.status === "CONDITIONAL" ? "bg-amber-950 text-amber-400 border border-amber-800" :
                                rule.status === "UNKNOWN" ? "bg-indigo-950 text-indigo-400 border border-indigo-800" :
                                "bg-rose-950 text-rose-400 border border-rose-800"
                              }`}>
                                {rule.status}
                              </span>
                            </div>
                            <div className="text-slate-400 flex justify-between text-[11px]">
                              <span>Limit: <strong className="text-slate-200">{rule.limit_value ?? "N/A"} {rule.unit}</strong></span>
                              <span>Vessel: <strong className="text-slate-200">{rule.vessel_value ?? "N/A"} {rule.unit}</strong></span>
                              {rule.margin !== null && rule.margin !== undefined && (
                                <span>Margin: <strong className={rule.margin >= 0 ? "text-emerald-400" : "text-rose-400"}>{rule.margin > 0 ? '+' : ''}{rule.margin.toFixed(2)}{rule.unit}</strong></span>
                              )}
                            </div>
                            <p className="text-[11px] text-slate-400 font-sans pt-1">
                              {rule.narrative}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
