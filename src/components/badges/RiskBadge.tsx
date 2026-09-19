import React from "react";
import { Badge } from "@/components/ui/badge";

interface RiskBadgeProps {
  level: string;
  className?: string;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level, className = "" }) => {
  const norm = (level || "UNKNOWN").toUpperCase();
  const getStyle = () => {
    switch (norm) {
      case "CRITICAL":
        return "bg-destructive/20 border-destructive/40 text-destructive animate-pulse";
      case "HIGH":
        return "bg-rose-500/15 border-rose-500/30 text-rose-500 dark:text-rose-400";
      case "MEDIUM":
        return "bg-amber-500/15 border-amber-500/30 text-amber-500 dark:text-amber-400";
      case "LOW":
        return "bg-emerald-500/15 border-emerald-500/30 text-emerald-500 dark:text-emerald-400";
      case "UNKNOWN":
      default:
        return "bg-muted border-border text-muted-foreground";
    }
  };

  return (
    <Badge
      variant="outline"
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-[11px] font-semibold tracking-wider uppercase h-5 ${getStyle()} ${className}`}
    >
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          norm === "CRITICAL"
            ? "bg-destructive animate-ping"
            : norm === "HIGH"
            ? "bg-rose-400"
            : norm === "MEDIUM"
            ? "bg-amber-400"
            : norm === "LOW"
            ? "bg-emerald-400"
            : "bg-muted-foreground"
        }`}
      />
      {norm} RISK
    </Badge>
  );
};
