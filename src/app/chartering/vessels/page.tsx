"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Ship, ArrowUpRight, Search, ShieldAlert, Anchor, ArrowRight } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { DataTable, ColumnDef } from "@/components/data-display/DataTable";
import { FilterBar, FilterGroup } from "@/components/data-display/FilterBar";
import { StatusBadge } from "@/components/badges/StatusBadge";
import { DataStatusBadge } from "@/components/badges/DataStatusBadge";
import { DEMO_VESSELS } from "@/data/demo/vessels";
import { Vessel as DemoVessel } from "@/types";
import { vesselsApi, Vessel as LiveVessel } from "@/lib/api";

export default function VesselSearchPage() {
  const [classFilter, setClassFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [vesselsList, setVesselsList] = useState<any[]>(DEMO_VESSELS);

  useEffect(() => {
    async function loadVessels() {
      try {
        const live = await vesselsApi.getVessels();
        if (live && live.length > 0) {
          const mapped = live.map(v => ({
            id: v.id,
            name: v.vessel_name,
            imoNumber: v.imo_number,
            flag: v.flag || "India",
            vesselClass: v.vessel_class,
            dwtMT: v.particulars?.summer_dwt ? `${v.particulars.summer_dwt.toLocaleString()} MT` : "UNKNOWN",
            loaMeters: v.particulars?.loa_m || "—",
            beamMeters: v.particulars?.beam_m || "—",
            draftMeters: v.particulars?.summer_draft_m ? `${v.particulars.summer_draft_m.toFixed(2)}m` : "—",
            status: v.availability?.current_status || "AVAILABLE",
            currentPort: v.availability?.current_port_name || "En Route",
            nextPort: v.availability?.open_port_name || "Prompt Orders",
            estimatedAvailabilityDate: v.availability?.open_date_start ? new Date(v.availability.open_date_start).toLocaleDateString() : "Prompt",
            dataStatus: v.is_snapshot_vessel ? (v.particulars?.is_verified ? "VERIFIED" : "PARTIAL") : "VERIFIED",
            is_snapshot_vessel: v.is_snapshot_vessel,
          }));
          setVesselsList([...mapped]);
        }
      } catch (err) {
        console.warn("Using demo vessels list", err);
      }
    }
    loadVessels();
  }, []);

  const filteredVessels = vesselsList.filter((v) => {
    if (classFilter !== "ALL" && !v.vesselClass.toUpperCase().includes(classFilter.toUpperCase())) return false;
    if (statusFilter !== "ALL" && v.status !== statusFilter) return false;
    return true;
  });

  const filterGroups: FilterGroup[] = [
    {
      id: "vesselClass",
      name: "Vessel Class",
      selectedValue: classFilter,
      onChange: setClassFilter,
      options: [
        { label: "All Classes", value: "ALL" },
        { label: "Capesize (120k+ DWT)", value: "Capesize" },
        { label: "Panamax / Kamsarmax", value: "Panamax" },
        { label: "Supramax (50k-65k DWT)", value: "Supramax" },
        { label: "Handysize (<40k DWT)", value: "Handysize" },
      ],
    },
    {
      id: "status",
      name: "Operational Status",
      selectedValue: statusFilter,
      onChange: setStatusFilter,
      options: [
        { label: "All Statuses", value: "ALL" },
        { label: "Available", value: "AVAILABLE" },
        { label: "At Sea", value: "BALLAST_TRANSIT" },
        { label: "At Anchorage", value: "AT_ANCHORAGE" },
      ],
    },
  ];

  const columns: ColumnDef<any>[] = [
    {
      header: "Vessel Name / IMO",
      accessorKey: "name",
      cell: (v) => (
        <div>
          <div className="font-bold text-slate-100 flex items-center gap-1.5">
            <Ship className="h-3.5 w-3.5 text-blue-400 shrink-0" />
            <Link href={`/intelligence/vessels/${v.id}`} className="hover:text-blue-400 transition-colors">
              {v.name}
            </Link>
            {v.is_snapshot_vessel && (
              <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                SNAPSHOT
              </span>
            )}
          </div>
          <div className="text-[10px] text-slate-400 font-mono">
            IMO: {v.imoNumber} • Flag: {v.flag}
          </div>
        </div>
      ),
    },
    {
      header: "Class & DWT",
      cell: (v) => (
        <div>
          <div className="font-bold text-blue-300 font-mono text-xs">
            {v.vesselClass}
          </div>
          <div className="text-[11px] text-slate-300 font-mono font-semibold">
            {v.dwtMT}
          </div>
        </div>
      ),
    },
    {
      header: "Dimensions (LOA × Beam × Draft)",
      cell: (v) => (
        <span className="font-mono text-xs text-slate-300">
          {v.loaMeters}m × {v.beamMeters}m × {v.draftMeters}
        </span>
      ),
    },
    {
      header: "Status",
      accessorKey: "status",
      cell: (v) => <StatusBadge status={v.status} size="sm" />,
    },
    {
      header: "Current / Next Port",
      cell: (v) => (
        <div className="text-xs font-mono">
          <span className="text-slate-400">{v.currentPort}</span>
          <span className="text-slate-500 mx-1">→</span>
          <span className="text-slate-200 font-semibold">{v.nextPort}</span>
        </div>
      ),
    },
    {
      header: "Availability Window",
      accessorKey: "estimatedAvailabilityDate",
      cell: (v) => (
        <span className="font-mono text-xs text-emerald-400 font-medium">
          {v.estimatedAvailabilityDate}
        </span>
      ),
    },
    {
      header: "Actions",
      cell: (v) => (
        <div className="flex items-center gap-2">
          <Link
            href={`/intelligence/vessels/${v.id}`}
            className="text-xs text-blue-400 hover:text-blue-300 font-medium inline-flex items-center gap-1"
          >
            <span>Particulars</span>
            <ArrowUpRight className="h-3 w-3" />
          </Link>
          <Link
            href={`/optimization/vessel-port?vessel_id=${v.id}`}
            className="text-xs text-emerald-400 hover:text-emerald-300 font-semibold inline-flex items-center gap-1"
          >
            <Anchor className="h-3 w-3" />
            <span>Feasibility</span>
          </Link>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="VESSEL SEARCH & CHARTER MATCHING"
        description="Filter and discover bulk tonnage available across overseas origin loading ports and Bay of Bengal trade lanes."
        status="LIVE VESSEL FLEET"
      />

      <FilterBar
        groups={filterGroups}
        onReset={() => {
          setClassFilter("ALL");
          setStatusFilter("ALL");
        }}
      />

      <DataTable
        data={filteredVessels}
        columns={columns}
        searchPlaceholder="Filter vessels by name, IMO, port, flag..."
        pageSize={6}
      />
    </div>
  );
}
