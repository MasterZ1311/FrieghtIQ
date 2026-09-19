"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Ship,
  Anchor,
  Clock,
  AlertTriangle,
  CheckCircle2,
  DollarSign,
  Compass,
  ArrowRight,
  RefreshCw,
  Sliders,
  Info,
  ShieldCheck,
  ShieldAlert,
  HelpCircle,
  Layers,
  MapPin,
  Calendar,
  Fuel,
  Activity,
  Maximize2,
  Minimize2,
  ExternalLink,
  ChevronRight,
  TrendingUp,
  X
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  idleApi,
  FleetIdleOverview,
  VesselEmploymentSummary,
  VesselEmploymentTimelineResponse,
  IdleAnalysisResponse,
  RepositioningOption,
  AlternativeEmploymentCandidate,
  VesselEmploymentState,
  DataStatusType,
  IdleScenarioType
} from "@/lib/api";

export default function IdleAndRepositioningPage() {
  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------
  const [overview, setOverview] = useState<FleetIdleOverview | null>(null);
  const [vessels, setVessels] = useState<VesselEmploymentSummary[]>([]);
  const [selectedVesselId, setSelectedVesselId] = useState<string>("vessel-vishva-vijay");
  const [loadingFleet, setLoadingFleet] = useState<boolean>(true);

  // Vessel timeline & scenario analysis
  const [timeline, setTimeline] = useState<VesselEmploymentTimelineResponse | null>(null);
  const [analysis, setAnalysis] = useState<IdleAnalysisResponse | null>(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState<boolean>(false);

  // Config assumptions
  const [speedAssumption, setSpeedAssumption] = useState<number>(12.5);
  const [bunkerPrice, setBunkerPrice] = useState<number>(620.0);
  const [dailyCostAssumption, setDailyCostAssumption] = useState<number>(14000.0);
  const [scenarioType, setScenarioType] = useState<IdleScenarioType>("EMPLOYMENT_GAP");
  const [showConfigDrawer, setShowConfigDrawer] = useState<boolean>(false);

  // Selected candidate cargo for map projection
  const [selectedCandidateIdx, setSelectedCandidateIdx] = useState<number>(0);

  // ---------------------------------------------------------------------------
  // Fetch Fleet Status
  // ---------------------------------------------------------------------------
  const loadFleet = async () => {
    setLoadingFleet(true);
    try {
      const res = await idleApi.getFleetStatus();
      setOverview(res.overview);
      setVessels(res.vessels);
      if (res.vessels.length > 0 && !selectedVesselId) {
        setSelectedVesselId(res.vessels[0].vessel_id);
      }
    } catch (err) {
      console.error("Failed to load fleet idle status:", err);
    } finally {
      setLoadingFleet(false);
    }
  };

  useEffect(() => {
    loadFleet();
  }, []);

  // ---------------------------------------------------------------------------
  // Fetch Vessel Analysis & Timeline
  // ---------------------------------------------------------------------------
  const loadVesselData = async (vesselId: string) => {
    if (!vesselId) return;
    setLoadingAnalysis(true);
    try {
      const [tlRes, anRes] = await Promise.all([
        idleApi.getVesselTimeline(vesselId),
        idleApi.analyzeVessel({
          vessel_id: vesselId,
          daily_vessel_cost_assumption: dailyCostAssumption,
          scenario_type: scenarioType
        })
      ]);
      setTimeline(tlRes);
      setAnalysis(anRes);
      setSelectedCandidateIdx(0);
    } catch (err) {
      console.error(`Failed to analyze vessel ${vesselId}:`, err);
    } finally {
      setLoadingAnalysis(false);
    }
  };

  useEffect(() => {
    if (selectedVesselId) {
      loadVesselData(selectedVesselId);
    }
  }, [selectedVesselId]);

  const handleRerunAnalysis = () => {
    if (selectedVesselId) {
      loadVesselData(selectedVesselId);
    }
  };

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------
  const selectedVesselSummary = useMemo(() => {
    return vessels.find((v) => v.vessel_id === selectedVesselId) || null;
  }, [vessels, selectedVesselId]);

  const activeCandidate = useMemo(() => {
    if (!analysis || !analysis.alternative_candidates || analysis.alternative_candidates.length === 0) {
      return null;
    }
    return analysis.alternative_candidates[selectedCandidateIdx] || analysis.alternative_candidates[0];
  }, [analysis, selectedCandidateIdx]);

  const activeRepositionOption = useMemo(() => {
    if (!analysis || !analysis.repositioning_options || analysis.repositioning_options.length === 0) {
      return null;
    }
    return analysis.repositioning_options[selectedCandidateIdx] || analysis.repositioning_options[0];
  }, [analysis, selectedCandidateIdx]);

  const getStateBadge = (state: VesselEmploymentState) => {
    switch (state) {
      case "EMPLOYED":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">EMPLOYED</span>;
      case "VOYAGE_COMPLETING":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">VOYAGE COMPLETING</span>;
      case "AVAILABLE":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/30">AVAILABLE</span>;
      case "NEXT_EMPLOYMENT_PENDING":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">FIXTURE PENDING</span>;
      case "IDLE_RISK":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30 animate-pulse">IDLE RISK</span>;
      case "IDLE":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">CONFIRMED IDLE</span>;
      case "REPOSITIONING":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/30">BALLAST REPOSITION</span>;
      case "ALTERNATIVE_EMPLOYMENT":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-500/10 text-teal-400 border border-teal-500/30">ALTERNATIVE FIXTURE</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/30">UNKNOWN</span>;
    }
  };

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case "CONFIRMED_IDLE":
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-rose-500/20 text-rose-300 border border-rose-500/40">CONFIRMED IDLE</span>;
      case "POTENTIAL_RISK":
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-amber-500/20 text-amber-300 border border-amber-500/40">POTENTIAL RISK</span>;
      case "LOW_RISK":
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">LOW RISK</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-slate-700 text-slate-300">UNKNOWN</span>;
    }
  };

  const getDeadheadBadge = (level: string) => {
    switch (level) {
      case "HIGH":
        return <span className="px-2 py-0.5 rounded text-xs font-bold bg-rose-900/50 text-rose-300 border border-rose-600">HIGH DEADHEAD RISK</span>;
      case "MEDIUM":
        return <span className="px-2 py-0.5 rounded text-xs font-bold bg-amber-900/50 text-amber-300 border border-amber-600">MEDIUM RISK</span>;
      case "LOW":
        return <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-900/50 text-emerald-300 border border-emerald-600">LOW DEADHEAD RISK</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-slate-800 text-slate-400">UNKNOWN</span>;
    }
  };

  return (
    <div className="space-y-6 pb-16">
      {/* --------------------------------------------------------------------- */}
      {/* 1. Header                                                             */}
      {/* --------------------------------------------------------------------- */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <PageHeader
          title="IDLE & REPOSITIONING"
          description="Vessel employment intelligence, prompt idle duration estimation, ballast repositioning feasibility, and mitigating alternative fixture evaluation."
          status="DECISION SUPPORT • PHASE 9"
        />
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowConfigDrawer(!showConfigDrawer)}
            className="flex items-center gap-2 px-3.5 py-2 text-xs font-medium rounded-lg bg-slate-800/90 text-slate-300 border border-slate-700 hover:bg-slate-700 transition"
          >
            <Sliders className="h-4 w-4 text-cyan-400" />
            <span>Assumptions & Parameters</span>
          </button>
          <button
            onClick={loadFleet}
            className="flex items-center gap-2 px-3.5 py-2 text-xs font-medium rounded-lg bg-cyan-600/90 text-white hover:bg-cyan-500 transition shadow-sm"
          >
            <RefreshCw className={`h-4 w-4 ${loadingFleet ? "animate-spin" : ""}`} />
            <span>Refresh Roster</span>
          </button>
        </div>
      </div>

      {/* --------------------------------------------------------------------- */}
      {/* 2. Fleet Overview KPIs (Dataset-backed, NO global AIS fake claims)    */}
      {/* --------------------------------------------------------------------- */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
        <div className="bg-slate-900/90 border border-slate-800/90 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Dataset Coverage</span>
            <Layers className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-white tracking-tight">
            {overview?.dataset_coverage_count ?? "—"} <span className="text-xs font-normal text-slate-400">Vessels</span>
          </div>
          <div className="mt-1 text-[11px] text-slate-400 leading-tight">
            {overview?.dataset_coverage_label || "Dataset coverage"}
          </div>
        </div>

        <div className="bg-slate-900/90 border border-slate-800/90 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Active Vessels</span>
            <Ship className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-400 tracking-tight">
            {overview?.active_vessels_count ?? "—"}
          </div>
          <div className="mt-1 text-[11px] text-slate-400 leading-tight">
            Laden transit or completing discharge
          </div>
        </div>

        <div className="bg-slate-900/90 border border-slate-800/90 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">Idle Risk</span>
            <AlertTriangle className="h-4 w-4 text-amber-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-amber-400 tracking-tight">
            {overview?.idle_risk_count ?? "—"}
          </div>
          <div className="mt-1 text-[11px] text-slate-400 leading-tight">
            Open window without confirmed fixture
          </div>
        </div>

        <div className="bg-slate-900/90 border border-slate-800/90 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-rose-400 uppercase tracking-wider">Currently Idle</span>
            <Clock className="h-4 w-4 text-rose-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-rose-400 tracking-tight">
            {overview?.currently_idle_count ?? "—"}
          </div>
          <div className="mt-1 text-[11px] text-slate-400 leading-tight">
            Over 3 days past prompt availability
          </div>
        </div>

        <div className="bg-slate-900/90 border border-slate-800/90 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-sky-400 uppercase tracking-wider">Repositioning</span>
            <Compass className="h-4 w-4 text-sky-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-sky-400 tracking-tight">
            {overview?.repositioning_count ?? "—"}
          </div>
          <div className="mt-1 text-[11px] text-slate-400 leading-tight">
            Steaming ballast to load port
          </div>
        </div>
      </div>

      {/* Dataset Provenance Alert */}
      <div className="flex items-start gap-2.5 px-4 py-2.5 rounded-lg bg-slate-900/60 border border-slate-800 text-xs text-slate-400">
        <Info className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-300">Data Provenance & Integrity Policy: </span>
          {overview?.data_provenance?.source || "SAIL Operational Snapshot Register"}.
          Fleet coverage is bounded strictly by calibrated vessel records. Unknown positions, missing daily costs, or unverified laycan dates remain explicitly labeled as{" "}
          <span className="text-amber-300 font-mono">UNKNOWN / UNAVAILABLE</span>. Zero cost or zero idle days are never substituted.
        </div>
      </div>

      {/* --------------------------------------------------------------------- */}
      {/* 3. Main Operational Interface                                         */}
      {/* --------------------------------------------------------------------- */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT COLUMN: Fleet Roster & Idle Risk Table (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
              <div className="flex items-center gap-2">
                <Ship className="h-4 w-4 text-cyan-400" />
                <h2 className="text-sm font-bold text-white tracking-wide uppercase">
                  Vessel Employment & Idle Exposure Roster
                </h2>
              </div>
              <span className="text-xs text-slate-400">
                Click vessel row to inspect timeline & repositioning
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3">Vessel & Class</th>
                    <th className="px-3 py-3">Current Location</th>
                    <th className="px-3 py-3">Status & State</th>
                    <th className="px-3 py-3">Availability</th>
                    <th className="px-3 py-3">Next Employment</th>
                    <th className="px-3 py-3">Idle Exposure</th>
                    <th className="px-3 py-3">Risk</th>
                    <th className="px-3 py-3 text-right">Data</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {vessels.map((v) => {
                    const isSelected = v.vessel_id === selectedVesselId;
                    return (
                      <tr
                        key={v.vessel_id}
                        onClick={() => setSelectedVesselId(v.vessel_id)}
                        className={`cursor-pointer transition-colors ${
                          isSelected
                            ? "bg-cyan-950/30 hover:bg-cyan-950/40 border-l-2 border-cyan-400"
                            : "hover:bg-slate-800/40"
                        }`}
                      >
                        <td className="px-4 py-3.5">
                          <div className="font-semibold text-white flex items-center gap-1.5">
                            {v.vessel_name}
                            {isSelected && <ChevronRight className="h-3 w-3 text-cyan-400" />}
                          </div>
                          <span className="text-[10px] font-mono text-slate-400">{v.vessel_class}</span>
                        </td>
                        <td className="px-3 py-3.5">
                          <div className="text-slate-200">{v.current_location}</div>
                          <div className="text-[10px] text-slate-500 truncate max-w-[130px]">{v.current_voyage}</div>
                        </td>
                        <td className="px-3 py-3.5 space-y-1">
                          {getStateBadge(v.employment_state)}
                        </td>
                        <td className="px-3 py-3.5">
                          {v.estimated_availability ? (
                            <div>
                              <div className="text-slate-200 font-medium">
                                {new Date(v.estimated_availability).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                              </div>
                              <span className="text-[10px] text-slate-500">Open Window</span>
                            </div>
                          ) : (
                            <span className="text-slate-500 italic">UNKNOWN</span>
                          )}
                        </td>
                        <td className="px-3 py-3.5">
                          <div className="text-slate-300 truncate max-w-[140px]" title={v.next_known_employment || ""}>
                            {v.next_known_employment || "UNRECORDED"}
                          </div>
                          {v.estimated_next_employment_at && (
                            <div className="text-[10px] text-cyan-400">
                              ETA: {new Date(v.estimated_next_employment_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                            </div>
                          )}
                        </td>
                        <td className="px-3 py-3.5">
                          <div className={`font-semibold ${v.idle_days !== null && v.idle_days !== undefined ? "text-amber-300" : "text-slate-400 italic"}`}>
                            {v.idle_exposure_label}
                          </div>
                          <div className="text-[10px] text-slate-500">{v.daily_cost_label}</div>
                        </td>
                        <td className="px-3 py-3.5">
                          {getRiskBadge(v.idle_risk_level)}
                        </td>
                        <td className="px-3 py-3.5 text-right">
                          <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                            v.data_status === "RECENT" || v.data_status === "LIVE"
                              ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                              : "bg-slate-800 text-slate-400"
                          }`}>
                            {v.data_status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* ----------------------------------------------------------------- */}
          {/* Alternative Employment Opportunities (Phase 3 + Phase 4)         */}
          {/* ----------------------------------------------------------------- */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
              <div className="flex items-center gap-2">
                <Compass className="h-4 w-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wide">
                  Alternative Employment Candidates
                </h3>
              </div>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
                Phase 3 Matching + Phase 4 Port Validation
              </span>
            </div>

            <div className="p-4">
              <div className="text-xs text-slate-400 mb-3 flex items-center justify-between">
                <span>
                  Querying actual database requirements for vessel candidate feasibility.
                </span>
                <span className="text-[10px] text-slate-500">
                  {analysis?.alternative_candidates?.length || 0} Open Fixture Candidates
                </span>
              </div>

              {loadingAnalysis ? (
                <div className="py-10 text-center text-slate-500 flex flex-col items-center gap-2">
                  <RefreshCw className="h-6 w-6 animate-spin text-cyan-400" />
                  <span className="text-xs">Evaluating technical & berth clearances across global routes...</span>
                </div>
              ) : !analysis?.alternative_candidates || analysis.alternative_candidates.length === 0 ? (
                <div className="py-8 text-center text-slate-500 text-xs">
                  No active cargo requirements found in database.
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-3">
                  {analysis.alternative_candidates.map((cand, idx) => {
                    const isSelected = idx === selectedCandidateIdx;
                    return (
                      <div
                        key={cand.cargo_id}
                        onClick={() => setSelectedCandidateIdx(idx)}
                        className={`p-3.5 rounded-lg border transition-all cursor-pointer ${
                          isSelected
                            ? "bg-slate-800/90 border-cyan-500/60 shadow-md ring-1 ring-cyan-500/30"
                            : "bg-slate-950/40 border-slate-800 hover:bg-slate-800/40"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <div className="text-sm font-semibold text-white flex items-center gap-2">
                              <span>{cand.cargo_name} ({cand.quantity_mt.toLocaleString()} MT)</span>
                              <span className="text-[10px] font-mono text-cyan-400 px-1.5 py-0.2 rounded bg-cyan-950/80 border border-cyan-800">
                                {cand.cargo_id}
                              </span>
                            </div>
                            <div className="text-xs text-slate-300 mt-1 flex items-center gap-1.5">
                              <span className="text-emerald-400 font-medium">{cand.origin_port_name}</span>
                              <ArrowRight className="h-3 w-3 text-slate-500" />
                              <span className="text-blue-400 font-medium">{cand.destination_port_name}</span>
                            </div>
                          </div>

                          <div className="text-right">
                            <span className={`px-2.5 py-0.5 rounded text-xs font-bold ${
                              cand.compatibility_status === "COMPATIBLE"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                : cand.compatibility_status === "PARTIAL"
                                ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                                : cand.compatibility_status === "NOT_COMPATIBLE"
                                ? "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                                : "bg-slate-700 text-slate-300"
                            }`}>
                              {cand.compatibility_status}
                            </span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-3 pt-3 border-t border-slate-800/80 text-[11px]">
                          <div>
                            <span className="text-slate-500 block">Laycan Window:</span>
                            <span className="text-slate-300 font-mono">
                              {cand.laycan_start ? new Date(cand.laycan_start).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "TBD"} –{" "}
                              {cand.laycan_end ? new Date(cand.laycan_end).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "TBD"}
                            </span>
                          </div>

                          <div>
                            <span className="text-slate-500 block">Port Feasibility:</span>
                            <span className={`font-semibold ${
                              cand.origin_port_status === "PASS" && cand.destination_port_status === "PASS"
                                ? "text-emerald-400"
                                : cand.origin_port_status === "FAIL" || cand.destination_port_status === "FAIL"
                                ? "text-rose-400"
                                : "text-amber-400"
                            }`}>
                              Load: {cand.origin_port_status} | Disch: {cand.destination_port_status}
                            </span>
                          </div>

                          <div>
                            <span className="text-slate-500 block">Repositioning:</span>
                            <span className="text-slate-300">
                              {cand.repositioning_distance_nm !== null && cand.repositioning_distance_nm !== undefined ? (
                                <span className="font-mono text-cyan-300">
                                  {cand.repositioning_distance_nm.toLocaleString()} NM
                                </span>
                              ) : (
                                <span className="text-slate-500 italic">UNKNOWN</span>
                              )}
                            </span>
                          </div>

                          <div>
                            <span className="text-slate-500 block">Distance Method:</span>
                            <span className={`text-[10px] font-mono px-1 py-0.5 rounded ${
                              cand.distance_method === "NAUTICAL_CHART"
                                ? "bg-emerald-950/60 text-emerald-300 border border-emerald-800"
                                : cand.distance_method === "SAME_PORT"
                                ? "bg-blue-950 text-blue-300"
                                : "bg-amber-950/60 text-amber-300 border border-amber-800"
                            }`}>
                              {cand.distance_method}
                            </span>
                          </div>
                        </div>

                        {/* Technical validation narratives */}
                        <div className="mt-2 text-[11px] text-slate-400 bg-slate-950/50 p-2 rounded border border-slate-800/60 flex flex-col gap-1">
                          <div>
                            <span className="text-slate-500 font-semibold">Phase 3 Matching: </span>
                            {cand.matching_summary}
                          </div>
                          <div>
                            <span className="text-slate-500 font-semibold">Phase 4 Berths: </span>
                            {cand.port_validation_summary}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Vessel Detail, Timeline & Repositioning Trajectory (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {/* Selected Vessel Intelligence Card */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-start justify-between border-b border-slate-800 pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-white tracking-tight">
                    {timeline?.vessel_name || selectedVesselSummary?.vessel_name || "Select Vessel"}
                  </h3>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-cyan-400">
                    {timeline?.vessel_class || selectedVesselSummary?.vessel_class}
                  </span>
                </div>
                <div className="text-xs text-slate-400 mt-1 flex items-center gap-2">
                  <MapPin className="h-3.5 w-3.5 text-cyan-400" />
                  <span>{timeline?.current_location || selectedVesselSummary?.current_location}</span>
                </div>
              </div>

              <div className="text-right">
                {timeline && getStateBadge(timeline.employment_state)}
                <div className="text-[10px] font-mono text-slate-500 mt-1">
                  {timeline?.data_freshness_label || "SYNTHETIC ESTIMATE"}
                </div>
              </div>
            </div>

            {/* --------------------------------------------------------------- */}
            {/* IDLE COST PANEL (No fake cost)                                 */}
            {/* --------------------------------------------------------------- */}
            <div className="grid grid-cols-3 gap-2.5 p-3 rounded-lg bg-slate-950/70 border border-slate-800/80">
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-semibold block">Idle Duration</span>
                <span className="text-sm font-bold text-amber-400 font-mono">
                  {analysis?.idle_days !== null && analysis?.idle_days !== undefined
                    ? `${analysis.idle_days.toFixed(1)} Days`
                    : "UNKNOWN"}
                </span>
                <span className="text-[9px] text-slate-500 block">Prompt Window</span>
              </div>

              <div>
                <span className="text-[10px] text-slate-400 uppercase font-semibold block">Daily Cost</span>
                <span className="text-sm font-bold text-slate-200 font-mono">
                  {analysis?.daily_vessel_cost
                    ? `$${analysis.daily_vessel_cost.toLocaleString()}/d`
                    : "NOT AVAILABLE"}
                </span>
                <span className="text-[9px] text-slate-500 block">Charter / OPEX</span>
              </div>

              <div>
                <span className="text-[10px] text-slate-400 uppercase font-semibold block">Modeled Cost</span>
                <span className="text-sm font-bold text-rose-400 font-mono">
                  {analysis?.idle_cost !== null && analysis?.idle_cost !== undefined
                    ? `$${analysis.idle_cost.toLocaleString()}`
                    : "UNAVAILABLE"}
                </span>
                <span className="text-[9px] text-slate-500 block">Holding Loss</span>
              </div>
            </div>

            {analysis?.daily_cost_status === "DAILY VESSEL COST: NOT AVAILABLE" && (
              <div className="text-[11px] text-amber-400/90 bg-amber-950/30 p-2 rounded border border-amber-800/40 flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                <span>DAILY VESSEL COST: NOT AVAILABLE. Holding loss cannot be calculated without explicit assumption or verified contract.</span>
              </div>
            )}

            {/* --------------------------------------------------------------- */}
            {/* REPOSITIONING ROUTE TRAJECTORY                                   */}
            {/* --------------------------------------------------------------- */}
            {activeRepositionOption && (
              <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-950/40 space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white uppercase flex items-center gap-1.5">
                    <Compass className="h-3.5 w-3.5 text-cyan-400" />
                    Ballast Repositioning Route
                  </span>
                  {getDeadheadBadge(activeRepositionOption.deadhead_risk)}
                </div>

                <div className="flex items-center justify-between text-xs bg-slate-900 p-2.5 rounded border border-slate-800">
                  <div>
                    <span className="text-[10px] text-slate-500 block">From</span>
                    <span className="text-slate-200 font-semibold">{timeline?.current_location || "Current Position"}</span>
                  </div>
                  <ArrowRight className="h-4 w-4 text-cyan-400" />
                  <div className="text-right">
                    <span className="text-[10px] text-slate-500 block">To Load Port</span>
                    <span className="text-slate-200 font-semibold">{activeRepositionOption.target_port_name}</span>
                  </div>
                </div>

                {/* Trajectory Metrics */}
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="bg-slate-900/60 p-2 rounded border border-slate-800/60">
                    <span className="text-[10px] text-slate-500 block">Distance</span>
                    <span className="font-mono text-cyan-300 font-bold">
                      {activeRepositionOption.distance_nm ? `${activeRepositionOption.distance_nm.toLocaleString()} NM` : "UNAVAILABLE"}
                    </span>
                    <span className="text-[9px] text-slate-400 block truncate" title={activeRepositionOption.distance_method}>
                      {activeRepositionOption.distance_method === "GEODESIC_APPROXIMATION" ? "GEODESIC APPROX" : activeRepositionOption.distance_method}
                    </span>
                  </div>

                  <div className="bg-slate-900/60 p-2 rounded border border-slate-800/60">
                    <span className="text-[10px] text-slate-500 block">Sailing Time</span>
                    <span className="font-mono text-slate-200 font-bold">
                      {activeRepositionOption.sailing_days ? `${activeRepositionOption.sailing_days.toFixed(1)} Days` : "UNAVAILABLE"}
                    </span>
                    <span className="text-[9px] text-slate-500 block">
                      @ {activeRepositionOption.speed_knots || 12.5} kts
                    </span>
                  </div>

                  <div className="bg-slate-900/60 p-2 rounded border border-slate-800/60">
                    <span className="text-[10px] text-slate-500 block">Est. Bunker Cost</span>
                    <span className="font-mono text-sky-300 font-bold">
                      {activeRepositionOption.estimated_bunker_cost
                        ? `$${activeRepositionOption.estimated_bunker_cost.toLocaleString()}`
                        : "UNAVAILABLE"}
                    </span>
                    <span className="text-[9px] text-slate-500 block">VLSFO @ $620</span>
                  </div>
                </div>

                <div className="text-[11px] text-slate-400 bg-slate-900/40 p-2 rounded border border-slate-800/40">
                  <div className="font-medium text-slate-300">{activeRepositionOption.timing_narrative}</div>
                  <div className="text-[10px] text-slate-500 mt-1">{activeRepositionOption.deadhead_narrative}</div>
                </div>
              </div>
            )}

            {/* --------------------------------------------------------------- */}
            {/* Employment Timeline                                             */}
            {/* --------------------------------------------------------------- */}
            <div className="border-t border-slate-800 pt-3">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-white uppercase flex items-center gap-1.5">
                  <Calendar className="h-3.5 w-3.5 text-cyan-400" />
                  Vessel Employment Lifecycle Timeline
                </span>
                <span className="text-[10px] text-slate-500">
                  {timeline?.events?.length || 0} Events Sourced
                </span>
              </div>

              {!timeline?.events || timeline.events.length === 0 ? (
                <div className="text-xs text-slate-500 italic py-3 text-center">
                  No historical or scheduled events recorded for this vessel.
                </div>
              ) : (
                <div className="space-y-3 relative pl-4 border-l border-slate-800">
                  {timeline.events.map((ev, i) => (
                    <div key={ev.id || i} className="relative group">
                      <div className="absolute -left-[21px] top-1.5 w-2.5 h-2.5 rounded-full bg-cyan-400 ring-4 ring-slate-900" />
                      <div className="bg-slate-950/60 border border-slate-800/80 rounded p-2.5 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-white">
                            {ev.event_type.replace("_", " ")}
                          </span>
                          <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded ${
                            ev.status === "COMPLETED" ? "bg-slate-800 text-slate-400" : "bg-emerald-950 text-emerald-400"
                          }`}>
                            {ev.status}
                          </span>
                        </div>

                        <div className="text-slate-300 text-[11px] mt-1">
                          {ev.origin_port_name && <span>From: {ev.origin_port_name} </span>}
                          {ev.destination_port_name && <span>To: {ev.destination_port_name}</span>}
                        </div>

                        <div className="flex items-center justify-between mt-1 text-[10px] text-slate-500">
                          <span>
                            {new Date(ev.event_start).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                            {ev.event_end && ` – ${new Date(ev.event_end).toLocaleDateString("en-US", { month: "short", day: "numeric" })}`}
                          </span>
                          {ev.source_id && <span className="font-mono text-slate-600">{ev.source_id}</span>}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* --------------------------------------------------------------------- */}
      {/* 4. Strategic Repositioning Economics Comparison Table                 */}
      {/* --------------------------------------------------------------------- */}
      {analysis?.economics_comparison && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
            <div className="flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-emerald-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wide">
                Trade-off Economic Comparison: Hold Idle vs Reposition
              </h3>
            </div>
            <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-slate-800 text-amber-300 border border-amber-700/50">
              {analysis.economics_comparison.comparison_status}
            </span>
          </div>

          <div className="p-5 space-y-4">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3">Strategy Option</th>
                    <th className="px-3 py-3">Idle Days</th>
                    <th className="px-3 py-3">Sailing Days</th>
                    <th className="px-3 py-3">Distance</th>
                    <th className="px-3 py-3">Bunker Cost</th>
                    <th className="px-3 py-3">Charter Cost</th>
                    <th className="px-3 py-3">Total Est. Cost</th>
                    <th className="px-3 py-3 text-right">Cost Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {/* WAIT Strategy */}
                  <tr className="bg-slate-950/20 hover:bg-slate-800/30">
                    <td className="px-4 py-3.5 font-semibold text-white">
                      {analysis.economics_comparison.wait_strategy.strategy_name}
                    </td>
                    <td className="px-3 py-3.5 font-mono text-amber-400">
                      {analysis.economics_comparison.wait_strategy.idle_days !== null && analysis.economics_comparison.wait_strategy.idle_days !== undefined
                        ? `${analysis.economics_comparison.wait_strategy.idle_days.toFixed(1)} d`
                        : "UNKNOWN"}
                    </td>
                    <td className="px-3 py-3.5 font-mono text-slate-500">0.0 d</td>
                    <td className="px-3 py-3.5 font-mono text-slate-500">0 NM</td>
                    <td className="px-3 py-3.5 font-mono text-slate-500">$0.00</td>
                    <td className="px-3 py-3.5 font-mono text-slate-300">
                      {analysis.economics_comparison.wait_strategy.daily_cost
                        ? `$${analysis.economics_comparison.wait_strategy.daily_cost.toLocaleString()}/d`
                        : "UNAVAILABLE"}
                    </td>
                    <td className="px-3 py-3.5 font-mono font-bold text-rose-400">
                      {analysis.economics_comparison.wait_strategy.estimated_total_cost
                        ? `$${analysis.economics_comparison.wait_strategy.estimated_total_cost.toLocaleString()}`
                        : "UNAVAILABLE"}
                    </td>
                    <td className="px-3 py-3.5 text-right">
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                        analysis.economics_comparison.wait_strategy.cost_status === "CALCULATED"
                          ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                          : "bg-slate-800 text-slate-400"
                      }`}>
                        {analysis.economics_comparison.wait_strategy.cost_status}
                      </span>
                    </td>
                  </tr>

                  {/* Repositioning Strategies */}
                  {analysis.economics_comparison.repositioning_strategies.map((strat, i) => (
                    <tr key={i} className="hover:bg-slate-800/30">
                      <td className="px-4 py-3.5 font-semibold text-cyan-300">
                        {strat.strategy_name}
                      </td>
                      <td className="px-3 py-3.5 font-mono text-slate-500">0.0 d</td>
                      <td className="px-3 py-3.5 font-mono text-slate-200">
                        {strat.repositioning_days ? `${strat.repositioning_days.toFixed(1)} d` : "UNAVAILABLE"}
                      </td>
                      <td className="px-3 py-3.5 font-mono text-slate-300">
                        {strat.distance_nm ? `${strat.distance_nm.toLocaleString()} NM` : "UNAVAILABLE"}
                      </td>
                      <td className="px-3 py-3.5 font-mono text-sky-300">
                        {strat.bunker_cost ? `$${strat.bunker_cost.toLocaleString()}` : "UNAVAILABLE"}
                      </td>
                      <td className="px-3 py-3.5 font-mono text-slate-300">
                        {strat.daily_cost ? `$${strat.daily_cost.toLocaleString()}/d` : "UNAVAILABLE"}
                      </td>
                      <td className="px-3 py-3.5 font-mono font-bold text-amber-300">
                        {strat.estimated_total_cost ? `$${strat.estimated_total_cost.toLocaleString()}` : "INCOMPLETE"}
                      </td>
                      <td className="px-3 py-3.5 text-right">
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                          strat.cost_status === "CALCULATED"
                            ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                            : "bg-amber-950 text-amber-300 border border-amber-800"
                        }`}>
                          {strat.cost_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Revenue Disclaimer Alert */}
            <div className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-400">
              <ShieldAlert className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-300">Commercial Revenue Integrity: </span>
                {analysis.economics_comparison.revenue_status}
                <div className="mt-1 text-[11px] text-slate-500">
                  {analysis.economics_comparison.recommendation_note}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* 5. Assumptions Configuration Drawer / Modal                           */}
      {/* --------------------------------------------------------------------- */}
      {showConfigDrawer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-lg w-full p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Sliders className="h-4 w-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-white uppercase">Operational Assumptions</h3>
              </div>
              <button
                onClick={() => setShowConfigDrawer(false)}
                className="text-slate-400 hover:text-white transition"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Ballast Speed Assumption (Knots)</label>
                <input
                  type="number"
                  step="0.5"
                  value={speedAssumption}
                  onChange={(e) => setSpeedAssumption(parseFloat(e.target.value) || 12.5)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-white font-mono"
                />
                <span className="text-[10px] text-slate-500 mt-0.5 block">Explicitly labeled as &quot;Speed assumption: X knots&quot; in reports.</span>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Bunker VLSFO Price ($/MT)</label>
                <input
                  type="number"
                  step="10"
                  value={bunkerPrice}
                  onChange={(e) => setBunkerPrice(parseFloat(e.target.value) || 620.0)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-white font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Daily Vessel Charter Rate / OPEX ($/day)</label>
                <input
                  type="number"
                  step="500"
                  value={dailyCostAssumption}
                  onChange={(e) => setDailyCostAssumption(parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-white font-mono"
                />
                <span className="text-[10px] text-slate-500 mt-0.5 block">Used for holding cost calculation. If unset, cost displays as UNAVAILABLE.</span>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Idle Scenario Classification</label>
                <select
                  value={scenarioType}
                  onChange={(e) => setScenarioType(e.target.value as IdleScenarioType)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-white"
                >
                  <option value="EMPLOYMENT_GAP">EMPLOYMENT_GAP (Awaiting fixture)</option>
                  <option value="PORT_DELAY">PORT_DELAY (Berth congestion)</option>
                  <option value="DEMAND_GAP">DEMAND_GAP (Regional shortage)</option>
                  <option value="EARLY_ARRIVAL">EARLY_ARRIVAL (Ahead of laycan)</option>
                </select>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-800">
              <button
                onClick={() => setShowConfigDrawer(false)}
                className="px-3 py-1.5 rounded text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowConfigDrawer(false);
                  handleRerunAnalysis();
                }}
                className="px-4 py-1.5 rounded text-xs font-semibold bg-cyan-600 text-white hover:bg-cyan-500 transition"
              >
                Apply & Recalculate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
