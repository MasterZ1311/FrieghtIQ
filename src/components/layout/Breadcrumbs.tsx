"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight, Home } from "lucide-react";

export const Breadcrumbs: React.FC = () => {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  const formatSegment = (seg: string) => {
    return seg
      .replace(/-/g, " ")
      .replace(/\b\w/g, (char) => char.toUpperCase());
  };

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs text-slate-400">
      <Link
        href="/dashboard"
        className="flex items-center gap-1 hover:text-slate-200 transition-colors"
      >
        <Home className="h-3.5 w-3.5 text-slate-500" />
        <span className="hidden sm:inline">Command Center</span>
      </Link>

      {segments.length > 0 && segments[0] !== "dashboard" && (
        <>
          {segments.map((segment, index) => {
            const url = `/${segments.slice(0, index + 1).join("/")}`;
            const isLast = index === segments.length - 1;

            return (
              <React.Fragment key={url}>
                <ChevronRight className="h-3 w-3 text-slate-600 shrink-0" />
                {isLast ? (
                  <span className="font-semibold text-slate-200 truncate max-w-[150px] sm:max-w-none">
                    {formatSegment(segment)}
                  </span>
                ) : (
                  <Link
                    href={url}
                    className="hover:text-slate-200 transition-colors capitalize truncate max-w-[120px]"
                  >
                    {formatSegment(segment)}
                  </Link>
                )}
              </React.Fragment>
            );
          })}
        </>
      )}
    </nav>
  );
};
