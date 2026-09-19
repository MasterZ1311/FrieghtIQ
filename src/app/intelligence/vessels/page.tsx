"use client";

import React, { useState } from "react";
import { Ship, Info } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { DataTable, ColumnDef } from "@/components/data-display/DataTable";
import { StatusBadge } from "@/components/badges/StatusBadge";
import { DataStatusBadge } from "@/components/badges/DataStatusBadge";
import { DEMO_VESSELS } from "@/data/demo/vessels";
import { Vessel } from "@/types";

export default function VesselIntelligencePage() {
  const columns: ColumnDef<Vessel>[] = [
    {
      header: "Vessel",
      accessorKey: "name",
      cell: (v) => (
        <div>
          <div className="font-bold text-slate-100 flex items-center gap-1.5">
            <Ship className="h-3.5 w-3.5 text-blue-400 shrink-0" />
            <span>{v.name}</span>
          </div>
          <div className="text-[10px] text-slate-400 font-mono">
            IMO: {v.imoNumber}
          </div>
        </div>
      ),
    },
    {
      header: "Class",
      accessorKey: "vesselClass",
      cell: (v) => (
        <span className="font-mono text-xs font-semibold text-blue-300">
          {v.vesselClass}
        </span>
      ),
    },
    {
      header: "DWT (MT)",
      accessorKey: "dwtMT",
      cell: (v) => (
        <span className="font-mono text-xs text-slate-200">
          {typeof v.dwtMT === "number" ? v.dwtMT.toLocaleString() : v.dwtMT}
        </span>
      ),
    },
    {
      header: "LOA (m)",
      accessorKey: "loaMeters",
      cell: (v) => (
        <span className="font-mono text-xs text-slate-300">
          {typeof v.loaMeters === "number" ? `${v.loaMeters}m` : v.loaMeters}
        </span>
      ),
    },
    {
      header: "Beam (m)",
      accessorKey: "beamMeters",
      cell: (v) => (
        <span className="font-mono text-xs text-slate-300">
          {typeof v.beamMeters === "number" ? `${v.beamMeters}m` : v.beamMeters}
        </span>
      ),
    },
    {
      header: "Draft (m)",
      accessorKey: "draftMeters",
      cell: (v) => (
        <span className="font-mono text-xs text-slate-300">
          {typeof v.draftMeters === "number" ? `${v.draftMeters}m` : v.draftMeters}
        </span>
      ),
    },
    {
      header: "Status",
      accessorKey: "status",
      cell: (v) => <StatusBadge status={v.status} size="sm" />,
    },
    {
      header: "Current Port",
      accessorKey: "currentPort",
      cell: (v) => (
        <span className="font-mono text-xs text-slate-300">
          {v.currentPort}
        </span>
      ),
    },
    {
      header: "Next Port",
      accessorKey: "nextPort",
      cell: (v) => (
        <span className="font-mono text-xs text-slate-300">
          {v.nextPort}
        </span>
      ),
    },
    {
      header: "Data Status",
      cell: (v) => <DataStatusBadge status={v.dataStatus} size="xs" />,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="VESSEL INTELLIGENCE"
        description="Monitor vessel availability, physical dimensions, cargo suitability, and operational positions across bulk supply corridors."
        status="DEMO ENVIRONMENT"
      />

      <div className="p-3.5 rounded-xl bg-blue-950/40 border border-blue-900/50 text-xs text-blue-200 flex items-center gap-2.5">
        <Info className="h-4 w-4 text-blue-400 shrink-0" />
        <span>
          <strong>Data Honesty Standard:</strong> Physical vessel parameters without verified naval registry filings are explicitly labeled as <span className="font-mono font-bold text-slate-300">UNKNOWN</span>. Live AIS transponder integrations will link in Phase 02.
        </span>
      </div>

      <DataTable
        data={DEMO_VESSELS}
        columns={columns}
        searchPlaceholder="Search vessel directory by name, IMO, port..."
        pageSize={6}
      />
    </div>
  );
}
