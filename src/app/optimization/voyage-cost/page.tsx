"use client";

import React, { useState, useEffect } from "react";
import {
  DollarSign,
  TrendingUp,
  Fuel,
  Anchor,
  Clock,
  AlertTriangle,
  RotateCcw,
  Sliders,
  Layers,
  ShieldCheck,
  Info,
  ChevronRight,
  ArrowUpRight,
  ArrowDownRight,
  Ship,
  Compass,
  CheckCircle2,
  RefreshCw
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatusBadge } from "@/components/badges/StatusBadge";
import { RiskBadge } from "@/components/badges/RiskBadge";
import {
  economicsApi,
  VoyageEconomicsAnalysisResponse,
  VoyageScenarioItem,
  CostComponentItem,
  SensitivityAnalysisResponse
} from "@/lib/api/economics";
import { portsApi, Port } from "@/lib/api/ports";
import { vesselsApi, Vessel } from "@/lib/api/vessels";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend
} from "recharts";

const COMPONENT_COLORS: Record<string, string> = {
  FREIGHT: "#3b82f6", // Blue
  BUNKER: "#f59e0b", // Amber
  PORT_DUES: "#10b981", // Emerald
  BERTH_CHARGES: "#06b6d4", // Cyan
  CARGO_HANDLING: "#38bdf8", // Sky Blue
  PILOTAGE_TOWAGE: "#14b8a6", // Teal
  AGENCY_SUNDRIES: "#64748b", // Slate
  TIME_CHARTER: "#ec4899", // Pink
  TIME_OPPORTUNITY: "#a855f7", // Indigo
  DELAY_DEMURRAGE: "#ef4444", // Red
  REPOSITIONING_BUNKER: "#eab308", // Yellow
  OTHER: "#94a3b8"
};

export default function VoyageEconomicsPage() {
  const [loading, setLoading] = useState<boolean>(true);
  const [recalculating, setRecalculating] = useState<boolean>(false);
  const [analysis, setAnalysis] = useState<VoyageEconomicsAnalysisResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"LEDGER" | "SCENARIOS" | "SENSITIVITY" | "DATA_QUALITY">("LEDGER");

  // Interactive Scenario & Sensitivity Inputs
  const [bunkerPriceSlider, setBunkerPriceSlider] = useState<number>(628.50);
  const [freightRateSlider, setFreightRateSlider] = useState<number>(14.50);
  const [speedSlider, setSpeedSlider] = useState<number>(11.5);
  const [delayHoursSlider, setDelayHoursSlider] = useState<number>(36.0);
  const [cargoQtySlider, setCargoQtySlider] = useState<number>(75000);
  const [dailyHireSlider, setDailyHireSlider] = useState<number>(16200);

  const [sensitivityData, setSensitivityData] = useState<SensitivityAnalysisResponse | null>(null);

  const fetchLatest = async () => {
    try {
      setLoading(true);
      const data = await economicsApi.getLatestAnalysis();
      setAnalysis(data);
      if (data.sensitivity) {
        setSensitivityData(data.sensitivity);
      }
      setBunkerPriceSlider(data.bunker_price_usd_per_mt || 628.50);
      setFreightRateSlider(data.freight_rate_usd_per_mt || 14.50);
      setSpeedSlider(data.operating_speed_knots || 11.5);
      setCargoQtySlider(data.cargo_quantity_mt || 75000);
      setDailyHireSlider(data.daily_charter_rate_usd || 16200);
    } catch (err) {
      console.error("Failed loading voyage economics:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLatest();
  }, []);

  const handleRecalculate = async () => {
    if (!analysis) return;
    try {
      setRecalculating(true);
      const updated = await economicsApi.analyzeVoyage({
        origin_port_id: analysis.origin_port_id,
        destination_port_id: analysis.destination_port_id,
        cargo_quantity_mt: cargoQtySlider,
        cargo_type: analysis.cargo_type,
        vessel_id: analysis.vessel_id,
        custom_speed_knots: speedSlider,
        custom_freight_rate_usd_per_mt: freightRateSlider,
        custom_bunker_price_usd_per_mt: bunkerPriceSlider,
        custom_daily_hire_usd: dailyHireSlider,
        congestion_delay_hours: delayHoursSlider,
        laytime_allowed_hours: 36.0
      });
      setAnalysis(updated);
      if (updated.sensitivity) {
        setSensitivityData(updated.sensitivity);
      }
    } catch (err) {
      console.error("Recalculation error:", err);
    } finally {
      setRecalculating(false);
    }
  };

  const handleReset = () => {
    fetchLatest();
  };

  if (loading || !analysis) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="VOYAGE FINANCIAL ECONOMICS"
          description="Loading voyage cost ledger, bunker fuel burn, port disbursements, and sensitivity models..."
          status="CALCULATING"
        />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 animate-pulse">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 bg-slate-900/60 border border-slate-800 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  // Cost Distribution Data for Donut Chart
  const breakdownChartData = [
    { name: "Freight", value: analysis.freight_cost_usd, color: COMPONENT_COLORS.FREIGHT },
    { name: "Bunker Fuel", value: analysis.bunker_cost_usd, color: COMPONENT_COLORS.BUNKER },
    { name: "Port Dues & Handling", value: analysis.port_cost_usd, color: COMPONENT_COLORS.PORT_DUES },
    { name: "Charter Time Cost", value: analysis.time_cost_usd, color: COMPONENT_COLORS.TIME_CHARTER },
    { name: "Demurrage Exposure", value: analysis.delay_cost_usd, color: COMPONENT_COLORS.DELAY_DEMURRAGE },
    { name: "Repositioning", value: analysis.repositioning_cost_usd, color: COMPONENT_COLORS.REPOSITIONING_BUNKER }
  ].filter((d) => d.value > 0);

  // Scenario Bar Chart Data
  const scenarioChartData = analysis.scenarios.map((sc) => ({
    name: sc.scenario_name,
    Freight: sc.cost_breakdown?.freight || 0,
    Bunker: sc.cost_breakdown?.bunker || 0,
    Port: sc.cost_breakdown?.port || 0,
    Time: sc.cost_breakdown?.time || 0,
    Delay: sc.cost_breakdown?.delay || 0,
    total: sc.total_cost,
    costPerMt: sc.cost_per_mt
  }));

  return (
    <div className="space-y-6 pb-12">
      {/* 1. PAGE HEADER & BENCHMARK BADGES */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <PageHeader
            title="VOYAGE FINANCIAL ECONOMICS"
            description="Itemized voyage financial ledger, bunker consumption curves, port disbursement schedules, expected demurrage exposure, and multidimensional sensitivity analysis."
            status="VERIFIED RECENT"
          />
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchLatest}
            className="flex items-center gap-2 px-3 py-1.5 rounded bg-slate-900 border border-slate-700 text-xs text-slate-300 hover:text-slate-100 hover:border-slate-600 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh Data
          </button>
        </div>
      </div>

      {/* 2. VOYAGE OVERVIEW HEADER STRIP */}
      <div className="p-4 rounded-lg bg-slate-900/90 border border-slate-800 shadow-md backdrop-blur-sm">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 text-xs">
          <div>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">Trade Lane</span>
            <div className="flex items-center gap-1.5 text-slate-100 font-medium">
              <span>{analysis.origin_port_name}</span>
              <ChevronRight className="w-3 h-3 text-slate-500" />
              <span>{analysis.destination_port_name}</span>
            </div>
            <span className="text-[10px] text-slate-500 font-mono">
              {analysis.origin_unlocode} → {analysis.destination_unlocode}
            </span>
          </div>

          <div>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">Nautical Distance</span>
            <div className="text-slate-100 font-mono font-bold text-sm">
              {analysis.distance_nm.toLocaleString()} <span className="text-xs font-normal text-slate-400">NM</span>
            </div>
            <span className="text-[10px] text-emerald-400 font-mono">Standard Charted Routing</span>
          </div>

          <div>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">Nominal Cargo</span>
            <div className="text-slate-100 font-mono font-bold text-sm">
              {analysis.cargo_quantity_mt.toLocaleString()} <span className="text-xs font-normal text-slate-400">MT</span>
            </div>
            <span className="text-[10px] text-slate-400">{analysis.cargo_type.replace(/_/g, " ")}</span>
          </div>

          <div>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">Candidate Vessel</span>
            <div className="text-slate-100 font-medium truncate">
              {analysis.vessel_name}
            </div>
            <span className="text-[10px] text-amber-400 font-mono">{analysis.vessel_class} Class</span>
          </div>

          <div>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">Cruising Speed</span>
            <div className="text-slate-100 font-mono font-bold text-sm">
              {analysis.operating_speed_knots.toFixed(1)} <span className="text-xs font-normal text-slate-400">kts</span>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">Sailing: {analysis.sailing_days.toFixed(1)} days</span>
          </div>

          <div>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">Total Voyage Days</span>
            <div className="text-slate-100 font-mono font-bold text-sm">
              {analysis.total_voyage_days.toFixed(1)} <span className="text-xs font-normal text-slate-400">days</span>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">Sea + Port (4.5d) + Wait</span>
          </div>
        </div>
      </div>

      {/* 3. FINANCIAL KPI DECK */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-lg bg-gradient-to-br from-slate-900 to-blue-950/30 border border-blue-900/40 space-y-1.5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
            <span>Total Delivered Voyage Cost</span>
            <DollarSign className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-mono font-bold text-blue-400">
            ${analysis.total_voyage_cost_usd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <p className="text-[11px] text-slate-400">
            Comprehensive delivered expense including freight, bunker, port & delays.
          </p>
        </div>

        <div className="p-4 rounded-lg bg-gradient-to-br from-slate-900 to-emerald-950/30 border border-emerald-900/40 space-y-1.5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
            <span>Delivered Cost per MT</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-mono font-bold text-emerald-400">
            ${analysis.cost_per_mt_usd.toFixed(2)} <span className="text-xs font-normal text-slate-400">/ MT</span>
          </div>
          <p className="text-[11px] text-slate-400">
            Net delivered cost for {analysis.cargo_quantity_mt.toLocaleString()} MT parcel.
          </p>
        </div>

        <div className="p-4 rounded-lg bg-gradient-to-br from-slate-900 to-amber-950/30 border border-amber-900/40 space-y-1.5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
            <span>Bunker Fuel Expenditure</span>
            <Fuel className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-mono font-bold text-amber-400">
            ${analysis.bunker_cost_usd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
            <span>Rate: ${analysis.bunker_price_usd_per_mt.toFixed(0)}/MT (VLSFO)</span>
            <span>{((analysis.bunker_cost_usd / analysis.total_voyage_cost_usd) * 100).toFixed(1)}% of total</span>
          </div>
        </div>

        <div className="p-4 rounded-lg bg-gradient-to-br from-slate-900 to-rose-950/30 border border-rose-900/40 space-y-1.5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
            <span>Expected Demurrage Exposure</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-mono font-bold text-rose-400">
            ${analysis.delay_cost_usd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
            <span>Net Delay: {analysis.demurrage_hours.toFixed(1)} hrs</span>
            <span>Agreed Laytime: 36h</span>
          </div>
        </div>
      </div>

      {/* 4. NAVIGATION TABS */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("LEDGER")}
          className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-medium transition ${
            activeTab === "LEDGER"
              ? "bg-blue-600/20 text-blue-400 border border-blue-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          Cost Ledger & Breakdown
        </button>

        <button
          onClick={() => setActiveTab("SCENARIOS")}
          className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-medium transition ${
            activeTab === "SCENARIOS"
              ? "bg-blue-600/20 text-blue-400 border border-blue-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
          }`}
        >
          <Compass className="w-3.5 h-3.5" />
          Scenario Matrix (6 Scenarios)
        </button>

        <button
          onClick={() => setActiveTab("SENSITIVITY")}
          className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-medium transition ${
            activeTab === "SENSITIVITY"
              ? "bg-blue-600/20 text-blue-400 border border-blue-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          Interactive Sensitivity Console
        </button>

        <button
          onClick={() => setActiveTab("DATA_QUALITY")}
          className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-medium transition ${
            activeTab === "DATA_QUALITY"
              ? "bg-blue-600/20 text-blue-400 border border-blue-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          Economic Data Quality Scorecard
        </button>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: COST LEDGER & BREAKDOWN */}
      {/* ========================================================================= */}
      {activeTab === "LEDGER" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left 2 Cols: Itemized Financial Table */}
          <div className="lg:col-span-2 space-y-4">
            <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-blue-400" />
                  Itemized Voyage Financial Ledger
                </h3>
                <span className="text-[11px] text-slate-400 font-mono">
                  {analysis.components.length} Ledger Line Items
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="text-[10px] uppercase font-mono text-slate-400 bg-slate-950/60 border-y border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3">Cost Component</th>
                      <th className="py-2.5 px-3">Source & Authority</th>
                      <th className="py-2.5 px-3 text-right">Quantity / Rate</th>
                      <th className="py-2.5 px-3 text-right">Amount (USD)</th>
                      <th className="py-2.5 px-3 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {analysis.components.map((comp, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition">
                        <td className="py-2.5 px-3">
                          <div className="font-semibold text-slate-200">
                            {comp.component_type.replace(/_/g, " ")}
                          </div>
                          {comp.assumption && (
                            <div className="text-[10px] text-slate-400 mt-0.5 max-w-md line-clamp-1">
                              {comp.assumption}
                            </div>
                          )}
                        </td>
                        <td className="py-2.5 px-3 text-slate-400 max-w-xs truncate">
                          {comp.source_id || "Certified Maritime Ledger"}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-300">
                          {comp.quantity ? comp.quantity.toLocaleString(undefined, { maximumFractionDigits: 1 }) : "—"}{" "}
                          {comp.unit && comp.unit !== "USD" ? <span className="text-slate-500 text-[10px]">{comp.unit}</span> : ""}
                          {comp.rate ? <div className="text-[10px] text-slate-500 font-mono">@ ${comp.rate.toFixed(2)}</div> : null}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-100">
                          ${comp.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          <StatusBadge status={comp.data_status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="border-t-2 border-slate-700 bg-slate-950/80 font-semibold text-slate-100">
                    <tr>
                      <td colSpan={3} className="py-3 px-3 text-right font-mono uppercase tracking-wider">
                        Total Delivered Voyage Expenditure:
                      </td>
                      <td className="py-3 px-3 text-right font-mono text-sm text-blue-400">
                        ${analysis.total_voyage_cost_usd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-3 text-center font-mono text-xs text-slate-400">
                        (${analysis.cost_per_mt_usd.toFixed(2)}/MT)
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          </div>

          {/* Right Col: Donut Chart Breakdown */}
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 shadow-sm space-y-3">
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <PieChart className="w-4 h-4 text-emerald-400" />
                Cost Component Distribution
              </h3>

              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={breakdownChartData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={85}
                      paddingAngle={3}
                    >
                      {breakdownChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(val: any) => [`$${Number(val || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}`, "Cost"]}
                      contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", fontSize: "11px" }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Legend List */}
              <div className="space-y-1.5 pt-2 border-t border-slate-800 text-xs font-mono">
                {breakdownChartData.map((item, i) => (
                  <div key={i} className="flex items-center justify-between text-slate-300">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                      <span className="text-[11px]">{item.name}</span>
                    </div>
                    <span className="font-semibold text-slate-200">
                      ${item.value.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      <span className="text-slate-500 ml-1 text-[10px]">
                        ({((item.value / analysis.total_voyage_cost_usd) * 100).toFixed(1)}%)
                      </span>
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Explanatory Note Card */}
            <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-2">
              <div className="flex items-center gap-2 text-slate-300 font-semibold">
                <Info className="w-4 h-4 text-blue-400" />
                Charter Party Economic Notice
              </div>
              <p className="text-slate-400 leading-relaxed text-[11px]">
                {analysis.explanation}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: SCENARIO COMPARISON (6 SCENARIOS) */}
      {/* ========================================================================= */}
      {activeTab === "SCENARIOS" && (
        <div className="space-y-6">
          {/* Top: Multi-Scenario Stacked Bar Chart */}
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <Compass className="w-4 h-4 text-cyan-400" />
                Scenario Economics Comparison (USD Total Expenditure)
              </h3>
              <span className="text-[11px] text-slate-400 font-mono">
                Base vs Low-Cost vs High-Cost vs Delays vs Steaming Modes
              </span>
            </div>

            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={scenarioChartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                  <YAxis
                    stroke="#64748b"
                    fontSize={11}
                    tickFormatter={(val) => `$${(val / 1000000).toFixed(1)}M`}
                  />
                  <Tooltip
                    formatter={(val: any) => [`$${Number(val || 0).toLocaleString()}`, ""]}
                    contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", fontSize: "11px" }}
                  />
                  <Legend wrapperStyle={{ fontSize: "11px" }} />
                  <Bar dataKey="Freight" stackId="a" fill={COMPONENT_COLORS.FREIGHT} />
                  <Bar dataKey="Bunker" stackId="a" fill={COMPONENT_COLORS.BUNKER} />
                  <Bar dataKey="Port" stackId="a" fill={COMPONENT_COLORS.PORT_DUES} />
                  <Bar dataKey="Time" stackId="a" fill={COMPONENT_COLORS.TIME_CHARTER} />
                  <Bar dataKey="Delay" stackId="a" fill={COMPONENT_COLORS.DELAY_DEMURRAGE} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Bottom: Detailed Scenarios Matrix Table */}
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 shadow-sm space-y-3">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-400" />
              Scenario Financial Specifications & Assumptions
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {analysis.scenarios.map((sc, i) => {
                const deltaFromBase = sc.total_cost - analysis.total_voyage_cost_usd;
                const pctFromBase = (deltaFromBase / analysis.total_voyage_cost_usd) * 100;
                const isFavorable = deltaFromBase <= 0;

                return (
                  <div
                    key={i}
                    className={`p-4 rounded-lg border transition ${
                      sc.scenario_name === "BASE"
                        ? "bg-slate-950 border-blue-500/50"
                        : "bg-slate-950/80 border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono font-bold text-xs text-slate-200">
                        {sc.scenario_name}
                      </span>
                      {sc.scenario_name !== "BASE" && (
                        <span
                          className={`flex items-center text-[11px] font-mono font-semibold ${
                            isFavorable ? "text-emerald-400" : "text-rose-400"
                          }`}
                        >
                          {isFavorable ? <ArrowDownRight className="w-3.5 h-3.5" /> : <ArrowUpRight className="w-3.5 h-3.5" />}
                          {pctFromBase >= 0 ? `+${pctFromBase.toFixed(1)}%` : `${pctFromBase.toFixed(1)}%`}
                        </span>
                      )}
                    </div>

                    <div className="text-lg font-mono font-bold text-slate-100">
                      ${sc.total_cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                    <div className="text-[11px] font-mono text-emerald-400 mb-3">
                      ${sc.cost_per_mt.toFixed(2)} / MT
                    </div>

                    <p className="text-[11px] text-slate-300 leading-relaxed mb-3">
                      {sc.description || sc.assumptions}
                    </p>

                    <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/80 text-[10px] font-mono text-slate-400">
                      <div>Speed: <span className="text-slate-200">{sc.speed?.toFixed(1) || "11.5"} kts</span></div>
                      <div>Transit: <span className="text-slate-200">{sc.sailing_days?.toFixed(1) || "21.2"} days</span></div>
                      <div>Bunker: <span className="text-slate-200">${sc.bunker_price?.toFixed(0) || "628"}/MT</span></div>
                      <div>Delay: <span className="text-slate-200">{sc.port_delay_hours?.toFixed(0) || "0"} hrs</span></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: SENSITIVITY CONSOLE */}
      {/* ========================================================================= */}
      {activeTab === "SENSITIVITY" && (
        <div className="space-y-6">
          {/* Controls Deck */}
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-blue-400" />
                  Dynamic Multivariable Sensitivity Sliders
                </h3>
                <p className="text-xs text-slate-400">
                  Adjust operational levers to trigger instantaneous backend model recalculations.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleRecalculate}
                  disabled={recalculating}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow transition disabled:opacity-50"
                >
                  {recalculating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <TrendingUp className="w-3.5 h-3.5" />}
                  Recalculate Economics
                </button>
                <button
                  onClick={handleReset}
                  className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition"
                >
                  Reset
                </button>
              </div>
            </div>

            {/* 6 Interactive Sliders Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pt-2">
              {/* Bunker Price */}
              <div className="space-y-1.5 p-3 rounded bg-slate-950 border border-slate-800">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Bunker Fuel Price (VLSFO)</span>
                  <span className="font-mono font-bold text-amber-400">${bunkerPriceSlider} / MT</span>
                </div>
                <input
                  type="range"
                  min="450"
                  max="900"
                  step="10"
                  value={bunkerPriceSlider}
                  onChange={(e) => setBunkerPriceSlider(Number(e.target.value))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
                />
                <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                  <span>$450/MT</span>
                  <span>$628.50 (Base)</span>
                  <span>$900/MT</span>
                </div>
              </div>

              {/* Freight Rate */}
              <div className="space-y-1.5 p-3 rounded bg-slate-950 border border-slate-800">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Freight Rate (Contract / Spot)</span>
                  <span className="font-mono font-bold text-blue-400">${freightRateSlider.toFixed(2)} / MT</span>
                </div>
                <input
                  type="range"
                  min="9.00"
                  max="24.00"
                  step="0.25"
                  value={freightRateSlider}
                  onChange={(e) => setFreightRateSlider(Number(e.target.value))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
                <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                  <span>$9.00 (P10)</span>
                  <span>$14.50 (Base)</span>
                  <span>$24.00 (P90)</span>
                </div>
              </div>

              {/* Vessel Cruising Speed */}
              <div className="space-y-1.5 p-3 rounded bg-slate-950 border border-slate-800">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Vessel Cruising Speed</span>
                  <span className="font-mono font-bold text-cyan-400">{speedSlider.toFixed(1)} kts</span>
                </div>
                <input
                  type="range"
                  min="9.0"
                  max="14.0"
                  step="0.5"
                  value={speedSlider}
                  onChange={(e) => setSpeedSlider(Number(e.target.value))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                />
                <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                  <span>9.0 kts (Slow)</span>
                  <span>11.5 kts (Eco)</span>
                  <span>14.0 kts (Max)</span>
                </div>
              </div>

              {/* Port Congestion Delay */}
              <div className="space-y-1.5 p-3 rounded bg-slate-950 border border-slate-800">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Port Bottleneck Delay</span>
                  <span className="font-mono font-bold text-rose-400">{delayHoursSlider} hrs</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="120"
                  step="6"
                  value={delayHoursSlider}
                  onChange={(e) => setDelayHoursSlider(Number(e.target.value))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-rose-500"
                />
                <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                  <span>0h</span>
                  <span>36h (Laytime)</span>
                  <span>120h (Heavy)</span>
                </div>
              </div>

              {/* Cargo Quantity */}
              <div className="space-y-1.5 p-3 rounded bg-slate-950 border border-slate-800">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Cargo Parcel Size</span>
                  <span className="font-mono font-bold text-emerald-400">{cargoQtySlider.toLocaleString()} MT</span>
                </div>
                <input
                  type="range"
                  min="50000"
                  max="180000"
                  step="5000"
                  value={cargoQtySlider}
                  onChange={(e) => setCargoQtySlider(Number(e.target.value))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                />
                <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                  <span>50k (Supramax)</span>
                  <span>75k (Panamax)</span>
                  <span>180k (Cape)</span>
                </div>
              </div>

              {/* Daily Charter Hire */}
              <div className="space-y-1.5 p-3 rounded bg-slate-950 border border-slate-800">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Daily Time Charter Rate</span>
                  <span className="font-mono font-bold text-sky-400">${dailyHireSlider.toLocaleString()} / day</span>
                </div>
                <input
                  type="range"
                  min="10000"
                  max="35000"
                  step="1000"
                  value={dailyHireSlider}
                  onChange={(e) => setDailyHireSlider(Number(e.target.value))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
                <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                  <span>$10k/d</span>
                  <span>$16.2k/d (Panamax)</span>
                  <span>$35k/d (Cape)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Dynamic Sensitivity Elasticity Tables */}
          {sensitivityData && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Bunker Sensitivity */}
              <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 shadow-sm space-y-3">
                <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                  <Fuel className="w-3.5 h-3.5 text-amber-400" />
                  Bunker Price Elasticity Curve
                </h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="text-[10px] uppercase font-mono text-slate-400 bg-slate-950/60 border-y border-slate-800">
                      <tr>
                        <th className="py-2 px-2">Shift</th>
                        <th className="py-2 px-2">Price (USD/MT)</th>
                        <th className="py-2 px-2 text-right">Total Cost</th>
                        <th className="py-2 px-2 text-right">Cost / MT</th>
                        <th className="py-2 px-2 text-right">Delta ($)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono">
                      {sensitivityData.bunker_sensitivity.map((row, i) => (
                        <tr key={i} className="hover:bg-slate-800/30">
                          <td className="py-2 px-2 text-slate-300">{row.delta_pct}</td>
                          <td className="py-2 px-2 text-amber-400">${row.bunker_price_usd.toFixed(2)}</td>
                          <td className="py-2 px-2 text-right text-slate-200">${row.total_cost_usd.toLocaleString()}</td>
                          <td className="py-2 px-2 text-right text-emerald-400">${row.cost_per_mt.toFixed(2)}</td>
                          <td className={`py-2 px-2 text-right ${row.delta_total_usd >= 0 ? "text-rose-400" : "text-emerald-400"}`}>
                            {row.delta_total_usd >= 0 ? `+$${row.delta_total_usd.toLocaleString()}` : `-$${Math.abs(row.delta_total_usd).toLocaleString()}`}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Speed Sensitivity */}
              <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 shadow-sm space-y-3">
                <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                  <Ship className="w-3.5 h-3.5 text-cyan-400" />
                  Speed vs Fuel vs Total Cost Trade-off
                </h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="text-[10px] uppercase font-mono text-slate-400 bg-slate-950/60 border-y border-slate-800">
                      <tr>
                        <th className="py-2 px-2">Knots</th>
                        <th className="py-2 px-2">Sailing Days</th>
                        <th className="py-2 px-2 text-right">Bunker Cost</th>
                        <th className="py-2 px-2 text-right">Time Cost</th>
                        <th className="py-2 px-2 text-right">Cost / MT</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono">
                      {sensitivityData.speed_sensitivity.map((row, i) => (
                        <tr key={i} className="hover:bg-slate-800/30">
                          <td className="py-2 px-2 font-bold text-cyan-400">{row.speed_knots.toFixed(1)} kts</td>
                          <td className="py-2 px-2 text-slate-300">{row.sailing_days.toFixed(1)}d</td>
                          <td className="py-2 px-2 text-right text-amber-400">${row.bunker_cost_usd.toLocaleString()}</td>
                          <td className="py-2 px-2 text-right text-sky-400">${row.time_cost_usd.toLocaleString()}</td>
                          <td className="py-2 px-2 text-right font-bold text-emerald-400">${row.cost_per_mt.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 4: ECONOMIC DATA QUALITY SCORECARD */}
      {/* ========================================================================= */}
      {activeTab === "DATA_QUALITY" && (
        <div className="space-y-6">
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Economic Provenance & Data Quality Matrix
                </h3>
                <p className="text-xs text-slate-400">
                  Transparent declaration of data freshness, official sources, and operational assumptions.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Confidence Tier:</span>
                <span className="px-2.5 py-1 rounded text-xs font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                  {analysis.data_quality_report.overall_confidence} CONFIDENCE
                </span>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="text-[10px] uppercase font-mono text-slate-400 bg-slate-950/60 border-y border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Field Name</th>
                    <th className="py-2.5 px-3">Effective Value</th>
                    <th className="py-2.5 px-3">Data Status</th>
                    <th className="py-2.5 px-3">Source & Dataset</th>
                    <th className="py-2.5 px-3">Confidence Impact</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {analysis.data_quality_report.items.map((item, i) => (
                    <tr key={i} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 font-semibold text-slate-200">{item.field}</td>
                      <td className="py-2.5 px-3 font-mono text-slate-100">{item.value}</td>
                      <td className="py-2.5 px-3">
                        <StatusBadge status={item.status as any} />
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">{item.source}</td>
                      <td className="py-2.5 px-3 text-slate-300 text-[11px]">{item.confidence_impact}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="p-3.5 rounded bg-slate-950 border border-slate-800 text-xs space-y-1">
              <div className="font-semibold text-amber-400 flex items-center gap-1.5">
                <Info className="w-4 h-4" />
                Audit & Limitation Notice:
              </div>
              <p className="text-slate-300 leading-relaxed text-[11px]">
                {analysis.data_quality_report.limitations_explanation}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
