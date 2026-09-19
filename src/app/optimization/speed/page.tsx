"use client";

import React, { useState, useEffect } from "react";
import {
  Gauge,
  TrendingUp,
  Fuel,
  Clock,
  DollarSign,
  AlertCircle,
  HelpCircle,
  Ship,
  Info,
  Sliders,
  CheckCircle2,
  RefreshCw,
  ArrowRight,
  ShieldCheck,
  Scale
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatusBadge } from "@/components/badges/StatusBadge";
import {
  economicsApi,
  VoyageEconomicsAnalysisResponse,
  SpeedScenarioItem,
  SpeedBreakEvenResponse,
  SpeedBreakEvenStep
} from "@/lib/api/economics";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area
} from "recharts";

export default function SpeedOptimizationPage() {
  const [loading, setLoading] = useState<boolean>(true);
  const [recalculating, setRecalculating] = useState<boolean>(false);
  const [analysis, setAnalysis] = useState<VoyageEconomicsAnalysisResponse | null>(null);

  // Input states for speed curve adjustments
  const [distanceNm, setDistanceNm] = useState<number>(5850.0);
  const [cargoQuantityMt, setCargoQuantityMt] = useState<number>(75000.0);
  const [baselineSpeedKnots, setBaselineSpeedKnots] = useState<number>(13.0);
  const [baselineConsumptionMtpd, setBaselineConsumptionMtpd] = useState<number>(32.0);
  const [bunkerPriceUsd, setBunkerPriceUsd] = useState<number>(628.50);
  const [dailyCharterRateUsd, setDailyCharterRateUsd] = useState<number>(16200.0);
  const [portCostUsd, setPortCostUsd] = useState<number>(312000.0);

  const [speedScenarios, setSpeedScenarios] = useState<SpeedScenarioItem[]>([]);
  const [breakEven, setBreakEven] = useState<SpeedBreakEvenResponse | null>(null);
  const [canDetermineOptimum, setCanDetermineOptimum] = useState<boolean>(true);
  const [preferredSpeed, setPreferredSpeed] = useState<number | null>(null);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const data = await economicsApi.getLatestAnalysis();
      setAnalysis(data);
      setDistanceNm(data.distance_nm);
      setCargoQuantityMt(data.cargo_quantity_mt);
      setBunkerPriceUsd(data.bunker_price_usd_per_mt || 628.50);
      setDailyCharterRateUsd(data.daily_charter_rate_usd || 16200.0);
      setPortCostUsd(data.port_cost_usd || 312000.0);

      if (data.speed_analysis) {
        setSpeedScenarios(data.speed_analysis.scenarios || []);
        setCanDetermineOptimum(data.speed_analysis.can_determine_optimum);
        setPreferredSpeed(data.speed_analysis.economically_preferred_speed_knots || null);
        if (data.speed_analysis.baseline_speed_knots) setBaselineSpeedKnots(data.speed_analysis.baseline_speed_knots);
        if (data.speed_analysis.baseline_consumption_mtpd) setBaselineConsumptionMtpd(data.speed_analysis.baseline_consumption_mtpd);
      }

      if (data.break_even) {
        setBreakEven(data.break_even);
      }
    } catch (err) {
      console.error("Failed loading speed economics:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const handleRecalculateSpeed = async () => {
    try {
      setRecalculating(true);
      const [speedRes, breakEvenRes] = await Promise.all([
        economicsApi.analyzeSpeed({
          distance_nm: distanceNm,
          cargo_quantity_mt: cargoQuantityMt,
          baseline_speed_knots: baselineSpeedKnots,
          baseline_consumption_mtpd: baselineConsumptionMtpd,
          bunker_price_usd_per_mt: bunkerPriceUsd,
          daily_charter_rate_usd: dailyCharterRateUsd,
          port_cost_usd: portCostUsd,
          candidate_speeds: [8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0]
        }),
        economicsApi.calculateBreakEven({
          distance_nm: distanceNm,
          cargo_quantity_mt: cargoQuantityMt,
          baseline_speed_knots: baselineSpeedKnots,
          baseline_consumption_mtpd: baselineConsumptionMtpd,
          bunker_price_usd_per_mt: bunkerPriceUsd,
          daily_charter_rate_usd: dailyCharterRateUsd
        })
      ]);

      setSpeedScenarios(speedRes.scenarios || []);
      setCanDetermineOptimum(speedRes.can_determine_optimum);
      setPreferredSpeed(speedRes.economically_preferred_speed_knots || null);
      setBreakEven(breakEvenRes);
    } catch (err) {
      console.error("Speed optimization recalculation failed:", err);
    } finally {
      setRecalculating(false);
    }
  };

  if (loading || !analysis) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="VESSEL SPEED OPTIMIZATION"
          description="Loading hydrodynamic cubic fuel curves, virtual arrival synchronization, and break-even speed analysis..."
          status="CALCULATING"
        />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-pulse">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-32 bg-slate-900/60 border border-slate-800 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  // Speed vs Cost Curve Data
  const speedCostChartData = speedScenarios.map((s) => ({
    speed: `${s.speed_knots.toFixed(1)} kts`,
    speedValue: s.speed_knots,
    "Bunker Cost": s.bunker_cost || 0,
    "Time Cost": s.time_cost || 0,
    "Total Voyage Cost": s.total_cost || 0,
    "Cost per MT": s.cost_per_mt || 0
  }));

  // Speed vs Duration & Consumption Chart Data
  const speedDurationChartData = speedScenarios.map((s) => ({
    speed: `${s.speed_knots.toFixed(1)} kts`,
    "Sailing Days": s.sailing_days,
    "Fuel Consumed (MT)": s.fuel_consumed || 0,
    "Fuel Rate (MT/day)": s.fuel_consumption || 0
  }));

  return (
    <div className="space-y-6 pb-12">
      {/* 1. PAGE HEADER & VERDICT STATUS */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <PageHeader
            title="VESSEL SPEED OPTIMIZATION"
            description="Hydrodynamic cubic fuel consumption curves (Admiralty coefficient law), virtual arrival synchronization, and marginal break-even speed analysis."
            status="HYDRODYNAMIC MODEL"
          />
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadInitialData}
            className="flex items-center gap-2 px-3 py-1.5 rounded bg-slate-900 border border-slate-700 text-xs text-slate-300 hover:text-slate-100 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Reset Parameters
          </button>
        </div>
      </div>

      {/* 2. ECONOMIC SPEED VERDICT BANNER */}
      <div className="p-4 rounded-lg bg-gradient-to-r from-slate-900 via-slate-900 to-blue-950/40 border border-slate-800 shadow-md">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                Economic Speed Verdict:
              </span>
              <span
                className={`px-2.5 py-0.5 rounded text-[11px] font-mono font-bold border ${
                  canDetermineOptimum
                    ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                    : "bg-amber-500/20 text-amber-300 border-amber-500/40"
                }`}
              >
                {canDetermineOptimum ? "ECONOMICALLY PREFERRED SPEED IDENTIFIED" : "INSUFFICIENT DATA"}
              </span>
            </div>

            <h3 className="text-base font-semibold text-slate-100">
              {canDetermineOptimum && preferredSpeed
                ? `Economically preferred speed under available assumptions: ${preferredSpeed.toFixed(1)} knots`
                : "Insufficient data to determine economic speed."}
            </h3>

            <p className="text-xs text-slate-400 max-w-2xl leading-relaxed">
              {canDetermineOptimum
                ? `Operating at ${preferredSpeed?.toFixed(1)} knots minimizes combined bunker fuel expenditure and charter hire duration. Speeding up burns exponentially more fuel; slowing down increases daily vessel hire overhead.`
                : "Baseline fuel consumption, bunker price, or daily charter hire rate is unavailable. In accordance with maritime integrity constraints, an optimal speed is not claimed without supporting data."}
            </p>
          </div>

          {/* Key Metrics Chips */}
          <div className="flex flex-wrap lg:flex-nowrap items-center gap-3 font-mono text-xs">
            <div className="p-2.5 rounded bg-slate-950 border border-slate-800 text-center min-w-[120px]">
              <span className="text-[10px] text-slate-400 block mb-0.5">Preferred Knot</span>
              <span className="text-base font-bold text-cyan-400">
                {preferredSpeed ? `${preferredSpeed.toFixed(1)} kts` : "—"}
              </span>
            </div>

            <div className="p-2.5 rounded bg-slate-950 border border-slate-800 text-center min-w-[140px]">
              <span className="text-[10px] text-slate-400 block mb-0.5">Economic Range</span>
              <span className="text-sm font-bold text-emerald-400">
                {breakEven?.economic_speed_range_min && breakEven?.economic_speed_range_max
                  ? `${breakEven.economic_speed_range_min.toFixed(1)} - ${breakEven.economic_speed_range_max.toFixed(1)} kts`
                  : "—"}
              </span>
            </div>

            <div className="p-2.5 rounded bg-slate-950 border border-slate-800 text-center min-w-[130px]">
              <span className="text-[10px] text-slate-400 block mb-0.5">Transit Time</span>
              <span className="text-sm font-bold text-slate-200">
                {preferredSpeed ? `${(distanceNm / preferredSpeed / 24.0).toFixed(1)} days` : "—"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. RECHARTS DUAL CURVES */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Curve 1: Speed vs Total Cost & Bunker Cost */}
        <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              Speed vs Delivered Voyage Cost (USD)
            </h3>
            <span className="text-[10px] font-mono text-slate-400">U-Shaped Cost Minimum</span>
          </div>

          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={speedCostChartData} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="speed" stroke="#64748b" fontSize={11} />
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
                <Line
                  type="monotone"
                  dataKey="Total Voyage Cost"
                  stroke="#3b82f6"
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: "#3b82f6" }}
                  activeDot={{ r: 6 }}
                />
                <Line
                  type="monotone"
                  dataKey="Bunker Cost"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  strokeDasharray="4 4"
                  dot={{ r: 3, fill: "#f59e0b" }}
                />
                <Line
                  type="monotone"
                  dataKey="Time Cost"
                  stroke="#ec4899"
                  strokeWidth={1.5}
                  dot={{ r: 3, fill: "#ec4899" }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="text-[11px] text-slate-400 font-mono">
            * Note inflection point: Beyond the preferred knot, cubic fuel consumption dominates time savings.
          </p>
        </div>

        {/* Curve 2: Speed vs Sailing Days & MT Fuel Consumed */}
        <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <Fuel className="w-4 h-4 text-amber-400" />
              Speed vs Fuel Burn & Sailing Duration
            </h3>
            <span className="text-[10px] font-mono text-slate-400">Admiralty Cubic Curve (F ∝ V³)</span>
          </div>

          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={speedDurationChartData} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="speed" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} yAxisId="left" />
                <YAxis stroke="#64748b" fontSize={11} yAxisId="right" orientation="right" />
                <Tooltip
                  formatter={(val: any) => [`${Number(val || 0).toFixed(1)}`, ""]}
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", fontSize: "11px" }}
                />
                <Legend wrapperStyle={{ fontSize: "11px" }} />
                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey="Fuel Consumed (MT)"
                  stroke="#f59e0b"
                  fill="#f59e0b"
                  fillOpacity={0.15}
                  strokeWidth={2}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="Sailing Days"
                  stroke="#06b6d4"
                  strokeWidth={2}
                  dot={{ r: 3, fill: "#06b6d4" }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <p className="text-[11px] text-slate-400 font-mono">
            * Right axis: Transit days (declining non-linearly). Left axis: Total MT fuel consumed (increasing cubically).
          </p>
        </div>
      </div>

      {/* 4. MARGINAL SPEED BREAK-EVEN ANALYSIS PANEL */}
      {breakEven && breakEven.is_evaluable && (
        <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <Scale className="w-4 h-4 text-sky-400" />
                Marginal Speed Break-Even Substitution Analysis
              </h3>
              <p className="text-xs text-slate-400">
                Marginal fuel cost increase per 0.5 knot acceleration vs time value of charter savings (Daily Hire: ${dailyCharterRateUsd.toLocaleString()}/day).
              </p>
            </div>

            <span className="text-[11px] font-mono text-slate-300">
              Break-Even Point: <span className="text-sky-400 font-bold">{breakEven.break_even_speed_knots?.toFixed(1)} kts</span>
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="text-[10px] uppercase font-mono text-slate-400 bg-slate-950/60 border-y border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Speed Step</th>
                  <th className="py-2.5 px-3 text-right">Time Saved</th>
                  <th className="py-2.5 px-3 text-right">Hire Value Saved</th>
                  <th className="py-2.5 px-3 text-right">Extra Fuel (MT)</th>
                  <th className="py-2.5 px-3 text-right">Extra Bunker Cost</th>
                  <th className="py-2.5 px-3 text-right">Net Marginal Gain</th>
                  <th className="py-2.5 px-3 text-center">Recommendation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {breakEven.marginal_steps.map((step, idx) => {
                  const isPositive = step.net_marginal_gain_usd > 0;
                  return (
                    <tr key={idx} className="hover:bg-slate-800/30 transition">
                      <td className="py-2.5 px-3 font-semibold text-slate-200">
                        {step.from_speed_knots.toFixed(1)} → {step.to_speed_knots.toFixed(1)} kts
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-300">
                        {step.time_saved_hours.toFixed(1)}h ({step.time_saved_days.toFixed(2)}d)
                      </td>
                      <td className="py-2.5 px-3 text-right text-emerald-400">
                        +${step.time_value_saved_usd.toLocaleString()}
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-300">
                        +{step.delta_fuel_consumed_mt.toFixed(1)} MT
                      </td>
                      <td className="py-2.5 px-3 text-right text-amber-400">
                        -${step.delta_bunker_cost_usd.toLocaleString()}
                      </td>
                      <td className={`py-2.5 px-3 text-right font-bold ${isPositive ? "text-emerald-400" : "text-rose-400"}`}>
                        {isPositive ? `+$${step.net_marginal_gain_usd.toLocaleString()}` : `-$${Math.abs(step.net_marginal_gain_usd).toLocaleString()}`}
                      </td>
                      <td className="py-2.5 px-3 text-center">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            isPositive
                              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                              : "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                          }`}
                        >
                          {isPositive ? "ACCELERATE" : "SLOW STEAM"}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 5. CANDIDATE SPEED SCENARIOS EVALUATION TABLE */}
      <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <Gauge className="w-4 h-4 text-cyan-400" />
            Detailed Candidate Speed Scenarios (8.0 to 14.0 Knots)
          </h3>
          <span className="text-[11px] text-slate-400 font-mono">
            {speedScenarios.length} Candidate Profiles Evaluated
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="text-[10px] uppercase font-mono text-slate-400 bg-slate-950/60 border-y border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Speed (Kts)</th>
                <th className="py-2.5 px-3">Sailing Days</th>
                <th className="py-2.5 px-3 text-right">Daily Fuel Burn</th>
                <th className="py-2.5 px-3 text-right">Fuel Consumed</th>
                <th className="py-2.5 px-3 text-right">Bunker Cost</th>
                <th className="py-2.5 px-3 text-right">Time Cost</th>
                <th className="py-2.5 px-3 text-right">Total Voyage Cost</th>
                <th className="py-2.5 px-3 text-right">Cost / MT</th>
                <th className="py-2.5 px-3 text-center">Operational Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {speedScenarios.map((s, idx) => {
                const isPreferred = s.status === "ECONOMICALLY_PREFERRED";
                return (
                  <tr
                    key={idx}
                    className={`transition ${
                      isPreferred
                        ? "bg-emerald-950/20 border-l-2 border-emerald-500"
                        : "hover:bg-slate-800/30"
                    }`}
                  >
                    <td className="py-2.5 px-3 font-bold text-slate-100 flex items-center gap-1.5">
                      {s.speed_knots.toFixed(1)}
                      {isPreferred && (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">{s.sailing_days.toFixed(1)} days</td>
                    <td className="py-2.5 px-3 text-right text-slate-300">
                      {s.fuel_consumption ? `${s.fuel_consumption.toFixed(1)} MT/d` : "—"}
                    </td>
                    <td className="py-2.5 px-3 text-right text-slate-300">
                      {s.fuel_consumed ? `${s.fuel_consumed.toFixed(1)} MT` : "—"}
                    </td>
                    <td className="py-2.5 px-3 text-right text-amber-400">
                      {s.bunker_cost ? `$${s.bunker_cost.toLocaleString()}` : "—"}
                    </td>
                    <td className="py-2.5 px-3 text-right text-sky-400">
                      {s.time_cost ? `$${s.time_cost.toLocaleString()}` : "—"}
                    </td>
                    <td className="py-2.5 px-3 text-right font-bold text-slate-100">
                      {s.total_cost ? `$${s.total_cost.toLocaleString()}` : "—"}
                    </td>
                    <td className="py-2.5 px-3 text-right font-bold text-emerald-400">
                      {s.cost_per_mt ? `$${s.cost_per_mt.toFixed(2)}` : "—"}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          s.status === "ECONOMICALLY_PREFERRED"
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                            : s.status === "SPEED_EXCEEDS_RATING"
                            ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                            : s.status === "SUBOPTIMAL"
                            ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                            : "bg-slate-800 text-slate-300"
                        }`}
                      >
                        {s.status.replace(/_/g, " ")}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 6. HYDRODYNAMIC MODEL ASSUMPTIONS & AUDIT PANEL */}
      <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-3">
        <div className="flex items-center gap-2 text-slate-200 font-semibold">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          Hydrodynamic Physics & Maritime Semantics Declaration
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-slate-400 leading-relaxed text-[11px]">
          <div>
            <strong className="text-slate-300 block mb-1">Admiralty Cubic Law Applied:</strong>
            Fuel consumption rate is modeled via the displacement hull relationship{" "}
            <code className="text-amber-400 font-mono">F(V) = F₀ · (V / V₀)³</code> where baseline consumption is calibrated from verified sea-trial data ({baselineConsumptionMtpd.toFixed(1)} MT/day @ {baselineSpeedKnots.toFixed(1)} kts).
          </div>

          <div>
            <strong className="text-slate-300 block mb-1">Optimization Constraint Boundary:</strong>
            Speeds below 7.5 kts violate minimum engine governor maneuvering safety; speeds exceeding certified maximum continuous rating (14.5 kts) are tagged as physically invalid.
          </div>
        </div>
      </div>
    </div>
  );
}
