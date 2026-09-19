"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  User,
  Sliders,
  Activity,
  Keyboard,
  LogOut,
  ChevronDown,
  Building,
  Shield,
  X,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

export const UserMenu: React.FC = () => {
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [showShortcutsModal, setShowShortcutsModal] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [showSignOutModal, setShowSignOutModal] = useState(false);

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger render={
          <Button
            variant="outline"
            size="sm"
            className="flex items-center gap-2 p-1.5 h-9 rounded-lg border border-border bg-card hover:bg-muted text-xs text-foreground transition-colors"
          >
            <Avatar className="w-6 h-6 rounded-md bg-primary/20 border border-primary/30 flex items-center justify-center text-primary font-bold text-xs">
              <AvatarFallback className="bg-primary/20 text-primary text-xs font-bold">S</AvatarFallback>
            </Avatar>
            <div className="text-left hidden md:block">
              <div className="font-semibold text-xs leading-none text-foreground">
                SAIL Chartering Desk
              </div>
              <div className="text-[10px] text-muted-foreground font-mono mt-0.5">
                Ministry of Steel
              </div>
            </div>
            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground ml-0.5" />
          </Button>
        } />

        <DropdownMenuContent align="end" className="w-64 p-1.5 rounded-xl border border-border bg-popover text-popover-foreground shadow-2xl">
          <DropdownMenuLabel className="p-2.5 rounded-lg bg-muted/60 mb-1 font-normal">
            <div className="font-bold text-foreground text-xs">SAIL Maritime Logistics</div>
            <div className="text-[11px] text-muted-foreground">coking-coal.chartering@sail.in</div>
            <div className="mt-1.5 flex items-center gap-1.5 text-[10px] font-mono text-emerald-500">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>Role: Chief Logistics Officer</span>
            </div>
          </DropdownMenuLabel>

          <DropdownMenuItem
            onClick={() => setShowProfileModal(true)}
            className="cursor-pointer flex items-center gap-2.5 px-2.5 py-2 text-xs rounded-lg hover:bg-muted focus:bg-muted"
          >
            <User className="h-4 w-4 text-primary" />
            <span>Operator Profile</span>
          </DropdownMenuItem>

          <DropdownMenuItem className="cursor-pointer p-0">
            <Link
              href="/settings"
              className="flex items-center gap-2.5 px-2.5 py-2 text-xs w-full rounded-lg hover:bg-muted focus:bg-muted"
            >
              <Sliders className="h-4 w-4 text-primary" />
              <span>Logistics Preferences</span>
            </Link>
          </DropdownMenuItem>

          <DropdownMenuItem
            onClick={() => setShowStatusModal(true)}
            className="cursor-pointer flex items-center gap-2.5 px-2.5 py-2 text-xs rounded-lg hover:bg-muted focus:bg-muted"
          >
            <Activity className="h-4 w-4 text-emerald-500" />
            <span>System & Telemetry Status</span>
          </DropdownMenuItem>

          <DropdownMenuItem
            onClick={() => setShowShortcutsModal(true)}
            className="cursor-pointer flex items-center gap-2.5 px-2.5 py-2 text-xs rounded-lg hover:bg-muted focus:bg-muted"
          >
            <Keyboard className="h-4 w-4 text-sky-500" />
            <span>Keyboard Shortcuts</span>
          </DropdownMenuItem>

          <DropdownMenuSeparator className="my-1" />

          <DropdownMenuItem
            onClick={() => setShowSignOutModal(true)}
            className="cursor-pointer flex items-center gap-2.5 px-2.5 py-2 text-xs rounded-lg text-rose-500 hover:bg-rose-500/10 focus:bg-rose-500/10"
          >
            <LogOut className="h-4 w-4 text-rose-500" />
            <span>Sign Out (Demo Session)</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* 1. Operator Profile Modal (shadcn Dialog) */}
      <Dialog open={showProfileModal} onOpenChange={setShowProfileModal}>
        <DialogContent className="max-w-md p-5 rounded-xl bg-card text-card-foreground border border-border">
          <DialogHeader>
            <DialogTitle className="text-sm font-bold flex items-center gap-2">
              <User className="h-4 w-4 text-primary" />
              <span>SAIL Operator Profile</span>
            </DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Official maritime chartering desk credential and access authority.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 my-2 text-xs">
            <div className="p-3 rounded-lg bg-muted/50 border border-border flex items-center gap-3">
              <Avatar className="w-10 h-10 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center text-primary font-bold text-sm">
                <AvatarFallback className="bg-primary/20 text-primary font-bold text-xs">SAIL</AvatarFallback>
              </Avatar>
              <div>
                <div className="font-bold text-foreground text-sm">Chief Logistics Officer</div>
                <div className="text-muted-foreground text-[11px]">coking-coal.chartering@sail.in</div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 rounded-lg bg-muted/40 border border-border">
                <div className="text-[10px] text-muted-foreground uppercase font-semibold">Entity</div>
                <div className="text-foreground font-medium mt-0.5">Steel Authority of India Ltd</div>
              </div>
              <div className="p-2.5 rounded-lg bg-muted/40 border border-border">
                <div className="text-[10px] text-muted-foreground uppercase font-semibold">Department</div>
                <div className="text-foreground font-medium mt-0.5">Commercial Directorate</div>
              </div>
              <div className="p-2.5 rounded-lg bg-muted/40 border border-border">
                <div className="text-[10px] text-muted-foreground uppercase font-semibold">Clearance Level</div>
                <div className="text-emerald-500 font-medium mt-0.5">Level 1 - Charter Approver</div>
              </div>
              <div className="p-2.5 rounded-lg bg-muted/40 border border-border">
                <div className="text-[10px] text-muted-foreground uppercase font-semibold">IAM Authority</div>
                <div className="text-sky-500 font-medium mt-0.5">Active Session</div>
              </div>
            </div>
          </div>

          <DialogFooter className="mt-4 flex justify-end gap-2">
            <Button
              variant="outline"
              size="sm"
              render={<Link href="/settings" onClick={() => setShowProfileModal(false)}>Logistics Settings</Link>}
            />
            <Button size="sm" onClick={() => setShowProfileModal(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 2. System Status Modal (shadcn Dialog) */}
      <Dialog open={showStatusModal} onOpenChange={setShowStatusModal}>
        <DialogContent className="max-w-md p-5 rounded-xl bg-card text-card-foreground border border-border">
          <DialogHeader>
            <DialogTitle className="text-sm font-bold flex items-center gap-2">
              <Activity className="h-4 w-4 text-emerald-500" />
              <span>FREIGHT IQ System Status</span>
            </DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Core engines and telemetry pipeline telemetry.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2.5 text-xs my-2">
            <div className="p-2.5 rounded-lg bg-muted/40 border border-border flex justify-between items-center">
              <span className="text-foreground">Application Shell & UI</span>
              <Badge variant="outline" className="font-mono text-emerald-500 border-emerald-500/30 bg-emerald-500/10">
                OPERATIONAL
              </Badge>
            </div>
            <div className="p-2.5 rounded-lg bg-muted/40 border border-border flex justify-between items-center">
              <span className="text-foreground">Design System Primitives</span>
              <Badge variant="outline" className="font-mono text-emerald-500 border-emerald-500/30 bg-emerald-500/10">
                SHADCN NOVA (MIST/BLUE)
              </Badge>
            </div>
            <div className="p-2.5 rounded-lg bg-muted/40 border border-border flex justify-between items-center">
              <span className="text-foreground">Live Telemetry Feeds</span>
              <Badge variant="outline" className="font-mono text-sky-500 border-sky-500/30 bg-sky-500/10">
                LIVE DEMO FEEDS
              </Badge>
            </div>
            <div className="p-2.5 rounded-lg bg-muted/40 border border-border flex justify-between items-center">
              <span className="text-foreground">Optimization Engine</span>
              <Badge variant="outline" className="font-mono text-primary border-primary/30 bg-primary/10">
                ACTIVE
              </Badge>
            </div>
          </div>

          <DialogFooter className="mt-4 flex justify-end">
            <Button size="sm" onClick={() => setShowStatusModal(false)}>
              Dismiss
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 3. Keyboard Shortcuts Modal (shadcn Dialog) */}
      <Dialog open={showShortcutsModal} onOpenChange={setShowShortcutsModal}>
        <DialogContent className="max-w-md p-5 rounded-xl bg-card text-card-foreground border border-border">
          <DialogHeader>
            <DialogTitle className="text-sm font-bold flex items-center gap-2">
              <Keyboard className="h-4 w-4 text-sky-500" />
              <span>Maritime Console Shortcuts</span>
            </DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Keyboard accelerators for quick maritime actions.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2 text-xs my-2">
            <div className="flex justify-between py-1.5 border-b border-border">
              <span className="text-muted-foreground">Open Command Palette</span>
              <kbd className="px-2 py-0.5 rounded bg-muted border border-border text-foreground font-mono text-[11px]">
                Ctrl + K
              </kbd>
            </div>
            <div className="flex justify-between py-1.5 border-b border-border">
              <span className="text-muted-foreground">Global Search</span>
              <kbd className="px-2 py-0.5 rounded bg-muted border border-border text-foreground font-mono text-[11px]">
                Ctrl + /
              </kbd>
            </div>
            <div className="flex justify-between py-1.5 border-b border-border">
              <span className="text-muted-foreground">New Charter Form</span>
              <kbd className="px-2 py-0.5 rounded bg-muted border border-border text-foreground font-mono text-[11px]">
                Alt + N
              </kbd>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-muted-foreground">Close Modals / Overlays</span>
              <kbd className="px-2 py-0.5 rounded bg-muted border border-border text-foreground font-mono text-[11px]">
                ESC
              </kbd>
            </div>
          </div>

          <DialogFooter className="mt-4 flex justify-end">
            <Button size="sm" onClick={() => setShowShortcutsModal(false)}>
              Done
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 4. Sign Out Modal (shadcn Dialog) */}
      <Dialog open={showSignOutModal} onOpenChange={setShowSignOutModal}>
        <DialogContent className="max-w-md p-5 rounded-xl bg-card text-card-foreground border border-border">
          <DialogHeader>
            <DialogTitle className="text-sm font-bold flex items-center gap-2">
              <LogOut className="h-4 w-4 text-rose-500" />
              <span>Session Management</span>
            </DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Reset and reload the active maritime demonstration session.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2 text-xs text-muted-foreground my-2">
            <p>
              You are currently in an active demonstration session connected to the local maritime optimization engines.
            </p>
            <p>
              Signing out will clear local cache and re-initialize the executive maritime command console.
            </p>
          </div>

          <DialogFooter className="mt-4 flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setShowSignOutModal(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => {
                setShowSignOutModal(false);
                window.location.reload();
              }}
            >
              Restart Session
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};
