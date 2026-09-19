"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { 
  Ship, Filter, CheckCircle, AlertTriangle, XCircle, 
  HelpCircle, RefreshCw, ArrowRight, Anchor, ChevronDown, ChevronUp, AlertCircle
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { matchingApi, MatchingRun, MatchingCandidate } from "@/lib/api";

export default function CandidateVesselsMatchingPage() {
  const params = useParams();
  const id = params.id as string;

  const [matchRun, setMatchRun] = useState<MatchingRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [expandedCandidates, setExpandedCandidates] = useState<Record<string, boolean>>({});

  const fetchMatches = async () => {
    try {
      setLoading(true);
      const res = await matchingApi.getLatestForRequirement(id);
      setMatchRun(res);
      // Automatically expand first two candidates
      if (res.candidates.length > 0) {
        setExpandedCandidates({
          [res.candidates[0].id]: true,
          ...(res.candidates[1] ? { [res.candidates[1].id]: true } : {})
        });
      }
    } catch (err) {
      console.error("Failed to load vessel matching run", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMatches();
  }, [id]);

  const toggleExpand = (candId: string) => {
    setExpandedCandidates(prev => ({ ...prev, [candId]: !prev[candId] }));
  };

  const filteredCandidates = matchRun?.candidates.filter(c => {
    if (filterStatus === "ALL") return true;
    return c.overall_status === filterStatus;
  }) || [];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "RELEVANT":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-500/40">
            <CheckCircle className="h-3.5 w-3.5" /> RELEVANT
          </span>
        );
      case "PARTIAL":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-950/80 text-amber-300 border border-amber-500/40">
            <AlertTriangle className="h-3.5 w-3.5" /> PARTIAL
          </span>
        );
      case "UNKNOWN":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-950/80 text-indigo-300 border border-indigo-500/40">
            <HelpCircle className="h-3.5 w-3.5" /> UNKNOWN / UNVERIFIED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-950/80 text-rose-300 border border-rose-500/40">
            <XCircle className="h-3.5 w-3.5" /> NOT RELEVANT
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
        <Link href="/chartering/requests" className="hover:text-slate-200">
          REQUESTS
        </Link>
        <span>/</span>
        <Link href={`/chartering/requests/${id}`} className="text-slate-300 hover:text-blue-400">
          REQUIREMENT DETAIL
        </Link>
        <span>/</span>
        <span className="text-blue-400">CANDIDATE MATCHING</span>
      </div>

      <PageHeader
        title="DETERMINISTIC VESSEL MATCHING"
        description="Rule-governed candidate filtering based on technical deadweight, laycan timing, vessel class suitability, and data completeness."
        status="MULTI-RULE EVALUATION"
        actions={
          <button
            onClick={() => fetchMatches()}
            disabled={loading}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition-colors"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin text-blue-400' : ''}`} />
            <span>Re-evaluate</span>
          </button>
        }
      />

      {/* Summary Scorecard */}
      {matchRun && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/80">
            <div className="text-[10px] font-mono text-slate-400 uppercase">Total Evaluated</div>
            <div className="text-2xl font-bold font-mono text-slate-100 mt-1">{matchRun.total_evaluated}</div>
          </div>
          <div className="p-3.5 rounded-xl border border-emerald-900/40 bg-emerald-950/20">
            <div className="text-[10px] font-mono text-emerald-400 uppercase">Relevant Fit</div>
            <div className="text-2xl font-bold font-mono text-emerald-300 mt-1">{matchRun.relevant_count}</div>
          </div>
          <div className="p-3.5 rounded-xl border border-amber-900/40 bg-amber-950/20">
            <div className="text-[10px] font-mono text-amber-400 uppercase">Partial Match</div>
            <div className="text-2xl font-bold font-mono text-amber-300 mt-1">{matchRun.partial_count}</div>
          </div>
          <div className="p-3.5 rounded-xl border border-indigo-900/40 bg-indigo-950/20">
            <div className="text-[10px] font-mono text-indigo-400 uppercase">Unverified / Unknown</div>
            <div className="text-2xl font-bold font-mono text-indigo-300 mt-1">{matchRun.unknown_count}</div>
          </div>
          <div className="p-3.5 rounded-xl border border-rose-900/40 bg-rose-950/20">
            <div className="text-[10px] font-mono text-rose-400 uppercase">Not Relevant</div>
            <div className="text-2xl font-bold font-mono text-rose-300 mt-1">{matchRun.not_relevant_count}</div>
          </div>
        </div>
      )}

      {/* Filters Bar */}
      <div className="flex items-center gap-2 p-2 rounded-lg bg-slate-900/80 border border-slate-800 text-xs">
        <Filter className="h-4 w-4 text-slate-400 ml-2" />
        <span className="text-slate-400 font-mono">STATUS FILTER:</span>
        {["ALL", "RELEVANT", "PARTIAL", "UNKNOWN", "NOT_RELEVANT"].map(st => (
          <button
            key={st}
            onClick={() => setFilterStatus(st)}
            className={`px-3 py-1 rounded-md font-mono text-xs transition-colors ${
              filterStatus === st
                ? "bg-primary text-white font-semibold shadow-sm"
                : "text-slate-300 hover:bg-slate-800"
            }`}
          >
            {st}
          </button>
        ))}
      </div>

      {/* Candidates List */}
      <div className="space-y-4">
        {filteredCandidates.map(candidate => {
          const vessel = candidate.vessel;
          const isExpanded = !!expandedCandidates[candidate.id];

          return (
            <div
              key={candidate.id}
              className="rounded-xl border border-slate-800 bg-slate-900/70 hover:border-slate-700 transition-all overflow-hidden"
            >
              {/* Card Header Row */}
              <div className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-3">
                    <Ship className="h-5 w-5 text-blue-400 shrink-0" />
                    <Link
                      href={`/intelligence/vessels/${vessel?.id}`}
                      className="text-base font-bold text-slate-100 hover:text-blue-400 transition-colors font-mono"
                    >
                      {vessel?.vessel_name || "Unknown Vessel"}
                    </Link>
                    <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 font-mono text-[11px] text-slate-300">
                      {vessel?.vessel_class}
                    </span>
                    {vessel?.is_snapshot_vessel && (
                      <span className="px-2 py-0.5 rounded bg-indigo-950 border border-indigo-700/60 font-mono text-[10px] text-indigo-300 font-semibold" title="Vessel observed in operational handling records">
                        SNAPSHOT VESSEL
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-400 flex flex-wrap gap-x-4 gap-y-1">
                    <span>IMO: <span className="font-mono text-slate-300">{vessel?.imo_number}</span></span>
                    <span>Flag: <span className="font-mono text-slate-300">{vessel?.flag || "N/A"}</span></span>
                    <span>Built: <span className="font-mono text-slate-300">{vessel?.year_built || "N/A"}</span></span>
                    <span>Summer DWT: <span className="font-mono text-cyan-400 font-bold">{vessel?.particulars?.summer_dwt ? `${vessel.particulars.summer_dwt.toLocaleString()} MT` : "UNKNOWN"}</span></span>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  {getStatusBadge(candidate.overall_status)}
                  <Link
                    href={`/optimization/vessel-port?vessel_id=${vessel?.id}`}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-200 transition-colors"
                  >
                    <Anchor className="h-3.5 w-3.5 text-emerald-400" />
                    <span>Port Feasibility</span>
                    <ArrowRight className="h-3 w-3 text-slate-400" />
                  </Link>
                  <button
                    onClick={() => toggleExpand(candidate.id)}
                    className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 transition-colors"
                    title={isExpanded ? "Collapse rules" : "Expand rules"}
                  >
                    {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                  </button>
                </div>
              </div>

              {/* Summary Explanation Bar */}
              <div className="px-4 py-2 bg-slate-950/50 border-t border-slate-800/80 text-xs text-slate-300 flex items-center justify-between">
                <div>
                  <span className="font-semibold text-slate-400">Synthesis: </span>
                  <span>{candidate.summary_explanation}</span>
                </div>
                {!candidate.is_data_complete && (
                  <span className="text-amber-400 font-mono text-[11px] flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" /> Missing Data: {candidate.missing_fields}
                  </span>
                )}
              </div>

              {/* Detailed Rule Breakdown (Collapsible) */}
              {isExpanded && (
                <div className="p-4 bg-slate-950/80 border-t border-slate-800 space-y-2">
                  <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-2">
                    Deterministic Multi-Rule Evaluation Results:
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {candidate.rule_results.map(rule => (
                      <div
                        key={rule.rule_name}
                        className="p-3 rounded-lg border border-slate-800/80 bg-slate-900/60 space-y-1.5"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] font-mono font-bold text-slate-200">
                            {rule.rule_name.replace(/_/g, ' ')}
                          </span>
                          <span className={`text-[10px] font-bold font-mono px-1.5 py-0.5 rounded ${
                            rule.status === "RELEVANT" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" :
                            rule.status === "PARTIAL" ? "bg-amber-950 text-amber-400 border border-amber-800" :
                            rule.status === "UNKNOWN" ? "bg-indigo-950 text-indigo-400 border border-indigo-800" :
                            "bg-rose-950 text-rose-400 border border-rose-800"
                          }`}>
                            {rule.status}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-400 flex justify-between font-mono">
                          <span>Evaluated: <strong className="text-slate-200">{rule.evaluated_value || "N/A"}</strong></span>
                          <span>Required: <strong className="text-slate-200">{rule.required_value || "N/A"}</strong></span>
                        </div>
                        <p className="text-[11px] text-slate-400 leading-tight">
                          {rule.explanation}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {filteredCandidates.length === 0 && (
          <div className="p-12 text-center text-slate-400 bg-slate-900/40 rounded-xl border border-slate-800">
            No candidates matched the selected filter &apos;{filterStatus}&apos;.
          </div>
        )}
      </div>
    </div>
  );
}
