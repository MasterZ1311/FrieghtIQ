import React from "react";
import { DataStatus } from "@/types";
import { Badge } from "@/components/ui/badge";

interface DataStatusBadgeProps {
  status: DataStatus | "DATA PENDING" | "DEMO DATA" | string;
  className?: string;
  size?: "xs" | "sm" | "md";
}

export const DataStatusBadge: React.FC<DataStatusBadgeProps> = ({
  status,
  className = "",
  size = "sm",
}) => {
  const getStyle = (val: string) => {
    switch (val) {
      case "LIVE":
        return "bg-emerald-500/15 border-emerald-500/30 text-emerald-500 dark:text-emerald-400";
      case "RECENT":
        return "bg-cyan-500/15 border-cyan-500/30 text-cyan-500 dark:text-cyan-300";
      case "DEMO":
      case "DEMO DATA":
      case "SYNTHETIC":
      case "DEMO ENVIRONMENT":
        return "bg-primary/15 border-primary/30 text-primary";
      case "STALE":
      case "DATA PENDING":
        return "bg-amber-500/15 border-amber-500/30 text-amber-500 dark:text-amber-400";
      case "UNAVAILABLE":
      case "DATA UNAVAILABLE":
        return "bg-destructive/15 border-destructive/30 text-destructive";
      case "UNKNOWN":
      default:
        return "bg-muted border-border text-muted-foreground";
    }
  };

  const pad =
    size === "xs"
      ? "px-1.5 py-0.5 text-[10px] h-4"
      : size === "md"
      ? "px-3 py-1 text-xs h-6"
      : "px-2 py-0.5 text-[11px] h-5";

  const displayText = status === "DEMO" ? "DEMO DATA" : status;

  return (
    <Badge
      variant="outline"
      className={`inline-flex items-center gap-1.5 font-mono font-medium uppercase tracking-wider ${pad} ${getStyle(
        status
      )} ${className}`}
    >
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          status === "LIVE"
            ? "bg-emerald-400 animate-pulse"
            : status === "DEMO" || status === "DEMO DATA" || status === "SYNTHETIC" || status === "DEMO ENVIRONMENT"
            ? "bg-primary"
            : status === "STALE" || status === "DATA PENDING"
            ? "bg-amber-400"
            : "bg-muted-foreground"
        }`}
      />
      {displayText}
    </Badge>
  );
};
