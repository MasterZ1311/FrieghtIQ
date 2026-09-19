"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Search, Bell, Menu, Command, ChevronDown } from "lucide-react";
import { CommandPalette } from "@/components/navigation/CommandPalette";
import { GlobalSearchModal } from "@/components/navigation/GlobalSearchModal";
import { NotificationPanel } from "@/components/navigation/NotificationPanel";
import { UserMenu } from "@/components/navigation/UserMenu";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import { DEMO_NOTIFICATIONS } from "@/data/demo/notifications";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

interface HeaderProps {
  onMobileMenuToggle: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onMobileMenuToggle }) => {
  const [isCommandOpen, setIsCommandOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isNotifOpen, setIsNotifOpen] = useState(false);

  const unreadNotifCount = DEMO_NOTIFICATIONS.filter((n) => !n.isRead).length;

  // Keyboard shortcut listener for Ctrl+K and Ctrl+/
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsCommandOpen((prev) => !prev);
      }
      if ((e.ctrlKey || e.metaKey) && e.key === "/") {
        e.preventDefault();
        setIsSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <header className="h-14 border-b border-border bg-card/95 sticky top-0 z-30 px-4 sm:px-6 flex items-center justify-between gap-4">
      {/* Left side: Mobile menu toggle and search trigger */}
      <div className="flex items-center gap-2.5">
        <Button
          variant="outline"
          size="icon-sm"
          onClick={onMobileMenuToggle}
          className="lg:hidden"
          aria-label="Toggle Navigation Drawer"
        >
          <Menu className="h-4 w-4" />
        </Button>

        {/* Global Search / Quick Search trigger */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsSearchOpen(true)}
          className="hidden sm:flex items-center justify-start gap-2.5 px-3 h-8 w-52 md:w-64 text-xs text-muted-foreground hover:text-foreground border-border bg-muted/30 hover:bg-muted/60"
        >
          <Search className="h-3.5 w-3.5 text-primary shrink-0" />
          <span className="truncate">Search vessels, ports...</span>
          <kbd className="ml-auto px-1.5 py-0.5 rounded bg-muted border border-border text-[10px] text-muted-foreground font-mono">
            Ctrl /
          </kbd>
        </Button>
      </div>

      {/* Center: Command Palette Trigger Button */}
      <div className="flex items-center">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsCommandOpen(true)}
          className="flex items-center gap-2 px-3 h-8 text-xs border-border bg-muted/40 hover:bg-muted hover:border-primary/50 text-foreground"
        >
          <Command className="h-3.5 w-3.5 text-primary" />
          <span className="hidden md:inline font-medium">Command Palette</span>
          <kbd className="px-1.5 py-0.5 rounded bg-muted border border-border text-[10px] text-primary font-mono">
            Ctrl + K
          </kbd>
        </Button>
      </div>

      {/* Right side: Global Data Status, Notifications, User Menu */}
      <div className="flex items-center gap-2.5">
        {/* Demo Mode Badge & Preset Scenarios Dropdown */}
        <div className="hidden lg:flex items-center gap-2">
          <Badge
            variant="outline"
            className="flex items-center gap-1.5 px-2 py-0.5 h-7 rounded-md font-mono text-[11px] bg-amber-500/10 border-amber-500/30 text-amber-500"
            title="DEMO MODE: Synthetic intelligence & telemetry."
          >
            <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse" />
            <span className="font-bold">DEMO (V1)</span>
          </Badge>

          <DropdownMenu>
            <DropdownMenuTrigger render={
              <Button
                variant="outline"
                size="sm"
                className="text-xs h-7 px-2.5 flex items-center gap-1 border-border text-foreground hover:bg-muted"
              >
                <span>Preset Scenarios</span>
                <ChevronDown className="h-3 w-3 text-muted-foreground" />
              </Button>
            } />
            <DropdownMenuContent align="end" className="w-64 p-1.5 rounded-xl border border-border bg-popover shadow-xl text-xs">
              <DropdownMenuLabel className="px-2 py-1 text-[10px] text-muted-foreground font-bold uppercase tracking-wider font-mono">
                Golden Demo Presets
              </DropdownMenuLabel>
              <DropdownMenuItem className="p-0 cursor-pointer">
                <Link
                  href="/chartering/decision/req-sail-2026-001"
                  className="block px-2.5 py-2 rounded-lg hover:bg-muted w-full text-foreground"
                >
                  <div className="font-bold text-primary">75K MT Coal (Primary)</div>
                  <div className="text-[10px] text-muted-foreground">Newcastle (AUNCL) &rarr; Paradip (INPRT)</div>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem className="p-0 cursor-pointer">
                <Link
                  href="/chartering/decision/req-sail-2026-002"
                  className="block px-2.5 py-2 rounded-lg hover:bg-muted w-full text-foreground"
                >
                  <div className="font-bold text-foreground">50K MT Coal</div>
                  <div className="text-[10px] text-muted-foreground">Gladstone (AUGLA) &rarr; Vizag (INVTZ)</div>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator className="my-1" />
              <div className="px-2.5 py-1.5 opacity-60 text-muted-foreground text-[11px]">
                <div className="font-semibold">75K MT Coal (Mozambique)</div>
                <div className="text-[10px]">Maputo &rarr; Paradip (Staged)</div>
              </div>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Notifications Trigger */}
        <Button
          variant="outline"
          size="icon-sm"
          onClick={() => setIsNotifOpen(true)}
          className="relative h-8 w-8 text-muted-foreground hover:text-foreground"
          aria-label="View notifications"
        >
          <Bell className="h-4 w-4" />
          {unreadNotifCount > 0 && (
            <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-primary ring-2 ring-card animate-pulse" />
          )}
        </Button>

        {/* Theme Switcher Toggle */}
        <ThemeToggle />

        {/* User Menu */}
        <UserMenu />
      </div>

      {/* Modals and Drawers */}
      <CommandPalette
        isOpen={isCommandOpen}
        onClose={() => setIsCommandOpen(false)}
      />

      <GlobalSearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
      />

      <NotificationPanel
        isOpen={isNotifOpen}
        onClose={() => setIsNotifOpen(false)}
      />
    </header>
  );
};
