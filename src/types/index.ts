/**
 * FREIGHT IQ — Foundational Domain Types & Interfaces
 * Phase 01: Architecture, Type Contracts & Metadata
 */

// Data Provenance & Reliability Status
export type DataStatus =
  | "LIVE"
  | "RECENT"
  | "STALE"
  | "DEMO"
  | "SYNTHETIC"
  | "UNAVAILABLE";

// Operational Status
export type OperationalStatus =
  | "ACTIVE"
  | "INACTIVE"
  | "AVAILABLE"
  | "UNAVAILABLE"
  | "AT SEA"
  | "AT PORT"
  | "AT ANCHORAGE"
  | "UNKNOWN";

// Risk Assessment Levels
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "UNKNOWN";

// Port & Vessel Constraint Evaluation Status
export type ConstraintStatus = "PASS" | "WARNING" | "FAIL" | "UNKNOWN";

// Confidence Rating
export type ConfidenceLevel = "HIGH" | "MEDIUM" | "LOW" | "UNRATED";

// Vessel Class Categories
export type VesselClass =
  | "Handysize"
  | "Supramax"
  | "Ultramax"
  | "Panamax"
  | "Kamsarmax"
  | "Capesize"
  | "VLOC"
  | "UNKNOWN";

// Cargo Classification for Steel Bulk Logistics
export type CargoType =
  | "Coking Coal"
  | "Thermal Coal"
  | "PCI Coal"
  | "Iron Ore Fines"
  | "Iron Ore Pellets"
  | "Limestone"
  | "Dolomite"
  | "Manganese Ore"
  | "Other Bulk";

// Charter Contract Options
export type ContractType =
  | "Spot"
  | "COA"
  | "Time Charter"
  | "Flexible";

// Cargo Request Lifecycle Status
export type RequestStatus =
  | "DRAFT"
  | "READY FOR ANALYSIS"
  | "ANALYZING"
  | "DATA INCOMPLETE"
  | "COMPLETED";

// Base interface for all entities with data honesty metadata
export interface BaseEntityMetadata {
  isDemo: boolean;
  source: string;
  sourceDate?: string;
  lastUpdated: string;
  dataStatus: DataStatus;
  confidence?: ConfidenceLevel;
}

// 1. Cargo Requirement / Request
export interface CargoRequest extends BaseEntityMetadata {
  id: string;
  referenceNumber: string;
  cargoType: CargoType;
  quantityMT: number;
  tolerancePercent: number;
  originPort: string;
  destinationPort: string;
  laycanStart: string;
  laycanEnd: string;
  requiredArrivalDate: string;
  preferredVesselClass: VesselClass;
  contractPreference: ContractType;
  dischargeRateMTPerDay?: number;
  maxFreightBudgetUSDPerMT?: number;
  specialRequirements?: string;
  status: RequestStatus;
  createdAt: string;
}

// 2. Vessel Profile & Operational Specifications
export interface Vessel extends BaseEntityMetadata {
  id: string;
  name: string;
  imoNumber: string | "UNKNOWN";
  vesselClass: VesselClass;
  flag: string | "UNKNOWN";
  builtYear: number | "UNKNOWN";
  dwtMT: number | "UNKNOWN";
  loaMeters: number | "UNKNOWN";
  beamMeters: number | "UNKNOWN";
  draftMeters: number | "UNKNOWN";
  status: OperationalStatus;
  currentPort: string | "UNKNOWN";
  nextPort: string | "UNKNOWN";
  estimatedAvailabilityDate: string | "UNKNOWN";
  compatibleCargo: CargoType[];
  isGeared: boolean | "UNKNOWN";
  ballastPosition?: string;
}

// 3. Port Profile & Maritime Infrastructure
export interface PortConstraint {
  maxLOAMeters: number | "UNKNOWN";
  maxBeamMeters: number | "UNKNOWN";
  maxDraftMeters: number | "UNKNOWN";
  tidalRestriction: boolean | "UNKNOWN";
  berthCount: number | "UNKNOWN";
  dischargeRateMTPerDay: number | "UNKNOWN";
  dataStatus: DataStatus;
}

export interface Port extends BaseEntityMetadata {
  id: string;
  code: string;
  name: string;
  country: string;
  coast: "East Coast India" | "Overseas Origin" | "Other";
  operationalStatus: OperationalStatus;
  coordinates: {
    lat: number;
    lng: number;
  };
  constraints: PortConstraint;
  knownCargoHandling: CargoType[];
  averageTurnaroundDays: number | "UNKNOWN";
  congestionAlertCount: number;
}

// 4. Voyage Route & Performance
export interface Voyage extends BaseEntityMetadata {
  id: string;
  originPortId: string;
  destinationPortId: string;
  routeDistanceNauticalMiles: number;
  estimatedTransitDays: number;
  bunkerConsumptionMTPerDay: number | "UNKNOWN";
  canalSurchargeUSD?: number;
  riskRating: RiskLevel;
}

// 5. Freight Rate Observation & Forecasting Series
export interface FreightObservation {
  date: string;
  routeId: string;
  vesselClass: VesselClass;
  rateUSDPerMT: number;
  source: string;
}

export interface ForecastPoint {
  date: string;
  historical?: number;
  p10?: number; // Optimistic bound (lower cost)
  p50?: number; // Median projection
  p90?: number; // Pessimistic bound (upper cost)
  forecast?: number;
  isProjected: boolean;
}

export interface FreightForecastSeries extends BaseEntityMetadata {
  id: string;
  route: string;
  vesselClass: VesselClass;
  unit: "$/MT";
  history: ForecastPoint[];
  forecastHorizonDays: number;
  algorithmNote: string;
}

// 6. Market Regime
export interface MarketRegime extends BaseEntityMetadata {
  currentRegime: "Bullish Spike" | "Softening / Bearish" | "Stable / Rangebound" | "High Volatility" | "UNKNOWN";
  volatilityIndex: number | "UNKNOWN";
  bdiReference: number | "UNKNOWN";
  bciReference: number | "UNKNOWN";
  recommendedPosture: "Fix Promptly" | "Wait & Watch" | "Index-Linked" | "Split Hedging" | "PENDING ANALYSIS";
}

// 7. Contract Scenario
export interface ContractScenario extends BaseEntityMetadata {
  scenarioId: string;
  contractType: ContractType;
  estimatedTotalCostUSD: number;
  costPerMT: number;
  riskExposure: RiskLevel;
  flexibilityScore: number; // 1-10
  rationale: string;
}

// 8. Risk Item
export type RiskCategory =
  | "Freight"
  | "Port"
  | "Vessel"
  | "Weather"
  | "Tidal"
  | "Congestion"
  | "Contract";

export interface RiskItem extends BaseEntityMetadata {
  id: string;
  category: RiskCategory;
  title: string;
  description: string;
  severity: RiskLevel;
  mitigationStrategy?: string;
  impactArea: string;
}

// 9. Dashboard Metric / KPI Widget
export interface MetricKPI {
  id: string;
  title: string;
  value: string | number;
  subtitle?: string;
  changePercent?: number;
  trend?: "up" | "down" | "neutral";
  status: DataStatus;
  badgeLabel?: string;
}

// 10. Data Source Registry
export interface DataSource {
  id: string;
  name: string;
  category: "Freight" | "AIS" | "Port Operations" | "Weather" | "Commodities";
  provider: string;
  status: DataStatus;
  lastSync: string;
  coverage: string;
  healthScore: number;
}
