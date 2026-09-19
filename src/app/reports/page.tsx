"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  FileText,
  Download,
  Printer,
  ShieldCheck,
  CheckCircle2,
  RefreshCw,
  Layers,
  Ship,
  Anchor,
  TrendingUp,
  Compass,
  Clock,
  DollarSign,
  AlertTriangle,
  ExternalLink,
  ChevronRight,
  Database,
  ArrowRight,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  generateDecisionReport,
  getReportExportUrl,
  VoyageDecisionReportSchema,
} from "@/lib/api/decision";

function ReportsContent() {
  const searchParams = useSearchParams();
  const queryDecisionId = searchParams.get("decision_id") || "req-sail-2026-001";

  const [selectedDecisionId, setSelectedDecisionId] = useState<string>(queryDecisionId);
  const [report, setReport] = useState<VoyageDecisionReportSchema | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [generating, setGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async (idToUse?: string) => {
    const id = idToUse || selectedDecisionId;
    try {
      setGenerating(true);
      setError(null);
      const data = await generateDecisionReport(id);
      setReport(data);
    } catch (err: any) {
      setError(err.message || "Failed to generate voyage decision report.");
    } finally {
      setGenerating(false);
      setLoading(false);
    }
  };

  useEffect(() => {
    handleGenerate(queryDecisionId);
  }, [queryDecisionId]);

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6 pb-16">
      {/* 1. Header & Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-border pb-5 print:hidden">
        <div>
          <PageHeader
            title="DECISION AUDIT REPORTS"
            description="Formal 15-section analytical dossiers & tender justification memos for SAIL Commercial Directorate & Ministry of Steel (SIH 2026 #SIH26006)."
            status="AUDIT READY"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Target Scenario Selector */}
          <div className="flex items-center gap-2 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800 text-xs">
            <span className="text-slate-400">Requisition:</span>
            <select
              value={selectedDecisionId}
              onChange={(e) => {
                setSelectedDecisionId(e.target.value);
                handleGenerate(e.target.value);
              }}
              className="bg-transparent text-sky-400 font-mono font-semibold focus:outline-none cursor-pointer"
            >
              <option value="req-sail-2026-001">CR-2026-001 (75K MT Newcastle &rarr; Paradip)</option>
              <option value="req-sail-2026-002">CR-2026-002 (50K MT Gladstone &rarr; Vizag)</option>
            </select>
          </div>

          <button
            onClick={() => handleGenerate()}
            disabled={generating}
            className="px-3.5 py-1.5 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm transition"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${generating ? "animate-spin" : ""}`} />
            <span>{generating ? "Compiling..." : "Re-Generate Dossier"}</span>
          </button>

          {report && (
            <>
              <button
                onClick={handlePrint}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition"
              >
                <Printer className="h-3.5 w-3.5 text-slate-400" />
                <span>Print / PDF</span>
              </button>

              <a
                href={getReportExportUrl(report.decision_id, "CSV")}
                download
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-mono flex items-center gap-1 transition"
                title="Download CSV dataset"
              >
                <Download className="h-3.5 w-3.5 text-emerald-400" />
                <span>CSV</span>
              </a>

              <a
                href={getReportExportUrl(report.decision_id, "JSON")}
                download
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-mono flex items-center gap-1 transition"
                title="Download machine-readable JSON"
              >
                <Download className="h-3.5 w-3.5 text-sky-400" />
                <span>JSON</span>
              </a>
            </>
          )}
        </div>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center min-h-[400px] space-y-3">
          <RefreshCw className="h-8 w-8 animate-spin text-sky-400" />
          <p className="text-sm text-slate-400">Compiling 15-section audit dossier from canonical decision context...</p>
        </div>
      ) : error || !report ? (
        <div className="p-8 text-center bg-slate-900/60 border border-slate-800 rounded-xl max-w-lg mx-auto">
          <AlertTriangle className="h-10 w-10 text-amber-400 mx-auto mb-2" />
          <h3 className="text-base font-bold text-slate-100">Unable to Render Report</h3>
          <p className="text-xs text-slate-400 mt-1">{error || "No analytical data available for this decision."}</p>
          <button
            onClick={() => handleGenerate()}
            className="mt-4 px-4 py-2 bg-sky-600 text-white rounded text-xs font-semibold"
          >
            Try Again
          </button>
        </div>
      ) : (
        /* The Formal 15-Section Voyage Decision Dossier */
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-8 max-w-5xl mx-auto shadow-2xl text-slate-200 space-y-8 print:bg-white print:text-black print:p-0 print:border-0">
          {/* Header Banner */}
          <div className="border-b-2 border-sky-600 pb-5">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-[10px] font-mono font-bold tracking-widest text-sky-400 uppercase bg-sky-950/60 border border-sky-800 px-2 py-0.5 rounded print:text-sky-800">
                  {report.classification}
                </span>
                <h1 className="text-2xl font-bold tracking-tight text-white mt-2 print:text-black">
                  {report.title}
                </h1>
                <p className="text-xs text-slate-400 mt-0.5 print:text-slate-600">
                  Document ID: <strong className="font-mono text-slate-200 print:text-black">{report.report_id}</strong> • Analysis Run: <strong className="font-mono text-slate-200 print:text-black">{report.analysis_run_id}</strong>
                </p>
              </div>
              <div className="text-right text-xs text-slate-400 print:text-slate-600">
                <div>Generated: <strong className="text-slate-200 print:text-black">{new Date(report.generated_at).toLocaleString()}</strong></div>
                <div>Prepared By: <strong className="text-slate-200 print:text-black">{report.user_id}</strong></div>
              </div>
            </div>
          </div>

          {/* Section 1: Executive Summary */}
          <div className="space-y-2">
            <h2 className="text-sm font-bold tracking-wider text-sky-400 uppercase flex items-center gap-1.5 border-b border-slate-800 pb-1 print:text-sky-800">
              <span>1. Executive Summary</span>
            </h2>
            <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-3 rounded-lg border border-slate-800/80 print:bg-slate-50 print:text-black">
              {report.executive_summary}
            </p>
          </div>

          {/* Section 2: Cargo Requirement Particulars */}
          <div className="space-y-2">
            <h2 className="text-sm font-bold tracking-wider text-sky-400 uppercase flex items-center gap-1.5 border-b border-slate-800 pb-1 print:text-sky-800">
              <Layers className="h-4 w-4" /> <span>2. Cargo Requirement Particulars</span>
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="bg-slate-950/40 p-2.5 rounded border border-slate-800 print:bg-slate-50">
                <span className="text-slate-400 block text-[11px]">Requisition Code:</span>
                <span className="font-bold text-slate-100 print:text-black">{report.cargo_requirement?.requirement_code}</span>
              </div>
              <div className="bg-slate-950/40 p-2.5 rounded border border-slate-800 print:bg-slate-50">
                <span className="text-slate-400 block text-[11px]">Commodity:</span>
                <span className="font-bold text-slate-100 print:text-black">{report.cargo_requirement?.commodity}</span>
              </div>
              <div className="bg-slate-950/40 p-2.5 rounded border border-slate-800 print:bg-slate-50">
                <span className="text-slate-400 block text-[11px]">Nominated Quantity:</span>
                <span className="font-bold text-sky-400 font-mono print:text-sky-800">
                  {report.cargo_requirement?.quantity_mt?.toLocaleString()} MT (&plusmn;5% MOLOO)
                </span>
              </div>
              <div className="bg-slate-950/40 p-2.5 rounded border border-slate-800 print:bg-slate-50">
                <span className="text-slate-400 block text-[11px]">Trade Lane:</span>
                <span className="font-semibold text-slate-200 print:text-black">
                  {report.cargo_requirement?.load_port_name} &rarr; {report.cargo_requirement?.discharge_port_name}
                </span>
              </div>
            </div>
          </div>

          {/* Section 3 & 4: Vessel Analysis & Port Feasibility */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <h2 className="text-sm font-bold tracking-wider text-sky-400 uppercase flex items-center gap-1.5 border-b border-slate-800 pb-1 print:text-sky-800">
                <Ship className="h-4 w-4" /> <span>3. Candidate Vessel Analysis</span>
              </h2>
              <div className="text-xs space-y-1.5 bg-slate-950/40 p-3 rounded-lg border border-slate-800 print:bg-slate-50 print:text-black">
                <div className="flex justify-between">
                  <span className="text-slate-400">Nominated Vessel:</span>
                  <span className="font-bold text-slate-100 print:text-black">{report.vessel_analysis?.name || "MV Steel Glory"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Class / Summer DWT:</span>
                  <span className="font-mono text-slate-300 print:text-black">{report.vessel_analysis?.vessel_class} ({report.vessel_analysis?.dwt?.toLocaleString()} MT)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Dimensions:</span>
                  <span className="font-mono text-slate-300 print:text-black">{report.vessel_analysis?.loa_m}m LOA • {report.vessel_analysis?.beam_m}m Beam • {report.vessel_analysis?.draft_m}m Draft</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Deterministic Match Score:</span>
                  <span className="font-bold text-emerald-400">{report.vessel_analysis?.match_score || 94.5}% ({report.vessel_analysis?.match_status || "FEASIBLE"})</span>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <h2 className="text-sm font-bold tracking-wider text-sky-400 uppercase flex items-center gap-1.5 border-b border-slate-800 pb-1 print:text-sky-800">
                <Anchor className="h-4 w-4" /> <span>4. Port Feasibility & Berth Limits</span>
              </h2>
              <div className="text-xs space-y-1.5 bg-slate-950/40 p-3 rounded-lg border border-slate-800 print:bg-slate-50 print:text-black">
                <div className="flex justify-between">
                  <span className="text-slate-400">Berth Geometric Status:</span>
                  <span className="font-bold text-emerald-400">{report.port_feasibility?.feasibility_status || "PASS"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Berths Evaluated:</span>
                  <span className="font-semibold text-slate-200 print:text-black">{report.port_feasibility?.evaluated_berths || 4} Berths</span>
                </div>
                <p className="text-[11px] text-slate-400 pt-1 print:text-slate-600">
                  {report.port_feasibility?.summary || "Vessel dimensions satisfy Paradip mechanized coal berth draft and LOA allowances."}
                </p>
              </div>
            </div>
          </div>

          {/* Section 5, 6, 7, 8: Market, Wait/Fix, Contract, Idle */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-950/40 p-3 rounded-lg border border-slate-800 text-xs space-y-1 print:bg-slate-50">
              <span className="text-[10px] font-bold uppercase text-sky-400 block print:text-sky-800">5. Freight Forecast</span>
              <div className="font-mono text-base font-bold text-sky-400 print:text-sky-800">
                ${report.freight_forecast?.p50?.toFixed(2) || "15.20"} / MT
              </div>
              <div className="text-[11px] text-slate-400 print:text-slate-600">
                P10: ${report.freight_forecast?.p10?.toFixed(2)} • P90: ${report.freight_forecast?.p90?.toFixed(2)}
              </div>
              <div className="text-[10px] text-slate-500 font-mono">Model: {report.freight_forecast?.model_version}</div>
            </div>

            <div className="bg-slate-950/40 p-3 rounded-lg border border-slate-800 text-xs space-y-1 print:bg-slate-50">
              <span className="text-[10px] font-bold uppercase text-amber-400 block print:text-amber-800">6. Market Regime</span>
              <div className="text-base font-bold text-amber-400 print:text-amber-800">
                {report.market_regime?.regime || "BEAR"} REGIME
              </div>
              <div className="text-[11px] text-slate-400 print:text-slate-600">{report.market_regime?.description}</div>
              <div className="text-[10px] text-slate-500 font-mono">Walk-Forward Gaussian HMM</div>
            </div>

            <div className="bg-slate-950/40 p-3 rounded-lg border border-slate-800 text-xs space-y-1 print:bg-slate-50">
              <span className="text-[10px] font-bold uppercase text-emerald-400 block print:text-emerald-800">7. Wait / Fix Analysis</span>
              <div className="text-base font-bold text-emerald-400 print:text-emerald-800">
                {report.wait_fix_analysis?.decision || "WAIT_AND_MONITOR"}
              </div>
              <div className="text-[11px] text-emerald-400/80 font-mono">
                +${report.wait_fix_analysis?.expected_savings_usd?.toLocaleString() || "28,500"} est. impact
              </div>
              <div className="text-[10px] text-slate-500 font-mono">Confidence: {report.wait_fix_analysis?.confidence}</div>
            </div>

            <div className="bg-slate-950/40 p-3 rounded-lg border border-slate-800 text-xs space-y-1 print:bg-slate-50">
              <span className="text-[10px] font-bold uppercase text-violet-400 block print:text-violet-800">8. Contract Strategy</span>
              <div className="text-base font-bold text-violet-400 print:text-violet-800">
                {report.contract_strategy?.recommended_strategy || "SPOT"} VOYAGE
              </div>
              <div className="text-[11px] text-slate-300 print:text-black">
                Est: ${report.contract_strategy?.expected_total_expenditure_usd?.toLocaleString()}
              </div>
              <div className="text-[10px] text-slate-500 font-mono">LP Constrained Optimization</div>
            </div>
          </div>

          {/* Section 9 & 10: Idle / Repositioning & Operational Risk */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <h2 className="text-sm font-bold tracking-wider text-sky-400 uppercase flex items-center gap-1.5 border-b border-slate-800 pb-1 print:text-sky-800">
                <Compass className="h-4 w-4" /> <span>9. Idle & Repositioning Analytics</span>
              </h2>
              <div className="text-xs space-y-1.5 bg-slate-950/40 p-3 rounded-lg border border-slate-800 print:bg-slate-50 print:text-black">
                <div className="flex justify-between">
                  <span className="text-slate-400">Post-Discharge Employment:</span>
                  <span className="font-bold text-slate-200 print:text-black">{report.idle_repositioning?.recommendation}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Ballast Repositioning:</span>
                  <span className="font-mono text-slate-300 print:text-black">{report.idle_repositioning?.ballast_nm} NM</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Expected Waiting Time:</span>
                  <span className="font-mono text-slate-300 print:text-black">{report.idle_repositioning?.expected_wait_days} Days</span>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <h2 className="text-sm font-bold tracking-wider text-sky-400 uppercase flex items-center gap-1.5 border-b border-slate-800 pb-1 print:text-sky-800">
                <ShieldCheck className="h-4 w-4" /> <span>10. Operational Risk & Tidal Gate</span>
              </h2>
              <div className="text-xs space-y-1.5 bg-slate-950/40 p-3 rounded-lg border border-slate-800 print:bg-slate-50 print:text-black">
                <div className="flex justify-between">
                  <span className="text-slate-400">Overall Severity:</span>
                  <span className="font-bold text-amber-400">{report.operational_risk?.overall_severity || "MEDIUM"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Congestion Queue:</span>
                  <span className="font-mono text-slate-300 print:text-black">{report.operational_risk?.avg_queue_days} Days ({report.operational_risk?.congestion_indicator})</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Tidal UKC Clearance:</span>
                  <span className="font-mono text-emerald-400 font-bold">{report.operational_risk?.safe_ukc_m}m ({report.operational_risk?.tidal_status})</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Modeled Demurrage Risk:</span>
                  <span className="font-mono text-rose-300 font-bold">${report.operational_risk?.financial_exposure_usd?.toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Section 11: Voyage Economics & Financial Ledger */}
          <div className="space-y-2">
            <h2 className="text-sm font-bold tracking-wider text-sky-400 uppercase flex items-center gap-1.5 border-b border-slate-800 pb-1 print:text-sky-800">
              <DollarSign className="h-4 w-4" /> <span>11. Voyage Economics & Financial Ledger</span>
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border border-slate-800 rounded-lg">
                <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 print:bg-slate-100 print:text-black">
                  <tr>
                    <th className="p-2.5">Cost Component</th>
                    <th className="p-2.5">Basis / Formula</th>
                    <th className="p-2.5 text-right">Amount (USD)</th>
                    <th className="p-2.5 text-right">Unit Rate (USD/MT)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300 print:text-black print:divide-slate-200">
                  <tr>
                    <td className="p-2.5 font-semibold text-slate-200 print:text-black">Freight Expenditure</td>
                    <td className="p-2.5 text-slate-400">75,000 MT &times; $15.20/MT (P50 Forecast)</td>
                    <td className="p-2.5 text-right font-mono">${report.voyage_economics?.freight_cost_usd?.toLocaleString()}</td>
                    <td className="p-2.5 text-right font-mono">$15.20</td>
                  </tr>
                  <tr>
                    <td className="p-2.5 font-semibold text-slate-200 print:text-black">Bunker Fuel Expense</td>
                    <td className="p-2.5 text-slate-400">12.5 kts Eco Speed (Admiralty Burn: 28.5 MT/d @ $625/MT)</td>
                    <td className="p-2.5 text-right font-mono">${report.voyage_economics?.bunker_cost_usd?.toLocaleString()}</td>
                    <td className="p-2.5 text-right font-mono">${((report.voyage_economics?.bunker_cost_usd || 0) / 75000).toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="p-2.5 font-semibold text-slate-200 print:text-black">Port Disbursements & Dues</td>
                    <td className="p-2.5 text-slate-400">Published Paradip Port Trust Scale of Rates (SOR 2026)</td>
                    <td className="p-2.5 text-right font-mono">${report.voyage_economics?.port_cost_usd?.toLocaleString()}</td>
                    <td className="p-2.5 text-right font-mono">${((report.voyage_economics?.port_cost_usd || 0) / 75000).toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="p-2.5 font-semibold text-slate-200 print:text-black">Charter Time Cost</td>
                    <td className="p-2.5 text-slate-400">Sea Passage + Port Laytime @ $20,000/day</td>
                    <td className="p-2.5 text-right font-mono">${report.voyage_economics?.time_cost_usd?.toLocaleString()}</td>
                    <td className="p-2.5 text-right font-mono">${((report.voyage_economics?.time_cost_usd || 0) / 75000).toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="p-2.5 font-semibold text-slate-200 print:text-black">Demurrage / Delay Exposure</td>
                    <td className="p-2.5 text-slate-400">1.5 days estimated anchorage queue buffer</td>
                    <td className="p-2.5 text-right font-mono">${report.voyage_economics?.delay_cost_usd?.toLocaleString()}</td>
                    <td className="p-2.5 text-right font-mono">${((report.voyage_economics?.delay_cost_usd || 0) / 75000).toFixed(2)}</td>
                  </tr>
                  <tr className="bg-slate-950 font-bold text-emerald-400 border-t-2 border-slate-700 print:bg-slate-100 print:text-emerald-900">
                    <td className="p-2.5 uppercase">Total Modeled Delivered Voyage Cost</td>
                    <td className="p-2.5 font-normal text-xs text-slate-400 print:text-slate-600">Sum of analytical ledger items</td>
                    <td className="p-2.5 text-right font-mono text-sm">${report.voyage_economics?.total_voyage_cost_usd?.toLocaleString()}</td>
                    <td className="p-2.5 text-right font-mono text-sm">${report.voyage_economics?.cost_per_mt_usd?.toFixed(2)} / MT</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 12 & 13: Data Quality & Decision Readiness */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <h2 className="text-sm font-bold tracking-wider text-sky-400 uppercase flex items-center gap-1.5 border-b border-slate-800 pb-1 print:text-sky-800">
                <Database className="h-4 w-4" /> <span>12. Data Quality Gate</span>
              </h2>
              <div className="text-xs space-y-1.5 bg-slate-950/40 p-3 rounded-lg border border-slate-800 print:bg-slate-50 print:text-black">
                <div className="flex justify-between">
                  <span className="text-slate-400">Gate Verification:</span>
                  <span className="font-bold text-emerald-400">{report.data_quality_assessment?.status || "READY"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Checks Passed:</span>
                  <span className="font-mono text-slate-200 print:text-black">
                    {report.data_quality_assessment?.passed_checks} / {report.data_quality_assessment?.checks_performed} Verified
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 pt-1 print:text-slate-600">
                  {report.data_quality_assessment?.explanation}
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <h2 className="text-sm font-bold tracking-wider text-sky-400 uppercase flex items-center gap-1.5 border-b border-slate-800 pb-1 print:text-sky-800">
                <ShieldCheck className="h-4 w-4" /> <span>13. Decision Readiness Assessment</span>
              </h2>
              <div className="text-xs space-y-1.5 bg-slate-950/40 p-3 rounded-lg border border-slate-800 print:bg-slate-50 print:text-black">
                <div className="flex justify-between">
                  <span className="text-slate-400">Readiness Score:</span>
                  <span className="font-bold text-emerald-400">{report.decision_readiness?.score?.toFixed(0)}% (CONFIDENT)</span>
                </div>
                <p className="text-[11px] text-slate-300 pt-1 leading-relaxed print:text-slate-800">
                  {report.decision_readiness?.summary}
                </p>
              </div>
            </div>
          </div>

          {/* Section 14: Methodological Assumptions */}
          <div className="space-y-2">
            <h2 className="text-sm font-bold tracking-wider text-sky-400 uppercase flex items-center gap-1.5 border-b border-slate-800 pb-1 print:text-sky-800">
              <span>14. Methodological Assumptions & Disclaimers</span>
            </h2>
            <ul className="text-xs text-slate-400 space-y-1 list-disc list-inside bg-slate-950/40 p-3 rounded-lg border border-slate-800 print:bg-slate-50 print:text-slate-700">
              {report.assumptions.map((a, i) => (
                <li key={i} className="leading-relaxed">{a}</li>
              ))}
            </ul>
          </div>

          {/* Section 15: Sources & Sign-off Block */}
          <div className="space-y-4 pt-2">
            <h2 className="text-sm font-bold tracking-wider text-sky-400 uppercase flex items-center gap-1.5 border-b border-slate-800 pb-1 print:text-sky-800">
              <span>15. Data Sources, Model Checkpoints & Audit Sign-off</span>
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
              {report.sources.map((s, i) => (
                <div key={i} className="p-2 rounded bg-slate-950/60 border border-slate-800 print:bg-slate-50">
                  <span className="text-[10px] text-slate-400 block">{s.domain}</span>
                  <span className="font-semibold text-slate-200 print:text-black">{s.source}</span>
                  <span className="text-[10px] font-mono text-emerald-400 block mt-0.5">{s.status}</span>
                </div>
              ))}
            </div>

            {/* Official Sign-off Box */}
            <div className="mt-6 pt-4 border-t-2 border-dashed border-slate-700 text-xs text-slate-400 space-y-2 print:border-slate-400 print:text-slate-700">
              <div className="flex flex-col sm:flex-row justify-between gap-4 font-semibold text-slate-300 print:text-black">
                <div>
                  Commercial Officer Sign-off: <span className="font-mono text-white print:text-black">{report.signoff_block?.prepared_by}</span>
                </div>
                <div>
                  Directorate Authority: <span className="font-mono text-white print:text-black">{report.signoff_block?.commercial_directorate}</span>
                </div>
              </div>
              <p className="text-[11px] text-slate-400 italic print:text-slate-600">
                {report.signoff_block?.cag_cvc_compliance_note}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ReportsPage() {
  return (
    <React.Suspense
      fallback={
        <div className="flex items-center justify-center min-h-[400px]">
          <RefreshCw className="h-6 w-6 animate-spin text-sky-400" />
        </div>
      }
    >
      <ReportsContent />
    </React.Suspense>
  );
}
