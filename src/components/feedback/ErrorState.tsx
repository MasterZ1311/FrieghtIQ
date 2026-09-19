"use client";

import React, { useState } from "react";
import { AlertTriangle, RefreshCw, ChevronDown, ChevronUp } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  message?: string;
  details?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Something went wrong",
  message = "An unexpected error occurred while processing maritime logistics telemetry.",
  details,
  onRetry,
  className = "",
}) => {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div
      className={`rounded-xl border border-rose-900/50 bg-rose-950/20 p-6 text-center sm:p-8 ${className}`}
    >
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-rose-900/40 text-rose-400 border border-rose-800/50 mb-4">
        <AlertTriangle className="h-6 w-6" />
      </div>

      <h3 className="text-lg font-bold text-slate-100 mb-1">{title}</h3>
      <p className="text-sm text-slate-400 max-w-md mx-auto mb-5">{message}</p>

      <div className="flex flex-wrap items-center justify-center gap-3">
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-2 rounded-lg bg-rose-600 hover:bg-rose-500 px-4 py-2 text-xs font-semibold text-white transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Try Again</span>
          </button>
        )}

        {details && (
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-surface hover:bg-surface-elevated px-3 py-2 text-xs font-medium text-slate-300 transition-colors"
          >
            <span>{showDetails ? "Hide Details" : "View Details"}</span>
            {showDetails ? (
              <ChevronUp className="h-3.5 w-3.5" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5" />
            )}
          </button>
        )}
      </div>

      {showDetails && details && (
        <div className="mt-4 text-left p-3 rounded bg-slate-950/90 border border-slate-800 font-mono text-[11px] text-rose-300 overflow-x-auto max-w-lg mx-auto">
          <pre>{details}</pre>
        </div>
      )}
    </div>
  );
};
