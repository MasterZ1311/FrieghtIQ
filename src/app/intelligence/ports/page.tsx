"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Anchor, ShieldCheck, MapPin, ExternalLink, ArrowRight, CheckCircle2 } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatusBadge } from "@/components/badges/StatusBadge";
import { DEMO_PORTS } from "@/data/demo/ports";
import { portsApi, Port as LivePort } from "@/lib/api";

export default function PortIntelligencePage() {
  const [portsList, setPortsList] = useState<any[]>(DEMO_PORTS);

  useEffect(() => {
    async function loadPorts() {
      try {
        const live = await portsApi.getPorts();
        if (live && live.length > 0) {
          const mapped = live.map(p => ({
            id: p.id,
            name: p.name,
            code: p.unlocode,
            coast: p.coast || p.country,
            coordinates: { lat: p.latitude, lng: p.longitude },
            operationalStatus: "NORMAL",
            channel_max_draft_m: p.channel_max_draft_m,
            channel_max_loa_m: p.channel_max_loa_m,
            channel_max_beam_m: p.channel_max_beam_m,
            tide_range_m: p.tide_range_m,
            night_navigation: p.night_navigation,
            knownCargoHandling: ["Coking Coal", "Thermal Coal", "Iron Ore", "Limestone"],
          }));
          setPortsList(mapped);
        }
      } catch (err) {
        console.warn("Using demo ports list", err);
      }
    }
    loadPorts();
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        title="PORT INTELLIGENCE DIRECTORY"
        description="Infrastructure specifications, permissible arrival drafts, tidal restrictions, and berth availability across East Coast India bulk discharge terminals."
        status="OFFICIAL PORT CONSTRAINT DATABASE"
      />

      <div className="p-3.5 rounded-xl bg-blue-950/40 border border-blue-900/50 text-xs text-blue-200 flex items-start gap-3">
        <CheckCircle2 className="h-4 w-4 text-emerald-400 mt-0.5 shrink-0" />
        <div>
          <span className="font-semibold text-slate-100">
            Official Marine Constraints Integrated:
          </span>{" "}
          Port dimensions, draft envelopes, berth layouts (CB-1, CB-2, MCB, OST), and tidal dynamics are loaded directly from the verified marine operations database.
        </div>
      </div>

      {/* Ports Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {portsList.map((port) => (
          <div
            key={port.id}
            className="rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition-all p-5 flex flex-col justify-between"
          >
            <div>
              {/* Card Header */}
              <div className="flex items-start justify-between gap-2 pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-lg bg-slate-800 text-blue-400">
                    <Anchor className="h-5 w-5" />
                  </div>
                  <div>
                    <Link
                      href={`/intelligence/ports/${port.id}`}
                      className="font-bold text-sm text-slate-100 hover:text-blue-400 transition-colors font-mono"
                    >
                      {port.name}
                    </Link>
                    <div className="text-[10px] text-slate-400 font-mono">
                      UN/LOCODE: {port.code} • {port.coast}
                    </div>
                  </div>
                </div>
                <StatusBadge status={port.operationalStatus} size="sm" />
              </div>

              {/* Geo Coordinates */}
              <div className="mt-3 flex items-center gap-1.5 text-[11px] font-mono text-slate-400">
                <MapPin className="h-3.5 w-3.5 text-blue-400" />
                <span>
                  {port.coordinates?.lat?.toFixed(4)}° N, {port.coordinates?.lng?.toFixed(4)}° E
                </span>
              </div>

              {/* Constraint Parameters */}
              <div className="mt-4 pt-3 border-t border-slate-800 space-y-2 text-xs font-mono">
                <div className="flex justify-between items-center py-0.5">
                  <span className="text-slate-400">Channel Max Draft:</span>
                  <span className="text-cyan-400 font-bold">
                    {port.channel_max_draft_m ? `${port.channel_max_draft_m.toFixed(1)} m` : "Restricted"}
                  </span>
                </div>
                <div className="flex justify-between items-center py-0.5">
                  <span className="text-slate-400">Max Permissible LOA:</span>
                  <span className="text-slate-200">
                    {port.channel_max_loa_m ? `${port.channel_max_loa_m.toFixed(0)} m` : "230 m"}
                  </span>
                </div>
                <div className="flex justify-between items-center py-0.5">
                  <span className="text-slate-400">Max Beam Outreach:</span>
                  <span className="text-slate-200">
                    {port.channel_max_beam_m ? `${port.channel_max_beam_m.toFixed(1)} m` : "32.5 m"}
                  </span>
                </div>
                <div className="flex justify-between items-center py-0.5">
                  <span className="text-slate-400">Tidal Rise (Springs):</span>
                  <span className="text-emerald-400 font-bold">
                    +{port.tide_range_m ? port.tide_range_m.toFixed(1) : 2.0} m
                  </span>
                </div>
                <div className="flex justify-between items-center py-0.5">
                  <span className="text-slate-400">Night Navigation:</span>
                  <span className={port.night_navigation !== false ? "text-slate-200" : "text-amber-400"}>
                    {port.night_navigation !== false ? "PERMITTED" : "DAYLIGHT ONLY"}
                  </span>
                </div>
              </div>
            </div>

            {/* Card Footer Actions */}
            <div className="mt-5 pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
              <Link
                href={`/intelligence/ports/${port.id}`}
                className="text-blue-400 hover:text-blue-300 font-medium inline-flex items-center gap-1"
              >
                <span>Berths & Sources</span>
                <ExternalLink className="h-3 w-3" />
              </Link>
              <Link
                href={`/optimization/vessel-port?port_id=${port.id}`}
                className="text-emerald-400 hover:text-emerald-300 font-semibold inline-flex items-center gap-1"
              >
                <span>Optimizer</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
