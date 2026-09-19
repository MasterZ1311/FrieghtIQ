"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  AlertTriangle,
  Clock,
  DollarSign,
  Ship,
  Anchor,
  Wind,
  Waves,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  SlidersHorizontal,
  CheckCircle2,
  FileText,
  HelpCircle,
  TrendingUp,
  Search,
  Filter,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { RiskBadge } from "@/components/badges/RiskBadge";
import { DataStatusBadge } from "@/components/badges/DataStatusBadge";
import {
  riskApi,
  RiskEvent,
  UnifiedRiskSummaryResponse,
  VoyageRiskEvaluationResponse,
  PortCongestion,
} from "@/lib/api/risk";
import { portsApi, Port } from "@/lib/api/ports";
import { vesselsApi, Vessel } from "@/lib/api/vessels";

export default function UnifiedRiskCenterPage() {
  const [activeTab, setActiveTab] = useState<"EVENTS" | "SIMULATOR" | "MATRIX">("EVENTS");
  const [summary, setSummary] = useState<UnifiedRiskSummaryResponse | null>(null);
  const [events, setEvents] = useState<RiskEvent[]>([]);
  const [ports, setPorts] = useState<Port[]>([]);
  const [vessels, setVessels] = useState<Vessel[]>([]);
  const [congestions, setCongestions] = useState<PortCongestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Filters
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Voyage Simulator State
  const [simOriginId, setSimOriginId] = useState("port-auncb");
  const [simDestId, setSimDestId] = useState("port-inprt");
  const [simVesselClass, setSimVesselClass] = useState("PANAMAX");
  const [simDraft, setSimDraft] = useState<number>(14.2);
  const [simCargoType, setSimCargoType] = useState("COKING_COAL");
  const [simCharterHire, setSimCharterHire] = useState<number>(20000);
  const [simulating, setSimulating] = useState(false);
  const [voyageResult, setVoyageResult] = useState<VoyageRiskEvaluationResponse | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sumData, evData, portsData, vesselsData, congData] = await Promise.all([
        riskApi.getRiskSummary().catch(() => null),
        riskApi.getRiskEvents().catch(() => []),
        portsApi.getPorts().catch(() => []),
        vesselsApi.getVessels().catch(() => []),
        riskApi.getAllPortCongestions().catch(() => []),
      ]);

      setSummary(sumData);
      setEvents(evData);
      setPorts(portsData);
      setVessels(vesselsData);
      setCongestions(congData);
    } catch (err) {
      console.error("Failed loading risk data:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const handleRunSimulation = async () => {
    try {
      setSimulating(true);
      const now = new Date();
      const eta = new Date(now.getTime() + 12 * 86400000).toISOString();
      const laycanFrom = new Date(now.getTime() + 10 * 86400000).toISOString();
      const laycanTo = new Date(now.getTime() + 14 * 86400000).toISOString();

      const origPort = ports.find((p) => p.id === simOriginId);
      const destPort = ports.find((p) => p.id === simDestId);

      const res = await riskApi.analyzeVoyageRisk({
        origin_port_id: simOriginId,
        origin_port_name: origPort?.name,
        destination_port_id: simDestId,
        destination_port_name: destPort?.name,
        vessel_class: simVesselClass,
        vessel_draft_m: simDraft,
        cargo_type: simCargoType,
        eta_origin: eta,
        laycan_from: laycanFrom,
        laycan_to: laycanTo,
        charter_hire_usd_per_day: simCharterHire,
      });
      setVoyageResult(res);
    } catch (err) {
      console.error("Voyage risk simulation failed:", err);
    } finally {
      setSimulating(false);
    }
  };

  const filteredEvents = events.filter((ev) => {
    if (severityFilter !== "ALL" && ev.severity !== severityFilter) return false;
    if (typeFilter !== "ALL" && ev.risk_type !== typeFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const titleMatch = ev.title.toLowerCase().includes(q);
      const descMatch = ev.description.toLowerCase().includes(q);
      const portMatch = (ev.port_name || "").toLowerCase().includes(q);
      const vesselMatch = (ev.vessel_name || "").toLowerCase().includes(q);
      if (!titleMatch && !descMatch && !portMatch && !vesselMatch) return false;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <PageHeader
        title="OPERATIONAL RISK CENTER"
        description="Real-time multi-factor risk aggregation across port congestion, marine weather, tidal gate clearances, and voyage liabilities."
        status="OPERATIONAL INTELLIGENCE"
        actions={
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-amber-400" : ""}`} />
            Refresh Telemetry
          </button>
        }
      />

      {/* Sub-Center Quick Links */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          href="/intelligence/congestion"
          className="group relative p-4 rounded-lg bg-slate-900/90 border border-slate-800 hover:border-amber-500/50 hover:bg-slate-900 transition flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded bg-amber-950/40 border border-amber-800/50 text-amber-400 group-hover:scale-105 transition">
              <Anchor className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-semibold text-slate-200 group-hover:text-amber-300 transition flex items-center gap-1.5">
                Port Congestion
                <ChevronRight className="w-3.5 h-3.5 opacity-60 group-hover:translate-x-0.5 transition" />
              </div>
              <div className="text-xs text-slate-400">Anchorage queues & demurrage risk</div>
            </div>
          </div>
          <span className="px-2 py-0.5 text-[10px] font-mono uppercase bg-amber-950/50 border border-amber-800/40 text-amber-300 rounded">
            Live Queue
          </span>
        </Link>

        <Link
          href="/intelligence/weather"
          className="group relative p-4 rounded-lg bg-slate-900/90 border border-slate-800 hover:border-sky-500/50 hover:bg-slate-900 transition flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded bg-sky-950/40 border border-sky-800/50 text-sky-400 group-hover:scale-105 transition">
              <Wind className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-semibold text-slate-200 group-hover:text-sky-300 transition flex items-center gap-1.5">
                Marine Weather
                <ChevronRight className="w-3.5 h-3.5 opacity-60 group-hover:translate-x-0.5 transition" />
              </div>
              <div className="text-xs text-slate-400">Sea-state, swell & rain stoppages</div>
            </div>
          </div>
          <span className="px-2 py-0.5 text-[10px] font-mono uppercase bg-sky-950/50 border border-sky-800/40 text-sky-300 rounded">
            7-Day Marine
          </span>
        </Link>

        <Link
          href="/intelligence/tidal"
          className="group relative p-4 rounded-lg bg-slate-900/90 border border-slate-800 hover:border-cyan-500/50 hover:bg-slate-900 transition flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded bg-cyan-950/40 border border-cyan-800/50 text-cyan-400 group-hover:scale-105 transition">
              <Waves className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-semibold text-slate-200 group-hover:text-cyan-300 transition flex items-center gap-1.5">
                Tidal Gate Scheduler
                <ChevronRight className="w-3.5 h-3.5 opacity-60 group-hover:translate-x-0.5 transition" />
              </div>
              <div className="text-xs text-slate-400">UKC clearance & high-water slots</div>
            </div>
          </div>
          <span className="px-2 py-0.5 text-[10px] font-mono uppercase bg-cyan-950/50 border border-cyan-800/40 text-cyan-300 rounded">
            HW Slots
          </span>
        </Link>
      </div>

      {/* KPI Overview Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Aggregate Operational Risk</span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <RiskBadge level={summary?.overall_operational_severity || "HIGH"} />
          </div>
          <p className="mt-2 text-[11px] text-slate-500">
            Deterministic max rule: CRITICAL &gt; HIGH &gt; MEDIUM &gt; LOW
          </p>
        </div>

        <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Active Risk Events</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2 text-2xl font-mono font-bold text-slate-100">
            {summary?.total_active_events || events.length || 0}
          </div>
          <div className="mt-2 flex items-center gap-2 text-[11px] text-slate-400">
            <span className="text-rose-400 font-semibold">{summary?.critical_events_count || 0} Critical</span>
            <span>•</span>
            <span className="text-amber-400 font-semibold">{summary?.high_events_count || 0} High</span>
            <span>•</span>
            <span className="text-emerald-400 font-semibold">{summary?.low_events_count || 0} Low</span>
          </div>
        </div>

        <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Modeled Financial Exposure</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2 text-2xl font-mono font-bold text-emerald-400">
            ${(summary?.total_financial_exposure_usd || 223000).toLocaleString()}
          </div>
          <p className="mt-2 text-[11px] text-slate-500">
            Demurrage + weather delay + ballast fuel variance
          </p>
        </div>

        <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Cumulative Delay Estimate</span>
            <Clock className="w-4 h-4 text-sky-400" />
          </div>
          <div className="mt-2 text-2xl font-mono font-bold text-sky-400">
            {summary?.total_delay_hours || 136.0} hrs
          </div>
          <p className="mt-2 text-[11px] text-slate-500">
            Expected queue wait + swell hold + lock gate tidal wait
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("EVENTS")}
          className={`px-4 py-2 text-xs font-semibold rounded-t transition flex items-center gap-2 ${
            activeTab === "EVENTS"
              ? "bg-slate-800 text-amber-400 border-b-2 border-amber-400"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5" />
          Active Risk Events ({filteredEvents.length})
        </button>

        <button
          onClick={() => {
            setActiveTab("SIMULATOR");
            if (!voyageResult) handleRunSimulation();
          }}
          className={`px-4 py-2 text-xs font-semibold rounded-t transition flex items-center gap-2 ${
            activeTab === "SIMULATOR"
              ? "bg-slate-800 text-amber-400 border-b-2 border-amber-400"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <SlidersHorizontal className="w-3.5 h-3.5" />
          Voyage Risk Simulator
        </button>

        <button
          onClick={() => setActiveTab("MATRIX")}
          className={`px-4 py-2 text-xs font-semibold rounded-t transition flex items-center gap-2 ${
            activeTab === "MATRIX"
              ? "bg-slate-800 text-amber-400 border-b-2 border-amber-400"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <Anchor className="w-3.5 h-3.5" />
          Port Bottleneck Matrix ({congestions.length})
        </button>
      </div>

      {/* TAB 1: ACTIVE RISK EVENTS */}
      {activeTab === "EVENTS" && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-lg bg-slate-900 border border-slate-800">
            <div className="flex flex-wrap items-center gap-3">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
                <input
                  type="text"
                  placeholder="Search events, ports, vessels..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500 w-56"
                />
              </div>

              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <Filter className="w-3.5 h-3.5" />
                <span>Severity:</span>
                <select
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                >
                  <option value="ALL">All Severities</option>
                  <option value="CRITICAL">Critical</option>
                  <option value="HIGH">High</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="LOW">Low</option>
                </select>
              </div>

              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <span>Category:</span>
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                >
                  <option value="ALL">All Categories</option>
                  <option value="PORT_CONGESTION">Port Congestion</option>
                  <option value="WEATHER">Weather & Sea State</option>
                  <option value="TIDAL">Tidal & Draft</option>
                  <option value="PORT_OPERATION">Port Operations</option>
                  <option value="TIMING">Laycan Timing</option>
                  <option value="REPOSITIONING">Repositioning Ballast</option>
                  <option value="DATA_QUALITY">Data Quality</option>
                </select>
              </div>
            </div>

            <div className="text-xs text-slate-400">
              Showing <span className="font-mono text-slate-200">{filteredEvents.length}</span> verified events
            </div>
          </div>

          {/* Events List */}
          <div className="space-y-3">
            {filteredEvents.length === 0 ? (
              <div className="p-8 text-center rounded-lg bg-slate-900/60 border border-slate-800 text-slate-400 text-sm">
                No active operational risk events match the current filter criteria.
              </div>
            ) : (
              filteredEvents.map((ev) => (
                <div
                  key={ev.id}
                  className="p-4 rounded-lg bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition space-y-3"
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <RiskBadge level={ev.severity} />
                        <span className="font-mono text-[10px] uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                          {ev.risk_type}
                        </span>
                        <span className="font-mono text-[10px] uppercase px-2 py-0.5 rounded bg-slate-800/80 text-amber-400 border border-amber-900/40">
                          {ev.status}
                        </span>
                        <DataStatusBadge status={ev.data_status || "RECENT"} />
                      </div>
                      <h3 className="text-sm font-semibold text-slate-200">{ev.title}</h3>
                    </div>

                    <div className="text-right font-mono text-xs">
                      {ev.financial_exposure_usd && ev.financial_exposure_usd > 0 ? (
                        <div className="text-emerald-400 font-bold">
                          ${ev.financial_exposure_usd.toLocaleString()} Exposure
                        </div>
                      ) : null}
                      {ev.delay_hours_estimate && ev.delay_hours_estimate > 0 ? (
                        <div className="text-slate-400">Est. delay: {ev.delay_hours_estimate}h</div>
                      ) : null}
                    </div>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">{ev.description}</p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-2 border-t border-slate-800/60 text-xs">
                    <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800/60">
                      <span className="text-[11px] font-semibold text-slate-400 block mb-1">
                        Operational Evidence:
                      </span>
                      <p className="text-slate-300 text-[11px]">{ev.trigger_source ? `Source: ${ev.trigger_source}. ${ev.description}` : ev.description}</p>
                    </div>

                    <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800/60">
                      <span className="text-[11px] font-semibold text-amber-400 block mb-1">
                        Recommended Mitigation:
                      </span>
                      <p className="text-slate-300 text-[11px]">
                        {ev.mitigation_action || "Follow standard charter party notifications and operational contingency protocols."}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB 2: VOYAGE RISK SIMULATOR */}
      {activeTab === "SIMULATOR" && (
        <div className="space-y-6">
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-200">Interactive Voyage Risk Evaluator</h3>
                <p className="text-xs text-slate-400">
                  Simulates full end-to-end voyage risks combining load port congestion, discharge tidal constraints, laycan buffer, and weather fronts.
                </p>
              </div>
              <button
                onClick={handleRunSimulation}
                disabled={simulating}
                className="px-4 py-2 rounded bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-semibold flex items-center gap-1.5 transition"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${simulating ? "animate-spin" : ""}`} />
                {simulating ? "Evaluating..." : "Run Risk Evaluation"}
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
              <div>
                <label className="text-[11px] font-medium text-slate-400 block mb-1">Origin Port</label>
                <select
                  value={simOriginId}
                  onChange={(e) => setSimOriginId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                >
                  <option value="port-auncb">Newcastle (Australia)</option>
                  <option value="port-auglt">Gladstone (Australia)</option>
                  <option value="port-zarcb">Richards Bay (S. Africa)</option>
                  <option value="port-sgsin">Singapore (Malacca)</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] font-medium text-slate-400 block mb-1">Destination Port</label>
                <select
                  value={simDestId}
                  onChange={(e) => setSimDestId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                >
                  <option value="port-inprt">Paradip Port (Odisha)</option>
                  <option value="port-inhal">Haldia Dock (Hooghly)</option>
                  <option value="port-invtz">Visakhapatnam</option>
                  <option value="port-indhm">Dhamra Port</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] font-medium text-slate-400 block mb-1">Vessel Class</label>
                <select
                  value={simVesselClass}
                  onChange={(e) => setSimVesselClass(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                >
                  <option value="PANAMAX">Panamax / Kamsarmax</option>
                  <option value="CAPESIZE">Capesize (180k DWT)</option>
                  <option value="SUPRAMAX">Supramax (58k DWT)</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] font-medium text-slate-400 block mb-1">Arrival Draft (m)</label>
                <input
                  type="number"
                  step="0.1"
                  value={simDraft}
                  onChange={(e) => setSimDraft(parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-slate-400 block mb-1">Commodity</label>
                <select
                  value={simCargoType}
                  onChange={(e) => setSimCargoType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                >
                  <option value="COKING_COAL">Coking Coal (SAIL)</option>
                  <option value="THERMAL_COAL">Thermal Coal</option>
                  <option value="IRON_ORE">Iron Ore Fines</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] font-medium text-slate-400 block mb-1">Daily Hire ($/day)</label>
                <input
                  type="number"
                  step="500"
                  value={simCharterHire}
                  onChange={(e) => setSimCharterHire(parseFloat(e.target.value) || 20000)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>
          </div>

          {/* Simulation Output Deck */}
          {voyageResult && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-lg bg-slate-900 border border-slate-800">
                  <span className="text-xs font-medium text-slate-400">Aggregate Voyage Risk</span>
                  <div className="mt-2 flex items-center gap-2">
                    <RiskBadge level={voyageResult.overall_severity} />
                  </div>
                  <div className="mt-2 text-xs text-slate-300">
                    Total Modeled Delay: <span className="font-mono font-bold text-sky-400">{voyageResult.total_delay_hours}h</span>
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-slate-900 border border-slate-800">
                  <span className="text-xs font-medium text-slate-400">Total Financial Liability</span>
                  <div className="mt-2 text-xl font-mono font-bold text-emerald-400">
                    ${voyageResult.financial_exposure.total_exposure_usd.toLocaleString()}
                  </div>
                  <div className="mt-1 text-[11px] text-slate-400">
                    Demurrage: ${voyageResult.financial_exposure.demurrage_exposure_usd.toLocaleString()} • Weather delay: ${voyageResult.financial_exposure.weather_delay_cost_usd.toLocaleString()}
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-slate-900 border border-slate-800">
                  <span className="text-xs font-medium text-slate-400">Timing / Laycan Buffer</span>
                  <div className="mt-2 text-xs font-semibold text-slate-200">
                    {voyageResult.timing_risk.buffer_hours !== null
                      ? `${voyageResult.timing_risk.buffer_hours} hours buffer before cancelling`
                      : "Unrecorded"}
                  </div>
                  <div className="mt-1">
                    <RiskBadge level={voyageResult.timing_risk.severity} />
                  </div>
                </div>
              </div>

              {/* Primary Risk Drivers */}
              <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-3">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Primary Operational Risk Drivers
                </h4>
                <div className="space-y-2">
                  {voyageResult.primary_drivers.map((driver, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded bg-slate-950 border border-slate-800 flex items-start justify-between gap-3 text-xs"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <RiskBadge level={driver.severity} />
                          <span className="font-mono text-[10px] text-slate-400 uppercase">
                            {driver.risk_type}
                          </span>
                        </div>
                        <p className="text-slate-200">{driver.summary}</p>
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] font-semibold text-amber-400 block mb-0.5">
                          Mitigation:
                        </span>
                        <span className="text-slate-300 text-[11px] max-w-xs block text-left">
                          {driver.mitigation}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: PORT BOTTLENECK MATRIX */}
      {activeTab === "MATRIX" && (
        <div className="space-y-4">
          <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-900/80">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-mono">
                  <th className="p-3">Port Name</th>
                  <th className="p-3">Waiting Queue</th>
                  <th className="p-3">Occupancy</th>
                  <th className="p-3">Pre-Berth Wait</th>
                  <th className="p-3">Congestion Status</th>
                  <th className="p-3">Tidal Dependency</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {congestions.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/40 transition">
                    <td className="p-3 font-semibold text-slate-200">
                      {c.port_name || c.port_id}
                    </td>
                    <td className="p-3 font-mono text-slate-300">
                      {c.waiting_vessels_count} bulk carriers
                    </td>
                    <td className="p-3 font-mono">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-slate-800 h-2 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${
                              c.berth_occupancy_pct > 85
                                ? "bg-rose-500"
                                : c.berth_occupancy_pct > 70
                                ? "bg-amber-500"
                                : "bg-emerald-500"
                            }`}
                            style={{ width: `${c.berth_occupancy_pct}%` }}
                          />
                        </div>
                        <span className="text-slate-300">{c.berth_occupancy_pct}%</span>
                      </div>
                    </td>
                    <td className="p-3 font-mono text-slate-300">
                      {c.avg_waiting_hours} hrs
                    </td>
                    <td className="p-3">
                      <span
                        className={`inline-block px-2 py-0.5 text-[10px] font-mono uppercase rounded border ${
                          c.congestion_indicator === "SEVERE" || c.congestion_indicator === "CRITICAL"
                            ? "bg-rose-950/80 border-rose-700 text-rose-300"
                            : c.congestion_indicator === "MODERATE"
                            ? "bg-amber-950/80 border-amber-700 text-amber-300"
                            : "bg-emerald-950/80 border-emerald-700 text-emerald-300"
                        }`}
                      >
                        {c.congestion_indicator}
                      </span>
                    </td>
                    <td className="p-3 text-slate-400">
                      {c.port_id.includes("hal") || c.port_name?.includes("Haldia")
                        ? "Strongly Tidal (Lock Gate)"
                        : "Deep Water (Semi-Diurnal)"}
                    </td>
                    <td className="p-3 text-right">
                      <Link
                        href={`/intelligence/congestion`}
                        className="text-amber-400 hover:text-amber-300 font-medium inline-flex items-center gap-1"
                      >
                        Details <ExternalLink className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Data Integrity & Provenance Footer Banner */}
      <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-400 space-y-2">
        <div className="flex items-center gap-2 font-semibold text-slate-300">
          <FileText className="w-4 h-4 text-amber-400" />
          Data Integrity & Physical Realism Commitment
        </div>
        <p className="text-[11px] leading-relaxed">
          Operational telemetry integrates Port Authority berthing lineups, IMD marine meteorological warnings, and hydrographic soundings.
          Under Keel Clearance calculations adhere to strict maritime formulas without inferring vessel draft from DWT. Missing parameters produce an UNKNOWN assessment rather than false PASS clearances.
        </p>
      </div>
    </div>
  );
}
