import React from "react";
import { ConfidenceLevel } from "@/types";

interface ConfidenceBadgeProps {
  level?: ConfidenceLevel | string;
  className?: string;
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({
  level = "UNRATED",
  className = "",
}) => {
  const getStyle = () => {
    switch (level) {
      case "HIGH":
        return "bg-emerald-950/60 border-emerald-700/60 text-emerald-300";
      case "MEDIUM":
        return "bg-cyan-950/60 border-cyan-700/60 text-cyan-300";
      case "LOW":
        return "bg-amber-950/60 border-amber-700/60 text-amber-300";
      case "UNRATED":
      default:
        return "bg-slate-900 border-slate-700 text-slate-400";
    }
  };

  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-mono tracking-tight uppercase rounded border ${getStyle()} ${className}`}
    >
      <span className="text-slate-400 font-sans">CONFIDENCE:</span>
      <span className="font-semibold">{level}</span>
    </span>
  );
};

interface SourceBadgeProps {
  source: string;
  className?: string;
}

export const SourceBadge: React.FC<SourceBadgeProps> = ({
  source,
  className = "",
}) => {
  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-mono text-slate-400 bg-slate-900/90 border border-slate-800 rounded tracking-tight ${className}`}
      title={`Data Provenance: ${source}`}
    >
      <span className="text-slate-400">SRC:</span>
      <span className="text-slate-300 truncate max-w-[140px]">{source}</span>
    </span>
  );
};
