"use client";

import React from "react";
import { Settings, Shield, Sliders, Database, Bell } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { DataStatusBadge } from "@/components/badges/DataStatusBadge";

export default function SettingsPage() {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <PageHeader
        title="SYSTEM SETTINGS & PREFERENCES"
        description="Global system parameters, organization units, default currency/units, and telemetry configurations."
        status="DEMO ENVIRONMENT"
      />

      <div className="space-y-4">
        {/* Organization Unit Section */}
        <div className="rounded-xl border border-border bg-surface p-5 space-y-3">
          <div className="flex items-center gap-2 pb-2 border-b border-border-subtle">
            <Shield className="h-4 w-4 text-blue-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Procurement Organization Context
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Organization:</label>
              <div className="p-2.5 rounded-lg bg-surface-elevated font-semibold text-slate-200 border border-border-subtle">
                Steel Authority of India Limited (SAIL)
              </div>
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Ministry / Dept:</label>
              <div className="p-2.5 rounded-lg bg-surface-elevated font-semibold text-slate-200 border border-border-subtle">
                Ministry of Steel, Government of India
              </div>
            </div>
          </div>
        </div>

        {/* Currency & Maritime Units */}
        <div className="rounded-xl border border-border bg-surface p-5 space-y-3">
          <div className="flex items-center gap-2 pb-2 border-b border-border-subtle">
            <Sliders className="h-4 w-4 text-cyan-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Units of Measurement & Monetary Standards
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Freight Currency:</label>
              <div className="p-2.5 rounded-lg bg-surface-elevated font-mono text-slate-200 border border-border-subtle">
                USD ($) / Metric Ton
              </div>
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Cargo Measure:</label>
              <div className="p-2.5 rounded-lg bg-surface-elevated font-mono text-slate-200 border border-border-subtle">
                Metric Tons (MT)
              </div>
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Distance & Speed:</label>
              <div className="p-2.5 rounded-lg bg-surface-elevated font-mono text-slate-200 border border-border-subtle">
                Nautical Miles (NM) / Knots (kts)
              </div>
            </div>
          </div>
        </div>

        {/* Telemetry Mode */}
        <div className="rounded-xl border border-border bg-surface p-5 space-y-3">
          <div className="flex items-center gap-2 pb-2 border-b border-border-subtle">
            <Database className="h-4 w-4 text-sky-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Telemetry Execution Environment
            </h3>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-surface-elevated border border-border-subtle">
            <div>
              <div className="font-semibold text-xs text-slate-200">
                Operating Mode: Phase 01 Staging Archetype
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                All data stores operate in transparent demo mode with strict metadata honesty tags.
              </div>
            </div>
            <DataStatusBadge status="DEMO ENVIRONMENT" size="sm" />
          </div>
        </div>
      </div>
    </div>
  );
}
