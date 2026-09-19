import React from "react";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { DataStatusBadge } from "@/components/badges/DataStatusBadge";

interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  status?: string;
  lastUpdated?: string;
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  actions,
  status = "DEMO ENVIRONMENT",
  lastUpdated,
  className = "",
}) => {
  return (
    <div className={`mb-6 pb-4 border-b border-border-subtle ${className}`}>
      {/* Breadcrumb line */}
      <div className="mb-2">
        <Breadcrumbs />
      </div>

      {/* Main title & Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100 uppercase font-sans">
              {title}
            </h1>
            {status && <DataStatusBadge status={status} size="xs" />}
          </div>

          {description && (
            <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
              {description}
            </p>
          )}
        </div>

        {/* Right side actions and timestamp */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 shrink-0">
          {lastUpdated && (
            <span className="text-[11px] font-mono text-slate-500">
              Updated: {lastUpdated}
            </span>
          )}
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      </div>
    </div>
  );
};
