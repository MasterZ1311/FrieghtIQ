export interface DemoNotification {
  id: string;
  title: string;
  description: string;
  timestamp: string;
  category: "freight" | "port" | "vessel" | "system";
  isRead: boolean;
  severity: "info" | "warning" | "error" | "success";
}

export const DEMO_NOTIFICATIONS: DemoNotification[] = [
  {
    id: "notif-01",
    title: "Freight Forecast Model Ready",
    description: "Synthetic forecast envelope generated for Newcastle → Paradip Capesize route.",
    timestamp: "10 mins ago",
    category: "freight",
    isRead: false,
    severity: "info",
  },
  {
    id: "notif-02",
    title: "Port Data Requires Verification",
    description: "Paradip CQ-1 draft constraint limits require validation from local port authority.",
    timestamp: "1 hour ago",
    category: "port",
    isRead: false,
    severity: "warning",
  },
  {
    id: "notif-03",
    title: "Vessel Position Stale",
    description: "MV Bengal Voyager AIS transponder update overdue (>24h). Position flagged as STALE.",
    timestamp: "3 hours ago",
    category: "vessel",
    isRead: true,
    severity: "warning",
  },
  {
    id: "notif-04",
    title: "New Cargo Requirement Created",
    description: "SAIL-RSP-2026-09-01 (75,000 MT Coking Coal) submitted for vessel matching.",
    timestamp: "5 hours ago",
    category: "system",
    isRead: true,
    severity: "success",
  },
];
