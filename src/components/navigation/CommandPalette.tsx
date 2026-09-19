"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  PlusCircle,
  Ship,
  TrendingUp,
  Anchor,
  Cpu,
  Clock,
  Bot,
  Layers,
  FileText,
  ShieldCheck,
  Database,
  Sliders,
  X,
  ArrowRight,
} from "lucide-react";

interface CommandItem {
  id: string;
  title: string;
  category: string;
  icon: React.ElementType;
  route: string;
  keywords?: string[];
}

const COMMANDS: CommandItem[] = [
  {
    id: "cmd-new-charter",
    title: "New Charter Requirement",
    category: "Chartering",
    icon: PlusCircle,
    route: "/chartering/new",
    keywords: ["create", "cargo", "procure", "add", "laycan"],
  },
  {
    id: "cmd-active-requests",
    title: "Active Cargo Requests",
    category: "Chartering",
    icon: Layers,
    route: "/chartering/requests",
    keywords: ["list", "orders", "drafts", "table"],
  },
  {
    id: "cmd-search-vessel",
    title: "Search Vessel",
    category: "Chartering",
    icon: Ship,
    route: "/chartering/vessels",
    keywords: ["find", "capesize", "panamax", "tonnage", "fleet"],
  },
  {
    id: "cmd-compare-voyages",
    title: "Compare Voyages",
    category: "Chartering",
    icon: Layers,
    route: "/chartering/comparison",
    keywords: ["evaluate", "routes", "scenario", "costs"],
  },
  {
    id: "cmd-freight-forecast",
    title: "Open Freight Forecast",
    category: "Intelligence",
    icon: TrendingUp,
    route: "/intelligence/freight",
    keywords: ["predict", "rates", "bdi", "c5", "curve"],
  },
  {
    id: "cmd-market-regime",
    title: "Market Regime Classification",
    category: "Intelligence",
    icon: TrendingUp,
    route: "/intelligence/regime",
    keywords: ["bullish", "bearish", "volatility", "hmm"],
  },
  {
    id: "cmd-wait-fix",
    title: "Open Wait vs Fix",
    category: "Intelligence",
    icon: Clock,
    route: "/intelligence/wait-fix",
    keywords: ["timing", "delay", "entry", "posture"],
  },
  {
    id: "cmd-check-port",
    title: "Check Port Intelligence",
    category: "Intelligence",
    icon: Anchor,
    route: "/intelligence/ports",
    keywords: ["paradip", "vizag", "haldia", "draft", "berth"],
  },
  {
    id: "cmd-vessel-optimizer",
    title: "Run Vessel-Port Optimizer",
    category: "Optimization",
    icon: Cpu,
    route: "/optimization/vessel-port",
    keywords: ["constraint", "draft", "loa", "dwt", "match"],
  },
  {
    id: "cmd-contract-strategy",
    title: "Contract Strategy (Spot vs COA)",
    category: "Optimization",
    icon: Sliders,
    route: "/optimization/contracts",
    keywords: ["coa", "spot", "time charter", "hedging"],
  },
  {
    id: "cmd-copilot",
    title: "Open Chartering Copilot",
    category: "AI",
    icon: Bot,
    route: "/ai/copilot",
    keywords: ["assistant", "chat", "llm", "advisor"],
  },
  {
    id: "cmd-risk-center",
    title: "Open Risk Center",
    category: "Risk",
    icon: ShieldCheck,
    route: "/risk",
    keywords: ["exposure", "weather", "congestion", "mitigation"],
  },
  {
    id: "cmd-data-explorer",
    title: "Data Explorer",
    category: "Data",
    icon: Database,
    route: "/data/explorer",
    keywords: ["raw", "telemetry", "export", "sources"],
  },
  {
    id: "cmd-generate-report",
    title: "Generate Decision Report",
    category: "Reports",
    icon: FileText,
    route: "/reports",
    keywords: ["pdf", "summary", "audit", "procurement"],
  },
];

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Filter commands
  const filtered = COMMANDS.filter((cmd) => {
    if (!query) return true;
    const q = query.toLowerCase();
    return (
      cmd.title.toLowerCase().includes(q) ||
      cmd.category.toLowerCase().includes(q) ||
      cmd.keywords?.some((k) => k.includes(q))
    );
  });

  // Keyboard navigation
  useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => {
        setQuery("");
        setSelectedIndex(0);
        inputRef.current?.focus();
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev < filtered.length - 1 ? prev + 1 : 0));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : filtered.length - 1));
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (filtered[selectedIndex]) {
          router.push(filtered[selectedIndex].route);
          onClose();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, filtered, selectedIndex, router, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 px-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
      {/* Click outside backdrop */}
      <div className="fixed inset-0" onClick={onClose} />

      <div className="relative w-full max-w-xl rounded-xl border border-border bg-surface-elevated shadow-2xl overflow-hidden z-10 flex flex-col max-h-[80vh]">
        {/* Search Input Bar */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-border-subtle bg-surface">
          <Search className="h-4 w-4 text-blue-400 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            placeholder="Type a command or jump to module..."
            className="flex-1 bg-transparent text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none"
          />
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-surface-hover"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Results List */}
        <div className="overflow-y-auto p-2 divide-y divide-border-subtle/30">
          {filtered.length > 0 ? (
            filtered.map((item, idx) => {
              const Icon = item.icon;
              const isSelected = idx === selectedIndex;

              return (
                <div
                  key={item.id}
                  onClick={() => {
                    router.push(item.route);
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`flex items-center justify-between gap-3 px-3 py-2.5 rounded-lg text-xs cursor-pointer transition-colors ${
                    isSelected
                      ? "bg-blue-600/20 text-blue-200 border border-blue-500/30"
                      : "text-slate-300 hover:bg-surface-hover border border-transparent"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-1.5 rounded-md ${
                        isSelected ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                    </div>
                    <div>
                      <div className="font-semibold">{item.title}</div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {item.category} • {item.route}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {isSelected && (
                      <span className="text-[10px] text-blue-400 font-mono hidden sm:inline">
                        Press Enter ↵
                      </span>
                    )}
                    <ArrowRight className="h-3.5 w-3.5 text-slate-500" />
                  </div>
                </div>
              );
            })
          ) : (
            <div className="p-8 text-center text-xs text-slate-400">
              No matching commands found for &ldquo;{query}&rdquo;
            </div>
          )}
        </div>

        {/* Footer shortcuts helper */}
        <div className="px-4 py-2 bg-surface border-t border-border-subtle flex items-center justify-between text-[11px] text-slate-400">
          <div className="flex items-center gap-3">
            <span>
              <kbd className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px] text-slate-300">
                ↑↓
              </kbd>{" "}
              Navigate
            </span>
            <span>
              <kbd className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px] text-slate-300">
                ↵
              </kbd>{" "}
              Select
            </span>
            <span>
              <kbd className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px] text-slate-300">
                ESC
              </kbd>{" "}
              Close
            </span>
          </div>
          <span className="font-mono text-[10px] text-blue-400">FREIGHT IQ Command Hub</span>
        </div>
      </div>
    </div>
  );
};
