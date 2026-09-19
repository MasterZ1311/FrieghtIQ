import React from "react";

export const SkeletonCard: React.FC<{ count?: number }> = ({ count = 1 }) => {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="rounded-xl border border-border bg-surface p-5 animate-pulse"
        >
          <div className="flex justify-between items-start mb-3">
            <div className="h-4 bg-slate-800 rounded w-28" />
            <div className="h-4 bg-slate-800 rounded w-12" />
          </div>
          <div className="h-8 bg-slate-800 rounded w-36 mb-2" />
          <div className="h-3 bg-slate-800 rounded w-48" />
        </div>
      ))}
    </>
  );
};

export const SkeletonTable: React.FC<{ rows?: number; cols?: number }> = ({
  rows = 5,
  cols = 6,
}) => {
  return (
    <div className="rounded-xl border border-border bg-surface overflow-hidden animate-pulse p-4">
      <div className="h-9 bg-slate-800/80 rounded mb-4 w-full" />
      <div className="space-y-3">
        {Array.from({ length: rows }).map((_, r) => (
          <div key={r} className="flex gap-4">
            {Array.from({ length: cols }).map((_, c) => (
              <div
                key={c}
                className="h-6 bg-slate-800/50 rounded flex-1"
                style={{ opacity: 1 - c * 0.1 }}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

export const SkeletonChart: React.FC = () => {
  return (
    <div className="rounded-xl border border-border bg-surface p-6 animate-pulse">
      <div className="flex justify-between mb-6">
        <div className="h-5 bg-slate-800 rounded w-44" />
        <div className="h-5 bg-slate-800 rounded w-24" />
      </div>
      <div className="h-64 bg-slate-800/30 rounded flex items-end justify-between p-4 gap-2">
        {Array.from({ length: 14 }).map((_, i) => (
          <div
            key={i}
            className="bg-slate-800/60 rounded-t w-full"
            style={{ height: `${20 + ((i * 17) % 70)}%` }}
          />
        ))}
      </div>
    </div>
  );
};
