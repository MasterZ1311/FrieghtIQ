import { z } from "zod";

export const CARGO_TYPES = [
  "Coking Coal",
  "Thermal Coal",
  "PCI Coal",
  "Iron Ore Fines",
  "Iron Ore Pellets",
  "Limestone",
  "Dolomite",
  "Manganese Ore",
  "Other Bulk",
] as const;

export const VESSEL_CLASSES = [
  "Handysize",
  "Supramax",
  "Ultramax",
  "Panamax",
  "Kamsarmax",
  "Capesize",
] as const;

export const CONTRACT_PREFERENCES = [
  "Spot",
  "COA",
  "Time Charter",
  "Flexible",
] as const;

export const charterRequirementSchema = z.object({
  referenceNumber: z.string().min(3, "Reference number is required"),
  cargoType: z.enum(CARGO_TYPES),
  quantityMT: z.number().min(5000, "Quantity must be at least 5,000 MT").max(400000, "Maximum bulk lot is 400,000 MT"),
  tolerancePercent: z.number().min(0).max(20),
  originPort: z.string().min(2, "Origin port is required"),
  destinationPort: z.string().min(2, "Destination port is required"),
  laycanStart: z.string().min(1, "Laycan start date is required"),
  laycanEnd: z.string().min(1, "Laycan end date is required"),
  requiredArrivalDate: z.string().min(1, "Required arrival date is required"),
  preferredVesselClass: z.enum(VESSEL_CLASSES),
  contractPreference: z.enum(CONTRACT_PREFERENCES),
  contractDurationMonths: z.number().min(0).max(36),
  maxFreightBudgetUSDPerMT: z.number().min(1).max(200),
  dischargeRateMTPerDay: z.number().min(1000).max(100000),
  specialRequirements: z.string().max(500).optional(),
});

export type CharterRequirementFormData = z.infer<typeof charterRequirementSchema>;
