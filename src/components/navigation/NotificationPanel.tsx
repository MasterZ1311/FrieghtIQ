"use client";

import React, { useState } from "react";
import { Bell, Info, AlertTriangle, CheckCircle, Clock, X, ExternalLink } from "lucide-react";
import { DEMO_NOTIFICATIONS, DemoNotification } from "@/data/demo/notifications";
import { DataStatusBadge } from "@/components/badges/DataStatusBadge";

interface NotificationPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export const NotificationPanel: React.FC<NotificationPanelProps> = ({
  isOpen,
  onClose,
}) => {
  const [notifications, setNotifications] = useState<DemoNotification[]>(DEMO_NOTIFICATIONS);

  if (!isOpen) return null;

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, isRead: true })));
  };

  const unreadCount = notifications.filter((n) => !n.isRead).length;

  const getIcon = (sev: string) => {
    switch (sev) {
      case "warning":
        return <AlertTriangle className="h-4 w-4 text-amber-400" />;
      case "success":
        return <CheckCircle className="h-4 w-4 text-emerald-400" />;
      case "error":
        return <AlertTriangle className="h-4 w-4 text-rose-400" />;
      case "info":
      default:
        return <Info className="h-4 w-4 text-blue-400" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="fixed inset-0" onClick={onClose} />

      <div className="relative w-full max-w-sm h-full bg-surface border-l border-border shadow-2xl flex flex-col z-10">
        {/* Panel Header */}
        <div className="p-4 border-b border-border-subtle bg-surface-elevated/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bell className="h-4 w-4 text-blue-400" />
            <span className="font-bold text-sm text-slate-100">Telemetry Notifications</span>
            {unreadCount > 0 && (
              <span className="px-1.5 py-0.5 rounded-full bg-blue-600 text-[10px] font-mono text-white font-bold">
                {unreadCount}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-surface-hover"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Action bar */}
        <div className="px-4 py-2 bg-surface-elevated/20 border-b border-border-subtle flex items-center justify-between text-xs">
          <DataStatusBadge status="DEMO EVENTS" size="xs" />
          {unreadCount > 0 && (
            <button
              onClick={markAllRead}
              className="text-[11px] text-blue-400 hover:text-blue-300 transition-colors"
            >
              Mark all as read
            </button>
          )}
        </div>

        {/* Notifications List */}
        <div className="flex-1 overflow-y-auto divide-y divide-border-subtle/50 p-2">
          {notifications.map((notif) => (
            <div
              key={notif.id}
              className={`p-3 rounded-lg mb-1 transition-colors ${
                notif.isRead
                  ? "opacity-75 hover:opacity-100 bg-surface/50"
                  : "bg-surface-elevated/60 border border-border-subtle"
              }`}
            >
              <div className="flex items-start gap-2.5">
                <div className="mt-0.5 shrink-0">{getIcon(notif.severity)}</div>
                <div className="flex-1">
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span className="text-xs font-semibold text-slate-200">
                      {notif.title}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500 whitespace-nowrap">
                      {notif.timestamp}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-normal">
                    {notif.description}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Panel Footer */}
        <div className="p-3 border-t border-border-subtle bg-surface-elevated/30 text-center">
          <p className="text-[11px] text-slate-400">
            System Telemetry Simulation • Phase 01 Foundation
          </p>
        </div>
      </div>
    </div>
  );
};
