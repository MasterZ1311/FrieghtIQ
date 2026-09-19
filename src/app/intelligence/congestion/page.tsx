"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Anchor,
  Clock,
  DollarSign,
  AlertTriangle,
  Ship,
  TrendingUp,
  RefreshCw,
  SlidersHorizontal,
  ChevronRight,
  Info,
  Calendar,
  Layers,
  ArrowRight,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { RiskBadge } from "@/components/badges/RiskBadge";
import { DataStatusBadge } from "@/components/badges/DataStatusBadge";
import { riskApi, CongestionEvaluationResponse, PortCongestion } from "@/lib/api/risk";
import { portsApi, Port } from "@/lib/api/ports";

export default function CongestionIntelligencePage() {
  const [ports, setPorts] = useState<Port[]>([]);
  const [selectedPortId, setSelectedPortId] = useState<string>("port-inprt");
  const [vesselClass, setVesselClass] = useState<string>("PANAMAX");
  const [laytimeHours, setLaytimeHours] = useState<number>(36);
  const [demurrageRate, setDemurrageRate] = useState<number>(18000);

  const [congestionData, setCongestionData] = useState<CongestionEvaluationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  // Initial load of ports
  useEffect(() => {
    async function loadPorts() {
      try {
        const pList = await portsApi.getPorts();
        setPorts(pList);
        if (pList.length > 0 && !pList.find((p: any) => p.id === selectedPortId)) {
          setSelectedPortId(pList[0].id);
        }
      } catch (err) {
        console.error("Failed fetching ports:", err);
      }
    }
    loadPorts();
  }, []);

  // Fetch congestion evaluation for selected port & parameters
  const fetchCongestion = async (showRefreshSpinner = false) => {
    try {
      if (showRefreshSpinner) setRefreshing(true);
      else setLoading(true);

      const res = await riskApi.getPortCongestionDetail(selectedPortId, {
        vessel_class: vesselClass,
        laytime_hours: laytimeHours,
        demurrage_rate: demurrageRate,
      });
      setCongestionData(res);
    } catch (err) {
      console.error("Error fetching congestion details:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (selectedPortId) {
      fetchCongestion();
    }
  }, [selectedPortId, vesselClass, laytimeHours, demurrageRate]);

  const selectedPort = ports.find((p) => p.id === selectedPortId);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        title="PORT CONGESTION & ANCHORAGE INTELLIGENCE"
        description="Real-time anchorage queue depth, berth occupancy rates, turnaround delays, and contractual demurrage exposure calculations."
        status="OPERATIONAL INTELLIGENCE"
        actions={
          <button
            onClick={() => fetchCongestion(true)}
            disabled={refreshing}
            className="flex items-center gap-2 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-amber-400" : ""}`} />
            Refresh Queue
          </button>
        }
      />

      {/* Port Selector Strip */}
      <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-slate-400">Select Monitored Terminal:</span>
          {[
            { id: "port-inprt", name: "Paradip (INPRT)" },
            { id: "port-inhal", name: "Haldia (INHAL)" },
            { id: "port-invtz", name: "Visakhapatnam (INVTZ)" },
            { id: "port-indhm", name: "Dhamra (INDHM)" },
            { id: "port-sgsin", name: "Singapore (SGSIN)" },
            { id: "port-auncb", name: "Newcastle (AUNCB)" },
            { id: "port-zarcb", name: "Richards Bay (ZARCB)" },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setSelectedPortId(item.id)}
              className={`px-3 py-1.5 text-xs font-mono rounded transition ${
                selectedPortId === item.id
                  ? "bg-amber-500 text-slate-950 font-bold shadow-md shadow-amber-500/20"
                  : "bg-slate-950 border border-slate-800 text-slate-300 hover:border-slate-700"
              }`}
            >
              {item.name}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Vessel Class:</span>
          <select
            value={vesselClass}
            onChange={(e) => setVesselClass(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 font-mono focus:outline-none focus:border-amber-500"
          >
            <option value="PANAMAX">Panamax / Kamsarmax</option>
            <option value="CAPESIZE">Capesize (180k DWT)</option>
            <option value="SUPRAMAX">Supramax (58k DWT)</option>
          </select>
        </div>
      </div>

      {/* Primary KPI Strip */}
      {congestionData && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 relative">
            <span className="text-xs font-medium text-slate-400">Congestion Indicator</span>
            <div className="mt-2 flex items-center gap-2">
              <span
                className={`px-3 py-1 text-xs font-mono font-bold uppercase rounded border ${
                  congestionData.indicator === "CRITICAL" || congestionData.indicator === "SEVERE"
                    ? "bg-rose-950 border-rose-600 text-rose-300"
                    : congestionData.indicator === "MODERATE"
                    ? "bg-amber-950 border-amber-600 text-amber-300"
                    : "bg-emerald-950 border-emerald-600 text-emerald-300"
                }`}
              >
                {congestionData.indicator} CONGESTION
              </span>
            </div>
            <p className="mt-2 text-[11px] text-slate-500">
              Assessed via berth occupancy & queue wait thresholds
            </p>
          </div>

          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800">
            <span className="text-xs font-medium text-slate-400">Waiting Vessels at Anchorage</span>
            <div className="mt-2 text-2xl font-mono font-bold text-slate-100 flex items-baseline gap-2">
              <span>{congestionData.congestion_data?.waiting_vessels_count || 14}</span>
              <span className="text-xs text-slate-400 font-normal">vessels</span>
            </div>
            <div className="mt-1 text-[11px] text-slate-400">
              Working at berth:{" "}
              <span className="text-emerald-400 font-mono font-semibold">
                {congestionData.congestion_data?.working_vessels_count || 8}
              </span>
            </div>
          </div>

          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800">
            <span className="text-xs font-medium text-slate-400">Pre-Berthing Wait Time</span>
            <div className="mt-2 text-2xl font-mono font-bold text-amber-400">
              {congestionData.avg_wait_hours} hrs
            </div>
            <div className="mt-1 text-[11px] text-slate-400">
              Avg Turnaround:{" "}
              <span className="font-mono text-slate-200">
                {congestionData.congestion_data?.avg_turnaround_hours || 76} hrs
              </span>
            </div>
          </div>

          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800">
            <span className="text-xs font-medium text-slate-400">Berth Occupancy Factor</span>
            <div className="mt-2 text-2xl font-mono font-bold text-sky-400">
              {congestionData.congestion_data?.berth_occupancy_pct || 88.5}%
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
              <div
                className={`h-full ${
                  (congestionData.congestion_data?.berth_occupancy_pct || 0) > 85
                    ? "bg-rose-500"
                    : (congestionData.congestion_data?.berth_occupancy_pct || 0) > 70
                    ? "bg-amber-500"
                    : "bg-emerald-500"
                }`}
                style={{ width: `${congestionData.congestion_data?.berth_occupancy_pct || 0}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Main Grid: Demurrage Exposure Calculator & Vessel Class Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Interactive Demurrage Calculator */}
        <div className="lg:col-span-6 p-5 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-emerald-400" />
                Demurrage Exposure Calculator
              </h3>
              <p className="text-xs text-slate-400">
                Models financial liability when pre-berthing waiting exceeds allowed charter laytime.
              </p>
            </div>
            <span className="px-2 py-0.5 text-[10px] font-mono uppercase rounded bg-slate-800 text-slate-300 border border-slate-700">
              Contract Model
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1">
                Contractual Laytime Allowed (Hours)
              </label>
              <input
                type="number"
                step="2"
                min="0"
                value={laytimeHours}
                onChange={(e) => setLaytimeHours(parseFloat(e.target.value) || 0)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-amber-500"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">
                Standard dry bulk charter: 36–48 hrs SHINC
              </span>
            </div>

            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1">
                Demurrage Rate ($/day)
              </label>
              <input
                type="number"
                step="500"
                min="0"
                value={demurrageRate}
                onChange={(e) => setDemurrageRate(parseFloat(e.target.value) || 0)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-amber-500"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">
                Hourly rate: ${(demurrageRate / 24).toFixed(0)}/hr
              </span>
            </div>
          </div>

          {congestionData && (
            <div className="p-4 rounded bg-slate-950/80 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Average Expected Waiting Time:</span>
                <span className="font-mono font-bold text-slate-200">{congestionData.avg_wait_hours} hrs</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Contract Laytime Allowance:</span>
                <span className="font-mono text-slate-300">{congestionData.laytime_allowed_hours} hrs</span>
              </div>
              <div className="flex items-center justify-between text-xs border-t border-slate-800 pt-2">
                <span className="text-slate-400">Hours on Demurrage:</span>
                <span
                  className={`font-mono font-bold ${
                    congestionData.demurrage_hours > 0 ? "text-rose-400" : "text-emerald-400"
                  }`}
                >
                  {congestionData.demurrage_hours} hrs
                </span>
              </div>

              <div className="flex items-center justify-between text-sm border-t border-slate-800 pt-2 font-semibold">
                <span className="text-slate-200">Modeled Demurrage Liability:</span>
                <span
                  className={`font-mono text-base ${
                    congestionData.demurrage_exposure_usd && congestionData.demurrage_exposure_usd > 0
                      ? "text-rose-400"
                      : "text-emerald-400"
                  }`}
                >
                  ${(congestionData.demurrage_exposure_usd || 0).toLocaleString()} USD
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Vessel Class Queue Breakdown */}
        <div className="lg:col-span-6 p-5 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Ship className="w-4 h-4 text-sky-400" />
                Queue Breakdown by Vessel Class
              </h3>
              <p className="text-xs text-slate-400">
                Segmented anchorage waiting time and queue depth by bulker size.
              </p>
            </div>
            <span className="text-xs font-mono text-slate-400">Live Segments</span>
          </div>

          <div className="space-y-3">
            <div className="p-3 rounded bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div className="space-y-0.5">
                <span className="text-xs font-semibold text-slate-200 block">Capesize (120k–200k DWT)</span>
                <span className="text-[11px] text-slate-400">Deep draft bulk iron ore / coking coal berths</span>
              </div>
              <div className="text-right font-mono text-xs">
                <span className="text-rose-400 font-bold block">
                  {congestionData?.congestion_data?.capesize_waiting_count || 6} waiting
                </span>
                <span className="text-slate-400">
                  Avg wait: {((congestionData?.avg_wait_hours || 42) * 1.25).toFixed(1)}h
                </span>
              </div>
            </div>

            <div className="p-3 rounded bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div className="space-y-0.5">
                <span className="text-xs font-semibold text-slate-200 block">Panamax / Kamsarmax (70k–85k DWT)</span>
                <span className="text-[11px] text-slate-400">Mechanized Coal Berths CB-1 / CB-2 / MCHP</span>
              </div>
              <div className="text-right font-mono text-xs">
                <span className="text-amber-400 font-bold block">
                  {congestionData?.congestion_data?.panamax_waiting_count || 6} waiting
                </span>
                <span className="text-slate-400">
                  Avg wait: {(congestionData?.avg_wait_hours || 42).toFixed(1)}h
                </span>
              </div>
            </div>

            <div className="p-3 rounded bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div className="space-y-0.5">
                <span className="text-xs font-semibold text-slate-200 block">Supramax / Ultramax (50k–65k DWT)</span>
                <span className="text-[11px] text-slate-400">Conventional grab & quay berths (CQ-1 / CQ-2)</span>
              </div>
              <div className="text-right font-mono text-xs">
                <span className="text-emerald-400 font-bold block">
                  {congestionData?.congestion_data?.supramax_waiting_count || 2} waiting
                </span>
                <span className="text-slate-400">
                  Avg wait: {((congestionData?.avg_wait_hours || 42) * 0.8).toFixed(1)}h
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 14-Day Queue & Waiting History */}
      {congestionData && congestionData.history && (
        <div className="p-5 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-amber-400" />
                14-Day Waiting Queue & Occupancy Telemetry
              </h3>
              <p className="text-xs text-slate-400">
                Historical daily pre-berthing wait hours and terminal berth saturation at {congestionData.port_name}.
              </p>
            </div>
            <DataStatusBadge status="RECENT" />
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2">
            {congestionData.history.map((pt, idx) => (
              <div
                key={idx}
                className="p-3 rounded bg-slate-950 border border-slate-800 text-center space-y-1"
              >
                <span className="text-[10px] font-mono text-slate-400 block">{pt.date.slice(5)}</span>
                <div className="text-sm font-mono font-bold text-amber-400">{pt.avg_waiting_hours}h</div>
                <div className="text-[10px] text-slate-500 font-mono">{pt.berth_occupancy_pct}% occ</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Explanations & Recommended Mitigations */}
      {congestionData && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              Operational Diagnosis
            </h4>
            <ul className="space-y-1.5 text-xs text-slate-300">
              {congestionData.explanations.map((exp, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                  <span>{exp}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-amber-400">
              Recommended Chartering Mitigations
            </h4>
            <ul className="space-y-1.5 text-xs text-slate-300">
              {congestionData.mitigations.map((mit, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                  <span>{mit}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
