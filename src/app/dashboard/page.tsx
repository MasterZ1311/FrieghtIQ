"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Ship,
  Anchor,
  ShieldAlert,
  Clock,
  ArrowUpRight,
  TrendingUp,
  FileCheck,
  PlusCircle,
  AlertTriangle,
  Info,
  Play,
  Bot,
  Layers,
  ArrowRight,
  DollarSign,
  Compass,
  Activity,
  CheckCircle2,
  RefreshCw,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { MetricCard } from "@/components/data-display/MetricCard";
import { DataTable, ColumnDef } from "@/components/data-display/DataTable";
import { StatusBadge } from "@/components/badges/StatusBadge";
import { DataStatusBadge } from "@/components/badges/DataStatusBadge";
import { DEMO_VESSELS } from "@/data/demo/vessels";
import { DEMO_PORTS } from "@/data/demo/ports";
import { Vessel } from "@/types";
import {
  getDashboardSummary,
  runDecisionAnalysis,
  ExecutiveDashboardSummarySchema,
} from "@/lib/api/decision";

export default function DashboardPage() {
  const router = useRouter();
  const [currentDateTime, setCurrentDateTime] = useState<string>("");
  const [summary, setSummary] = useState<ExecutiveDashboardSummarySchema | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [analyzing, setAnalyzing] = useState<boolean>(false);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentDateTime(
        now.toLocaleDateString("en-US", {
          weekday: "short",
          month: "short",
          day: "numeric",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false,
          timeZoneName: "short",
        })
      );
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const loadSummary = async () => {
    try {
      setLoading(true);
      const data = await getDashboardSummary();
      setSummary(data);
    } catch (e) {
      console.warn("Could not load executive dashboard summary:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, []);

  const handleRunPrimaryAnalysis = async () => {
    if (!summary?.primary_decision?.cargo_id) return;
    try {
      setAnalyzing(true);
      await runDecisionAnalysis({ cargo_id: summary.primary_decision.cargo_id });
      await loadSummary();
    } catch (err: any) {
      alert(`Pipeline execution error: ${err.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  // Vessel Columns for Command Center Table
  const vesselColumns: ColumnDef<Vessel>[] = [
    {
      header: "Vessel Name",
      accessorKey: "name",
      cell: (v) => (
        <div>
          <div className="font-bold text-foreground flex items-center gap-1.5">
            <Ship className="h-3.5 w-3.5 text-primary shrink-0" />
            <span>{v.name}</span>
          </div>
          <div className="text-[10px] text-muted-foreground font-mono">IMO: {v.imoNumber}</div>
        </div>
      ),
    },
    {
      header: "Class",
      accessorKey: "vesselClass",
      cell: (v) => (
        <Badge variant="secondary" className="font-mono text-xs font-semibold text-primary">
          {v.vesselClass}
        </Badge>
      ),
    },
    {
      header: "Compatible Cargo",
      cell: (v) => (
        <span className="text-[11px] text-muted-foreground truncate max-w-[140px] block">
          {v.compatibleCargo.join(", ")}
        </span>
      ),
    },
    {
      header: "LOA / Draft",
      cell: (v) => (
        <span className="font-mono text-xs text-muted-foreground">
          {typeof v.loaMeters === "number" ? `${v.loaMeters}m` : v.loaMeters} /{" "}
          {typeof v.draftMeters === "number" ? `${v.draftMeters}m` : v.draftMeters}
        </span>
      ),
    },
    {
      header: "Capacity",
      cell: (v) => (
        <span className="font-mono text-xs text-muted-foreground">
          {typeof v.dwtMT === "number" ? `${v.dwtMT.toLocaleString("en-US")} DWT` : v.dwtMT}
        </span>
      ),
    },
    {
      header: "Status",
      accessorKey: "status",
      cell: (v) => <StatusBadge status={v.status} size="sm" />,
    },
  ];

  const primaryDec = summary?.primary_decision;
  const decisionId = primaryDec?.decision_id || primaryDec?.cargo_id || "req-sail-2026-001";

  return (
    <div className="space-y-6 pb-12">
      {/* 1. Header & Live Indicator */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <span>Executive Command Center</span>
              <Badge variant="outline" className="bg-primary/10 text-primary border-primary/30 font-bold text-[11px]">
                PHASE 13 UNIFIED
              </Badge>
            </h1>
          </div>
          <p className="text-xs text-muted-foreground">
            End-to-End Maritime Freight Forecasting & Vessel Chartering Intelligence • SAIL Commercial Directorate
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 bg-muted/40 px-3 py-1.5 rounded-lg border border-border text-xs text-muted-foreground font-mono">
            <Clock className="h-3.5 w-3.5 text-primary" />
            <span>{currentDateTime || "Syncing UTC..."}</span>
          </div>

          <Link href="/chartering/requests">
            <Button size="sm" className="gap-1.5 text-xs font-semibold shadow-sm">
              <PlusCircle className="h-3.5 w-3.5" />
              <span>New Requisition</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* 2. Top Executive Metrics (5 Core Cards) */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3.5">
        <MetricCard
          title="Active Cargo Requests"
          value={summary ? summary.active_cargo_requests_count.toString() : "2"}
          subtitle="Nominated SAIL Requisitions"
        />
        <MetricCard
          title="Pending Decisions"
          value={summary ? summary.pending_decisions_count.toString() : "1"}
          subtitle="Awaiting Charter Order"
        />
        <MetricCard
          title="Relevant Vessels"
          value={summary ? summary.matched_vessels_count.toString() : "9"}
          subtitle="Screened in Fleet Register"
        />
        <MetricCard
          title="High-Risk Voyages"
          value={summary ? summary.high_risk_voyages_count.toString() : "1"}
          subtitle="Demurrage / Weather Alert"
        />
        <MetricCard
          title="Partial Analyses"
          value={summary ? summary.partial_analyses_count.toString() : "0"}
          subtitle="Graceful Fallback Mode"
        />
      </div>

      {/* 3. ACTIVE CHARTERING DECISION SHOWCASE CARD (Primary Scenario) */}
      <Card className="border-2 border-primary/40 bg-gradient-to-br from-card via-card to-primary/10 p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-primary/5 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none" />

        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 pb-4 border-b border-border">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <Badge variant="outline" className="bg-primary/15 text-primary border-primary/30 uppercase tracking-wider font-bold text-[10px]">
                Active Chartering Decision #1
              </Badge>
              <Badge variant="outline" className="bg-amber-500/15 text-amber-500 dark:text-amber-400 border-amber-500/30 font-bold text-[10px]">
                30-DAY REQUIREMENT
              </Badge>
              <Badge variant="secondary" className="font-mono text-emerald-500 dark:text-emerald-400 text-[10px]">
                PIPELINE: {primaryDec?.pipeline_state || "READY"}
              </Badge>
            </div>
            <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
              <span>75,000 MT COKING COAL</span>
              <span className="text-muted-foreground font-normal">•</span>
              <span className="text-primary">Port of Newcastle (AUNCL) &rarr; Paradip Port (INPRT)</span>
            </h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Candidate Vessel: <strong>{primaryDec?.vessel?.name || "MV Steel Glory"}</strong> ({primaryDec?.vessel?.vessel_class || "PANAMAX"}) • Match Score: <strong>{primaryDec?.vessel?.match_score || 94.5}%</strong> • Berth Feasibility: <strong>PASS</strong>
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRunPrimaryAnalysis}
              disabled={analyzing}
              className="gap-1.5 text-xs font-semibold"
            >
              {analyzing ? (
                <RefreshCw className="h-3.5 w-3.5 animate-spin text-primary" />
              ) : (
                <Play className="h-3.5 w-3.5 text-primary" />
              )}
              <span>{analyzing ? "Analyzing..." : "Re-Run Pipeline"}</span>
            </Button>

            <Link href={`/copilot?decision_id=${decisionId}`}>
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5 text-xs font-semibold border-primary/40 bg-primary/10 text-primary hover:bg-primary/20"
              >
                <Bot className="h-3.5 w-3.5 text-primary" />
                <span>Ask Copilot</span>
              </Button>
            </Link>

            <Link href={`/chartering/decision/${decisionId}`}>
              <Button
                size="sm"
                className="gap-1.5 text-xs font-bold shadow-md shadow-primary/20"
              >
                <span>Open Decision Workspace</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>
        </div>

        {/* Multi-Engine Decision Matrix Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 mt-4">
          <Card className="p-3 bg-muted/40 border-border">
            <div className="text-[10px] text-muted-foreground uppercase font-semibold truncate">Freight Forecast</div>
            <div className="text-sm font-bold text-primary font-mono mt-0.5 truncate">
              ${primaryDec?.forecast.p50.toFixed(2) || "15.20"} <span className="text-[10px] text-muted-foreground">/ MT</span>
            </div>
            <div className="text-[10px] text-muted-foreground truncate">P10: ${primaryDec?.forecast.p10.toFixed(2) || "13.80"} • P90: ${primaryDec?.forecast.p90.toFixed(2) || "17.10"}</div>
          </Card>

          <Card className="p-3 bg-muted/40 border-border">
            <div className="text-[10px] text-muted-foreground uppercase font-semibold truncate">Market Regime</div>
            <div className="text-sm font-bold text-amber-500 dark:text-amber-400 mt-0.5 truncate">
              {primaryDec?.regime.regime || "BEAR"}
            </div>
            <div className="text-[10px] text-muted-foreground truncate">Softening (-3.5% M-o-M)</div>
          </Card>

          <Card className="p-3 bg-muted/40 border-border">
            <div className="text-[10px] text-muted-foreground uppercase font-semibold truncate">Wait / Fix Option</div>
            <div className={`text-sm font-bold mt-0.5 truncate ${
              primaryDec?.wait_fix.decision === "FIX_NOW" ? "text-primary" : "text-emerald-500 dark:text-emerald-400"
            }`}>
              {primaryDec?.wait_fix.decision || "WAIT_AND_MONITOR"}
            </div>
            <div className="text-[10px] font-mono truncate text-muted-foreground">
              {(() => {
                const s = primaryDec?.wait_fix.expected_savings_usd;
                if (s === undefined || s === null) return "+$28,500 est.";
                if (s >= 0) return `+$${s.toLocaleString("en-US")} est.`;
                return `-$${Math.abs(s).toLocaleString("en-US")} est.`;
              })()}
            </div>
          </Card>

          <Card className="p-3 bg-muted/40 border-border">
            <div className="text-[10px] text-muted-foreground uppercase font-semibold truncate">Contract Mode</div>
            <div className="text-sm font-bold text-primary mt-0.5 truncate" title={primaryDec?.contract.recommended_strategy || "SPOT"}>
              {primaryDec?.contract.recommended_strategy ? primaryDec.contract.recommended_strategy.replace(/_/g, " ") : "SPOT VOYAGE"}
            </div>
            <div className="text-[10px] text-muted-foreground truncate">Min risk-adjusted outlay</div>
          </Card>

          <Card className="p-3 bg-muted/40 border-border">
            <div className="text-[10px] text-muted-foreground uppercase font-semibold truncate">Operational Risk</div>
            <div className="text-sm font-bold text-amber-500 dark:text-amber-400 mt-0.5 truncate">
              {primaryDec?.risk.overall_severity || "MEDIUM"}
            </div>
            <div className="text-[10px] text-muted-foreground truncate">Queue: 1.5d • Tidal: PASS</div>
          </Card>

          <Card className="p-3 bg-muted/40 border-border">
            <div className="text-[10px] text-muted-foreground uppercase font-semibold truncate">Voyage Economics</div>
            <div className="text-sm font-bold text-emerald-500 dark:text-emerald-400 font-mono mt-0.5 truncate">
              ${primaryDec?.economics.cost_per_mt_usd.toFixed(2) || "22.46"} <span className="text-[10px] text-muted-foreground">/ MT</span>
            </div>
            <div className="text-[10px] text-muted-foreground font-mono truncate">
              ${primaryDec?.economics.total_voyage_cost_usd.toLocaleString("en-US") || "1,684,500"} total
            </div>
          </Card>
        </div>
      </Card>

      {/* 4. Three Integrated Command Panels: Market, Operations, Economics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Panel A: Market Intelligence */}
        <Card className="border-border bg-card/70 flex flex-col justify-between">
          <div>
            <CardHeader className="pb-3 border-b border-border">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-bold text-foreground flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-primary" />
                  <span>Market Intelligence</span>
                </CardTitle>
                <Link href="/intelligence/freight" className="text-xs text-primary hover:text-primary/80 flex items-center gap-1 font-medium">
                  <span>Curve</span>
                  <ArrowUpRight className="h-3 w-3" />
                </Link>
              </div>
            </CardHeader>
            <CardContent className="pt-3 space-y-2.5 text-xs">
              <div className="flex justify-between py-1 border-b border-border/60">
                <span className="text-muted-foreground">Benchmark Route:</span>
                <span className="font-semibold text-foreground">AUNCL-INPRT (Panamax)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/60">
                <span className="text-muted-foreground">P50 Freight Forecast:</span>
                <span className="font-mono text-primary font-bold">
                  ${summary?.market_overview.p50_rate.toFixed(2) || "15.20"}/MT
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/60">
                <span className="text-muted-foreground">Detected Regime:</span>
                <span className="font-semibold text-amber-500 dark:text-amber-400">
                  {summary?.market_overview.regime || "BEAR"} REGIME
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-muted-foreground">Forecast Uncertainty:</span>
                <span className="text-foreground font-mono">18.5% (TFT Walk-Forward)</span>
              </div>
            </CardContent>
          </div>
          <div>
            <Separator />
            <div className="p-3 text-[11px] text-muted-foreground">
              Model status: Temporal Fusion Transformer v1.0 ONLINE
            </div>
          </div>
        </Card>

        {/* Panel B: Operations & Risk */}
        <Card className="border-border bg-card/70 flex flex-col justify-between">
          <div>
            <CardHeader className="pb-3 border-b border-border">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-bold text-foreground flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4 text-amber-500 dark:text-amber-400" />
                  <span>Operations & Risk</span>
                </CardTitle>
                <Link href="/risk" className="text-xs text-amber-500 hover:text-amber-400 flex items-center gap-1 font-medium">
                  <span>Center</span>
                  <ArrowUpRight className="h-3 w-3" />
                </Link>
              </div>
            </CardHeader>
            <CardContent className="pt-3 space-y-2.5 text-xs">
              <div className="flex justify-between py-1 border-b border-border/60">
                <span className="text-muted-foreground">Paradip Congestion:</span>
                <span className="font-semibold text-amber-500 dark:text-amber-400">
                  {summary?.operations_overview.congestion || "MODERATE"} ({summary?.operations_overview.queue_days || 1.5}d)
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/60">
                <span className="text-muted-foreground">Tidal Window (UKC):</span>
                <span className="font-mono text-emerald-500 dark:text-emerald-400 font-bold">
                  {summary?.operations_overview.tidal_window || "PASS"} (1.2m Clearance)
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/60">
                <span className="text-muted-foreground">Weather Status:</span>
                <span className="font-semibold text-foreground">
                  {summary?.operations_overview.weather_status || "MONSOON_RECEDING"}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-muted-foreground">Demurrage Risk Exposure:</span>
                <span className="text-rose-500 dark:text-rose-400 font-mono font-bold">$27,250.00</span>
              </div>
            </CardContent>
          </div>
          <div>
            <Separator />
            <div className="p-3 text-[11px] text-muted-foreground">
              Real-time AIS anchorage queue & tidal harmonizer
            </div>
          </div>
        </Card>

        {/* Panel C: Voyage Economics */}
        <Card className="border-border bg-card/70 flex flex-col justify-between">
          <div>
            <CardHeader className="pb-3 border-b border-border">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-bold text-foreground flex items-center gap-2">
                  <DollarSign className="h-4 w-4 text-emerald-500 dark:text-emerald-400" />
                  <span>Voyage Economics</span>
                </CardTitle>
                <Link href="/optimization/voyage-cost" className="text-xs text-emerald-500 hover:text-emerald-400 flex items-center gap-1 font-medium">
                  <span>Ledger</span>
                  <ArrowUpRight className="h-3 w-3" />
                </Link>
              </div>
            </CardHeader>
            <CardContent className="pt-3 space-y-2.5 text-xs">
              <div className="flex justify-between py-1 border-b border-border/60">
                <span className="text-muted-foreground">Total Modeled Voyage Cost:</span>
                <span className="font-mono text-emerald-500 dark:text-emerald-400 font-bold">
                  ${summary?.economics_overview.total_cost.toLocaleString("en-US") || "1,684,500"}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/60">
                <span className="text-muted-foreground">Delivered Cost / MT:</span>
                <span className="font-mono text-emerald-500 dark:text-emerald-300 font-bold">
                  ${summary?.economics_overview.cost_per_mt.toFixed(2) || "22.46"}/MT
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/60">
                <span className="text-muted-foreground">Bunker Fuel Benchmark:</span>
                <span className="font-mono text-foreground">
                  {summary?.economics_overview.bunker_benchmark || "$625.00/MT (VLSFO)"}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-muted-foreground">Speed Scenario:</span>
                <span className="font-semibold text-foreground">12.5 kts Eco (385k Bunker)</span>
              </div>
            </CardContent>
          </div>
          <div>
            <Separator />
            <div className="p-3 text-[11px] text-muted-foreground">
              Admiralty cubic hydrodynamics & port disbursement rates
            </div>
          </div>
        </Card>
      </div>

      {/* 5. Command Center Vessel Fleet & Port Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <DataTable
            columns={vesselColumns}
            data={DEMO_VESSELS.slice(0, 5)}
            title="Candidate Vessel Screening (Fleet Register)"
            headerAction={
              <Link
                href="/intelligence/vessels"
                className="text-xs text-primary hover:text-primary/80 font-medium inline-flex items-center gap-1"
              >
                <span>Full Register</span>
                <ArrowUpRight className="h-3 w-3" />
              </Link>
            }
          />
        </div>

        {/* Port Terminal Infrastructure */}
        <Card className="border-border bg-card p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-border mb-4">
              <div>
                <CardTitle className="text-base font-bold text-foreground flex items-center gap-2">
                  <span>Port Terminal Limits</span>
                  <DataStatusBadge status="VERIFIED SOR" size="xs" />
                </CardTitle>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Scale of Rates berth draft & LOA constraints
                </p>
              </div>
              <Link
                href="/intelligence/ports"
                className="text-xs text-primary hover:text-primary/80 font-medium inline-flex items-center gap-1"
              >
                <span>Specs</span>
                <ArrowUpRight className="h-3 w-3" />
              </Link>
            </div>

            <div className="space-y-2.5">
              {DEMO_PORTS.map((port) => (
                <div
                  key={port.id}
                  className="p-3 rounded-lg border border-border bg-muted/30 hover:bg-muted/60 transition-colors flex items-center justify-between gap-3"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-md bg-muted text-primary shrink-0">
                      <Anchor className="h-4 w-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="font-semibold text-xs text-foreground">{port.name}</span>
                        <span className="text-[10px] text-muted-foreground font-mono">({port.code})</span>
                      </div>
                      <div className="text-[11px] text-muted-foreground mt-0.5 truncate max-w-[160px]">
                        Cargo: {port.knownCargoHandling.slice(0, 2).join(", ")}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <StatusBadge status={port.operationalStatus} size="sm" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
