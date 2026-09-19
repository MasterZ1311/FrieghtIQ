import React from "react";
import { GitCompare } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/feedback/EmptyState";

export default function VoyageComparisonPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="VOYAGE SCENARIO COMPARISON"
        description="Side-by-side comparative simulation of candidate vessel fixtures, route bunkering costs, and port laytime economics."
        status="DEMO ENVIRONMENT"
      />

      <EmptyState
        title="Voyage Scenario Comparison Matrix"
        description="No active candidate comparison session selected. Select two or more active vessel offers or cargo requirements to run side-by-side voyage financial simulation."
        statusLabel="MODULE STAGED"
        plannedPhase="Phase 02 Optimization Solver"
        icon={GitCompare}
        actionLabel="Create Charter Requirement"
        actionHref="/chartering/new"
        technicalSpecs={[
          "Bunker fuel consumption curves at varying economic transit speeds",
          "Canal transit toll modeling (Suez Canal / Malacca Strait choke points)",
          "Comparative demurrage vs. despatch calculations across discharge berths",
          "Port turnaround probability distribution under seasonal congestion",
        ]}
      />
    </div>
  );
}
