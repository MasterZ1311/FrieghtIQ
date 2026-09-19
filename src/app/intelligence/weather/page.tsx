"use client";

import React, { useState, useEffect } from "react";
import {
  Wind,
  CloudRain,
  Waves,
  Compass,
  Thermometer,
  Eye,
  Gauge,
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  RefreshCw,
  Calendar,
  Layers,
  FileText,
  AlertOctagon,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { RiskBadge } from "@/components/badges/RiskBadge";
import { DataStatusBadge } from "@/components/badges/DataStatusBadge";
import { riskApi, WeatherEvaluationResponse, WeatherObservation } from "@/lib/api/risk";
import { portsApi, Port } from "@/lib/api/ports";

export default function WeatherIntelligencePage() {
  const [selectedPortId, setSelectedPortId] = useState<string>("port-inprt");
  const [cargoType, setCargoType] = useState<string>("COKING_COAL");
  const [weatherData, setWeatherData] = useState<WeatherEvaluationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const fetchWeather = async (showSpinner = false) => {
    try {
      if (showSpinner) setRefreshing(true);
      else setLoading(true);

      const res = await riskApi.getPortWeather(selectedPortId, cargoType);
      setWeatherData(res);
    } catch (err) {
      console.error("Error fetching weather intelligence:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchWeather();
  }, [selectedPortId, cargoType]);

  const current = weatherData?.current_weather;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        title="MARINE METEOROLOGICAL INTELLIGENCE"
        description="Real-time sea-state observations, bulk cargo rainfall stoppage risks, swell cutoffs, and 7-day marine forecasts across key trading ports."
        status="OPERATIONAL INTELLIGENCE"
        actions={
          <button
            onClick={() => fetchWeather(true)}
            disabled={refreshing}
            className="flex items-center gap-2 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-amber-400" : ""}`} />
            Refresh Meteorological Feed
          </button>
        }
      />

      {/* Port & Cargo Selector */}
      <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-slate-400">Terminal Location:</span>
          {[
            { id: "port-inprt", name: "Paradip (Bay of Bengal)" },
            { id: "port-inhal", name: "Haldia (Hooghly River)" },
            { id: "port-invtz", name: "Visakhapatnam" },
            { id: "port-sgsin", name: "Singapore Roads" },
            { id: "port-auncb", name: "Newcastle (Pacific)" },
            { id: "port-zarcb", name: "Richards Bay (Indian Ocean)" },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setSelectedPortId(item.id)}
              className={`px-3 py-1.5 text-xs font-mono rounded transition ${
                selectedPortId === item.id
                  ? "bg-sky-500 text-slate-950 font-bold shadow-md shadow-sky-500/20"
                  : "bg-slate-950 border border-slate-800 text-slate-300 hover:border-slate-700"
              }`}
            >
              {item.name}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Commodity Sensitivity:</span>
          <select
            value={cargoType}
            onChange={(e) => setCargoType(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 font-mono focus:outline-none focus:border-sky-500"
          >
            <option value="COKING_COAL">Coking Coal (Moisture Strict)</option>
            <option value="THERMAL_COAL">Thermal Coal</option>
            <option value="IRON_ORE">Iron Ore Fines</option>
            <option value="GRAIN">Grain / Agri Bulk</option>
          </select>
        </div>
      </div>

      {/* Cyclone / Storm Warning Banner */}
      {current?.cyclone_alert && (
        <div className="p-4 rounded-lg bg-red-950/80 border border-red-500 text-red-100 flex items-start gap-3 animate-pulse">
          <AlertOctagon className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-xs font-bold uppercase tracking-wider text-red-200">
              Active Tropical Depression / Cyclone Alert
            </h4>
            <p className="text-xs text-red-200/90 leading-relaxed">
              Severe meteorological warning in maritime quadrant. Harbor Master protocol mandates suspension of outer anchorage pilotage and emergency unberthing standby.
            </p>
          </div>
        </div>
      )}

      {/* Current Meteorological Instruments Deck */}
      {current && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[11px] font-medium">Wind Speed</span>
              <Wind className="w-3.5 h-3.5 text-sky-400" />
            </div>
            <div className="text-xl font-mono font-bold text-slate-100">
              {current.wind_speed_knots} <span className="text-xs font-normal text-slate-400">kts</span>
            </div>
            <div className="text-[10px] font-mono text-slate-400">
              Gusts: {current.gust_speed_knots || ((current.wind_speed_knots ?? 0) * 1.35).toFixed(1)} kts
            </div>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[11px] font-medium">Wave Height (Hs)</span>
              <Waves className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <div className="text-xl font-mono font-bold text-cyan-400">
              {current.wave_height_m} <span className="text-xs font-normal text-slate-400">m</span>
            </div>
            <div className="text-[10px] font-mono text-slate-400">
              Swell: {current.swell_height_m || ((current.wave_height_m ?? 0) * 0.85).toFixed(1)}m
            </div>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[11px] font-medium">Precipitation</span>
              <CloudRain className="w-3.5 h-3.5 text-blue-400" />
            </div>
            <div
              className={`text-xl font-mono font-bold ${
                (current.precipitation_mm || 0) > 2.0 ? "text-rose-400" : "text-emerald-400"
              }`}
            >
              {current.precipitation_mm} <span className="text-xs font-normal text-slate-400">mm/h</span>
            </div>
            <div className="text-[10px] text-slate-400">
              {(current.precipitation_mm || 0) > 2.0 ? "Hold Sealing Triggered" : "Nominal"}
            </div>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[11px] font-medium">Wind Direction</span>
              <Compass className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div className="text-xl font-mono font-bold text-slate-100">
              {current.wind_direction_deg || 180}°
            </div>
            <div className="text-[10px] text-slate-400">South-Southwest</div>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[11px] font-medium">Barometer</span>
              <Gauge className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="text-xl font-mono font-bold text-slate-100">
              {current.pressure_hpa || 1008} <span className="text-xs font-normal text-slate-400">hPa</span>
            </div>
            <div className="text-[10px] text-slate-400">Stable Pressure</div>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[11px] font-medium">Visibility</span>
              <Eye className="w-3.5 h-3.5 text-indigo-400" />
            </div>
            <div className="text-xl font-mono font-bold text-slate-100">
              {current.visibility_km || 10} <span className="text-xs font-normal text-slate-400">km</span>
            </div>
            <div className="text-[10px] text-slate-400">Unrestricted Fairway</div>
          </div>
        </div>
      )}

      {/* Operational Thresholds & Cutoffs */}
      {weatherData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Rain / Bulk Moisture Stoppage */}
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <CloudRain className="w-4 h-4 text-sky-400" />
                Bulk Cargo Stoppage Risk
              </span>
              <RiskBadge level={weatherData.handling_stoppage_risk} />
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Coking coal and iron ore holds must be battened down during rainfall exceeding 2.0 mm/h to prevent cargo slurry liquefaction and moisture limit breaches.
            </p>
            <div className="p-2.5 rounded bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-300">
              Protocol:{" "}
              <span className="text-amber-400 font-semibold">
                {current?.cargo_handling_stoppage ? "Mandatory Hatch Tarping" : "Unrestricted Unloading"}
              </span>
            </div>
          </div>

          {/* Shore Crane Wind Cutoff */}
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Wind className="w-4 h-4 text-amber-400" />
                Crane / Unloader Wind Limit
              </span>
              <RiskBadge
                level={
                  (current?.wind_speed_knots || 0) > 35
                    ? "HIGH"
                    : (current?.wind_speed_knots || 0) > 25
                    ? "MEDIUM"
                    : "LOW"
                }
              />
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Mobile harbor cranes and CSU boom unloader safe wind cutoff threshold is 35 knots. Winds &gt;25 knots reduce handling cycle speed by 15–20%.
            </p>
            <div className="p-2.5 rounded bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-300">
              Threshold Margin:{" "}
              <span className="text-slate-200 font-semibold">
                {Math.max(0, 35 - (current?.wind_speed_knots || 0)).toFixed(1)} kts buffer
              </span>
            </div>
          </div>

          {/* Pilotage & Swell Cutoff */}
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Waves className="w-4 h-4 text-cyan-400" />
                Pilot Boarding Swell Limit
              </span>
              <RiskBadge level={weatherData.navigation_risk} />
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Pilot cutter embarkation at outer boarding grounds is suspended when significant swell exceeds 3.0 meters due to craft boarding hazard.
            </p>
            <div className="p-2.5 rounded bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-300">
              Pilotage Ground:{" "}
              <span className="text-emerald-400 font-semibold">
                {(current?.wave_height_m || 0) > 3.0 ? "Pilotage Suspended" : "Open & Accessible"}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 7-Day Marine Forecast Cards */}
      {weatherData && weatherData.forecast && (
        <div className="p-5 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-sky-400" />
                7-Day Operational Marine Forecast Deck
              </h3>
              <p className="text-xs text-slate-400">
                Daily projected wind velocity, significant wave height, and bulk dry discharge feasibility.
              </p>
            </div>
            <DataStatusBadge status="RECENT" />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
            {weatherData.forecast.map((fc, idx) => (
              <div
                key={idx}
                className="p-3 rounded bg-slate-950 border border-slate-800 space-y-2 text-center"
              >
                <div className="text-[11px] font-mono font-semibold text-slate-300">
                  {fc.forecast_date.slice(5)}
                </div>

                <div className="space-y-1">
                  <div className="text-xs text-slate-400 flex items-center justify-between font-mono">
                    <span>Wind:</span>
                    <span className="text-slate-200 font-bold">{fc.wind_speed_knots} kts</span>
                  </div>
                  <div className="text-xs text-slate-400 flex items-center justify-between font-mono">
                    <span>Waves:</span>
                    <span className="text-cyan-400 font-bold">{fc.wave_height_m}m</span>
                  </div>
                  <div className="text-xs text-slate-400 flex items-center justify-between font-mono">
                    <span>Rain:</span>
                    <span className="text-blue-400 font-bold">{fc.precipitation_mm} mm</span>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800/80">
                  {fc.cargo_handling_stoppage ? (
                    <span className="px-1.5 py-0.5 text-[9px] font-mono uppercase rounded bg-rose-950 border border-rose-800 text-rose-300 block">
                      Stoppage Risk
                    </span>
                  ) : (
                    <span className="px-1.5 py-0.5 text-[9px] font-mono uppercase rounded bg-emerald-950 border border-emerald-800 text-emerald-300 block">
                      Clear Handling
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Explanations & Actionable Mitigations */}
      {weatherData && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              Meteorological Assessment
            </h4>
            <ul className="space-y-1.5 text-xs text-slate-300">
              {weatherData.explanations.map((exp, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-sky-400 mt-1.5 shrink-0" />
                  <span>{exp}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-amber-400">
              Chartering & Vessel Master Guidance
            </h4>
            <ul className="space-y-1.5 text-xs text-slate-300">
              {weatherData.mitigations.map((mit, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                  <span>{mit}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
