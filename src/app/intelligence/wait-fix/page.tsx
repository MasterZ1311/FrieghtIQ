"use client";

import React, { useState, useEffect, useMemo, Suspense } from "react";
import {
  Clock,
  ShieldAlert,
  Sliders,
  DollarSign,
  TrendingDown,
  TrendingUp,
  Minus,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Ship,
  Anchor,
  FileText,
  Calendar,
  Layers,
  RefreshCw,
  ChevronRight,
  X,
  Info,
  Activity,
  ArrowRight,
  Database,
  BarChart3,
  Scale
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
  Legend,
  ReferenceLine
} from "recharts";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  waitFixApi,
  WaitFixAnalysisResponse,
  WaitFixDecision,
  DecisionConfidence,
  ScenarioItem,
  cargoApi,
  CargoRequirement,
  portsApi,
  Port,
  DataStatusType
} from "@/lib/api";

function WaitVsFixContent() {
  // Cargo requirements & ports
  const [cargoRequirements, setCargoRequirements] = useState<CargoRequirement[]>([]);
  const [ports, setPorts] = useState<Port[]>([]);
  const [selectedReqId, setSelectedReqId] = useState<string>("CR-2026-001");

  // Form parameters
  const [originPort, setOriginPort] = useState<string>("newcastle-au");
  const [destinationPort, setDestinationPort] = useState<string>("paradip-in");
  const [cargoType, setCargoType] = useState<string>("COKING_COAL");
  const [cargoQuantity, setCargoQuantity] = useState<number>(75000);
  const [vesselClass, setVesselClass] = useState<string>("PANAMAX");
  const [decisionHorizonDays, setDecisionHorizonDays] = useState<number>(30);
  const [referenceFixRate, setReferenceFixRate] = useState<number>(24.50);

  // Analysis state
  const [analysis, setAnalysis] = useState<WaitFixAnalysisResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [assumptionsOpen, setAssumptionsOpen] = useState<boolean>(false);

  // Initial load: Ports & Cargo Requirements & Latest Analysis
  useEffect(() => {
    async function init() {
      setLoading(true);
      setError(null);
      try {
        const [portsList, reqsList] = await Promise.all([
          portsApi.getPorts().catch(() => []),
          cargoApi.getRequirements().catch(() => []),
        ]);
        setPorts(portsList);
        setCargoRequirements(reqsList);

        // Try to fetch latest or analyze default
        try {
          const latest = await waitFixApi.getLatest();
          if (latest) {
            setAnalysis(latest);
            if (latest.cargo_request_id) setSelectedReqId(latest.cargo_request_id);
            setOriginPort(latest.origin_port_id);
            setDestinationPort(latest.destination_port_id);
            setCargoQuantity(latest.cargo_quantity);
            setVesselClass(latest.vessel_class);
            setCargoType(latest.cargo_type);
            setReferenceFixRate(latest.assumptions?.reference_fix_rate || 24.50);
            setDecisionHorizonDays(latest.assumptions?.decision_horizon_days || 30);
          }
        } catch {
          // Fallback: analyze default Newcastle -> Paradip 75k MT
          const fallback = await waitFixApi.analyze({
            cargo_request_id: "CR-2026-001",
            origin_port_id: "newcastle-au",
            destination_port_id: "paradip-in",
            cargo_type: "COKING_COAL",
            cargo_quantity: 75000,
            vessel_class: "PANAMAX",
            decision_horizon_days: 30,
            reference_fix_rate: 24.50,
          });
          setAnalysis(fallback);
        }
      } catch (err: any) {
        console.error("Failed to initialize Wait vs Fix", err);
        setError(err.message || "Failed to load timing intelligence.");
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  // Handle cargo requirement selection change
  const handleRequirementChange = (reqId: string) => {
    setSelectedReqId(reqId);
    if (reqId === "CUSTOM") return;

    const req = cargoRequirements.find((r) => r.id === reqId || r.requirement_code === reqId);
    if (req) {
      setOriginPort(req.load_port_id || "newcastle-au");
      setDestinationPort(req.discharge_port_id || "paradip-in");
      setCargoQuantity(req.quantity_mt);
      setCargoType(req.cargo_type);
      if (req.preferred_vessel_classes) {
        const cls = req.preferred_vessel_classes.split(",")[0].trim().toUpperCase();
        setVesselClass(cls);
      }
      if (req.target_freight_usd_pmt) {
        setReferenceFixRate(req.target_freight_usd_pmt);
      }
    }
  };

  // Run or re-run analysis
  const runAnalysis = async () => {
    setAnalyzing(true);
    setError(null);
    try {
      const res = await waitFixApi.analyze({
        cargo_request_id: selectedReqId !== "CUSTOM" ? selectedReqId : undefined,
        origin_port_id: originPort,
        destination_port_id: destinationPort,
        cargo_type: cargoType,
        cargo_quantity: Number(cargoQuantity),
        vessel_class: vesselClass,
        decision_horizon_days: Number(decisionHorizonDays),
        reference_fix_rate: Number(referenceFixRate),
      });
      setAnalysis(res);
    } catch (err: any) {
      console.error("Failed to analyze wait vs fix", err);
      setError(err.message || "Analysis request failed. Verify route compatibility.");
    } finally {
      setAnalyzing(false);
    }
  };

  // Helper styles for decision states
  const getDecisionStyle = (dec?: WaitFixDecision) => {
    switch (dec) {
      case "WAIT":
        return {
          badge: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40",
          accent: "text-emerald-400",
          border: "border-emerald-500/30",
          glow: "shadow-[0_0_25px_rgba(16,185,129,0.15)]",
          label: "WAIT",
          description: "Modeled forward dynamics favor retaining chartering flexibility. Sufficient decision time remains before laycan commitment.",
          icon: Clock,
        };
      case "FIX_NOW":
        return {
          badge: "bg-blue-500/20 text-blue-400 border-blue-500/40",
          accent: "text-blue-400",
          border: "border-blue-500/30",
          glow: "shadow-[0_0_25px_rgba(59,130,246,0.15)]",
          label: "FIX NOW",
          description: "Modeled economics favor prompt commitment. Upward rate risk or narrow decision horizon outweighs postponement option value.",
          icon: CheckCircle2,
        };
      case "MONITOR":
        return {
          badge: "bg-amber-500/20 text-amber-400 border-amber-500/40",
          accent: "text-amber-400",
          border: "border-amber-500/30",
          glow: "shadow-[0_0_25px_rgba(245,158,11,0.15)]",
          label: "MONITOR",
          description: "Modeled delta is within neutral threshold or uncertainty is elevated. Maintain active surveillance without immediate fixing.",
          icon: Activity,
        };
      case "DECISION_WINDOW_EXPIRED":
        return {
          badge: "bg-rose-500/20 text-rose-400 border-rose-500/40",
          accent: "text-rose-400",
          border: "border-rose-500/30",
          glow: "shadow-[0_0_25px_rgba(244,63,94,0.15)]",
          label: "WINDOW EXPIRED",
          description: "Decision horizon has closed (remaining days <= 0). Prompt market execution required; delay is no longer modeled.",
          icon: AlertTriangle,
        };
      case "NOT_EVALUABLE":
        return {
          badge: "bg-red-500/20 text-red-400 border-red-500/40",
          accent: "text-red-400",
          border: "border-red-500/30",
          glow: "shadow-[0_0_25px_rgba(239,68,68,0.15)]",
          label: "NOT EVALUABLE",
          description: "Physical feasibility check failed (e.g. port draft or berth constraint violation). Route cannot accommodate this vessel.",
          icon: AlertTriangle,
        };
      default:
        return {
          badge: "bg-slate-700/50 text-slate-300 border-slate-600",
          accent: "text-slate-300",
          border: "border-slate-700",
          glow: "",
          label: "PENDING",
          description: "Evaluating quantitative freight scenarios...",
          icon: HelpCircle,
        };
    }
  };

  // Helper styles for confidence
  const getConfidenceStyle = (conf?: DecisionConfidence) => {
    switch (conf) {
      case "HIGH":
        return { badge: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30", label: "HIGH CONFIDENCE" };
      case "MEDIUM":
        return { badge: "bg-amber-500/15 text-amber-400 border-amber-500/30", label: "MEDIUM CONFIDENCE" };
      case "LOW":
        return { badge: "bg-rose-500/15 text-rose-400 border-rose-500/30", label: "LOW CONFIDENCE" };
      default:
        return { badge: "bg-slate-700 text-slate-300 border-slate-600", label: "CALCULATING" };
    }
  };

  // Chart data: Scenario fan chart (Spot -> 7d -> 14d -> 30d)
  const chartData = useMemo(() => {
    if (!analysis) return [];
    const spot = analysis.current_freight_rate || 24.50;
    const refFix = analysis.assumptions?.reference_fix_rate || 24.50;
    const p10 = analysis.p10_rate;
    const p50 = analysis.p50_rate;
    const p90 = analysis.p90_rate;

    return [
      {
        horizon: "Spot (Today)",
        days: 0,
        referenceFix: refFix,
        spot: spot,
        p10: spot,
        p50: spot,
        p90: spot,
        expectedWait: spot,
      },
      {
        horizon: "7 Days",
        days: 7,
        referenceFix: refFix,
        p10: Number((spot + (p10 - spot) * 0.35).toFixed(2)),
        p50: Number((spot + (p50 - spot) * 0.35).toFixed(2)),
        p90: Number((spot + (p90 - spot) * 0.35).toFixed(2)),
        expectedWait: Number((spot + (analysis.expected_wait_rate - spot) * 0.35).toFixed(2)),
      },
      {
        horizon: "14 Days",
        days: 14,
        referenceFix: refFix,
        p10: Number((spot + (p10 - spot) * 0.65).toFixed(2)),
        p50: Number((spot + (p50 - spot) * 0.65).toFixed(2)),
        p90: Number((spot + (p90 - spot) * 0.65).toFixed(2)),
        expectedWait: Number((spot + (analysis.expected_wait_rate - spot) * 0.65).toFixed(2)),
      },
      {
        horizon: `${analysis.assumptions?.decision_horizon_days || 30} Days (Horizon)`,
        days: analysis.assumptions?.decision_horizon_days || 30,
        referenceFix: refFix,
        p10: p10,
        p50: p50,
        p90: p90,
        expectedWait: analysis.expected_wait_rate,
      },
    ];
  }, [analysis]);

  const decStyle = getDecisionStyle(analysis?.decision);
  const confStyle = getConfidenceStyle(analysis?.decision_confidence);

  return (
    <div className="space-y-6">
      {/* 1. Header */}
      <PageHeader
        title="WAIT vs FIX DECISION ENGINE"
        description="Quantitative charter-timing intelligence modeling the economic trade-off of prompt fixing versus postponement under market uncertainty."
        status="ACTIVE"
      />

      {/* 2. Strict Synthetic Data Notice */}
      <div className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-4 text-amber-300 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-inner">
        <div className="flex items-start gap-3">
          <ShieldAlert className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-xs px-2 py-0.5 rounded bg-amber-500/20 border border-amber-500/40 text-amber-300 tracking-wider">
                DEMO / SYNTHETIC DATA
              </span>
              <span className="text-xs font-semibold text-amber-200">
                Decision Support Protocol (SIH26006)
              </span>
            </div>
            <p className="text-xs text-amber-300/80 leading-relaxed">
              Modeled freight differences and option valuations are decision-support estimates derived from synthetic Baltic trade-lane indices.
              Not guaranteed savings. Black-76 formulation represents flexibility valuation, not financial derivative commitments.
            </p>
          </div>
        </div>
        <div className="text-xs font-mono text-amber-400/90 whitespace-nowrap pl-8 sm:pl-0">
          Source: {analysis?.assumptions?.dataset_version || "FREIGHT-SYNTH-2026-Q1"}
        </div>
      </div>

      {/* 3. Cargo Requirement & Parameter Selector Bar */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-4 backdrop-blur-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2 text-xs font-bold font-mono text-slate-300 tracking-wider uppercase">
            <Sliders className="h-4 w-4 text-blue-400" />
            <span>CARGO CONTEXT & DECISION HORIZON</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setAssumptionsOpen(true)}
              className="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 text-xs font-medium text-slate-300 hover:text-white hover:border-slate-600 transition-colors flex items-center gap-1.5"
            >
              <Info className="h-3.5 w-3.5 text-blue-400" />
              <span>View Assumptions</span>
            </button>
            <button
              onClick={runAnalysis}
              disabled={analyzing || loading}
              className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-xs font-semibold text-white transition-colors flex items-center gap-1.5 shadow-sm shadow-blue-500/20"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${analyzing ? "animate-spin" : ""}`} />
              <span>{analyzing ? "Evaluating..." : "Run Analysis"}</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4 text-xs">
          {/* Cargo Req */}
          <div>
            <label className="block text-slate-400 font-mono mb-1">Cargo Requirement</label>
            <select
              value={selectedReqId}
              onChange={(e) => handleRequirementChange(e.target.value)}
              className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-2.5 py-2 text-slate-200 focus:outline-none focus:border-blue-500 font-mono text-xs"
            >
              {cargoRequirements.map((r) => (
                <option key={r.id} value={r.requirement_code || r.id}>
                  {r.requirement_code || r.id} — {r.quantity_mt.toLocaleString()} MT ({r.cargo_type})
                </option>
              ))}
              <option value="CUSTOM">Custom Parameters</option>
            </select>
          </div>

          {/* Origin */}
          <div>
            <label className="block text-slate-400 font-mono mb-1">Origin Port</label>
            <select
              value={originPort}
              onChange={(e) => setOriginPort(e.target.value)}
              className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-2.5 py-2 text-slate-200 focus:outline-none focus:border-blue-500 font-mono text-xs"
            >
              {ports.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.country})
                </option>
              ))}
            </select>
          </div>

          {/* Destination */}
          <div>
            <label className="block text-slate-400 font-mono mb-1">Destination Port</label>
            <select
              value={destinationPort}
              onChange={(e) => setDestinationPort(e.target.value)}
              className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-2.5 py-2 text-slate-200 focus:outline-none focus:border-blue-500 font-mono text-xs"
            >
              {ports.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.country})
                </option>
              ))}
            </select>
          </div>

          {/* Vessel Class */}
          <div>
            <label className="block text-slate-400 font-mono mb-1">Vessel Class</label>
            <select
              value={vesselClass}
              onChange={(e) => setVesselClass(e.target.value)}
              className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-2.5 py-2 text-slate-200 focus:outline-none focus:border-blue-500 font-mono text-xs"
            >
              <option value="PANAMAX">Panamax</option>
              <option value="CAPESIZE">Capesize</option>
              <option value="SUPRAMAX">Supramax</option>
              <option value="NEWCASTLEMAX">Newcastlemax (Constraint Demo)</option>
            </select>
          </div>

          {/* Quantity */}
          <div>
            <label className="block text-slate-400 font-mono mb-1">Cargo Quantity (MT)</label>
            <input
              type="number"
              value={cargoQuantity}
              onChange={(e) => setCargoQuantity(Number(e.target.value))}
              step="1000"
              className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-2.5 py-2 text-slate-200 focus:outline-none focus:border-blue-500 font-mono text-xs"
            />
          </div>

          {/* Decision Horizon & Fix Rate */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-slate-400 font-mono">Horizon (Days)</label>
              <span className="text-blue-400 font-mono font-bold">{decisionHorizonDays}d</span>
            </div>
            <input
              type="range"
              min="3"
              max="60"
              value={decisionHorizonDays}
              onChange={(e) => setDecisionHorizonDays(Number(e.target.value))}
              className="w-full accent-blue-500 cursor-pointer h-2 bg-slate-800 rounded-lg"
            />
          </div>
        </div>

        {error && (
          <div className="p-3 rounded-lg border border-rose-500/30 bg-rose-950/20 text-rose-300 text-xs flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* 4. MAIN DECISION HERO CARD */}
      <div className={`rounded-xl border ${decStyle.border} bg-slate-900/80 p-6 backdrop-blur-md transition-all ${decStyle.glow}`}>
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          {/* Left: Decision Badge & Description */}
          <div className="space-y-3 max-w-2xl">
            <div className="flex flex-wrap items-center gap-3">
              <span className={`px-4 py-1.5 rounded-lg border font-mono font-black text-sm tracking-wider flex items-center gap-2 ${decStyle.badge}`}>
                <decStyle.icon className="h-4 w-4" />
                {decStyle.label}
              </span>
              <span className={`px-3 py-1 rounded-md border font-mono text-xs font-semibold ${confStyle.badge}`}>
                {confStyle.label}
              </span>
              <span className="text-xs font-mono text-slate-400 flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5 text-slate-500" />
                Remaining Window:{" "}
                <strong className="text-slate-200">
                  {analysis?.remaining_days !== undefined ? `${analysis.remaining_days} days` : "--"}
                </strong>
              </span>
            </div>

            <p className="text-sm text-slate-300 leading-relaxed font-normal">
              {decStyle.description}
            </p>

            {analysis?.decision_deadline && (
              <div className="text-xs font-mono text-slate-400">
                Latest modeled decision date:{" "}
                <span className="text-blue-400 font-semibold">{analysis.decision_deadline}</span>
                <span className="text-slate-500 ml-2">(Before laycan exposure limit)</span>
              </div>
            )}
          </div>

          {/* Right: Key Economic Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 border-t lg:border-t-0 lg:border-l border-slate-800 pt-4 lg:pt-0 lg:pl-6 shrink-0">
            <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
              <span className="block text-[11px] font-mono text-slate-400 uppercase">Modeled Difference</span>
              <span className={`text-lg font-bold font-mono ${
                (analysis?.expected_modeled_difference || 0) > 0 ? "text-emerald-400" :
                (analysis?.expected_modeled_difference || 0) < 0 ? "text-rose-400" : "text-slate-300"
              }`}>
                {(analysis?.expected_modeled_difference || 0) > 0 ? "+" : ""}
                ${Math.abs(analysis?.expected_modeled_difference || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </span>
              <span className="block text-[10px] text-slate-500 mt-0.5">
                {(analysis?.expected_modeled_difference || 0) >= 0 ? "Favors waiting" : "Favors prompt fixing"}
              </span>
            </div>

            <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
              <span className="block text-[11px] font-mono text-slate-400 uppercase">Expected Wait Rate</span>
              <span className="text-lg font-bold font-mono text-slate-100">
                ${analysis?.expected_wait_rate?.toFixed(2) || "--"}
              </span>
              <span className="block text-[10px] text-slate-500 mt-0.5">
                vs ${analysis?.assumptions?.reference_fix_rate?.toFixed(2) || "--"} fix
              </span>
            </div>

            <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3 col-span-2 sm:col-span-1">
              <span className="block text-[11px] font-mono text-slate-400 uppercase">Total Freight Impact</span>
              <span className="text-lg font-bold font-mono text-blue-400">
                ${analysis?.expected_wait_cost ? (analysis.expected_wait_cost / 1_000_000).toFixed(2) : "--"}M
              </span>
              <span className="block text-[10px] text-slate-500 mt-0.5">
                Total modeled cost
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 5. TWO-COLUMN GRID: Charts & Option Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Rate Scenario Fan Chart & Economics Table */}
        <div className="lg:col-span-2 space-y-6">
          {/* Rate Scenario Chart */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h3 className="text-sm font-bold font-mono text-slate-200 flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-blue-400" />
                  RATE SCENARIO TRAJECTORY (P10 / P50 / P90)
                </h3>
                <p className="text-xs text-slate-400">
                  Forward freight curve projection across decision window with Swanson-Megill uncertainty envelope
                </p>
              </div>
              <div className="flex items-center gap-3 text-xs font-mono">
                <span className="flex items-center gap-1.5 text-slate-300">
                  <span className="w-2.5 h-0.5 bg-blue-400 inline-block" /> Central (P50)
                </span>
                <span className="flex items-center gap-1.5 text-slate-400">
                  <span className="w-2.5 h-0.5 bg-emerald-400 inline-block" /> Low (P10)
                </span>
                <span className="flex items-center gap-1.5 text-slate-400">
                  <span className="w-2.5 h-0.5 bg-rose-400 inline-block" /> High (P90)
                </span>
              </div>
            </div>

            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="horizon" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis
                    stroke="#64748b"
                    tick={{ fontSize: 11 }}
                    domain={['auto', 'auto']}
                    unit=" $/MT"
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px", fontSize: "12px" }}
                    formatter={(value: any, name: any) => {
                      if (name === "referenceFix") return [`$${Number(value).toFixed(2)}/MT`, "Reference Fix"];
                      if (name === "p50") return [`$${Number(value).toFixed(2)}/MT`, "Central Forecast (P50)"];
                      if (name === "p10") return [`$${Number(value).toFixed(2)}/MT`, "Low Scenario (P10)"];
                      if (name === "p90") return [`$${Number(value).toFixed(2)}/MT`, "High Scenario (P90)"];
                      if (name === "expectedWait") return [`$${Number(value).toFixed(2)}/MT`, "Weighted Wait Rate"];
                      return [value, String(name || "")];
                    }}
                  />
                  <ReferenceLine
                    y={analysis?.assumptions?.reference_fix_rate || 24.50}
                    stroke="#f59e0b"
                    strokeDasharray="4 4"
                    label={{ value: "Current Fix Rate", fill: "#f59e0b", fontSize: 10, position: "insideTopRight" }}
                  />
                  {/* Uncertainty spread area */}
                  <Area
                    type="monotone"
                    dataKey="p90"
                    stroke="none"
                    fill="#3b82f6"
                    fillOpacity={0.08}
                  />
                  <Line
                    type="monotone"
                    dataKey="p10"
                    stroke="#10b981"
                    strokeWidth={1.5}
                    strokeDasharray="4 2"
                    dot={{ r: 3, fill: "#10b981" }}
                  />
                  <Line
                    type="monotone"
                    dataKey="p50"
                    stroke="#3b82f6"
                    strokeWidth={2.5}
                    dot={{ r: 4, fill: "#3b82f6" }}
                  />
                  <Line
                    type="monotone"
                    dataKey="p90"
                    stroke="#f43f5e"
                    strokeWidth={1.5}
                    strokeDasharray="4 2"
                    dot={{ r: 3, fill: "#f43f5e" }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Scenario Economics Table */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold font-mono text-slate-200 flex items-center gap-2">
                <Scale className="h-4 w-4 text-blue-400" />
                SCENARIO FREIGHT ECONOMICS
              </h3>
              <span className="text-xs font-mono text-slate-400">
                Quantity: <strong className="text-slate-200">{analysis?.cargo_quantity.toLocaleString()} MT</strong>
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs font-mono text-left">
                <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Scenario</th>
                    <th className="py-2.5 px-3">Freight Rate</th>
                    <th className="py-2.5 px-3">Probability</th>
                    <th className="py-2.5 px-3">Freight Cost</th>
                    <th className="py-2.5 px-3 text-right">Difference vs Fix</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {analysis?.scenarios?.map((s) => {
                    const isPositive = s.difference_vs_fix > 0;
                    return (
                      <tr key={s.scenario_name} className="hover:bg-slate-800/40">
                        <td className="py-2.5 px-3 font-semibold text-slate-200 flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${
                            s.scenario_name === "LOW" ? "bg-emerald-400" :
                            s.scenario_name === "CENTRAL" ? "bg-blue-400" : "bg-rose-400"
                          }`} />
                          {s.scenario_name} {s.scenario_name === "LOW" ? "(P10)" : s.scenario_name === "CENTRAL" ? "(P50)" : "(P90)"}
                        </td>
                        <td className="py-2.5 px-3 text-slate-100 font-bold">${s.rate.toFixed(2)}/MT</td>
                        <td className="py-2.5 px-3 text-slate-300">{(s.probability * 100).toFixed(0)}%</td>
                        <td className="py-2.5 px-3 text-slate-200">${s.freight_cost.toLocaleString()}</td>
                        <td className={`py-2.5 px-3 text-right font-bold ${
                          isPositive ? "text-emerald-400" : s.difference_vs_fix < 0 ? "text-rose-400" : "text-slate-400"
                        }`}>
                          {isPositive ? "+" : ""}${s.difference_vs_fix.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </td>
                      </tr>
                    );
                  })}
                  {/* Weighted Expected Row */}
                  <tr className="bg-slate-950/90 font-bold border-t border-slate-700">
                    <td className="py-3 px-3 text-blue-400">EXPECTED (WEIGHTED)</td>
                    <td className="py-3 px-3 text-blue-400">${analysis?.expected_wait_rate.toFixed(2)}/MT</td>
                    <td className="py-3 px-3 text-slate-400">100%</td>
                    <td className="py-3 px-3 text-blue-400">${analysis?.expected_wait_cost.toLocaleString()}</td>
                    <td className={`py-3 px-3 text-right ${
                      (analysis?.expected_modeled_difference || 0) > 0 ? "text-emerald-400" : "text-rose-400"
                    }`}>
                      {(analysis?.expected_modeled_difference || 0) > 0 ? "+" : ""}$
                      {analysis?.expected_modeled_difference?.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="text-[11px] text-slate-500 font-sans italic">
              *Probabilities utilize extended Swanson-Megill three-point estimation (P10=30%, P50=40%, P90=30%) reflecting bounded forward distributions.
            </p>
          </div>
        </div>

        {/* Right 1 Col: Option Value, Alignment, Quality */}
        <div className="space-y-6">
          {/* Option Value Card */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold font-mono text-slate-200 flex items-center gap-1.5 uppercase">
                <DollarSign className="h-4 w-4 text-emerald-400" />
                WAIT OPTION VALUE
              </span>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                analysis?.option_analysis?.status === "AVAILABLE"
                  ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
                  : "bg-amber-500/15 text-amber-400 border-amber-500/30"
              }`}>
                {analysis?.option_analysis?.status || "PENDING"}
              </span>
            </div>

            {analysis?.option_analysis?.status === "AVAILABLE" ? (
              <div className="space-y-3">
                <div className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800">
                  <span className="block text-[11px] text-slate-400 font-mono">Delay Flexibility Valuation</span>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className="text-2xl font-black font-mono text-emerald-400">
                      ${analysis.option_analysis.option_value_usd?.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </span>
                    <span className="text-xs font-mono text-slate-400">
                      (${analysis.option_analysis.option_value_pmt?.toFixed(2)}/MT)
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed">
                  Estimated economic value of retaining the ability to delay commitment under the current model assumptions.
                </p>

                <div className="space-y-1 text-xs font-mono border-t border-slate-800 pt-2 text-slate-400">
                  <div className="flex justify-between py-0.5">
                    <span>Methodology:</span>
                    <span className="text-slate-200">{analysis.option_analysis.methodology}</span>
                  </div>
                  <div className="flex justify-between py-0.5">
                    <span>Implied Volatility (&sigma;):</span>
                    <span className="text-slate-200">
                      {analysis.option_analysis.parameters?.volatility
                        ? `${(analysis.option_analysis.parameters.volatility * 100).toFixed(1)}% p.a.`
                        : "28.0%"}
                    </span>
                  </div>
                  <div className="flex justify-between py-0.5">
                    <span>Discount Rate (r):</span>
                    <span className="text-slate-200">
                      {analysis.option_analysis.parameters?.discount_rate
                        ? `${(analysis.option_analysis.parameters.discount_rate * 100).toFixed(1)}%`
                        : "5.0%"}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 space-y-2 text-center">
                <AlertTriangle className="h-6 w-6 text-amber-400 mx-auto" />
                <span className="block text-xs font-mono font-bold text-amber-300">OPTION VALUE UNAVAILABLE</span>
                <p className="text-xs text-slate-400">
                  {analysis?.option_analysis?.rationale || "Required parameter inputs (decision window or volatility) are outside evaluation bounds."}
                </p>
              </div>
            )}
          </div>

          {/* Forecast x Regime Card */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-3">
            <h4 className="text-xs font-bold font-mono text-slate-200 flex items-center gap-1.5 uppercase">
              <Activity className="h-4 w-4 text-blue-400" />
              FORECAST &times; REGIME ALIGNMENT
            </h4>

            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="block text-[10px] text-slate-400">Forecast Slope</span>
                <span className="text-xs font-bold text-slate-200 mt-0.5 block">
                  {analysis?.p50_rate && analysis?.current_freight_rate
                    ? analysis.p50_rate < analysis.current_freight_rate
                      ? "SOFTENING (-)"
                      : "FIRMING (+)"
                    : "NEUTRAL"}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="block text-[10px] text-slate-400">Market Regime</span>
                <span className="text-xs font-bold text-amber-400 mt-0.5 block">
                  {analysis?.assumptions?.regime_model?.includes("BEAR") ? "BEAR" : "NEUTRAL / MIXED"}
                </span>
              </div>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400">Signal Relationship:</span>
              <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-blue-500/15 text-blue-400 border border-blue-500/30">
                {analysis?.forecast_regime_alignment || "ALIGNED"}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
              Signal alignment serves as supporting contextual evidence, not as a standalone automated recommendation.
            </p>
          </div>

          {/* Decision Data Quality Card */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold font-mono text-slate-200 flex items-center gap-1.5 uppercase">
                <Database className="h-4 w-4 text-emerald-400" />
                DECISION DATA QUALITY
              </h4>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-bold">
                {analysis?.data_quality?.overall_quality || "HIGH"} QUALITY
              </span>
            </div>

            <div className="space-y-1.5 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Forecast Data</span>
                <span className="text-emerald-400">{analysis?.data_quality?.forecast_data || "AVAILABLE"}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Regime Intelligence</span>
                <span className="text-emerald-400">{analysis?.data_quality?.regime_data || "AVAILABLE"}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Port Feasibility</span>
                <span className="text-emerald-400">{analysis?.data_quality?.port_feasibility || "PASS"}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Vessel Feasibility</span>
                <span className="text-emerald-400">{analysis?.data_quality?.vessel_feasibility || "AVAILABLE"}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Reference Fix Rate</span>
                <span className="text-emerald-400">{analysis?.data_quality?.reference_fix_rate || "AVAILABLE"}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 6. EXPLANATION PANELS: Why this result? & What could change this? */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Why this result? */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-3">
          <h3 className="text-sm font-bold font-mono text-slate-200 flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            WHY THIS RESULT?
          </h3>
          <p className="text-xs text-slate-400">
            Primary quantitative evidence driving the {analysis?.decision} recommendation:
          </p>
          <ul className="space-y-2 text-xs text-slate-300">
            {analysis?.why_this_result?.map((point, idx) => (
              <li key={idx} className="flex items-start gap-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/70">
                <ArrowRight className="h-3.5 w-3.5 text-blue-400 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{point}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* What could change this? */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-3">
          <h3 className="text-sm font-bold font-mono text-slate-200 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-400" />
            WHAT COULD CHANGE THIS?
          </h3>
          <p className="text-xs text-slate-400">
            Market catalysts and sensitivity triggers that would invert the posture:
          </p>
          <ul className="space-y-2 text-xs text-slate-300">
            {analysis?.what_could_change_this?.map((point, idx) => (
              <li key={idx} className="flex items-start gap-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/70">
                <ChevronRight className="h-3.5 w-3.5 text-amber-400 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{point}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* 7. ASSUMPTIONS DRAWER / MODAL */}
      {assumptionsOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-xl bg-slate-900 border-l border-slate-800 h-full overflow-y-auto p-6 space-y-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2 text-sm font-bold font-mono text-slate-200">
                <FileText className="h-4 w-4 text-blue-400" />
                <span>MODEL ASSUMPTIONS & METHODOLOGY</span>
              </div>
              <button
                onClick={() => setAssumptionsOpen(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Core parameters */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold font-mono text-slate-300 uppercase tracking-wider">
                Economic & Market Parameters
              </h4>
              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-400 block text-[11px]">Current Freight Rate (S)</span>
                  <span className="text-slate-100 font-bold text-sm mt-0.5 block">
                    ${analysis?.assumptions?.current_freight_rate?.toFixed(2)} / MT
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-400 block text-[11px]">Reference Fix Rate (K)</span>
                  <span className="text-slate-100 font-bold text-sm mt-0.5 block">
                    ${analysis?.assumptions?.reference_fix_rate?.toFixed(2)} / MT
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-400 block text-[11px]">Annualized Volatility (&sigma;)</span>
                  <span className="text-slate-100 font-bold text-sm mt-0.5 block">
                    {((analysis?.assumptions?.historical_volatility_annualized || 0.28) * 100).toFixed(1)}% p.a.
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-400 block text-[11px]">Annual Discount Rate (r)</span>
                  <span className="text-slate-100 font-bold text-sm mt-0.5 block">
                    {((analysis?.assumptions?.discount_rate_annual || 0.05) * 100).toFixed(1)}% p.a.
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-400 block text-[11px]">Decision Window (T)</span>
                  <span className="text-slate-100 font-bold text-sm mt-0.5 block">
                    {analysis?.assumptions?.decision_horizon_days} Days
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-400 block text-[11px]">Remaining Days</span>
                  <span className="text-slate-100 font-bold text-sm mt-0.5 block">
                    {analysis?.assumptions?.remaining_days} Days
                  </span>
                </div>
              </div>
            </div>

            {/* Model Provenance */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold font-mono text-slate-300 uppercase tracking-wider">
                Model & Data Provenance
              </h4>
              <div className="space-y-2 text-xs font-mono bg-slate-950 p-4 rounded-lg border border-slate-800">
                <div className="flex justify-between py-1 border-b border-slate-800/70">
                  <span className="text-slate-400">Forecasting Model:</span>
                  <span className="text-slate-200">{analysis?.assumptions?.forecast_model || "TFT-v1.0.0"}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/70">
                  <span className="text-slate-400">Market Regime Model:</span>
                  <span className="text-slate-200">{analysis?.assumptions?.regime_model || "HMM-Gaussian-v1.0.0"}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/70">
                  <span className="text-slate-400">Dataset Version:</span>
                  <span className="text-slate-200">{analysis?.assumptions?.dataset_version || "FREIGHT-SYNTH-2026-Q1"}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Data Integrity Status:</span>
                  <span className="text-amber-400">{analysis?.assumptions?.data_status || "SYNTHETIC"}</span>
                </div>
              </div>
            </div>

            {/* Mathematical Formulations */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold font-mono text-slate-300 uppercase tracking-wider">
                Mathematical Foundations
              </h4>
              <div className="space-y-3 text-xs text-slate-300">
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-[11px] space-y-1">
                  <div className="text-blue-400 font-bold">1. Scenario Expected Rate</div>
                  <div>E[Rate] = (0.30 &times; P10) + (0.40 &times; P50) + (0.30 &times; P90)</div>
                  <div className="text-slate-500 italic">Extended Swanson-Megill 3-point approximation</div>
                </div>

                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-[11px] space-y-1">
                  <div className="text-emerald-400 font-bold">2. Modeled Freight Economics</div>
                  <div>Expected Wait Cost = E[Rate] &times; Cargo Quantity</div>
                  <div>Current Fix Cost = Reference Fix Rate &times; Cargo Quantity</div>
                  <div>Modeled Difference = Current Fix Cost - Expected Wait Cost</div>
                </div>

                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-[11px] space-y-1">
                  <div className="text-amber-400 font-bold">3. Black-76 Postponement Flexibility</div>
                  <div>Option Value = e^(-rT) &times; [K &times; N(-d2) - S &times; N(-d1)]</div>
                  <div className="text-slate-500 italic">Timing option value of postponement; not a derivative promise</div>
                </div>
              </div>
            </div>

            <div className="pt-2">
              <button
                onClick={() => setAssumptionsOpen(false)}
                className="w-full py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors"
              >
                Close Assumptions
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function WaitVsFixPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-slate-500 font-mono text-xs">Loading timing intelligence engine...</div>}>
      <WaitVsFixContent />
    </Suspense>
  );
}
