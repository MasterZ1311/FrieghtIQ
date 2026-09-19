"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Search, Ship, Anchor, Layers, FileText, Compass, X } from "lucide-react";
import { DEMO_VESSELS } from "@/data/demo/vessels";
import { DEMO_PORTS } from "@/data/demo/ports";
import { DEMO_REQUESTS } from "@/data/demo/requests";
import { DataStatusBadge } from "@/components/badges/DataStatusBadge";

interface GlobalSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type SearchCategory = "ALL" | "VESSELS" | "PORTS" | "REQUESTS" | "REPORTS";

export const GlobalSearchModal: React.FC<GlobalSearchModalProps> = ({
  isOpen,
  onClose,
}) => {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<SearchCategory>("ALL");
  const [query, setQuery] = useState("");

  if (!isOpen) return null;

  const q = query.toLowerCase();

  const matchedVessels = DEMO_VESSELS.filter(
    (v) =>
      v.name.toLowerCase().includes(q) ||
      v.vesselClass.toLowerCase().includes(q) ||
      v.currentPort.toLowerCase().includes(q)
  );

  const matchedPorts = DEMO_PORTS.filter(
    (p) =>
      p.name.toLowerCase().includes(q) ||
      p.code.toLowerCase().includes(q) ||
      p.knownCargoHandling.some((c) => c.toLowerCase().includes(q))
  );

  const matchedRequests = DEMO_REQUESTS.filter(
    (r) =>
      r.referenceNumber.toLowerCase().includes(q) ||
      r.cargoType.toLowerCase().includes(q) ||
      r.originPort.toLowerCase().includes(q) ||
      r.destinationPort.toLowerCase().includes(q)
  );

  const handleNavigate = (path: string) => {
    router.push(path);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-20 px-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="fixed inset-0" onClick={onClose} />

      <div className="relative w-full max-w-2xl rounded-xl border border-border bg-surface-elevated shadow-2xl overflow-hidden z-10 flex flex-col max-h-[85vh]">
        {/* Search header */}
        <div className="p-4 border-b border-border-subtle bg-surface flex items-center gap-3">
          <Search className="h-5 w-5 text-blue-400 shrink-0" />
          <input
            type="text"
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search vessels, East Coast ports, active cargo requests..."
            className="flex-1 bg-transparent text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none"
          />
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-surface-hover"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Category Tabs & Notice */}
        <div className="px-4 py-2 bg-surface-elevated/40 border-b border-border-subtle flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-1">
            {(["ALL", "VESSELS", "PORTS", "REQUESTS", "REPORTS"] as SearchCategory[]).map(
              (tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-2.5 py-1 rounded-md text-xs font-mono transition-colors ${
                    activeTab === tab
                      ? "bg-blue-900/60 text-blue-300 border border-blue-700/50"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {tab}
                </button>
              )
            )}
          </div>
          <DataStatusBadge status="DEMO SEARCH" size="xs" />
        </div>

        {/* Results Body */}
        <div className="overflow-y-auto p-3 space-y-4">
          {/* Vessels Group */}
          {(activeTab === "ALL" || activeTab === "VESSELS") && matchedVessels.length > 0 && (
            <div>
              <div className="px-2 py-1 text-[11px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Ship className="h-3.5 w-3.5 text-blue-400" />
                <span>Vessels ({matchedVessels.length})</span>
              </div>
              <div className="mt-1 space-y-1">
                {matchedVessels.map((v) => (
                  <div
                    key={v.id}
                    onClick={() => handleNavigate("/intelligence/vessels")}
                    className="flex items-center justify-between p-2.5 rounded-lg hover:bg-surface-hover cursor-pointer text-xs transition-colors border border-transparent hover:border-border"
                  >
                    <div>
                      <span className="font-semibold text-slate-200">{v.name}</span>
                      <span className="text-slate-400 ml-2 font-mono">
                        {v.vesselClass} • DWT: {v.dwtMT.toLocaleString()} MT
                      </span>
                    </div>
                    <span className="text-[11px] font-mono text-cyan-400">
                      {v.currentPort} → {v.nextPort}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Ports Group */}
          {(activeTab === "ALL" || activeTab === "PORTS") && matchedPorts.length > 0 && (
            <div>
              <div className="px-2 py-1 text-[11px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Anchor className="h-3.5 w-3.5 text-cyan-400" />
                <span>East Coast Ports ({matchedPorts.length})</span>
              </div>
              <div className="mt-1 space-y-1">
                {matchedPorts.map((p) => (
                  <div
                    key={p.id}
                    onClick={() => handleNavigate("/intelligence/ports")}
                    className="flex items-center justify-between p-2.5 rounded-lg hover:bg-surface-hover cursor-pointer text-xs transition-colors border border-transparent hover:border-border"
                  >
                    <div>
                      <span className="font-semibold text-slate-200">{p.name}</span>
                      <span className="text-slate-400 ml-2 font-mono">({p.code})</span>
                    </div>
                    <span className="text-[11px] text-amber-400 font-mono">
                      DATA PENDING
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Requests Group */}
          {(activeTab === "ALL" || activeTab === "REQUESTS") && matchedRequests.length > 0 && (
            <div>
              <div className="px-2 py-1 text-[11px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Layers className="h-3.5 w-3.5 text-emerald-400" />
                <span>Cargo Requests ({matchedRequests.length})</span>
              </div>
              <div className="mt-1 space-y-1">
                {matchedRequests.map((r) => (
                  <div
                    key={r.id}
                    onClick={() => handleNavigate("/chartering/requests")}
                    className="flex items-center justify-between p-2.5 rounded-lg hover:bg-surface-hover cursor-pointer text-xs transition-colors border border-transparent hover:border-border"
                  >
                    <div>
                      <span className="font-semibold text-slate-200">{r.referenceNumber}</span>
                      <span className="text-slate-400 ml-2 font-mono">
                        {r.quantityMT.toLocaleString()} MT {r.cargoType}
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {r.originPort} → {r.destinationPort}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Empty / Not found */}
          {matchedVessels.length === 0 && matchedPorts.length === 0 && matchedRequests.length === 0 && (
            <div className="p-8 text-center text-xs text-slate-400">
              No matching records found across simulated maritime databases.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2.5 bg-surface border-t border-border-subtle flex items-center justify-between text-[11px] text-slate-400">
          <span>Search scope: Static Archetype Datasets (Phase 01)</span>
          <span className="text-blue-400 font-mono">Ready for Elasticsearch / PostgreSQL API</span>
        </div>
      </div>
    </div>
  );
};
