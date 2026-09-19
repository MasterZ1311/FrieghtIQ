import React from "react";

interface FreightIqLogoProps {
  collapsed?: boolean;
  className?: string;
  size?: "sm" | "md" | "lg";
}

export const FreightIqLogo: React.FC<FreightIqLogoProps> = ({
  collapsed = false,
  className = "",
  size = "md",
}) => {
  const iconSize = size === "sm" ? 28 : size === "lg" ? 40 : 32;

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Nautical Navigational + Route Vector Mark */}
      <div
        className="relative flex items-center justify-center rounded-lg bg-gradient-to-br from-blue-700 via-blue-800 to-slate-900 border border-blue-500/30 shadow-md shadow-blue-900/30 shrink-0"
        style={{ width: iconSize, height: iconSize }}
      >
        <svg
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-5/6 h-5/6 text-blue-400"
        >
          {/* Base F stem */}
          <path
            d="M8 6H24M8 6V26M8 15H20"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Maritime wave / route telemetry pulse */}
          <path
            d="M14 24C16.5 22 19 26 22 24C24 22.5 25.5 23.5 26 24"
            stroke="#38BDF8"
            strokeWidth="2.5"
            strokeLinecap="round"
          />
          {/* Signal beacon dot */}
          <circle cx="23" cy="7" r="2" fill="#60A5FA" />
        </svg>
      </div>

      {!collapsed && (
        <div className="flex flex-col select-none">
          <div className="flex items-center gap-1.5">
            <span className="font-bold tracking-wider text-base text-slate-100 font-sans">
              FREIGHT<span className="text-blue-400 font-extrabold ml-0.5">IQ</span>
            </span>
            <span className="text-[9px] font-semibold uppercase tracking-widest px-1.5 py-0.5 rounded bg-blue-950/80 border border-blue-800/50 text-blue-300">
              SAIL
            </span>
          </div>
          <span className="text-[10px] text-slate-400 tracking-tight font-medium">
            Maritime Intelligence System
          </span>
        </div>
      )}
    </div>
  );
};
