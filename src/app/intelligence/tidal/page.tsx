"use client";

import React, { useState, useEffect } from "react";
import {
  Waves,
  Clock,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  HelpCircle,
  RefreshCw,
  Calendar,
  Compass,
  FileText,
  SlidersHorizontal,
  ChevronRight,
  Anchor,
  Info,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { DataStatusBadge } from "@/components/badges/DataStatusBadge";
import {
  riskApi,
  TidalWindow,
  TidalEvaluationResponse,
  TidalWindowStatus,
} from "@/lib/api/risk";
import { portsApi, Port } from "@/lib/api/ports";

export default function TidalWindowsPage() {
  const [selectedPortId, setSelectedPortId] = useState<string>("port-inhal");
  const [vesselDraft, setVesselDraft] = useState<number>(12.2);
  const [berthDraft, setBerthDraft] = useState<number>(8.5);
  const [requiredUkc, setRequiredUkc] = useState<number>(0.5);

  const [windows, setWindows] = useState<TidalWindow[]>([]);
  const [evaluation, setEvaluation] = useState<TidalEvaluationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  // Load windows and run UKC calculation
  const fetchTidalData = async (showSpinner = false) => {
    try {
      if (showSpinner) setRefreshing(true);
      else setLoading(true);

      const [winList, evalRes] = await Promise.all([
        riskApi.getPortTidalWindows(selectedPortId),
        riskApi.evaluateTidalGate({
          port_id: selectedPortId,
          vessel_draft_m: vesselDraft,
          berth_draft_m: berthDraft,
          required_ukc_m: requiredUkc,
        }),
      ]);

      setWindows(winList);
      setEvaluation(evalRes);
    } catch (err) {
      console.error("Error fetching tidal data:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchTidalData();
  }, [selectedPortId, vesselDraft, berthDraft, requiredUkc]);

  // Status badge styling helper
  const renderStatusBadge = (status: string) => {
    switch (status) {
      case "PASS":
        return (
          <span className="px-2.5 py-1 text-xs font-mono font-bold uppercase rounded bg-emerald-950 border border-emerald-600 text-emerald-300 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5" />
            PASS — ALL-TIDE ACCESSIBLE
          </span>
        );
      case "CONDITIONAL":
        return (
          <span className="px-2.5 py-1 text-xs font-mono font-bold uppercase rounded bg-amber-950 border border-amber-600 text-amber-300 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" />
            CONDITIONAL — HIGH-WATER SLOT REQUIRED
          </span>
        );
      case "FAIL":
        return (
          <span className="px-2.5 py-1 text-xs font-mono font-bold uppercase rounded bg-rose-950 border border-rose-600 text-rose-300 flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5" />
            FAIL — INSUFFICIENT TIDAL DEPTH
          </span>
        );
      case "UNKNOWN":
      default:
        return (
          <span className="px-2.5 py-1 text-xs font-mono font-bold uppercase rounded bg-slate-900 border border-slate-700 text-slate-400 flex items-center gap-1.5">
            <HelpCircle className="w-3.5 h-3.5" />
            UNKNOWN — DRAFT UNRECORDED
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        title="TIDAL GATE SCHEDULER & UKC ENGINE"
        description="Hydrographic Under Keel Clearance (UKC) evaluation, semi-diurnal tidal height predictions, and high-water navigation slots for draft-constrained ports."
        status="OPERATIONAL INTELLIGENCE"
        actions={
          <button
            onClick={() => fetchTidalData(true)}
            disabled={refreshing}
            className="flex items-center gap-2 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-cyan-400" : ""}`} />
            Refresh Harmonic Tide
          </button>
        }
      />

      {/* Port Selector Strip */}
      <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-slate-400">Tidal Port Location:</span>
          {[
            { id: "port-inhal", name: "Haldia Dock (Strongly Tidal River Lock)" },
            { id: "port-inprt", name: "Paradip Port (Tidal Lagoon)" },
            { id: "port-indhm", name: "Dhamra Port (Tidal Estuary)" },
            { id: "port-invtz", name: "Visakhapatnam (Deep Harbour)" },
            { id: "port-auncb", name: "Newcastle (Hunter River)" },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => {
                setSelectedPortId(item.id);
                if (item.id === "port-inhal") {
                  setBerthDraft(8.5);
                  setVesselDraft(12.2);
                } else if (item.id === "port-inprt") {
                  setBerthDraft(16.0);
                  setVesselDraft(14.5);
                } else {
                  setBerthDraft(14.0);
                  setVesselDraft(12.0);
                }
              }}
              className={`px-3 py-1.5 text-xs font-mono rounded transition ${
                selectedPortId === item.id
                  ? "bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20"
                  : "bg-slate-950 border border-slate-800 text-slate-300 hover:border-slate-700"
              }`}
            >
              {item.name}
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid: Interactive UKC Calculator & Depth Balance */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Interactive UKC Calculator */}
        <div className="lg:col-span-6 p-5 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Waves className="w-4 h-4 text-cyan-400" />
                Under Keel Clearance (UKC) Calculator
              </h3>
              <p className="text-xs text-slate-400">
                Calculates available depth vs required depth without guessing unrecorded drafts.
              </p>
            </div>
            <span className="px-2 py-0.5 text-[10px] font-mono uppercase rounded bg-slate-800 text-slate-300 border border-slate-700">
              Hydrographic Form
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1">
                Vessel Arrival Draft (m)
              </label>
              <input
                type="number"
                step="0.1"
                value={vesselDraft}
                onChange={(e) => setVesselDraft(parseFloat(e.target.value) || 0)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">
                Hydrostatic Master draft
              </span>
            </div>

            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1">
                Chart Datum Depth (m)
              </label>
              <input
                type="number"
                step="0.1"
                value={berthDraft}
                onChange={(e) => setBerthDraft(parseFloat(e.target.value) || 0)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">
                Authorized dredged depth
              </span>
            </div>

            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1">
                Required UKC Buffer (m)
              </label>
              <input
                type="number"
                step="0.1"
                value={requiredUkc}
                onChange={(e) => setRequiredUkc(parseFloat(e.target.value) || 0.5)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">
                0.5m berth / 1.0m channel
              </span>
            </div>
          </div>

          {evaluation && (
            <div className="p-4 rounded bg-slate-950/90 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <span className="text-xs text-slate-400">Tidal Feasibility Assessment:</span>
                {renderStatusBadge(evaluation.status)}
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs font-mono">
                <div className="p-2 rounded bg-slate-900 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Vessel Draft</span>
                  <span className="font-bold text-slate-200">{evaluation.vessel_draft_m}m</span>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Required UKC</span>
                  <span className="font-bold text-slate-200">+{evaluation.required_ukc_m}m</span>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Required Depth</span>
                  <span className="font-bold text-sky-400">{evaluation.required_depth_m}m</span>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">UKC Safety Margin</span>
                  <span
                    className={`font-bold ${
                      (evaluation.ukc_margin_m || 0) >= 0 ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {evaluation.ukc_margin_m !== null ? `${evaluation.ukc_margin_m}m` : "N/A"}
                  </span>
                </div>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/50 p-2.5 rounded border border-slate-800/80">
                {evaluation.explanation}
              </p>

              <div className="text-xs text-amber-300 bg-amber-950/30 p-2.5 rounded border border-amber-900/40 flex items-start gap-2">
                <span className="font-semibold text-amber-400 shrink-0">Action:</span>
                <span>{evaluation.mitigation}</span>
              </div>
            </div>
          )}
        </div>

        {/* Physical Depth Breakdown Graphic Card */}
        <div className="lg:col-span-6 p-5 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Compass className="w-4 h-4 text-sky-400" />
                Physical Water Column Diagram
              </h3>
              <p className="text-xs text-slate-400">
                Visualizing available water column vs required vessel keel immersion.
              </p>
            </div>
            <DataStatusBadge status="RECENT" />
          </div>

          <div className="space-y-4 py-2">
            <div className="space-y-1 text-xs">
              <div className="flex items-center justify-between text-slate-400">
                <span>Available Depth (Base Chart Datum + High Water Tide):</span>
                <span className="font-mono font-bold text-cyan-400">
                  {((berthDraft || 8.5) + (selectedPortId === "port-inhal" ? 5.4 : 2.7)).toFixed(2)}m
                </span>
              </div>
              <div className="w-full bg-slate-950 h-5 rounded overflow-hidden flex border border-slate-800">
                <div
                  className="bg-sky-600 h-full text-[10px] font-mono text-white flex items-center justify-center"
                  style={{ width: "65%" }}
                >
                  Dredged Bed {berthDraft}m
                </div>
                <div
                  className="bg-cyan-400 h-full text-[10px] font-mono text-slate-950 font-bold flex items-center justify-center"
                  style={{ width: "35%" }}
                >
                  +{selectedPortId === "port-inhal" ? "5.4m Tide" : "2.7m Tide"}
                </div>
              </div>
            </div>

            <div className="space-y-1 text-xs">
              <div className="flex items-center justify-between text-slate-400">
                <span>Required Water Column (Vessel Draft + UKC Buffer):</span>
                <span className="font-mono font-bold text-amber-400">
                  {((vesselDraft || 12.2) + (requiredUkc || 0.5)).toFixed(2)}m
                </span>
              </div>
              <div className="w-full bg-slate-950 h-5 rounded overflow-hidden flex border border-slate-800">
                <div
                  className="bg-amber-600 h-full text-[10px] font-mono text-white flex items-center justify-center"
                  style={{ width: "85%" }}
                >
                  Vessel Draft {vesselDraft}m
                </div>
                <div
                  className="bg-emerald-500 h-full text-[10px] font-mono text-slate-950 font-bold flex items-center justify-center"
                  style={{ width: "15%" }}
                >
                  UKC {requiredUkc}m
                </div>
              </div>
            </div>

            <div className="p-3 rounded bg-slate-950 border border-slate-800 text-xs text-slate-400 space-y-1.5">
              <div className="font-semibold text-slate-300 flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5 text-cyan-400" />
                Riverine & Lock Gate Siltation Notice
              </div>
              <p className="text-[11px] leading-relaxed">
                At Haldia Dock Complex, river sandbars at Auckland, Jellingham, and Middleton bar channels restrict low-water passage to 8.2m CD. Panamax vessels drafting 11.5m–12.5m must strictly synchronize navigation with High Water spring tide windows.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 48-Hour Tidal Window Slots Calendar */}
      <div className="p-5 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Calendar className="w-4 h-4 text-cyan-400" />
              Harmonic Tidal Window Schedule (Next 48–72 Hours)
            </h3>
            <p className="text-xs text-slate-400">
              High and Low water slots calculated via semi-diurnal harmonic sinusoidal curve above Chart Datum.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {windows.length} scheduled tide slots
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {windows.slice(0, 8).map((w, idx) => {
            const isHigh = (w.predicted_tide_height_m || 0) > 2.5;
            return (
              <div
                key={w.id || idx}
                className={`p-3.5 rounded-lg border text-xs space-y-2 transition ${
                  isHigh
                    ? "bg-slate-950/90 border-cyan-800/60 hover:border-cyan-500"
                    : "bg-slate-950/60 border-slate-800 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span
                    className={`font-mono text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${
                      isHigh
                        ? "bg-cyan-950 text-cyan-300 border border-cyan-800"
                        : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    {isHigh ? "High Water Window" : "Low Water Slot"}
                  </span>
                  <span className="font-mono text-[10px] text-slate-400">
                    {w.window_start ? w.window_start.slice(11, 16) : ""} UTC
                  </span>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Predicted Tide:</span>
                    <span className="font-mono font-bold text-cyan-400">
                      +{w.predicted_tide_height_m}m CD
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Total Depth:</span>
                    <span className="font-mono font-bold text-slate-200">
                      {w.total_available_depth_m || ((berthDraft || 8.5) + (w.predicted_tide_height_m || 0)).toFixed(1)}m
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Slot Window:</span>
                    <span className="font-mono text-[11px] text-slate-300">
                      {w.window_start?.slice(11, 16)} - {w.window_end?.slice(11, 16)}
                    </span>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800/80">
                  <span
                    className={`text-[10px] font-mono block text-center uppercase py-0.5 rounded ${
                      isHigh
                        ? "bg-emerald-950/60 text-emerald-300 border border-emerald-800/40"
                        : "bg-amber-950/60 text-amber-300 border border-amber-800/40"
                    }`}
                  >
                    {isHigh ? "Clearance Feasible" : "Draft Constrained"}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
