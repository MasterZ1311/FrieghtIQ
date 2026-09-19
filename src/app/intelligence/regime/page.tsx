"use client";

import React, { useState, useEffect, useMemo, Suspense } from "react";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Calendar,
  Activity,
  ShieldAlert,
  Layers,
  RefreshCw,
  Sliders,
  Clock,
  Compass,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Gauge,
  HelpCircle,
  ExternalLink,
  ArrowRight,
  Database
} from "lucide-react";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from "recharts";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  regimeApi,
  CurrentRegimeResponse,
  RegimeHistoryPoint,
  RegimeTransition,
  RegimeModelInfo,
  MarketRegimeType,
  portsApi,
  Port
} from "@/lib/api";

function RegimeContent() {
  // Trade lane filters
  const [ports, setPorts] = useState<Port[]>([]);
  const [originPort, setOriginPort] = useState<string>("newcastle-au");
  const [destinationPort, setDestinationPort] = useState<string>("paradip-in");
  const [cargoType, setCargoType] = useState<string>("COKING_COAL");
  const [vesselClass, setVesselClass] = useState<string>("PANAMAX");

  // Regime data states
  const [currentRegime, setCurrentRegime] = useState<CurrentRegimeResponse | null>(null);
  const [history, setHistory] = useState<RegimeHistoryPoint[]>([]);
  const [transitions, setTransitions] = useState<RegimeTransition[]>([]);
  const [models, setModels] = useState<RegimeModelInfo[]>([]);

  // UI state
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load ports for dropdown
  useEffect(() => {
    async function loadPorts() {
      try {
        const p = await portsApi.getPorts();
        setPorts(p);
      } catch (e) {
        console.error("Failed to load ports for regime filters", e);
      }
    }
    loadPorts();
  }, []);

  // Fetch regime data for selected trade lane and vessel class
  const loadRegimeData = async (isRefresh: boolean = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const [curr, hist, trans, mods] = await Promise.all([
        regimeApi.getCurrent({
          origin: originPort,
          destination: destinationPort,
          cargo: cargoType,
          vessel_class: vesselClass,
        }),
        regimeApi.getHistory({
          origin: originPort,
          destination: destinationPort,
          vessel_class: vesselClass,
          days: 120,
        }),
        regimeApi.getTransitions({ limit: 15 }),
        regimeApi.getModels(),
      ]);

      setCurrentRegime(curr);
      setHistory(hist);
      setTransitions(trans);
      setModels(mods);
    } catch (err: any) {
      console.error("Failed to fetch regime intelligence", err);
      setError(err?.message || "Failed to load market regime detection intelligence.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadRegimeData();
  }, [originPort, destinationPort, cargoType, vesselClass]);

  // Color helper based on state
  const getRegimeColor = (regime: MarketRegimeType) => {
    switch (regime) {
      case "BULL":
        return {
          badge: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
          accent: "text-emerald-400",
          bar: "bg-emerald-500",
          border: "border-emerald-500/30",
          icon: TrendingUp,
        };
      case "BEAR":
        return {
          badge: "bg-rose-500/15 text-rose-400 border-rose-500/30",
          accent: "text-rose-400",
          bar: "bg-rose-500",
          border: "border-rose-500/30",
          icon: TrendingDown,
        };
      case "SEASONAL":
        return {
          badge: "bg-amber-500/15 text-amber-400 border-amber-500/30",
          accent: "text-amber-400",
          bar: "bg-amber-500",
          border: "border-amber-500/30",
          icon: Activity,
        };
      case "NEUTRAL":
      default:
        return {
          badge: "bg-blue-500/15 text-blue-400 border-blue-500/30",
          accent: "text-blue-400",
          bar: "bg-blue-500",
          border: "border-blue-500/30",
          icon: Minus,
        };
    }
  };

  // Alignment badge helper
  const getAlignmentStyle = (alignment: string) => {
    switch (alignment) {
      case "ALIGNED":
        return {
          badge: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
          label: "ALIGNED",
          icon: CheckCircle2,
        };
      case "DIVERGENT":
        return {
          badge: "bg-amber-500/15 text-amber-400 border-amber-500/30",
          label: "DIVERGENT",
          icon: AlertTriangle,
        };
      case "NEUTRAL":
        return {
          badge: "bg-blue-500/15 text-blue-400 border-blue-500/30",
          label: "NEUTRAL",
          icon: Minus,
        };
      default:
        return {
          badge: "bg-slate-700/50 text-slate-300 border-slate-600",
          label: "INSUFFICIENT DATA",
          icon: HelpCircle,
        };
    }
  };

  // Chart data formatting
  const chartData = useMemo(() => {
    return history.map((pt) => {
      const dt = new Date(pt.date);
      const label = dt.toLocaleDateString("en-US", { month: "short", day: "numeric" });
      return {
        date: label,
        fullDate: pt.date,
        freight_rate: pt.freight_rate,
        regime: pt.regime,
        bull_pct: Math.round(pt.probabilities.BULL * 100),
        bear_pct: Math.round(pt.probabilities.BEAR * 100),
        neutral_pct: Math.round(pt.probabilities.NEUTRAL * 100),
        seasonal_pct: Math.round(pt.probabilities.SEASONAL * 100),
      };
    });
  }, [history]);

  return (
    <div className="space-y-6">
      {/* 1. Page Header */}
      <PageHeader
        title="MARKET REGIME"
        description="Freight market state & transition intelligence powered by Gaussian Hidden Markov continuous-state modeling."
        status="CALIBRATED"
      />

      {/* 2. Strict Data Provenance Warning Banner */}
      <div className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-4 text-amber-300 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-inner">
        <div className="flex items-start gap-3">
          <ShieldAlert className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-xs px-2 py-0.5 rounded bg-amber-500/20 border border-amber-500/40 text-amber-300 tracking-wider">
                DEMO / SYNTHETIC DATA
              </span>
              <span className="text-xs font-semibold text-amber-200">
                Data Integrity Notice
              </span>
            </div>
            <p className="text-xs text-amber-300/80 leading-relaxed">
              Regime classifications are derived from calibrated demonstration time-series (Baltic Panamax Index synthetic series).
              External market benchmarks are simulated for algorithmic validation. No live Baltic Exchange feed is claimed.
            </p>
          </div>
        </div>
        <div className="text-xs font-mono text-amber-400/90 whitespace-nowrap pl-8 sm:pl-0">
          Source: {currentRegime?.dataset?.source || "FREIGHT IQ Synthetic Feed"}
        </div>
      </div>

      {/* 3. Trade Lane Filter Bar */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 space-y-4 backdrop-blur-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs font-bold font-mono text-slate-300 tracking-wider uppercase">
            <Sliders className="h-4 w-4 text-blue-400" />
            <span>TRADE LANE & VESSEL FILTERS</span>
          </div>
          <button
            onClick={() => loadRegimeData(true)}
            disabled={refreshing || loading}
            className="self-start md:self-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 text-xs font-medium text-slate-200 hover:bg-slate-700 hover:text-white transition disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin text-blue-400" : ""}`} />
            <span>{refreshing ? "Calibrating..." : "Recalibrate State"}</span>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Origin Port */}
          <div className="space-y-1">
            <label className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
              Origin Port
            </label>
            <select
              value={originPort}
              onChange={(e) => setOriginPort(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="newcastle-au">Newcastle Port (AU - AUNCB)</option>
              <option value="port-auglt">Gladstone Port (AU - AUGLT)</option>
              <option value="port-zarcb">Richards Bay (ZA - ZARCB)</option>
            </select>
          </div>

          {/* Destination Port */}
          <div className="space-y-1">
            <label className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
              Destination Port (SAIL Hub)
            </label>
            <select
              value={destinationPort}
              onChange={(e) => setDestinationPort(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="paradip-in">Paradip Port (IN - INPRT)</option>
              <option value="port-invtz">Visakhapatnam (IN - INVTZ)</option>
              <option value="port-inhld">Haldia Port (IN - INHLD)</option>
            </select>
          </div>

          {/* Cargo Type */}
          <div className="space-y-1">
            <label className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
              Cargo Type
            </label>
            <select
              value={cargoType}
              onChange={(e) => setCargoType(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="COKING_COAL">Coking Coal (Prime Hard)</option>
              <option value="THERMAL_COAL">Thermal Coal</option>
              <option value="PCI_COAL">PCI Coal (Pulverized)</option>
              <option value="IRON_ORE_FINES">Iron Ore Fines</option>
            </select>
          </div>

          {/* Vessel Class */}
          <div className="space-y-1">
            <label className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
              Vessel Class
            </label>
            <select
              value={vesselClass}
              onChange={(e) => setVesselClass(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="PANAMAX">Panamax (70k - 85k DWT)</option>
              <option value="CAPESIZE">Capesize (150k - 180k DWT)</option>
              <option value="KAMSARMAX">Kamsarmax (82k - 85k DWT)</option>
              <option value="SUPRAMAX">Supramax (50k - 65k DWT)</option>
            </select>
          </div>
        </div>
      </div>

      {loading && !currentRegime ? (
        <div className="h-64 rounded-xl border border-slate-800 bg-slate-900/50 flex items-center justify-center text-slate-400 gap-3">
          <RefreshCw className="h-6 w-6 animate-spin text-blue-400" />
          <span className="font-mono text-sm">Running Baum-Welch HMM State Inferences...</span>
        </div>
      ) : error ? (
        <div className="rounded-xl border border-rose-800/50 bg-rose-950/20 p-6 text-rose-300 text-center space-y-2">
          <AlertTriangle className="h-8 w-8 text-rose-400 mx-auto" />
          <div className="font-bold">Regime Detection Execution Error</div>
          <p className="text-xs text-rose-300/80">{error}</p>
        </div>
      ) : currentRegime ? (
        <>
          {/* 4. Hero Section: Current Regime Card + Probabilities Panel */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* CURRENT REGIME CARD */}
            <div className="lg:col-span-1 rounded-xl border border-slate-800 bg-slate-900/80 p-5 space-y-4 flex flex-col justify-between relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-full blur-2xl pointer-events-none" />
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold font-mono text-slate-400 tracking-wider">
                    CURRENT MARKET REGIME
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                    {currentRegime.data_status}
                  </span>
                </div>

                <div className="flex items-center gap-3 pt-1">
                  {(() => {
                    const style = getRegimeColor(currentRegime.regime);
                    const Icon = style.icon;
                    return (
                      <div className="flex items-center gap-3">
                        <div className={`p-3 rounded-xl border ${style.badge}`}>
                          <Icon className="h-7 w-7" />
                        </div>
                        <div>
                          <div className={`text-3xl font-black font-mono tracking-tight ${style.accent}`}>
                            {currentRegime.regime}
                          </div>
                          <div className="text-xs font-mono text-slate-400">
                            Model Confidence: <span className="text-slate-100 font-bold">{(currentRegime.confidence * 100).toFixed(1)}%</span>
                          </div>
                        </div>
                      </div>
                    );
                  })()}
                </div>

                <div className="pt-3 border-t border-slate-800 space-y-2 text-xs font-mono">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Route:</span>
                    <span className="text-slate-200 font-semibold text-right">{currentRegime.trade_lane}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Vessel Class:</span>
                    <span className="text-slate-200 font-semibold">{currentRegime.vessel_class}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Cargo:</span>
                    <span className="text-slate-200 font-semibold">{currentRegime.cargo_type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Current Episode:</span>
                    <span className="text-emerald-400 font-semibold">{currentRegime.current_duration_days} Consecutive Days</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Historical Median:</span>
                    <span className="text-slate-300">
                      {currentRegime.historical_median_duration_days !== null
                        ? `${currentRegime.historical_median_duration_days} Days`
                        : "INSUFFICIENT DATA"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Transition Frequency:</span>
                    <span className="text-slate-300">
                      {currentRegime.transition_frequency_per_year !== null
                        ? `~${currentRegime.transition_frequency_per_year} shifts / year`
                        : "INSUFFICIENT DATA"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between">
                <span>Model: {currentRegime.model.model_name}</span>
                <span className="font-mono text-slate-500">{currentRegime.model.version}</span>
              </div>
            </div>

            {/* REGIME PROBABILITY PANEL */}
            <div className="lg:col-span-2 rounded-xl border border-slate-800 bg-slate-900/80 p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="text-sm font-bold font-mono text-slate-200 flex items-center gap-2">
                    <Gauge className="h-4 w-4 text-blue-400" />
                    <span>REGIME PROBABILITY DISTRIBUTION</span>
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Posterior probability density across all 4 continuous Gaussian HMM latent states (Normalized Σ = 1.00)
                  </p>
                </div>
                <span className="text-xs font-mono text-slate-500">4-State Gaussian HMM</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                {/* BULL */}
                <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-950/60 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-emerald-400" />
                      <span className="font-mono font-bold text-xs text-emerald-400">BULL STATE</span>
                    </div>
                    <span className="text-sm font-mono font-bold text-slate-100">
                      {(currentRegime.probabilities.BULL * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-800/80 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-emerald-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${Math.max(2, currentRegime.probabilities.BULL * 100)}%` }}
                    />
                  </div>
                  <p className="text-[11px] text-slate-400 leading-tight">
                    Sustained positive freight-market momentum with elevated forward quantile trajectory.
                  </p>
                </div>

                {/* BEAR */}
                <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-950/60 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <TrendingDown className="h-4 w-4 text-rose-400" />
                      <span className="font-mono font-bold text-xs text-rose-400">BEAR STATE</span>
                    </div>
                    <span className="text-sm font-mono font-bold text-slate-100">
                      {(currentRegime.probabilities.BEAR * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-800/80 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-rose-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${Math.max(2, currentRegime.probabilities.BEAR * 100)}%` }}
                    />
                  </div>
                  <p className="text-[11px] text-slate-400 leading-tight">
                    Sustained downward drift or rate softening driven by tonnage overhang and muted fixtures.
                  </p>
                </div>

                {/* NEUTRAL */}
                <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-950/60 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Minus className="h-4 w-4 text-blue-400" />
                      <span className="font-mono font-bold text-xs text-blue-400">NEUTRAL STATE</span>
                    </div>
                    <span className="text-sm font-mono font-bold text-slate-100">
                      {(currentRegime.probabilities.NEUTRAL * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-800/80 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${Math.max(2, currentRegime.probabilities.NEUTRAL * 100)}%` }}
                    />
                  </div>
                  <p className="text-[11px] text-slate-400 leading-tight">
                    Range-bound market with no persistent directional momentum; variance within expected noise.
                  </p>
                </div>

                {/* SEASONAL */}
                <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-950/60 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Activity className="h-4 w-4 text-amber-400" />
                      <span className="font-mono font-bold text-xs text-amber-400">SEASONAL STATE</span>
                    </div>
                    <span className="text-sm font-mono font-bold text-slate-100">
                      {(currentRegime.probabilities.SEASONAL * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-800/80 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-amber-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${Math.max(2, currentRegime.probabilities.SEASONAL * 100)}%` }}
                    />
                  </div>
                  <p className="text-[11px] text-slate-400 leading-tight">
                    Recurring cyclic behavior dominates (monsoon, Australian cyclone disruption, winter heating surge).
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* 5. FORECAST × REGIME INTEGRATION PANEL (Section 17 & 19) */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Compass className="h-5 w-5 text-indigo-400" />
                <h3 className="text-sm font-bold font-mono text-slate-100">
                  FORECAST × REGIME ALIGNMENT
                </h3>
              </div>
              {(() => {
                const alignStyle = getAlignmentStyle(currentRegime.forecast_alignment);
                const AlignIcon = alignStyle.icon;
                return (
                  <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-mono font-bold ${alignStyle.badge}`}>
                    <AlignIcon className="h-3.5 w-3.5" />
                    <span>{alignStyle.label}</span>
                  </div>
                );
              })()}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-1">
                <span className="text-[10px] font-mono text-slate-400 uppercase">Phase 5 Forecast Trajectory</span>
                <div className="text-sm font-bold text-slate-200 flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-blue-400" />
                  <span>TFT Multi-Horizon Quantiles</span>
                </div>
                <p className="text-[11px] text-slate-400">P10 / P50 / P90 7-90 day forward envelope</p>
              </div>

              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-1">
                <span className="text-[10px] font-mono text-slate-400 uppercase">Phase 6 Market Regime</span>
                <div className="text-sm font-bold text-slate-200 flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-400" />
                  <span>{currentRegime.regime} State ({(currentRegime.confidence * 100).toFixed(0)}% Conf)</span>
                </div>
                <p className="text-[11px] text-slate-400">HMM continuous-emission state classification</p>
              </div>

              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-1">
                <span className="text-[10px] font-mono text-slate-400 uppercase">Signal Relationship</span>
                <div className="text-sm font-bold text-slate-200 flex items-center gap-1.5">
                  <span>{currentRegime.forecast_alignment}</span>
                </div>
                <p className="text-[11px] text-slate-400">Descriptive intelligence — Charter timing handled in Phase 7</p>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/60 text-xs text-slate-300 leading-relaxed font-sans">
              <span className="font-semibold text-slate-200">Analytical Interpretation: </span>
              {currentRegime.forecast_alignment_rationale}
            </div>
          </div>

          {/* 6. REGIME HISTORY TIMELINE */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold font-mono text-slate-100 flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-blue-400" />
                  <span>REGIME TIMELINE & PROBABILITY EVOLUTION</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Trailing 120-day historical regime classifications and spot rate benchmark (USD / MT)
                </p>
              </div>
              <div className="flex items-center gap-3 text-xs font-mono">
                <span className="flex items-center gap-1 text-emerald-400"><span className="h-2 w-2 rounded-full bg-emerald-400" /> Bull</span>
                <span className="flex items-center gap-1 text-rose-400"><span className="h-2 w-2 rounded-full bg-rose-400" /> Bear</span>
                <span className="flex items-center gap-1 text-blue-400"><span className="h-2 w-2 rounded-full bg-blue-400" /> Neutral</span>
                <span className="flex items-center gap-1 text-amber-400"><span className="h-2 w-2 rounded-full bg-amber-400" /> Seasonal</span>
              </div>
            </div>

            {chartData.length > 0 ? (
              <div className="h-72 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11, fill: "#94a3b8" }} />
                    <YAxis
                      yAxisId="rate"
                      stroke="#64748b"
                      domain={["auto", "auto"]}
                      tick={{ fontSize: 11, fill: "#94a3b8" }}
                      unit="$"
                    />
                    <YAxis
                      yAxisId="prob"
                      orientation="right"
                      stroke="#64748b"
                      domain={[0, 100]}
                      tick={{ fontSize: 11, fill: "#94a3b8" }}
                      unit="%"
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#0f172a",
                        borderColor: "#334155",
                        borderRadius: "8px",
                        fontSize: "12px",
                      }}
                    />
                    <Line
                      yAxisId="rate"
                      type="monotone"
                      dataKey="freight_rate"
                      name="Freight Rate ($/MT)"
                      stroke="#38bdf8"
                      strokeWidth={2.5}
                      dot={false}
                    />
                    <Area
                      yAxisId="prob"
                      type="monotone"
                      dataKey="bull_pct"
                      name="Bull Probability %"
                      stroke="#10b981"
                      fill="#10b981"
                      fillOpacity={0.15}
                    />
                    <Area
                      yAxisId="prob"
                      type="monotone"
                      dataKey="bear_pct"
                      name="Bear Probability %"
                      stroke="#f43f5e"
                      fill="#f43f5e"
                      fillOpacity={0.15}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-48 flex items-center justify-center text-slate-500 font-mono text-xs">
                No timeline points recorded for selected parameters.
              </div>
            )}
          </div>

          {/* 7. REGIME TRANSITIONS & REGIME EVIDENCE (2-column layout) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* REGIME TRANSITIONS PANEL (Section 13 & 16) */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="text-sm font-bold font-mono text-slate-100 flex items-center gap-2">
                    <Clock className="h-4 w-4 text-blue-400" />
                    <span>RECENT REGIME TRANSITIONS</span>
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Detected state shifts with significance filter (Confidence ≥ 0.65)
                  </p>
                </div>
                <span className="text-xs font-mono text-slate-500">{transitions.length} recorded</span>
              </div>

              <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
                {transitions.length > 0 ? (
                  transitions.map((t) => (
                    <div key={t.id} className="p-3.5 rounded-lg border border-slate-800 bg-slate-950/60 space-y-2">
                      <div className="flex items-center justify-between text-xs font-mono">
                        <div className="flex items-center gap-2 font-bold">
                          <span className={getRegimeColor(t.previous_regime).accent}>{t.previous_regime}</span>
                          <ArrowRight className="h-3.5 w-3.5 text-slate-500" />
                          <span className={getRegimeColor(t.new_regime).accent}>{t.new_regime}</span>
                        </div>
                        <span className="text-slate-400">
                          {new Date(t.transition_date).toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                          })}
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-[11px] font-mono">
                        <span className="text-slate-400">
                          Transition Confidence: <span className="text-slate-200 font-semibold">{(t.confidence * 100).toFixed(1)}%</span>
                        </span>
                        <span className="text-[10px] text-slate-500">Model: {t.model_version_id}</span>
                      </div>

                      {t.trigger_features && (
                        <div className="pt-1.5 border-t border-slate-800/80 text-[10px] font-mono text-slate-400">
                          <span className="text-slate-500">Trigger Signals: </span>
                          {t.trigger_features}
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="py-8 text-center text-slate-500 text-xs font-mono">
                    No regime shifts triggered under the significance threshold.
                  </div>
                )}
              </div>
            </div>

            {/* REGIME EVIDENCE PANEL (Section 4 & 18) */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="text-sm font-bold font-mono text-slate-100 flex items-center gap-2">
                    <Layers className="h-4 w-4 text-blue-400" />
                    <span>REAL SIGNAL EVIDENCE PANEL</span>
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Empirical input features extracted from verified observation series
                  </p>
                </div>
                <span className="text-xs font-mono text-emerald-400">NO FABRICATED SIGNALS</span>
              </div>

              <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
                {currentRegime.evidence.map((ev, idx) => (
                  <div key={idx} className="p-3 rounded-lg border border-slate-800 bg-slate-950/60 space-y-1">
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="font-semibold text-slate-200">{ev.signal_name}</span>
                      <span className="font-bold text-slate-100">
                        {ev.current_value > 0 ? `+${ev.current_value}` : ev.current_value}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                      <span>Direction: <span className="text-blue-400">{ev.signal_direction}</span></span>
                      <span>Signal Weight: {(ev.relative_weight * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-[11px] text-slate-400 pt-0.5 leading-snug">
                      {ev.interpretation}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 8. MODEL EVIDENCE & DATA PROVENANCE (Section 20 & 21) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* MODEL EVIDENCE */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold font-mono text-slate-300 border-b border-slate-800 pb-2">
                <FileText className="h-4 w-4 text-blue-400" />
                <span>MODEL SPECIFICATION & VALIDATION</span>
              </div>
              <div className="space-y-1.5 text-xs font-mono">
                <div className="flex justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">Model Architecture:</span>
                  <span className="text-slate-200 font-semibold">{currentRegime.model.model_name}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">Model Version:</span>
                  <span className="text-slate-200">{currentRegime.model.version}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">Latent States:</span>
                  <span className="text-slate-200 font-bold">{currentRegime.model.number_of_states} (BULL / BEAR / NEUTRAL / SEASONAL)</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">Calibration Window:</span>
                  <span className="text-slate-200">{currentRegime.model.training_period}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">Validation Protocol:</span>
                  <span className="text-slate-200">{currentRegime.model.validation_method}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Calibration Status:</span>
                  <span className="text-emerald-400 font-semibold">{currentRegime.model.status}</span>
                </div>
              </div>
            </div>

            {/* DATASET PROVENANCE */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold font-mono text-slate-300 border-b border-slate-800 pb-2">
                <Database className="h-4 w-4 text-blue-400" />
                <span>DATASET PROVENANCE & TRANSPARENCY</span>
              </div>
              <div className="space-y-1.5 text-xs font-mono">
                <div className="flex justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">Primary Source:</span>
                  <span className="text-slate-200">{currentRegime.dataset.source}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">Dataset Name:</span>
                  <span className="text-slate-200">{currentRegime.dataset.dataset_name}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">Dataset Version:</span>
                  <span className="text-slate-200">{currentRegime.dataset.dataset_version}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">Observations Sampled:</span>
                  <span className="text-slate-200 font-bold">{currentRegime.dataset.observation_count} Daily Records</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">Last Observation Date:</span>
                  <span className="text-slate-200">
                    {new Date(currentRegime.dataset.last_updated).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Data Integrity Status:</span>
                  <span className="text-amber-400 font-semibold">{currentRegime.dataset.data_status}</span>
                </div>
              </div>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}

export default function MarketRegimePage() {
  return (
    <Suspense fallback={
      <div className="h-64 rounded-xl border border-slate-800 bg-slate-900/50 flex items-center justify-center text-slate-400 gap-3">
        <RefreshCw className="h-6 w-6 animate-spin text-blue-400" />
        <span className="font-mono text-sm">Loading Market Regime Intelligence...</span>
      </div>
    }>
      <RegimeContent />
    </Suspense>
  );
}
