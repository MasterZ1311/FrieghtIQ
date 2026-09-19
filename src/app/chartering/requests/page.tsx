"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { PlusCircle, Layers, ArrowUpRight, FileText, Ship, ArrowRight } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { DataTable, ColumnDef } from "@/components/data-display/DataTable";
import { StatusBadge } from "@/components/badges/StatusBadge";
import { FilterBar, FilterGroup } from "@/components/data-display/FilterBar";
import { DEMO_REQUESTS } from "@/data/demo/requests";
import { CargoRequest } from "@/types";
import { cargoApi } from "@/lib/api";

export default function ActiveRequestsPage() {
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [cargoFilter, setCargoFilter] = useState("ALL");
  const [requestsList, setRequestsList] = useState<any[]>(DEMO_REQUESTS);

  useEffect(() => {
    async function loadRequirements() {
      try {
        const liveReqs = await cargoApi.getRequirements();
        if (liveReqs && liveReqs.length > 0) {
          const mapped = liveReqs.map(r => ({
            id: r.id,
            referenceNumber: r.requirement_code,
            title: r.title,
            cargoType: r.cargo_type.replace(/_/g, ' '),
            quantityMT: r.quantity_mt,
            tolerancePercent: r.tolerance_pct,
            originPort: r.load_port?.name || "Newcastle (Australia)",
            destinationPort: r.discharge_port?.name || "Paradip (India)",
            laycanStart: new Date(r.laycan_start).toLocaleDateString(),
            laycanEnd: new Date(r.laycan_end).toLocaleDateString(),
            contractPreference: "Spot",
            status: r.status,
            createdAt: r.created_at,
          }));
          // Put live requirements first
          setRequestsList([...mapped, ...DEMO_REQUESTS]);
        }
      } catch (err) {
        console.warn("Using demo requests list", err);
      }
    }
    loadRequirements();
  }, []);

  const filteredRequests = requestsList.filter((req) => {
    if (statusFilter !== "ALL" && req.status !== statusFilter) return false;
    if (cargoFilter !== "ALL" && req.cargoType !== cargoFilter) return false;
    return true;
  });

  const filterGroups: FilterGroup[] = [
    {
      id: "status",
      name: "Request Status",
      selectedValue: statusFilter,
      onChange: setStatusFilter,
      options: [
        { label: "All Statuses", value: "ALL" },
        { label: "Ready for Analysis", value: "READY FOR ANALYSIS" },
        { label: "Analyzing", value: "ANALYZING" },
        { label: "Data Incomplete", value: "DATA INCOMPLETE" },
        { label: "Draft", value: "DRAFT" },
      ],
    },
    {
      id: "cargo",
      name: "Cargo Type",
      selectedValue: cargoFilter,
      onChange: setCargoFilter,
      options: [
        { label: "All Cargoes", value: "ALL" },
        { label: "Coking Coal", value: "Coking Coal" },
        { label: "Limestone", value: "Limestone" },
      ],
    },
  ];

  const columns: ColumnDef<CargoRequest>[] = [
    {
      header: "Request ID / Ref",
      accessorKey: "referenceNumber",
      cell: (req) => (
        <div>
          <div className="font-bold text-slate-100 font-mono flex items-center gap-1.5">
            <FileText className="h-3.5 w-3.5 text-blue-400 shrink-0" />
            <span>{req.referenceNumber}</span>
          </div>
          <div className="text-[10px] text-slate-400">ID: {req.id}</div>
        </div>
      ),
    },
    {
      header: "Cargo & Quantity",
      cell: (req) => (
        <div>
          <div className="font-semibold text-slate-200">{req.cargoType}</div>
          <div className="text-[11px] font-mono text-cyan-400">
            {req.quantityMT.toLocaleString()} MT (±{req.tolerancePercent}%)
          </div>
        </div>
      ),
    },
    {
      header: "Route (Origin → Dest)",
      cell: (req) => (
        <div className="font-mono text-xs">
          <span className="text-slate-400">{req.originPort}</span>
          <span className="text-blue-400 mx-1">→</span>
          <span className="text-slate-200 font-semibold">{req.destinationPort}</span>
        </div>
      ),
    },
    {
      header: "Target Laycan",
      cell: (req) => (
        <div className="text-xs font-mono text-slate-300">
          {req.laycanStart} to {req.laycanEnd}
        </div>
      ),
    },
    {
      header: "Contract Type",
      accessorKey: "contractPreference",
      cell: (req) => (
        <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 font-mono text-xs text-slate-200">
          {req.contractPreference}
        </span>
      ),
    },
    {
      header: "Status",
      accessorKey: "status",
      cell: (req) => <StatusBadge status={req.status} size="sm" />,
    },
    {
      header: "Created Date",
      accessorKey: "createdAt",
      cell: (req) => (
        <span className="text-[11px] font-mono text-slate-400">
          {req.createdAt.split("T")[0]}
        </span>
      ),
    },
    {
      header: "Actions",
      cell: (req) => (
        <div className="flex items-center gap-3">
          <Link
            href={`/chartering/requests/${req.id}`}
            className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 font-medium"
          >
            <span>Detail</span>
            <ArrowUpRight className="h-3 w-3" />
          </Link>
          <Link
            href={`/chartering/requests/${req.id}/vessels`}
            className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 font-semibold"
          >
            <Ship className="h-3 w-3" />
            <span>Match</span>
          </Link>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="ACTIVE CARGO REQUESTS"
        description="Monitor procurement lots, tender requests, and chartering lifecycles across SAIL integrated steel plants."
        status="DEMO ENVIRONMENT"
        actions={
          <Link
            href="/chartering/new"
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-primary hover:bg-primary-hover text-xs font-semibold text-white shadow-sm transition-colors"
          >
            <PlusCircle className="h-4 w-4" />
            <span>New Requirement</span>
          </Link>
        }
      />

      <FilterBar
        groups={filterGroups}
        onReset={() => {
          setStatusFilter("ALL");
          setCargoFilter("ALL");
        }}
      />

      <DataTable
        data={filteredRequests}
        columns={columns}
        searchPlaceholder="Search active requests by ref, cargo, port..."
        pageSize={5}
      />
    </div>
  );
}
