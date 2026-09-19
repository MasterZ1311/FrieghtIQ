import React from "react";
import { LucideIcon, ShieldAlert, Compass, ArrowRight } from "lucide-react";
import Link from "next/link";

interface EmptyStateProps {
  title: string;
  description: string;
  statusLabel?: string;
  icon?: LucideIcon;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
  plannedPhase?: string;
  technicalSpecs?: string[];
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  statusLabel = "MODULE COMING IN NEXT PHASE",
  icon: Icon = Compass,
  actionLabel,
  actionHref,
  onAction,
  plannedPhase = "Phase 02 / 03 Integration",
  technicalSpecs,
  className = "",
}) => {
  return (
    <div
      className={`relative overflow-hidden rounded-xl border border-border bg-gradient-to-b from-surface to-surface-elevated/40 p-8 text-center sm:p-12 ${className}`}
    >
      {/* Background nautical grid watermark */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e3a5f15_1px,transparent_1px),linear-gradient(to_bottom,#1e3a5f15_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />

      <div className="relative z-10 mx-auto max-w-xl flex flex-col items-center">
        {/* Module Status Ribbon */}
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-950/60 px-3 py-1 text-xs font-semibold text-blue-400">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
          <span>{statusLabel}</span>
          <span className="text-slate-400">|</span>
          <span className="text-slate-400 font-normal">{plannedPhase}</span>
        </div>

        {/* Icon */}
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-xl border border-border bg-surface-elevated text-blue-400 shadow-inner">
          <Icon className="h-7 w-7" />
        </div>

        {/* Title & Description */}
        <h3 className="text-xl font-bold tracking-tight text-slate-100 mb-2">
          {title}
        </h3>
        <p className="text-sm text-slate-400 leading-relaxed max-w-lg mb-6">
          {description}
        </p>

        {/* Architectural Specs List if provided */}
        {technicalSpecs && technicalSpecs.length > 0 && (
          <div className="w-full max-w-md bg-background/80 rounded-lg border border-border-subtle p-4 mb-6 text-left">
            <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 block mb-2 font-semibold">
              Planned Engine Architecture:
            </span>
            <ul className="space-y-1.5 text-xs text-slate-300">
              {technicalSpecs.map((spec, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-blue-400 font-mono">›</span>
                  <span>{spec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Action Button */}
        {actionLabel && actionHref && (
          <Link
            href={actionHref}
            className="inline-flex items-center gap-2 rounded-lg bg-primary hover:bg-primary-hover px-4 py-2 text-xs font-semibold text-white shadow-sm transition-colors"
          >
            <span>{actionLabel}</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        )}

        {actionLabel && onAction && !actionHref && (
          <button
            onClick={onAction}
            className="inline-flex items-center gap-2 rounded-lg bg-primary hover:bg-primary-hover px-4 py-2 text-xs font-semibold text-white shadow-sm transition-colors"
          >
            <span>{actionLabel}</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        )}
      </div>
    </div>
  );
};
