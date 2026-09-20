"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  PlusCircle,
  Layers,
  Search,
  GitCompare,
  TrendingUp,
  BarChart3,
  Clock,
  Ship,
  Anchor,
  AlertCircle,
  CloudRain,
  Waves,
  Cpu,
  FileCheck,
  DollarSign,
  Hourglass,
  Gauge,
  Bot,
  ShieldCheck,
  CheckCircle2,
  Database,
  FileText,
  UploadCloud,
  Brain,
  Settings,
  ChevronLeft,
  ChevronRight,
  X,
} from "lucide-react";
import { FreightIqLogo } from "@/components/brand/FreightIqLogo";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";

interface NavItem {
  title: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const NAVIGATION_SECTIONS: NavSection[] = [
  {
    title: "COMMAND CENTER",
    items: [
      { title: "Command Center", href: "/dashboard", icon: LayoutDashboard },
    ],
  },
  {
    title: "CHARTERING",
    items: [
      { title: "New Requirement", href: "/chartering/new", icon: PlusCircle, badge: "NEW" },
      { title: "Active Requests", href: "/chartering/requests", icon: Layers },
      { title: "Vessel Search", href: "/chartering/vessels", icon: Search },
      { title: "Voyage Comparison", href: "/chartering/comparison", icon: GitCompare },
    ],
  },
  {
    title: "INTELLIGENCE",
    items: [
      { title: "Freight Forecast", href: "/intelligence/freight", icon: TrendingUp },
      { title: "Market Regime", href: "/intelligence/regime", icon: BarChart3 },
      { title: "Wait vs Fix", href: "/intelligence/wait-fix", icon: Clock },
      { title: "Vessel Intelligence", href: "/intelligence/vessels", icon: Ship },
      { title: "Port Intelligence", href: "/intelligence/ports", icon: Anchor },
      { title: "Congestion", href: "/intelligence/congestion", icon: AlertCircle },
      { title: "Weather", href: "/intelligence/weather", icon: CloudRain },
      { title: "Tidal Windows", href: "/intelligence/tidal", icon: Waves },
    ],
  },
  {
    title: "OPTIMIZATION",
    items: [
      { title: "Vessel-Port Optimizer", href: "/optimization/vessel-port", icon: Cpu },
      { title: "Contract Strategy", href: "/optimization/contracts", icon: FileCheck },
      { title: "Voyage Economics", href: "/optimization/voyage-cost", icon: DollarSign },
      { title: "Idle Scenarios", href: "/optimization/idle", icon: Hourglass },
      { title: "Speed Optimization", href: "/optimization/speed", icon: Gauge },
    ],
  },
  {
    title: "AI",
    items: [
      { title: "Chartering Copilot", href: "/ai/copilot", icon: Bot, badge: "AI" },
    ],
  },
  {
    title: "RISK",
    items: [
      { title: "Risk Center", href: "/risk", icon: ShieldCheck },
      { title: "Data Quality", href: "/risk/data-quality", icon: CheckCircle2 },
    ],
  },
  {
    title: "DATA",
    items: [
      { title: "Data Explorer", href: "/data/explorer", icon: Database },
      { title: "Reports", href: "/reports", icon: FileText },
    ],
  },
  {
    title: "ADMIN",
    items: [
      { title: "Data Ingestion", href: "/admin/ingestion", icon: UploadCloud },
      { title: "Model Management", href: "/admin/models", icon: Brain },
      { title: "Settings", href: "/settings", icon: Settings },
    ],
  },
];

interface SidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  collapsed,
  onToggleCollapse,
  mobileOpen,
  onMobileClose,
}) => {
  const pathname = usePathname();

  const isRouteActive = (href: string) => {
    if (href === "/dashboard") {
      return pathname === "/dashboard" || pathname === "/";
    }
    return pathname.startsWith(href);
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-slate-950/80 z-40 lg:hidden backdrop-blur-sm transition-opacity"
          onClick={onMobileClose}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 flex flex-col bg-card border-r border-border transition-all duration-200 ${
          mobileOpen
            ? "translate-x-0 w-64 z-50 visible pointer-events-auto shadow-2xl"
            : "-translate-x-full w-64 lg:translate-x-0 z-40 invisible pointer-events-none lg:visible lg:pointer-events-auto"
        } ${collapsed ? "lg:w-16" : "lg:w-64"}`}
      >
        {/* Sidebar Header */}
        <div className="h-14 flex items-center justify-between px-3.5 border-b border-border bg-muted/20">
          <Link href="/dashboard" className="flex items-center overflow-hidden">
            <FreightIqLogo collapsed={collapsed} size="sm" />
          </Link>

          {/* Close for mobile, collapse toggle for desktop */}
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={onMobileClose}
            className="lg:hidden text-muted-foreground hover:text-foreground h-9 w-9 flex items-center justify-center rounded-lg"
            aria-label="Close sidebar"
          >
            <X className="h-5 w-5" />
          </Button>

          <Button
            variant="ghost"
            size="icon-xs"
            onClick={onToggleCollapse}
            className="hidden lg:flex text-muted-foreground hover:text-foreground"
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Navigation Sections */}
        <div className="flex-1 overflow-y-auto py-3 px-2 space-y-5">
          {NAVIGATION_SECTIONS.map((section) => (
            <div key={section.title} className="space-y-1">
              {/* Section Header */}
              {!collapsed && (
                <div className="px-2.5 text-[10px] font-mono uppercase tracking-widest text-muted-foreground font-semibold select-none">
                  {section.title}
                </div>
              )}

              {/* Items */}
              <div className="space-y-0.5">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const active = isRouteActive(item.href);

                  const linkContent = (
                    <Link
                      href={item.href}
                      onClick={onMobileClose}
                      className={`group relative flex items-center gap-3 px-2.5 py-2.5 rounded-lg text-xs font-medium transition-all ${
                        active
                          ? "bg-primary/15 text-foreground dark:text-white font-semibold border-l-2 border-primary"
                          : "text-muted-foreground hover:text-foreground dark:hover:text-white hover:bg-muted/60"
                      }`}
                    >
                      <Icon
                        className={`h-4 w-4 shrink-0 transition-colors ${
                          active
                            ? "text-primary"
                            : "text-muted-foreground group-hover:text-foreground dark:group-hover:text-white"
                        }`}
                      />

                      {!collapsed && (
                        <div className="flex-1 flex items-center justify-between truncate">
                          <span className="truncate">{item.title}</span>
                          {item.badge && (
                            <Badge
                              variant={item.badge === "AI" ? "default" : "secondary"}
                              className="text-[9px] font-mono font-bold px-1.5 py-0 h-4"
                            >
                              {item.badge}
                            </Badge>
                          )}
                        </div>
                      )}
                    </Link>
                  );

                  if (collapsed) {
                    return (
                      <Tooltip key={item.href}>
                        <TooltipTrigger render={linkContent} />
                        <TooltipContent side="right" sideOffset={8}>
                          <span>{item.title}</span>
                          {item.badge && (
                            <span className="ml-1.5 font-mono text-[9px] opacity-80">({item.badge})</span>
                          )}
                        </TooltipContent>
                      </Tooltip>
                    );
                  }

                  return <React.Fragment key={item.href}>{linkContent}</React.Fragment>;
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Sidebar Footer */}
        <div className="p-3 border-t border-border bg-muted/10 text-[11px] text-muted-foreground">
          {!collapsed ? (
            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between text-[10px] font-mono">
                <span className="text-muted-foreground">SIH 2026: SIH26006</span>
                <span className="text-primary font-semibold">PHASE 01</span>
              </div>
              <div className="text-[10px] text-muted-foreground truncate">
                Ministry of Steel • SAIL
              </div>
            </div>
          ) : (
            <div className="text-center font-mono text-[10px] text-primary font-bold">
              P1
            </div>
          )}
        </div>
      </aside>
    </>
  );
};
