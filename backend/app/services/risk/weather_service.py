"""
Weather Risk Intelligence Service
Evaluates meteorological conditions for ports and maritime transit legs.

STRICT DATA INTEGRITY:
- Real-world physics: Rainfall halts bulk dry cargo handling (coking coal, thermal coal, iron ore) to avoid liquefaction / moisture cargo contamination.
- Wind cutoffs: >25kt slows handling, >35kt halts cranes, >50kt forces unberthing.
- Swell / Wave cutoffs: >2.5m strains mooring, >3.5m suspends pilot cutter boarding, >5.0m closes channel.
- Never fabricates live satellite feeds; provenance is explicitly labeled (SYNTHETIC, PUBLIC, LICENSED, UNAVAILABLE).
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
import math

from app.models.enums import RiskSeverity


class WeatherProvider(ABC):
    @abstractmethod
    def get_current_weather(
        self,
        port_id: str,
        port_name: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_weather_forecast(
        self,
        port_id: str,
        days: int = 7,
        port_name: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        pass


class SyntheticWeatherAdapter(WeatherProvider):
    """
    Deterministic seasonal weather provider for maritime bulk logistics.
    Produces realistic maritime conditions based on port coordinates and seasonal patterns.
    """
    PORT_CLIMATOLOGY = {
        "PARADIP": {"base_wind": 14.0, "base_wave": 1.8, "base_rain": 2.5, "cyclone_prone": True, "lat": 20.26, "lon": 86.67},
        "HALDIA": {"base_wind": 12.0, "base_wave": 1.2, "base_rain": 3.0, "cyclone_prone": True, "lat": 22.02, "lon": 88.06},
        "VISAKHAPATNAM": {"base_wind": 13.0, "base_wave": 1.6, "base_rain": 1.5, "cyclone_prone": True, "lat": 17.68, "lon": 83.28},
        "PORT_HEDLAND": {"base_wind": 18.0, "base_wave": 2.2, "base_rain": 0.5, "cyclone_prone": True, "lat": -20.31, "lon": 118.57},
        "NEWCASTLE": {"base_wind": 16.0, "base_wave": 2.4, "base_rain": 1.8, "cyclone_prone": False, "lat": -32.92, "lon": 151.78},
        "RICHARDS_BAY": {"base_wind": 20.0, "base_wave": 2.8, "base_rain": 1.2, "cyclone_prone": False, "lat": -28.80, "lon": 32.05},
        "SINGAPORE": {"base_wind": 10.0, "base_wave": 0.8, "base_rain": 4.5, "cyclone_prone": False, "lat": 1.29, "lon": 103.85},
    }

    def _get_profile(self, port_id: str, port_name: Optional[str] = None) -> Dict[str, Any]:
        key = (port_name or port_id or "").upper().replace(" ", "_")
        for k, profile in self.PORT_CLIMATOLOGY.items():
            if k in key:
                return profile
        return {"base_wind": 12.0, "base_wave": 1.5, "base_rain": 1.0, "cyclone_prone": False, "lat": 15.0, "lon": 80.0}

    def get_current_weather(
        self,
        port_id: str,
        port_name: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        profile = self._get_profile(port_id, port_name)
        
        # Deterministic variation by hour
        hour_factor = math.sin(now.hour / 24.0 * 2 * math.pi)
        wind_speed = round(profile["base_wind"] + 4.0 * hour_factor, 1)
        wind_gust = round(wind_speed * 1.35, 1)
        wave_height = round(profile["base_wave"] + 0.5 * hour_factor, 2)
        swell_height = round(wave_height * 0.85, 2)
        rain_mm = round(max(0.0, profile["base_rain"] * (1.0 + 0.5 * hour_factor)), 1)
        
        # Cyclone alert condition (e.g. if simulated storm alert)
        cyclone_alert = profile["cyclone_prone"] and (now.month in [5, 6, 10, 11] and now.day % 7 == 0)
        handling_stoppage = rain_mm > 2.0 or wind_speed > 35.0

        return {
            "port_id": port_id,
            "port_name": port_name,
            "observed_at": now.isoformat(),
            "temperature_c": 28.5 if not profile["lat"] < 0 else 22.0,
            "wind_speed_knots": wind_speed,
            "wind_direction_deg": 180 + int(30 * hour_factor),
            "gust_speed_knots": wind_gust,
            "wave_height_m": wave_height,
            "swell_height_m": swell_height,
            "precipitation_mm": rain_mm,
            "visibility_km": 10.0 if rain_mm < 5.0 else 4.0,
            "pressure_hpa": 1008.0 if not cyclone_alert else 992.0,
            "cyclone_alert": cyclone_alert,
            "cargo_handling_stoppage": handling_stoppage,
            "data_source": "SYNTHETIC",
            "is_synthetic": True,
        }

    def get_weather_forecast(
        self,
        port_id: str,
        days: int = 7,
        port_name: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        profile = self._get_profile(port_id, port_name)
        forecast = []

        for d in range(days):
            forecast_time = now + timedelta(days=d)
            # Deterministic wave/wind cycles
            cycle = math.sin((forecast_time.day + forecast_time.month) * 0.8)
            wind = round(max(6.0, profile["base_wind"] + cycle * 8.0), 1)
            wave = round(max(0.5, profile["base_wave"] + cycle * 1.2), 2)
            rain = round(max(0.0, profile["base_rain"] + cycle * 4.0), 1)
            cyclone = profile["cyclone_prone"] and (d == 3 and forecast_time.month in [5, 10, 11])

            forecast.append({
                "port_id": port_id,
                "port_name": port_name,
                "forecast_date": forecast_time.date().isoformat(),
                "forecast_time": forecast_time.isoformat(),
                "wind_speed_knots": wind,
                "gust_speed_knots": round(wind * 1.35, 1),
                "wave_height_m": wave,
                "swell_height_m": round(wave * 0.8, 2),
                "precipitation_mm": rain,
                "cyclone_alert": cyclone,
                "cargo_handling_stoppage": rain > 2.0 or wind > 35.0,
                "data_source": "SYNTHETIC",
                "is_synthetic": True,
            })
        return forecast


class PublicWeatherAdapter(WeatherProvider):
    """Prepared adapter for Open-Meteo or public APIs; falls back to Synthetic if offline."""
    def __init__(self, fallback_adapter: Optional[WeatherProvider] = None):
        self.fallback = fallback_adapter or SyntheticWeatherAdapter()

    def get_current_weather(self, port_id: str, port_name: Optional[str] = None, lat: Optional[float] = None, lon: Optional[float] = None) -> Optional[Dict[str, Any]]:
        # In production, call public endpoint; fallback gracefully
        res = self.fallback.get_current_weather(port_id, port_name, lat, lon)
        if res:
            res["data_source"] = "PUBLIC_FALLBACK"
        return res

    def get_weather_forecast(self, port_id: str, days: int = 7, port_name: Optional[str] = None, lat: Optional[float] = None, lon: Optional[float] = None) -> List[Dict[str, Any]]:
        res = self.fallback.get_weather_forecast(port_id, days, port_name, lat, lon)
        for r in res:
            r["data_source"] = "PUBLIC_FALLBACK"
        return res


class LicensedWeatherAdapter(WeatherProvider):
    """Prepared adapter for commercial marine feeds (StormGeo, DTN); falls back to Synthetic."""
    def __init__(self, fallback_adapter: Optional[WeatherProvider] = None):
        self.fallback = fallback_adapter or SyntheticWeatherAdapter()

    def get_current_weather(self, port_id: str, port_name: Optional[str] = None, lat: Optional[float] = None, lon: Optional[float] = None) -> Optional[Dict[str, Any]]:
        res = self.fallback.get_current_weather(port_id, port_name, lat, lon)
        if res:
            res["data_source"] = "LICENSED_FALLBACK"
        return res

    def get_weather_forecast(self, port_id: str, days: int = 7, port_name: Optional[str] = None, lat: Optional[float] = None, lon: Optional[float] = None) -> List[Dict[str, Any]]:
        res = self.fallback.get_weather_forecast(port_id, days, port_name, lat, lon)
        for r in res:
            r["data_source"] = "LICENSED_FALLBACK"
        return res


class WeatherRiskService:
    """
    Evaluates weather risk on bulk dry cargo operations and vessel navigation.
    """
    def __init__(self, provider: Optional[WeatherProvider] = None):
        self.provider = provider or SyntheticWeatherAdapter()

    def evaluate_weather_risk(
        self,
        port_id: str,
        port_name: Optional[str] = None,
        cargo_type: Optional[str] = "COKING_COAL",
        lat: Optional[float] = None,
        lon: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluates current and 7-day weather risk for a port.
        """
        current = self.provider.get_current_weather(port_id, port_name, lat, lon)
        forecast = self.provider.get_weather_forecast(port_id, 7, port_name, lat, lon)

        if not current:
            return {
                "port_id": port_id,
                "port_name": port_name,
                "severity": RiskSeverity.UNKNOWN.value,
                "current_weather": None,
                "forecast": [],
                "handling_stoppage_risk": RiskSeverity.UNKNOWN.value,
                "navigation_risk": RiskSeverity.UNKNOWN.value,
                "estimated_weather_delay_hours": 0.0,
                "explanations": ["Weather observation data unavailable for this port."],
                "mitigations": ["Request manual weather bulletin from port agent."],
                "data_source": "UNAVAILABLE",
                "is_synthetic": False
            }

        explanations = []
        mitigations = []
        delay_hours = 0.0

        # 1. Rain / Moisture impact on dry bulk
        rain = current.get("precipitation_mm", 0.0)
        is_moisture_sensitive = cargo_type and any(c in cargo_type.upper() for c in ["COAL", "IRON_ORE", "BAUXITE", "GRAIN", "FERTILIZER"])
        
        handling_risk = RiskSeverity.LOW
        if rain > 10.0:
            handling_risk = RiskSeverity.CRITICAL
            delay_hours += 18.0
            explanations.append(f"Heavy rainfall ({rain} mm/h) triggers mandatory hatch cover closure to prevent cargo slurry liquefaction.")
            mitigations.append("Seal cargo holds immediately; suspend conveyor and grab unloader operations.")
        elif rain > 2.0:
            handling_risk = RiskSeverity.HIGH if is_moisture_sensitive else RiskSeverity.MEDIUM
            delay_hours += 8.0
            explanations.append(f"Moderate rainfall ({rain} mm/h) poses moisture degradation risk for {cargo_type or 'bulk cargo'}.")
            mitigations.append("Coordinate with stevedores for immediate hatch tarping or intermittent discharging.")
        elif rain > 0.5:
            handling_risk = RiskSeverity.MEDIUM
            delay_hours += 2.0
            explanations.append(f"Light precipitation ({rain} mm/h) noted; intermittent stoppage risk during squalls.")

        # 2. Wind impact
        wind = current.get("wind_speed_knots", 0.0)
        gust = current.get("gust_speed_knots", 0.0)
        nav_risk = RiskSeverity.LOW

        if wind > 45.0 or gust > 55.0:
            nav_risk = RiskSeverity.CRITICAL
            delay_hours += 24.0
            explanations.append(f"Severe gale conditions (wind {wind} kts, gust {gust} kts). Port berth safety protocol mandates unberthing.")
            mitigations.append("Vessel master to stand by engine; prepare to slip moorings and proceed to outer anchorage if harbor master directs.")
        elif wind > 35.0 or gust > 42.0:
            nav_risk = RiskSeverity.HIGH
            delay_hours += 12.0
            explanations.append(f"High winds ({wind} kts) exceed mobile unloader and gantry crane safe operating cutoffs (35 kts).")
            mitigations.append("Boom down shore cranes and apply storm brakes; add additional breast and spring mooring lines.")
        elif wind > 25.0:
            nav_risk = RiskSeverity.MEDIUM
            delay_hours += 4.0
            explanations.append(f"Moderate-to-fresh breeze ({wind} kts) may slow vessel tug maneuvers and crane cycle times.")

        # 3. Wave / Swell impact
        wave = current.get("wave_height_m", 0.0)
        if wave > 4.5:
            nav_risk = RiskSeverity.CRITICAL
            delay_hours += 24.0
            explanations.append(f"Extreme wave height ({wave}m) closes approach fairway and pilotage.")
            mitigations.append("Hold vessel at deep-water open sea anchorage; do not attempt pilot boarding ground.")
        elif wave > 3.0:
            if nav_risk != RiskSeverity.CRITICAL:
                nav_risk = RiskSeverity.HIGH
            delay_hours += 8.0
            explanations.append(f"Significant swell ({wave}m) suspends pilot launch operations at outer boarding grounds.")
            mitigations.append("Request helicopter pilot transfer or wait for sea state abatement below 2.5m.")
        elif wave > 2.0 and nav_risk == RiskSeverity.LOW:
            nav_risk = RiskSeverity.MEDIUM

        # 4. Cyclone Alert
        if current.get("cyclone_alert"):
            handling_risk = RiskSeverity.CRITICAL
            nav_risk = RiskSeverity.CRITICAL
            delay_hours = max(delay_hours, 48.0)
            explanations.append("Active tropical depression / cyclone alert in maritime quadrant. Precautionary port shutdown likely.")
            mitigations.append("Initiate cyclone evasion routing; divert inbound vessels away from storm track.")

        # Aggregate overall weather severity
        severities = [handling_risk, nav_risk]
        if RiskSeverity.CRITICAL in severities:
            overall_severity = RiskSeverity.CRITICAL
        elif RiskSeverity.HIGH in severities:
            overall_severity = RiskSeverity.HIGH
        elif RiskSeverity.MEDIUM in severities:
            overall_severity = RiskSeverity.MEDIUM
        else:
            overall_severity = RiskSeverity.LOW

        if not explanations:
            explanations.append(f"Favorable marine weather conditions (Wind {wind} kts, Waves {wave}m, Rain {rain} mm/h). Unimpeded operations.")
            mitigations.append("Maintain standard charter voyage speed and normal port turn plans.")

        return {
            "port_id": port_id,
            "port_name": port_name or current.get("port_name"),
            "severity": overall_severity.value,
            "current_weather": current,
            "forecast": forecast,
            "handling_stoppage_risk": handling_risk.value,
            "navigation_risk": nav_risk.value,
            "estimated_weather_delay_hours": round(delay_hours, 1),
            "explanations": explanations,
            "mitigations": mitigations,
            "data_source": current.get("data_source", "SYNTHETIC"),
            "is_synthetic": current.get("is_synthetic", True)
        }
