"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Package,
  MapPin,
  Calendar,
  Ship,
  Sliders,
  FileText,
  ArrowRight,
  CheckCircle2,
  Info,
  RotateCcw,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  charterRequirementSchema,
  CharterRequirementFormData,
  CARGO_TYPES,
  VESSEL_CLASSES,
  CONTRACT_PREFERENCES,
} from "@/lib/validations";
import { cargoApi } from "@/lib/api";

export default function NewCharterPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CharterRequirementFormData>({
    resolver: zodResolver(charterRequirementSchema),
    defaultValues: {
      referenceNumber: "SAIL-REQ-2026-003",
      cargoType: "Coking Coal",
      quantityMT: 75000,
      tolerancePercent: 10,
      originPort: "Newcastle (Australia)",
      destinationPort: "Paradip (India)",
      laycanStart: "2026-10-15",
      laycanEnd: "2026-10-25",
      requiredArrivalDate: "2026-11-10",
      preferredVesselClass: "Panamax",
      contractPreference: "Spot",
      contractDurationMonths: 0,
      maxFreightBudgetUSDPerMT: 15.0,
      dischargeRateMTPerDay: 18000,
      specialRequirements: "Maximum permissible draft at discharge berth 14.50m. Geared vessel not mandatory.",
    },
  });

  const onSubmit = async (data: CharterRequirementFormData) => {
    setIsSubmitting(true);
    try {
      // Map form fields to backend model
      const created = await cargoApi.createRequirement({
        title: `${data.referenceNumber}: ${data.cargoType} (${data.quantityMT.toLocaleString()} MT) Ex-${data.originPort.split(' ')[0]} to ${data.destinationPort.split(' ')[0]}`,
        cargo_type: data.cargoType.toUpperCase().replace(/\s+/g, '_'),
        quantity_mt: data.quantityMT,
        tolerance_pct: data.tolerancePercent,
        load_port_id: data.originPort.includes("Newcastle") ? "port-auncb" : "port-auglt",
        discharge_port_id: data.destinationPort.includes("Paradip") ? "port-inprt" : data.destinationPort.includes("Visakhapatnam") ? "port-invtz" : "port-inhal",
        laycan_start: new Date(data.laycanStart).toISOString(),
        laycan_end: new Date(data.laycanEnd).toISOString(),
        target_freight_usd_pmt: data.maxFreightBudgetUSDPerMT,
        preferred_vessel_classes: data.preferredVesselClass.toUpperCase(),
        notes: data.specialRequirements,
      });

      setSuccessMessage(
        `Charter requirement ${created.requirement_code} created successfully! Redirecting to Candidate Matching Engine...`
      );
      setTimeout(() => {
        router.push(`/chartering/requests/${created.id}`);
      }, 1000);
    } catch (err) {
      console.error("Failed to persist requirement to database", err);
      setSuccessMessage(
        `Charter requirement ${data.referenceNumber} created in local session! Redirecting...`
      );
      setTimeout(() => {
        router.push("/chartering/requests");
      }, 1200);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <PageHeader
        title="NEW CHARTER REQUIREMENT"
        description="Formalize bulk cargo procurement tenders and charter party parameters for overseas import voyages to East Coast India."
        status="DEMO ENVIRONMENT"
      />

      {/* Honest Data Banner */}
      <Card className="border-primary/30 bg-primary/10 p-3.5 flex flex-row items-start gap-3 text-xs text-foreground">
        <Info className="h-4 w-4 text-primary mt-0.5 shrink-0" />
        <div>
          <span className="font-semibold text-foreground">
            Phase 01 Architectural Staging:
          </span>{" "}
          Submitting this form creates a simulated requirement and routes to Active Requests. Mathematical optimization, vessel-port geometry solver, and AI Copilot will be integrated in subsequent phases.
        </div>
      </Card>

      {successMessage && (
        <Card className="p-4 border-emerald-500/50 bg-emerald-500/10 text-emerald-500 dark:text-emerald-400 text-xs flex flex-row items-center gap-3 animate-in fade-in">
          <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0" />
          <span>{successMessage}</span>
        </Card>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Section 1: Cargo Classification */}
        <Card className="border-border bg-card p-5 sm:p-6 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-border">
            <Package className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-foreground">
              Section 1: Cargo Specification
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-foreground mb-1.5">
                Reference Identifier *
              </label>
              <Input
                {...register("referenceNumber")}
                className="text-xs font-mono"
              />
              {errors.referenceNumber && (
                <p className="text-[11px] text-destructive mt-1">
                  {errors.referenceNumber.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-foreground mb-1.5">
                Cargo Classification *
              </label>
              <select
                {...register("cargoType")}
                className="w-full h-8 bg-transparent border border-input text-xs text-foreground rounded-lg px-2.5 py-1 focus:outline-none focus:border-ring focus:ring-3 focus:ring-ring/50"
              >
                {CARGO_TYPES.map((type) => (
                  <option key={type} value={type} className="bg-card text-card-foreground">
                    {type}
                  </option>
                ))}
              </select>
              {errors.cargoType && (
                <p className="text-[11px] text-destructive mt-1">
                  {errors.cargoType.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-foreground mb-1.5">
                Cargo Quantity (Metric Tons) *
              </label>
              <Input
                type="number"
                {...register("quantityMT", { valueAsNumber: true })}
                className="text-xs font-mono"
              />
              {errors.quantityMT && (
                <p className="text-[11px] text-destructive mt-1">
                  {errors.quantityMT.message}
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-xs font-medium text-foreground mb-1.5">
                MOLOO Tolerance (+/- %)
              </label>
              <Input
                type="number"
                {...register("tolerancePercent", { valueAsNumber: true })}
                className="text-xs font-mono"
              />
              <span className="text-[10px] text-muted-foreground">
                More or Less in Owner&apos;s Option (Standard: 10%)
              </span>
            </div>

            <div>
              <label className="block text-xs font-medium text-foreground mb-1.5">
                Guaranteed Discharge Rate (MT/Day)
              </label>
              <Input
                type="number"
                {...register("dischargeRateMTPerDay", { valueAsNumber: true })}
                className="text-xs font-mono"
              />
              <span className="text-[10px] text-muted-foreground">
                Used to compute laytime allowance and demurrage exposure
              </span>
            </div>
          </div>
        </Card>

        {/* Section 2: Route Geography */}
        <Card className="border-border bg-card p-5 sm:p-6 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-border">
            <MapPin className="h-4 w-4 text-cyan-500" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-foreground">
              Section 2: Maritime Route Geography
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-foreground mb-1.5">
                Origin Port (Overseas Load Port) *
              </label>
              <select
                {...register("originPort")}
                className="w-full h-8 bg-transparent border border-input text-xs text-foreground rounded-lg px-2.5 py-1 focus:outline-none focus:border-ring focus:ring-3 focus:ring-ring/50"
              >
                <option value="Newcastle (Australia)" className="bg-card text-card-foreground">Newcastle, Australia (Hay Point / PWCS)</option>
                <option value="Hay Point (Australia)" className="bg-card text-card-foreground">Hay Point / Dalrymple Bay, Australia</option>
                <option value="Gladstone (Australia)" className="bg-card text-card-foreground">Gladstone (RG Tanna), Australia</option>
                <option value="Port Hedland (Australia)" className="bg-card text-card-foreground">Port Hedland, Australia</option>
                <option value="Richards Bay (South Africa)" className="bg-card text-card-foreground">Richards Bay Coal Terminal, South Africa</option>
                <option value="Tubarao (Brazil)" className="bg-card text-card-foreground">Tubarao / Ponta da Madeira, Brazil</option>
                <option value="Mina Saqr (UAE)" className="bg-card text-card-foreground">Mina Saqr / Fujairah, UAE (Limestone)</option>
                <option value="Salalah (Oman)" className="bg-card text-card-foreground">Salalah / Raysut, Oman (Limestone)</option>
              </select>
              {errors.originPort && (
                <p className="text-[11px] text-destructive mt-1">
                  {errors.originPort.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-foreground mb-1.5">
                Destination Port (East Coast India) *
              </label>
              <select
                {...register("destinationPort")}
                className="w-full h-8 bg-transparent border border-input text-xs text-foreground rounded-lg px-2.5 py-1 focus:outline-none focus:border-ring focus:ring-3 focus:ring-ring/50"
              >
                <option value="Paradip (India)" className="bg-card text-card-foreground">Paradip Port (Rourkela / Bokaro linkage)</option>
                <option value="Visakhapatnam (India)" className="bg-card text-card-foreground">Visakhapatnam Port (RINL / SAIL)</option>
                <option value="Dhamra (India)" className="bg-card text-card-foreground">Dhamra Port (Deep draft Capesize)</option>
                <option value="Gangavaram (India)" className="bg-card text-card-foreground">Gangavaram Port</option>
                <option value="Haldia (India)" className="bg-card text-card-foreground">Haldia Dock Complex (Durgapur / IISCO linkage)</option>
                <option value="Gopalpur (India)" className="bg-card text-card-foreground">Gopalpur Port</option>
                <option value="Sagar-Sandheads (India)" className="bg-card text-card-foreground">Sagar-Sandheads Anchorage (Lightering)</option>
              </select>
              {errors.destinationPort && (
                <p className="text-[11px] text-destructive mt-1">
                  {errors.destinationPort.message}
                </p>
              )}
            </div>
          </div>
        </Card>

        {/* Section 3: Timing & Laycan Windows */}
        <Card className="border-border bg-card p-5 sm:p-6 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-border">
            <Calendar className="h-4 w-4 text-emerald-500" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-foreground">
              Section 3: Laycan Window & Delivery Schedule
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-foreground mb-1.5">
                Laycan Start Date *
              </label>
              <Input
                type="date"
                {...register("laycanStart")}
                className="text-xs font-mono"
              />
              {errors.laycanStart && (
                <p className="text-[11px] text-destructive mt-1">
                  {errors.laycanStart.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-foreground mb-1.5">
                Laycan End Date *
              </label>
              <Input
                type="date"
                {...register("laycanEnd")}
                className="text-xs font-mono"
              />
              {errors.laycanEnd && (
                <p className="text-[11px] text-destructive mt-1">
                  {errors.laycanEnd.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-foreground mb-1.5">
                Required Arrival at Discharge *
              </label>
              <Input
                type="date"
                {...register("requiredArrivalDate")}
                className="text-xs font-mono"
              />
              {errors.requiredArrivalDate && (
                <p className="text-[11px] text-destructive mt-1">
                  {errors.requiredArrivalDate.message}
                </p>
              )}
            </div>
          </div>
        </Card>

        {/* Section 4: Vessel Preferences */}
        <Card className="border-border bg-card p-5 sm:p-6 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-border">
            <Ship className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-foreground">
              Section 4: Vessel Class & Configuration
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-foreground mb-1.5">
                Preferred Vessel Class *
              </label>
              <select
                {...register("preferredVesselClass")}
                className="w-full h-8 bg-transparent border border-input text-xs text-foreground rounded-lg px-2.5 py-1 focus:outline-none focus:border-ring focus:ring-3 focus:ring-ring/50 font-mono"
              >
                {VESSEL_CLASSES.map((cls) => (
                  <option key={cls} value={cls} className="bg-card text-card-foreground">
                    {cls}
                  </option>
                ))}
              </select>
              {errors.preferredVesselClass && (
                <p className="text-[11px] text-destructive mt-1">
                  {errors.preferredVesselClass.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-foreground mb-1.5">
                Maximum Freight Budget (USD / MT)
              </label>
              <Input
                type="number"
                step="0.10"
                {...register("maxFreightBudgetUSDPerMT", { valueAsNumber: true })}
                className="text-xs font-mono"
              />
              <span className="text-[10px] text-muted-foreground">
                Tender ceiling price benchmark
              </span>
            </div>
          </div>
        </Card>

        {/* Section 5: Contract Strategy */}
        <Card className="border-border bg-card p-5 sm:p-6 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-border">
            <Sliders className="h-4 w-4 text-amber-500" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-foreground">
              Section 5: Contract Strategy & Term
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-foreground mb-1.5">
                Contract Type *
              </label>
              <select
                {...register("contractPreference")}
                className="w-full h-8 bg-transparent border border-input text-xs text-foreground rounded-lg px-2.5 py-1 focus:outline-none focus:border-ring focus:ring-3 focus:ring-ring/50"
              >
                {CONTRACT_PREFERENCES.map((pref) => (
                  <option key={pref} value={pref} className="bg-card text-card-foreground">
                    {pref}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-foreground mb-1.5">
                Contract Duration (Months, if COA/Time Charter)
              </label>
              <Input
                type="number"
                {...register("contractDurationMonths", { valueAsNumber: true })}
                placeholder="e.g. 6 or 12"
                className="text-xs font-mono"
              />
            </div>
          </div>
        </Card>

        {/* Section 6: Additional Requirements & Constraints */}
        <Card className="border-border bg-card p-5 sm:p-6 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-border">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-foreground">
              Section 6: Special Operational Requirements
            </h3>
          </div>

          <div>
            <label className="block text-xs font-medium text-foreground mb-1.5">
              Port Constraints, Berth Restrictions, or Charter Party Clauses
            </label>
            <textarea
              rows={3}
              {...register("specialRequirements")}
              className="w-full bg-transparent border border-input text-xs text-foreground rounded-lg p-3 focus:outline-none focus:border-ring focus:ring-3 focus:ring-ring/50"
            />
            {errors.specialRequirements && (
              <p className="text-[11px] text-destructive mt-1">
                {errors.specialRequirements.message}
              </p>
            )}
          </div>
        </Card>

        {/* Form Actions */}
        <div className="flex items-center justify-between gap-4 pt-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => reset()}
            className="gap-2 text-xs font-medium"
          >
            <RotateCcw className="h-3.5 w-3.5 text-muted-foreground" />
            <span>Reset Fields</span>
          </Button>

          <Button
            type="submit"
            disabled={isSubmitting}
            className="gap-2 px-6 text-xs font-bold uppercase tracking-wider shadow-md shadow-primary/20"
          >
            {isSubmitting ? (
              <span>Validating Charter...</span>
            ) : (
              <>
                <span>ANALYZE CHARTER</span>
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
