import React from "react";
import { Database } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/feedback/EmptyState";

export default function DataExplorerPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="MARITIME DATA EXPLORER"
        description="Query, inspect, and export time-series datasets: Baltic freight indices, vessel position histories, bunker spot prices, and port turnaround times."
        status="DEMO ENVIRONMENT"
      />

      <EmptyState
        title="Telemetry & Time-Series Data Explorer"
        description="Data Explorer query builder will activate in Phase 02 when the analytical warehouse (PostgreSQL / DuckDB) is initialized. Users will be able to run SQL queries and export CSV/Parquet datasets."
        statusLabel="MODULE STAGED"
        plannedPhase="Phase 02 Data Warehouse"
        icon={Database}
        actionLabel="View Data Quality Audit"
        actionHref="/risk/data-quality"
        technicalSpecs={[
          "TimescaleDB / DuckDB partition engine for high-frequency AIS positions",
          "Custom SQL query console with rate-limiting and query cost estimator",
          "Export capabilities: CSV, Parquet, and JSON format",
          "Automated schema mapping for SAIL ERP procurement records",
        ]}
      />
    </div>
  );
}
