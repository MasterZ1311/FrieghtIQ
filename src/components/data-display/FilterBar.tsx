"use client";

import React from "react";
import { Filter, X } from "lucide-react";

export interface FilterOption {
  label: string;
  value: string;
}

export interface FilterGroup {
  id: string;
  name: string;
  options: FilterOption[];
  selectedValue: string;
  onChange: (val: string) => void;
}

interface FilterBarProps {
  groups: FilterGroup[];
  onReset?: () => void;
  className?: string;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  groups,
  onReset,
  className = "",
}) => {
  const hasActiveFilter = groups.some(
    (g) => g.selectedValue !== "ALL" && g.selectedValue !== ""
  );

  return (
    <div
      className={`flex flex-wrap items-center gap-3 p-3 rounded-xl border border-border bg-surface-elevated/40 text-xs ${className}`}
    >
      <div className="flex items-center gap-1.5 text-slate-400 font-mono text-[11px] uppercase tracking-wider mr-1">
        <Filter className="h-3.5 w-3.5 text-blue-400" />
        <span>Filters:</span>
      </div>

      {groups.map((group) => (
        <div key={group.id} className="flex items-center gap-1.5">
          <label className="text-slate-400 font-medium text-[11px]">
            {group.name}:
          </label>
          <select
            value={group.selectedValue}
            onChange={(e) => group.onChange(e.target.value)}
            className="bg-background border border-border rounded-lg px-2.5 py-1 text-slate-200 focus:outline-none focus:border-blue-500 text-xs"
          >
            {group.options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      ))}

      {hasActiveFilter && onReset && (
        <button
          onClick={onReset}
          className="ml-auto inline-flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200 px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 transition-colors"
        >
          <X className="h-3 w-3" />
          <span>Reset Filters</span>
        </button>
      )}
    </div>
  );
};
