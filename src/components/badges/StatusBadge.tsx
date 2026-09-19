import React from "react";
import { OperationalStatus, RequestStatus } from "@/types";
import { Badge } from "@/components/ui/badge";

interface StatusBadgeProps {
  status: OperationalStatus | RequestStatus | string;
  size?: "sm" | "md";
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = "sm",
  className = "",
}) => {
  const getBadgeVariant = (val: string) => {
    switch (val) {
      case "ACTIVE":
      case "READY FOR ANALYSIS":
      case "COMPLETED":
        return "bg-emerald-500/15 border-emerald-500/30 text-emerald-500 dark:text-emerald-400";
      case "AVAILABLE":
        return "bg-cyan-500/15 border-cyan-500/30 text-cyan-500 dark:text-cyan-300";
      case "AT SEA":
        return "bg-primary/15 border-primary/30 text-primary";
      case "AT PORT":
        return "bg-indigo-500/15 border-indigo-500/30 text-indigo-400";
      case "AT ANCHORAGE":
      case "ANALYZING":
        return "bg-amber-500/15 border-amber-500/30 text-amber-500 dark:text-amber-400";
      case "DATA INCOMPLETE":
      case "INACTIVE":
      case "UNAVAILABLE":
        return "bg-rose-500/15 border-rose-500/30 text-rose-500 dark:text-rose-400";
      case "DRAFT":
        return "bg-muted border-border text-muted-foreground";
      case "UNKNOWN":
      default:
        return "bg-muted/60 border-border text-muted-foreground";
    }
  };

  const pad = size === "sm" ? "px-2 py-0.5 text-[11px] h-5" : "px-2.5 py-1 text-xs h-6";

  return (
    <Badge
      variant="outline"
      className={`inline-flex items-center gap-1.5 font-medium tracking-wide uppercase ${pad} ${getBadgeVariant(
        status
      )} ${className}`}
    >
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          status === "ACTIVE" || status === "AVAILABLE" || status === "READY FOR ANALYSIS"
            ? "bg-emerald-400 animate-pulse"
            : status === "AT SEA"
            ? "bg-primary"
            : status === "ANALYZING"
            ? "bg-amber-400 animate-pulse"
            : "bg-current opacity-70"
        }`}
      />
      {status}
    </Badge>
  );
};
