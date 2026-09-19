"use client";

import React, { useState, useEffect, useMemo, Suspense } from "react";
import {
  FileCheck,
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
  Scale,
  Percent,
  Compass
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  Cell
} from "recharts";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  contractsApi,
  StrategyComparisonResponse,
  StrategyDetail,
  ContractStrategyType,
  CoverageTierResult,
  BreakEvenAnalysisResult,
  cargoApi,
  CargoRequirement,
  portsApi,
  Port,
  DecisionConfidence
} from "@/lib/api";

function ContractStrategyContent() {
  // Cargo & trade lane parameters
  const [cargoRequirements, setCargoRequirements] = useState<CargoRequirement[]>([]);
  const [ports, setPorts] = useState<Port[]>([]);
  const [selectedReqId, setSelectedReqId] = useState<string>("CR-2026-001");

  const [originPort, setOriginPort] = useState<string>("newcastle-au");
  const [destinationPort, setDestinationPort] = useState<string>("paradip-in");
  const [cargoType, setCargoType] = useState<string>("COKING_COAL");
  const [totalRequirementMt, setTotalRequirementMt] = useState<number>(300000);
  const [parcelSizeMt, setParcelSizeMt] = useState<number>(75000);
  const [vesselClass, setVesselClass] = useState<string>("PANAMAX");
  const [planningHorizonDays, setPlanningHorizonDays] = useState<number>(180);
  const [referenceContractRate, setReferenceContractRate] = useState<number>(24.00);

  // Active strategy view & coverage slider
  const [activeStrategyKey, setActiveStrategyKey] = useState<ContractStrategyType>("MEDIUM_TERM_MULTIPLE_VOYAGE");
  const [coveragePct, setCoveragePct] = useState<number>(75);
  const [coverageSimResult, setCoverageSimResult] = useState<CoverageTierResult | null>(null);

  // Engine state
  const [analysis, setAnalysis] = useState<StrategyComparisonResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [assumptionsOpen, setAssumptionsOpen] = useState<boolean>(false);

  // Initial load
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

        // Run baseline analysis for Newcastle -> Paradip 300k MT
        const res = await contractsApi.analyze({
          cargo_request_id: "CR-2026-001",
          origin_port_id: "newcastle-au",
          destination_port_id: "paradip-in",
          cargo_type: "COKING_COAL",
          total_requirement_mt: 300000,
          parcel_size_mt: 75000,
          vessel_class: "PANAMAX",
          planning_horizon_days: 180,
          reference_contract_rate: 24.00,
        });
        setAnalysis(res);

        // Preload coverage simulation at 75%
        if (res.coverage_spectrum && res.coverage_spectrum.length > 0) {
          const tier75 = res.coverage_spectrum.find((t) => t.coverage_percentage === 75);
          if (tier75) setCoverageSimResult(tier75);
        }
      } catch (err: any) {
        console.error("Failed to initialize contract strategy engine", err);
        setError(err.message || "Failed to load contract strategies.");
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
      setCargoType(req.cargo_type);
      // For multi-voyage simulation, scale single requirement if needed
      setTotalRequirementMt(Math.max(req.quantity_mt * 4, 300000));
      setParcelSizeMt(req.quantity_mt || 75000);
      if (req.preferred_vessel_classes) {
        const cls = req.preferred_vessel_classes.split(",")[0].trim().toUpperCase();
        setVesselClass(cls);
      }
      if (req.target_freight_usd_pmt) {
        setReferenceContractRate(req.target_freight_usd_pmt);
      }
    }
  };

  // Run or re-run analysis
  const runEvaluation = async () => {
    setEvaluating(true);
    setError(null);
    try {
      const res = await contractsApi.analyze({
        cargo_request_id: selectedReqId !== "CUSTOM" ? selectedReqId : undefined,
        origin_port_id: originPort,
        destination_port_id: destinationPort,
        cargo_type: cargoType,
        total_requirement_mt: Number(totalRequirementMt),
        parcel_size_mt: Number(parcelSizeMt),
        vessel_class: vesselClass,
        planning_horizon_days: Number(planningHorizonDays),
        reference_contract_rate: Number(referenceContractRate),
      });
      setAnalysis(res);
      // Update coverage sim
      updateCoverageSimulation(coveragePct, res);
    } catch (err: any) {
      console.error("Failed to evaluate contract strategy", err);
      setError(err.message || "Strategy analysis failed. Verify route compatibility.");
    } finally {
      setEvaluating(false);
    }
  };

  // Handle coverage slider change without full engine reload
  const updateCoverageSimulation = async (pct: number, currentAnalysis?: StrategyComparisonResponse) => {
    setCoveragePct(pct);
    const a = currentAnalysis || analysis;
    if (!a) return;

    try {
      const sim = await contractsApi.simulateCoverage({
        total_quantity: Number(totalRequirementMt),
        coverage_percentage: pct,
        contract_rate: a.strategies?.MEDIUM_TERM_MULTIPLE_VOYAGE?.reference_rate || 23.28,
        spot_expected_rate: a.strategies?.SPOT?.expected_rate || 24.30,
        spot_p10: a.strategies?.SPOT?.scenarios?.find(s => s.scenario_name === "BEAR")?.rate || 22.80,
        spot_p90: a.strategies?.SPOT?.scenarios?.find(s => s.scenario_name === "BULL")?.rate || 26.50,
        planning_horizon_days: Number(planningHorizonDays)
      });
      setCoverageSimResult(sim);
    } catch (e) {
      console.error("Coverage simulation error", e);
    }
  };

  const activeStrategy: StrategyDetail | undefined = analysis?.strategies?.[activeStrategyKey];

  // Helper styles for strategy badges
  const getStrategyStyle = (stratKey: ContractStrategyType) => {
    switch (stratKey) {
      case "SPOT":
        return {
          badge: "bg-blue-500/20 text-blue-400 border-blue-500/40",
          accent: "text-blue-400",
          border: "border-blue-500/40",
          label: "SPOT SINGLE / REPEAT",
          desc: "Single voyage fixtures. Maximum flexibility, 100% spot market volatility exposure.",
        };
      case "SHORT_TERM_MULTIPLE_VOYAGE":
        return {
          badge: "bg-amber-500/20 text-amber-400 border-amber-500/40",
          accent: "text-amber-400",
          border: "border-amber-500/40",
          label: "SHORT-TERM MULTI-VOYAGE",
          desc: "90-day COA commitment (2-3 voyages). Balanced risk with partial spot optionality.",
        };
      case "MEDIUM_TERM_MULTIPLE_VOYAGE":
        return {
          badge: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40",
          accent: "text-emerald-400",
          border: "border-emerald-500/40",
          label: "MEDIUM-TERM MULTI-VOYAGE",
          desc: "180-day COA commitment (4+ voyages). Complete freight cost certainty and guaranteed vessel supply.",
        };
    }
  };

  // Helper styles for confidence
  const getConfidenceStyle = (conf?: DecisionConfidence) => {
    switch (conf) {
      case "HIGH":
        return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
      case "MEDIUM":
        return "bg-amber-500/15 text-amber-400 border-amber-500/30";
      case "LOW":
        return "bg-rose-500/15 text-rose-400 border-rose-500/30";
      default:
        return "bg-slate-700 text-slate-300 border-slate-600";
    }
  };

  // Chart data: Scenario comparison across Bear, Base, Bull
  const scenarioChartData = useMemo(() => {
    if (!analysis?.scenario_matrix) return [];
    const bear = analysis.scenario_matrix.filter((c) => c.scenario_name === "BEAR");
    const base = analysis.scenario_matrix.filter((c) => c.scenario_name === "BASE");
    const bull = analysis.scenario_matrix.filter((c) => c.scenario_name === "BULL");

    const getCost = (cells: any[], type: ContractStrategyType) => {
      const match = cells.find((c) => c.strategy_type === type);
      return match ? Number((match.freight_cost_usd / 1_000_000).toFixed(2)) : 0;
    };

    return [
      {
        scenario: "BEAR (Softening -8%)",
        spot: getCost(bear, "SPOT"),
        shortTerm: getCost(bear, "SHORT_TERM_MULTIPLE_VOYAGE"),
        mediumTerm: getCost(bear, "MEDIUM_TERM_MULTIPLE_VOYAGE"),
      },
      {
        scenario: "BASE (TFT Central)",
        spot: getCost(base, "SPOT"),
        shortTerm: getCost(base, "SHORT_TERM_MULTIPLE_VOYAGE"),
        mediumTerm: getCost(base, "MEDIUM_TERM_MULTIPLE_VOYAGE"),
      },
      {
        scenario: "BULL (Spike +12%)",
        spot: getCost(bull, "SPOT"),
        shortTerm: getCost(bull, "SHORT_TERM_MULTIPLE_VOYAGE"),
        mediumTerm: getCost(bull, "MEDIUM_TERM_MULTIPLE_VOYAGE"),
      },
    ];
  }, [analysis]);

  return (
    <div className="space-y-6">
      {/* 1. Header */}
      <PageHeader
        title="CONTRACT STRATEGY ENGINE"
        description="Strategic multi-voyage procurement intelligence evaluating Spot versus Contract of Affreightment (COA) portfolio allocations."
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
              Strategic evaluations model scenario procurement economics. Not a binding commercial charter party or guaranteed cost saving.
              Reference rates reflect calibrated volume commitments against synthetic Baltic Panamax indices.
            </p>
          </div>
        </div>
        <div className="text-xs font-mono text-amber-400/90 whitespace-nowrap pl-8 sm:pl-0">
          Source: {analysis?.data_provenance?.dataset_version || "FREIGHT-SYNTH-2026-Q1"}
        </div>
      </div>

      {/* 3. Requirement Summary & Filter Bar */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-4 backdrop-blur-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2 text-xs font-bold font-mono text-slate-300 tracking-wider uppercase">
            <Sliders className="h-4 w-4 text-blue-400" />
            <span>BULK PROCUREMENT DEMAND & VOYAGE PLANNING CONTEXT</span>
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
              onClick={runEvaluation}
              disabled={evaluating || loading}
              className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-xs font-semibold text-white transition-colors flex items-center gap-1.5 shadow-sm shadow-blue-500/20"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${evaluating ? "animate-spin" : ""}`} />
              <span>{evaluating ? "Evaluating..." : "Evaluate Strategies"}</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4 text-xs">
          <div>
            <label className="block text-slate-400 font-mono mb-1">Cargo Requirement</label>
            <select
              value={selectedReqId}
              onChange={(e) => handleRequirementChange(e.target.value)}
              className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-2.5 py-2 text-slate-200 focus:outline-none focus:border-blue-500 font-mono text-xs"
            >
              {cargoRequirements.map((r) => (
                <option key={r.id} value={r.requirement_code || r.id}>
                  {r.requirement_code || r.id} — {r.cargo_type}
                </option>
              ))}
              <option value="CUSTOM">Custom Parameters</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-400 font-mono mb-1">Total Requirement (MT)</label>
            <input
              type="number"
              value={totalRequirementMt}
              onChange={(e) => setTotalRequirementMt(Number(e.target.value))}
              step="10000"
              className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-2.5 py-2 text-slate-200 focus:outline-none focus:border-blue-500 font-mono text-xs"
            />
          </div>

          <div>
            <label className="block text-slate-400 font-mono mb-1">Voyage Parcel (MT)</label>
            <input
              type="number"
              value={parcelSizeMt}
              onChange={(e) => setParcelSizeMt(Number(e.target.value))}
              step="5000"
              className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-2.5 py-2 text-slate-200 focus:outline-none focus:border-blue-500 font-mono text-xs"
            />
          </div>

          <div>
            <label className="block text-slate-400 font-mono mb-1">Vessel Class</label>
            <select
              value={vesselClass}
              onChange={(e) => setVesselClass(e.target.value)}
              className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-2.5 py-2 text-slate-200 focus:outline-none focus:border-blue-500 font-mono text-xs"
            >
              <option value="PANAMAX">Panamax (75k MT)</option>
              <option value="CAPESIZE">Capesize (120k+ MT)</option>
              <option value="SUPRAMAX">Supramax (55k MT)</option>
              <option value="NEWCASTLEMAX">Newcastlemax (Gated Demo)</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-400 font-mono mb-1">Reference Rate ($/MT)</label>
            <input
              type="number"
              value={referenceContractRate}
              onChange={(e) => setReferenceContractRate(Number(e.target.value))}
              step="0.25"
              className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-2.5 py-2 text-slate-200 focus:outline-none focus:border-blue-500 font-mono text-xs"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-slate-400 font-mono">Horizon (Days)</label>
              <span className="text-blue-400 font-mono font-bold">{planningHorizonDays}d</span>
            </div>
            <input
              type="range"
              min="60"
              max="365"
              value={planningHorizonDays}
              onChange={(e) => setPlanningHorizonDays(Number(e.target.value))}
              className="w-full accent-blue-500 cursor-pointer h-2 bg-slate-800 rounded-lg"
            />
          </div>
        </div>

        {/* Voyage Planning KPI strip */}
        <div className="flex flex-wrap items-center gap-4 pt-2 border-t border-slate-800/60 text-xs font-mono text-slate-300">
          <span className="flex items-center gap-1.5">
            <Ship className="h-3.5 w-3.5 text-blue-400" />
            Expected Voyages:{" "}
            <strong className="text-white">{analysis?.voyage_plan?.expected_voyages || 4} voyages</strong>
          </span>
          <span className="text-slate-600">•</span>
          <span>
            Parcel Frequency: ~{analysis?.voyage_plan?.voyage_frequency_days || 45} days
          </span>
          <span className="text-slate-600">•</span>
          <span>
            Remainder Cargo:{" "}
            <strong className={analysis?.voyage_plan?.remainder_mt ? "text-amber-400" : "text-emerald-400"}>
              {analysis?.voyage_plan?.remainder_mt ? `${analysis.voyage_plan.remainder_mt.toLocaleString()} MT` : "0 MT (Exact Multiple)"}
            </strong>
          </span>
          <span className="text-slate-600">•</span>
          <span>
            Port Feasibility:{" "}
            <strong className={analysis?.port_feasibility_status === "PASS" ? "text-emerald-400" : "text-rose-400"}>
              {analysis?.port_feasibility_status || "PASS"}
            </strong>
          </span>
        </div>

        {error && (
          <div className="p-3 rounded-lg border border-rose-500/30 bg-rose-950/20 text-rose-300 text-xs flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* 4. STRATEGY CARDS (SPOT, SHORT-TERM, MEDIUM-TERM) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {(["SPOT", "SHORT_TERM_MULTIPLE_VOYAGE", "MEDIUM_TERM_MULTIPLE_VOYAGE"] as ContractStrategyType[]).map((stratKey) => {
          const strat = analysis?.strategies?.[stratKey];
          const style = getStrategyStyle(stratKey);
          const isSelected = activeStrategyKey === stratKey;

          return (
            <div
              key={stratKey}
              onClick={() => setActiveStrategyKey(stratKey)}
              className={`rounded-xl border p-5 transition-all cursor-pointer backdrop-blur-sm space-y-4 ${
                isSelected
                  ? `${style.border} bg-slate-900/90 shadow-[0_0_25px_rgba(59,130,246,0.15)] ring-1 ring-blue-500/30`
                  : "border-slate-800 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-900/80"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className={`px-2.5 py-1 rounded-md border text-[11px] font-mono font-bold tracking-wider ${style.badge}`}>
                  {style.label}
                </span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-mono border font-semibold ${getConfidenceStyle(strat?.decision_confidence)}`}>
                  {strat?.decision_confidence || "HIGH"}
                </span>
              </div>

              <div>
                <span className="block text-[11px] font-mono text-slate-400 uppercase">Expected Total Freight</span>
                <div className="flex items-baseline gap-2 mt-0.5">
                  <span className="text-2xl font-black font-mono text-slate-100">
                    ${strat?.expected_cost ? (strat.expected_cost / 1_000_000).toFixed(2) : "--"}M
                  </span>
                  <span className="text-xs font-mono text-slate-400">
                    (${strat?.expected_rate?.toFixed(2) || "--"}/MT)
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  {style.desc}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/80 text-xs font-mono">
                <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/70">
                  <span className="block text-[10px] text-slate-500 uppercase">Market Exposure</span>
                  <span className={`text-xs font-bold mt-0.5 block ${
                    (strat?.market_exposure || 0) > 0.6 ? "text-rose-400" : (strat?.market_exposure || 0) > 0.3 ? "text-amber-400" : "text-emerald-400"
                  }`}>
                    {((strat?.market_exposure || 0) * 100).toFixed(0)}% Exposure
                  </span>
                </div>

                <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/70">
                  <span className="block text-[10px] text-slate-500 uppercase">Flexibility Index</span>
                  <span className={`text-xs font-bold mt-0.5 block ${
                    (strat?.flexibility_measure || 0) > 0.7 ? "text-emerald-400" : (strat?.flexibility_measure || 0) > 0.4 ? "text-blue-400" : "text-slate-400"
                  }`}>
                    {((strat?.flexibility_measure || 0) * 100).toFixed(0)}% Agility
                  </span>
                </div>
              </div>

              <div className="space-y-1 text-xs font-mono text-slate-400 pt-1">
                <div className="flex justify-between py-0.5">
                  <span>Contract Duration:</span>
                  <span className="text-slate-200">{strat?.contract_duration || "--"}</span>
                </div>
                <div className="flex justify-between py-0.5">
                  <span>Planned Voyages:</span>
                  <span className="text-slate-200">{strat?.voyage_count || "--"} Voyages</span>
                </div>
                <div className="flex justify-between py-0.5">
                  <span>Contracted Volume:</span>
                  <span className="text-slate-200">
                    {strat?.contracted_quantity ? `${(strat.contracted_quantity / 1000).toFixed(0)}k MT` : "0 MT (Spot)"}
                  </span>
                </div>
                <div className="flex justify-between py-0.5">
                  <span>Risk-Adjusted Cost:</span>
                  <span className="text-blue-400 font-semibold">
                    ${strat?.risk_adjusted_cost ? (strat.risk_adjusted_cost / 1_000_000).toFixed(2) : "--"}M
                  </span>
                </div>
              </div>

              <div className="text-[11px] font-mono text-center pt-2 text-blue-400/90 font-medium">
                {isSelected ? "● Currently Inspecting Strategy" : "Click to View Details"}
              </div>
            </div>
          );
        })}
      </div>

      {/* 5. STRATEGY COMPARISON TABLE */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold font-mono text-slate-200 flex items-center gap-2">
            <Scale className="h-4 w-4 text-blue-400" />
            STRATEGY PORTFOLIO COMPARISON
          </h3>
          <span className="text-xs font-mono text-slate-400">
            Total Demand: <strong className="text-slate-200">{analysis?.total_requirement_mt.toLocaleString()} MT</strong>
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs font-mono text-left">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Evaluation Metric</th>
                <th className="py-2.5 px-3 text-blue-400">Spot Single / Repeat</th>
                <th className="py-2.5 px-3 text-amber-400">Short-Term Multi-Voyage</th>
                <th className="py-2.5 px-3 text-emerald-400">Medium-Term Multi-Voyage</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              <tr className="hover:bg-slate-800/30">
                <td className="py-2.5 px-3 text-slate-400">Voyage Commitment</td>
                <td className="py-2.5 px-3 text-slate-200">1-by-1 Prompt Fix</td>
                <td className="py-2.5 px-3 text-slate-200">2 Voyages (~90 Days)</td>
                <td className="py-2.5 px-3 text-slate-200">4 Voyages (~180 Days)</td>
              </tr>
              <tr className="hover:bg-slate-800/30">
                <td className="py-2.5 px-3 text-slate-400">Volume Allocation</td>
                <td className="py-2.5 px-3 text-slate-200">100% Spot (0 MT Hedged)</td>
                <td className="py-2.5 px-3 text-slate-200">50% Contract / 50% Spot</td>
                <td className="py-2.5 px-3 text-slate-200">100% Contract (Fully Hedged)</td>
              </tr>
              <tr className="hover:bg-slate-800/30">
                <td className="py-2.5 px-3 text-slate-400">Operational Flexibility</td>
                <td className="py-2.5 px-3 text-emerald-400 font-bold">
                  {((analysis?.strategies?.SPOT?.flexibility_measure || 0.95) * 100).toFixed(0)}% (High)
                </td>
                <td className="py-2.5 px-3 text-blue-400 font-bold">
                  {((analysis?.strategies?.SHORT_TERM_MULTIPLE_VOYAGE?.flexibility_measure || 0.58) * 100).toFixed(0)}% (Moderate)
                </td>
                <td className="py-2.5 px-3 text-slate-400 font-bold">
                  {((analysis?.strategies?.MEDIUM_TERM_MULTIPLE_VOYAGE?.flexibility_measure || 0.20) * 100).toFixed(0)}% (Low)
                </td>
              </tr>
              <tr className="hover:bg-slate-800/30">
                <td className="py-2.5 px-3 text-slate-400">Spot Market Exposure</td>
                <td className="py-2.5 px-3 text-rose-400 font-bold">
                  {((analysis?.strategies?.SPOT?.market_exposure || 1.0) * 100).toFixed(0)}% (Full)
                </td>
                <td className="py-2.5 px-3 text-amber-400 font-bold">
                  {((analysis?.strategies?.SHORT_TERM_MULTIPLE_VOYAGE?.market_exposure || 0.45) * 100).toFixed(0)}% (Moderate)
                </td>
                <td className="py-2.5 px-3 text-emerald-400 font-bold">
                  {((analysis?.strategies?.MEDIUM_TERM_MULTIPLE_VOYAGE?.market_exposure || 0.05) * 100).toFixed(0)}% (Minimal)
                </td>
              </tr>
              <tr className="hover:bg-slate-800/30 font-bold">
                <td className="py-2.5 px-3 text-slate-300">Expected Freight Rate</td>
                <td className="py-2.5 px-3 text-blue-400">${analysis?.strategies?.SPOT?.expected_rate?.toFixed(2)}/MT</td>
                <td className="py-2.5 px-3 text-amber-400">${analysis?.strategies?.SHORT_TERM_MULTIPLE_VOYAGE?.expected_rate?.toFixed(2)}/MT</td>
                <td className="py-2.5 px-3 text-emerald-400">${analysis?.strategies?.MEDIUM_TERM_MULTIPLE_VOYAGE?.expected_rate?.toFixed(2)}/MT</td>
              </tr>
              <tr className="hover:bg-slate-800/30">
                <td className="py-2.5 px-3 text-slate-400">P10 Freight Cost (Bear)</td>
                <td className="py-2.5 px-3 text-slate-200">${(analysis?.strategies?.SPOT?.p10_cost || 0) / 1_000_000 < 1 ? "--" : `${((analysis?.strategies?.SPOT?.p10_cost || 0) / 1_000_000).toFixed(2)}M`}</td>
                <td className="py-2.5 px-3 text-slate-200">${(analysis?.strategies?.SHORT_TERM_MULTIPLE_VOYAGE?.p10_cost || 0) / 1_000_000 < 1 ? "--" : `${((analysis?.strategies?.SHORT_TERM_MULTIPLE_VOYAGE?.p10_cost || 0) / 1_000_000).toFixed(2)}M`}</td>
                <td className="py-2.5 px-3 text-slate-200">${(analysis?.strategies?.MEDIUM_TERM_MULTIPLE_VOYAGE?.p10_cost || 0) / 1_000_000 < 1 ? "--" : `${((analysis?.strategies?.MEDIUM_TERM_MULTIPLE_VOYAGE?.p10_cost || 0) / 1_000_000).toFixed(2)}M`}</td>
              </tr>
              <tr className="hover:bg-slate-800/30">
                <td className="py-2.5 px-3 text-slate-400">P90 Freight Cost (Bull)</td>
                <td className="py-2.5 px-3 text-rose-400 font-semibold">${((analysis?.strategies?.SPOT?.p90_cost || 0) / 1_000_000).toFixed(2)}M</td>
                <td className="py-2.5 px-3 text-amber-400 font-semibold">${((analysis?.strategies?.SHORT_TERM_MULTIPLE_VOYAGE?.p90_cost || 0) / 1_000_000).toFixed(2)}M</td>
                <td className="py-2.5 px-3 text-emerald-400 font-semibold">${((analysis?.strategies?.MEDIUM_TERM_MULTIPLE_VOYAGE?.p90_cost || 0) / 1_000_000).toFixed(2)}M</td>
              </tr>
              <tr className="bg-slate-950/90 font-bold border-t border-slate-700">
                <td className="py-3 px-3 text-slate-200">Risk-Adjusted Total Cost</td>
                <td className="py-3 px-3 text-blue-400">${((analysis?.strategies?.SPOT?.risk_adjusted_cost || 0) / 1_000_000).toFixed(2)}M</td>
                <td className="py-3 px-3 text-amber-400">${((analysis?.strategies?.SHORT_TERM_MULTIPLE_VOYAGE?.risk_adjusted_cost || 0) / 1_000_000).toFixed(2)}M</td>
                <td className="py-3 px-3 text-emerald-400">${((analysis?.strategies?.MEDIUM_TERM_MULTIPLE_VOYAGE?.risk_adjusted_cost || 0) / 1_000_000).toFixed(2)}M</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* 6. TWO-COLUMN: SCENARIO MATRIX & BREAK-EVEN ANALYSIS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scenario Matrix Chart & Table */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold font-mono text-slate-200 flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-blue-400" />
              MARKET SCENARIO ANALYSIS (BEAR / BASE / BULL)
            </h3>
            <span className="text-xs font-mono text-slate-400">Total Freight ($M)</span>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scenarioChartData} margin={{ top: 10, right: 10, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="scenario" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} unit="M" />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px", fontSize: "12px" }}
                  formatter={(val: any, name: any) => [`$${val}M`, name]}
                />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="spot" name="Spot Strategy" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="shortTerm" name="Short-Term COA" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                <Bar dataKey="mediumTerm" name="Medium-Term COA" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
            Under Bear conditions, Spot captures freight curve softening; under Bull conditions, Medium-Term COA provides full cost containment.
          </p>
        </div>

        {/* Break-Even Analysis Card */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold font-mono text-slate-200 flex items-center gap-2">
                <Compass className="h-4 w-4 text-emerald-400" />
                MODELED BREAK-EVEN SPOT RATE
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                {analysis?.break_even_analysis?.status || "AVAILABLE"}
              </span>
            </div>

            <div className="mt-4 p-4 rounded-lg bg-slate-950/70 border border-slate-800 space-y-3">
              <div className="flex items-baseline justify-between">
                <div>
                  <span className="block text-[11px] text-slate-400 font-mono">Threshold Break-Even Rate</span>
                  <span className="text-2xl font-black font-mono text-emerald-400 mt-1 block">
                    ${analysis?.break_even_analysis?.modeled_break_even_spot_rate_usd_pmt?.toFixed(2) || "--"} / MT
                  </span>
                </div>
                <div className="text-right">
                  <span className="block text-[11px] text-slate-400 font-mono">Current Spot Benchmark</span>
                  <span className="text-lg font-bold font-mono text-slate-200 mt-1 block">
                    ${analysis?.break_even_analysis?.current_spot_rate_usd_pmt?.toFixed(2) || "--"} / MT
                  </span>
                </div>
              </div>

              <div className="text-xs font-mono text-slate-400 pt-2 border-t border-slate-800/80 flex justify-between">
                <span>Rate Spread:</span>
                <span className={`font-semibold ${
                  (analysis?.break_even_analysis?.rate_delta_usd_pmt || 0) < 0 ? "text-emerald-400" : "text-amber-400"
                }`}>
                  {(analysis?.break_even_analysis?.rate_delta_usd_pmt || 0) < 0 ? "" : "+"}
                  ${analysis?.break_even_analysis?.rate_delta_usd_pmt?.toFixed(2)}/MT (
                  {(analysis?.break_even_analysis?.rate_delta_pct || 0).toFixed(1)}%)
                </span>
              </div>
            </div>

            <div className="mt-4 p-3 rounded-lg bg-slate-950/40 border border-slate-800/60 text-xs text-slate-300 leading-relaxed font-sans">
              <strong>Interpretation: </strong>
              {analysis?.break_even_analysis?.decision_interpretation ||
                "Modeled break-even represents the average spot market threshold over the 180-day horizon where multi-voyage COA achieves economic parity."}
            </div>
          </div>

          <div className="text-[11px] font-mono text-slate-500 italic pt-2">
            *Modeled break-even rate. Not a guaranteed saving. Sensitivity based on 300,000 MT planned Newcastle-Paradip volume.
          </div>
        </div>
      </div>

      {/* 7. INTERACTIVE CONTRACT COVERAGE SLIDER */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold font-mono text-slate-200 flex items-center gap-2">
              <Percent className="h-4 w-4 text-blue-400" />
              INTERACTIVE CONTRACT PORTFOLIO COVERAGE SIMULATOR
            </h3>
            <p className="text-xs text-slate-400">
              Simulate volume split between contracted multi-voyage commitments and open spot market exposure
            </p>
          </div>
          <div className="text-xs font-mono text-blue-400 bg-blue-500/10 border border-blue-500/30 px-3 py-1 rounded-lg">
            Coverage Ratio: <strong className="text-white">{coveragePct}% Contracted</strong> / {100 - coveragePct}% Spot
          </div>
        </div>

        <div className="space-y-2">
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            value={coveragePct}
            onChange={(e) => updateCoverageSimulation(Number(e.target.value))}
            className="w-full accent-blue-500 cursor-pointer h-2 bg-slate-800 rounded-lg"
          />
          <div className="flex justify-between text-[11px] font-mono text-slate-500">
            <span>0% (100% Spot)</span>
            <span>25% Contract</span>
            <span>50% Balanced</span>
            <span>75% Contract</span>
            <span>100% Fully Hedged</span>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs font-mono pt-2">
          <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800">
            <span className="block text-[10px] text-slate-400 uppercase">Contracted Volume</span>
            <span className="text-sm font-bold text-emerald-400 mt-1 block">
              {coverageSimResult?.contracted_quantity_mt?.toLocaleString() || (totalRequirementMt * 0.75).toLocaleString()} MT
            </span>
          </div>

          <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800">
            <span className="block text-[10px] text-slate-400 uppercase">Spot Exposure</span>
            <span className="text-sm font-bold text-blue-400 mt-1 block">
              {coverageSimResult?.spot_quantity_mt?.toLocaleString() || (totalRequirementMt * 0.25).toLocaleString()} MT
            </span>
          </div>

          <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800">
            <span className="block text-[10px] text-slate-400 uppercase">Expected Freight Cost</span>
            <span className="text-sm font-bold text-slate-100 mt-1 block">
              ${coverageSimResult?.expected_cost ? (coverageSimResult.expected_cost / 1_000_000).toFixed(2) : "--"}M
            </span>
          </div>

          <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800">
            <span className="block text-[10px] text-slate-400 uppercase">Cost Range (P10-P90)</span>
            <span className="text-sm font-bold text-amber-400 mt-1 block">
              ${coverageSimResult?.cost_range_usd ? (coverageSimResult.cost_range_usd / 1000).toFixed(0) : "--"}k Spread
            </span>
          </div>

          <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800 col-span-2 sm:col-span-1">
            <span className="block text-[10px] text-slate-400 uppercase">Risk-Adjusted Cost</span>
            <span className="text-sm font-bold text-blue-400 mt-1 block">
              ${coverageSimResult?.risk_adjusted_cost ? (coverageSimResult.risk_adjusted_cost / 1_000_000).toFixed(2) : "--"}M
            </span>
          </div>
        </div>
      </div>

      {/* 8. STRATEGY EXPLANATIONS: WHY THIS FITS & KEY TRADE-OFF */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-3">
          <h3 className="text-sm font-bold font-mono text-slate-200 flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            WHY THIS STRATEGY FITS ({activeStrategy?.strategy_label || "ACTIVE STRATEGY"})
          </h3>
          <ul className="space-y-2 text-xs text-slate-300">
            {activeStrategy?.why_this_fits?.map((point, idx) => (
              <li key={idx} className="flex items-start gap-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/70">
                <ArrowRight className="h-3.5 w-3.5 text-blue-400 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{point}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-3">
          <h3 className="text-sm font-bold font-mono text-slate-200 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-400" />
            KEY STRATEGIC TRADE-OFF
          </h3>
          <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 space-y-3">
            <div className="text-xs font-mono font-bold text-amber-300">
              Core Compromise:
            </div>
            <p className="text-xs text-slate-300 leading-relaxed font-sans">
              {activeStrategy?.key_trade_off ||
                "Locking forward multi-voyage capacity removes freight spike exposure while forfeiting downside spot capture."}
            </p>
            <div className="text-[11px] font-mono text-slate-400 pt-2 border-t border-slate-800/80">
              Decision Rule: Align with corporate risk mandate: choose Spot for operational agility, COA for budget certainty.
            </div>
          </div>
        </div>
      </div>

      {/* 9. ASSUMPTIONS DRAWER / MODAL */}
      {assumptionsOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-xl bg-slate-900 border-l border-slate-800 h-full overflow-y-auto p-6 space-y-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2 text-sm font-bold font-mono text-slate-200">
                <FileText className="h-4 w-4 text-blue-400" />
                <span>CONTRACT MODEL ASSUMPTIONS & LINEAGE</span>
              </div>
              <button
                onClick={() => setAssumptionsOpen(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-3">
              <h4 className="text-xs font-bold font-mono text-slate-300 uppercase tracking-wider">
                Demand & Route Parameters
              </h4>
              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-400 block text-[11px]">Total Requirement</span>
                  <span className="text-slate-100 font-bold text-sm mt-0.5 block">
                    {totalRequirementMt.toLocaleString()} MT
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-400 block text-[11px]">Voyage Parcel Size</span>
                  <span className="text-slate-100 font-bold text-sm mt-0.5 block">
                    {parcelSizeMt.toLocaleString()} MT
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-400 block text-[11px]">Planning Horizon</span>
                  <span className="text-slate-100 font-bold text-sm mt-0.5 block">
                    {planningHorizonDays} Days (Semi-Annual)
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-400 block text-[11px]">Reference Contract Rate</span>
                  <span className="text-slate-100 font-bold text-sm mt-0.5 block">
                    ${referenceContractRate.toFixed(2)} / MT
                  </span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="text-xs font-bold font-mono text-slate-300 uppercase tracking-wider">
                Data Provenance & Lineage
              </h4>
              <div className="space-y-2 text-xs font-mono bg-slate-950 p-4 rounded-lg border border-slate-800">
                <div className="flex justify-between py-1 border-b border-slate-800/70">
                  <span className="text-slate-400">Forecasting Engine:</span>
                  <span className="text-slate-200">{analysis?.data_provenance?.forecasting_model || "TFT-v1.0.0"}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/70">
                  <span className="text-slate-400">Market Regime Engine:</span>
                  <span className="text-slate-200">{analysis?.data_provenance?.market_regime_model || "HMM-Gaussian-v1.0.0"}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/70">
                  <span className="text-slate-400">Wait/Fix Decision Model:</span>
                  <span className="text-slate-200">{analysis?.data_provenance?.wait_fix_model || "WAIT_FIX_V1.0"}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/70">
                  <span className="text-slate-400">Dataset Version:</span>
                  <span className="text-slate-200">{analysis?.data_provenance?.dataset_version || "FREIGHT-SYNTH-2026-Q1"}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Data Status:</span>
                  <span className="text-amber-400">SYNTHETIC (SIH Demo Feed)</span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="text-xs font-bold font-mono text-slate-300 uppercase tracking-wider">
                Mathematical Formulations
              </h4>
              <div className="space-y-3 text-xs text-slate-300">
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-[11px] space-y-1">
                  <div className="text-blue-400 font-bold">1. Multi-Voyage Parcel Scheduling</div>
                  <div>Expected Voyages = &lceil;Total Requirement / Parcel Size&rceil;</div>
                  <div className="text-slate-500 italic">Guarantees non-discarding remainder cargo</div>
                </div>

                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-[11px] space-y-1">
                  <div className="text-emerald-400 font-bold">2. Hybrid Coverage Allocation</div>
                  <div>Contracted MT + Spot MT = Total Requirement</div>
                  <div>Total Cost = (Contracted MT &times; R_contract) + (Spot MT &times; E[R_spot])</div>
                </div>

                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-[11px] space-y-1">
                  <div className="text-amber-400 font-bold">3. Risk-Adjusted Cost</div>
                  <div>Risk-Adjusted Cost = Expected Cost + Uncertainty Spread Penalty + Commitment Penalty</div>
                  <div className="text-slate-500 italic">Parametric penalization of unhedged spot volatility</div>
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

export default function ContractStrategyPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-slate-500 font-mono text-xs">Loading contract strategy solver...</div>}>
      <ContractStrategyContent />
    </Suspense>
  );
}
