import React from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { MetricKPI } from "@/types";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export interface MetricCardProps {
  kpi?: MetricKPI;
  title?: string;
  label?: string;
  value?: string | number;
  subtitle?: string;
  subtext?: string;
  changePercent?: number;
  change?: string;
  changeType?: "positive" | "negative" | "neutral" | string;
  trend?: "up" | "down" | "neutral";
  status?: string;
  badgeLabel?: string;
  className?: string;
  onClick?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  kpi,
  title: propTitle,
  label: propLabel,
  value: propValue,
  subtitle: propSubtitle,
  subtext: propSubtext,
  changePercent: propChangePercent,
  trend: propTrend,
  status: propStatus,
  badgeLabel: propBadgeLabel,
  className = "",
  onClick,
}) => {
  const title = propTitle || propLabel || kpi?.title || "METRIC";
  const value = propValue !== undefined ? propValue : kpi?.value ?? "—";
  const subtitle = propSubtitle || propSubtext || kpi?.subtitle;
  const changePercent = propChangePercent !== undefined ? propChangePercent : kpi?.changePercent;
  const trend = propTrend || kpi?.trend;
  const badgeLabel = propBadgeLabel || kpi?.badgeLabel || propStatus || kpi?.status || "LIVE DATA";

  return (
    <Card
      onClick={onClick}
      className={`group relative overflow-hidden transition-all duration-200 hover:ring-2 hover:ring-primary/40 ${
        onClick ? "cursor-pointer" : ""
      } ${className}`}
    >
      <CardContent className="p-4 flex flex-col justify-between h-full">
        {/* Top row: Title and Status Badge */}
        <div className="flex items-center justify-between gap-2 mb-2">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground truncate font-mono">
            {title}
          </span>
          <Badge variant="outline" className="text-[10px] font-mono py-0 px-1.5 h-4 text-foreground dark:text-white border-primary/30 bg-primary/5">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse mr-1" />
            {badgeLabel}
          </Badge>
        </div>

        {/* Main Metric Value */}
        <div className="flex items-baseline justify-between gap-2 my-1">
          <div className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground font-mono tabular-nums">
            {value}
          </div>

          {changePercent !== undefined && changePercent !== null && (
            <div
              className={`inline-flex items-center gap-1 text-xs font-semibold tabular-nums font-mono ${
                trend === "up"
                  ? "text-emerald-500"
                  : trend === "down"
                  ? "text-rose-500"
                  : "text-muted-foreground"
              }`}
            >
              {trend === "up" && <TrendingUp className="h-3.5 w-3.5" />}
              {trend === "down" && <TrendingDown className="h-3.5 w-3.5" />}
              {trend === "neutral" && <Minus className="h-3.5 w-3.5" />}
              <span>{changePercent > 0 ? `+${changePercent}%` : `${changePercent}%`}</span>
            </div>
          )}
        </div>

        {/* Subtitle / Operational Context */}
        {subtitle && (
          <p className="text-xs text-muted-foreground truncate font-sans mt-0.5">
            {subtitle}
          </p>
        )}

        {/* Subtle indicator bar */}
        <div className="absolute bottom-0 left-3 right-3 h-0.5 bg-border group-hover:bg-primary transition-colors" />
      </CardContent>
    </Card>
  );
};
