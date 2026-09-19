import { FreightForecastSeries } from "@/types";

export const DEMO_FREIGHT_RATES: FreightForecastSeries = {
  id: "series-newcastle-paradip",
  route: "Newcastle (Australia) → Paradip (India)",
  vesselClass: "Capesize",
  unit: "$/MT",
  isDemo: true,
  source: "Simulated Bulk Index (Baltic C5/C3 Benchmark Proxy)",
  sourceDate: "2026-09-15",
  lastUpdated: "2026-09-18T12:00:00Z",
  dataStatus: "DEMO",
  confidence: "MEDIUM",
  forecastHorizonDays: 45,
  algorithmNote: "Architectural Demo Model: Future phases will connect Temporal Fusion Transformer (TFT) & HMM regime switching.",
  history: [
    { date: "Aug 01", historical: 14.20, isProjected: false },
    { date: "Aug 08", historical: 14.55, isProjected: false },
    { date: "Aug 15", historical: 13.90, isProjected: false },
    { date: "Aug 22", historical: 14.10, isProjected: false },
    { date: "Aug 29", historical: 13.75, isProjected: false },
    { date: "Sep 05", historical: 13.40, isProjected: false },
    { date: "Sep 12", historical: 13.65, isProjected: false },
    { date: "Sep 18", historical: 13.80, isProjected: false },
    // Forecast horizon with P10, P50, P90 envelopes
    { date: "Sep 25", p10: 13.10, p50: 13.85, p90: 14.40, forecast: 13.85, isProjected: true },
    { date: "Oct 02", p10: 12.90, p50: 13.95, p90: 14.75, forecast: 13.95, isProjected: true },
    { date: "Oct 09", p10: 12.65, p50: 14.10, p90: 15.20, forecast: 14.10, isProjected: true },
    { date: "Oct 16", p10: 12.40, p50: 14.30, p90: 15.65, forecast: 14.30, isProjected: true },
    { date: "Oct 23", p10: 12.20, p50: 14.45, p90: 16.10, forecast: 14.45, isProjected: true },
    { date: "Oct 30", p10: 11.95, p50: 14.60, p90: 16.50, forecast: 14.60, isProjected: true },
  ],
};

export const DEMO_ALTERNATIVE_ROUTES: { id: string; name: string; currentRate: string; change: string }[] = [
  { id: "r1", name: "Hay Point → Visakhapatnam (Panamax)", currentRate: "$15.10 / MT", change: "+0.45%" },
  { id: "r2", name: "Richards Bay → Dhamra (Supramax)", currentRate: "$18.60 / MT", change: "-1.10%" },
  { id: "r3", name: "Gladstone → Haldia (Handysize)", currentRate: "$21.30 / MT", change: "+0.20%" },
  { id: "r4", name: "Port Hedland → Paradip (Capesize)", currentRate: "$11.80 / MT", change: "-0.85%" },
];
