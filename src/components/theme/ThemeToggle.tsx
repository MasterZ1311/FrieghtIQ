"use client";

import React, { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "./ThemeProvider";

export function ThemeToggle({ className = "" }: { className?: string }) {
  const { theme, toggleTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), 0);
    return () => clearTimeout(timer);
  }, []);

  if (!mounted) {
    return (
      <div className={`w-9 h-9 rounded-lg border border-border bg-surface flex items-center justify-center opacity-70 ${className}`}>
        <div className="w-4 h-4 rounded-full bg-slate-400/40 animate-pulse" />
      </div>
    );
  }

  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={`relative group p-2 rounded-lg border border-border bg-surface hover:bg-surface-hover transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500/40 ${className}`}
      title={isDark ? "Switch to Light Theme (White & Light Ash with Blue text)" : "Switch to Dark Theme (Black & Grey with Blue text)"}
      aria-label="Toggle Color Theme"
    >
      <div className="relative w-5 h-5 flex items-center justify-center">
        {isDark ? (
          <Sun className="w-4 h-4 text-blue-400 group-hover:text-blue-300 transition-transform duration-300 group-hover:rotate-45" />
        ) : (
          <Moon className="w-4 h-4 text-blue-600 group-hover:text-blue-700 transition-transform duration-300 group-hover:-rotate-12" />
        )}
      </div>
      <span className="sr-only">
        {isDark ? "Light Theme" : "Dark Theme"}
      </span>
    </button>
  );
}
