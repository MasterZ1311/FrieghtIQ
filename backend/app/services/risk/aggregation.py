"""
Risk Aggregation Service
Deterministically aggregates operational risk components across Port Congestion,
Weather, Tidal Gates, Vessel Operations, Timing, and Data Quality.

STRICT DETERMINISTIC RULES:
- Severity hierarchy: CRITICAL > HIGH > MEDIUM > LOW > UNKNOWN.
- An aggregate score is CRITICAL if ANY individual evaluated component is CRITICAL.
- An aggregate score is HIGH if ANY component is HIGH and none is CRITICAL.
- An aggregate score is MEDIUM if ANY component is MEDIUM and none is HIGH/CRITICAL.
- No arbitrary 0-100 numerical black-box scores.
- Clear itemized financial exposure breakdown (demurrage + weather delay + idle cost).
"""
from typing import List, Dict, Any, Optional
from app.models.enums import RiskSeverity, RiskType


class RiskAggregationService:
    SEVERITY_ORDER = {
        RiskSeverity.CRITICAL.value: 4,
        RiskSeverity.HIGH.value: 3,
        RiskSeverity.MEDIUM.value: 2,
        RiskSeverity.LOW.value: 1,
        RiskSeverity.UNKNOWN.value: 0
    }

    @classmethod
    def determine_overall_severity(cls, severities: List[str]) -> str:
        """
        Determines aggregate severity from a list of component severities.
        """
        if not severities:
            return RiskSeverity.UNKNOWN.value

        valid_sevs = [s for s in severities if s in cls.SEVERITY_ORDER]
        if not valid_sevs:
            return RiskSeverity.UNKNOWN.value

        # If any is CRITICAL -> CRITICAL
        if RiskSeverity.CRITICAL.value in valid_sevs:
            return RiskSeverity.CRITICAL.value
        # If any is HIGH -> HIGH
        if RiskSeverity.HIGH.value in valid_sevs:
            return RiskSeverity.HIGH.value
        # If any is MEDIUM -> MEDIUM
        if RiskSeverity.MEDIUM.value in valid_sevs:
            return RiskSeverity.MEDIUM.value
        # If all are LOW -> LOW
        if all(s == RiskSeverity.LOW.value for s in valid_sevs):
            return RiskSeverity.LOW.value
        # If all are UNKNOWN -> UNKNOWN
        if all(s == RiskSeverity.UNKNOWN.value for s in valid_sevs):
            return RiskSeverity.UNKNOWN.value

        # Max fallback
        max_val = max(cls.SEVERITY_ORDER.get(s, 0) for s in valid_sevs)
        for k, v in cls.SEVERITY_ORDER.items():
            if v == max_val:
                return k
        return RiskSeverity.UNKNOWN.value

    @classmethod
    def aggregate_operational_risks(
        cls,
        risk_components: List[Dict[str, Any]],
        charter_hire_rate_usd_per_day: float = 20000.0,
        fuel_drift_cost_usd_per_day: float = 3500.0
    ) -> Dict[str, Any]:
        """
        Aggregates a list of risk components (weather, congestion, tidal, timing, operational, etc.).
        """
        component_severities = [comp.get("severity", RiskSeverity.UNKNOWN.value) for comp in risk_components]
        overall_severity = cls.determine_overall_severity(component_severities)

        # Financial exposure accumulation
        total_demurrage_usd = 0.0
        total_weather_delay_hours = 0.0
        total_idle_cost_usd = 0.0
        total_delay_hours = 0.0

        all_explanations = []
        all_mitigations = []
        primary_drivers = []

        for comp in risk_components:
            comp_type = comp.get("risk_type", "GENERAL")
            comp_sev = comp.get("severity", RiskSeverity.UNKNOWN.value)

            # Exposure metrics
            if "demurrage_exposure_usd" in comp and comp["demurrage_exposure_usd"] is not None:
                total_demurrage_usd += float(comp["demurrage_exposure_usd"])

            if "estimated_weather_delay_hours" in comp and comp["estimated_weather_delay_hours"] is not None:
                total_weather_delay_hours += float(comp["estimated_weather_delay_hours"])

            if "cost_exposure_usd" in comp and comp["cost_exposure_usd"] is not None:
                total_idle_cost_usd += float(comp["cost_exposure_usd"])

            if "expected_delay_hours" in comp and comp["expected_delay_hours"] is not None:
                total_delay_hours += float(comp["expected_delay_hours"])

            # Explanations and mitigations
            for exp in comp.get("explanations", []):
                all_explanations.append(f"[{comp_type}] {exp}")
            for mit in comp.get("mitigations", []):
                if mit not in all_mitigations:
                    all_mitigations.append(mit)

            # Identify primary drivers (HIGH or CRITICAL, or matching overall severity)
            if comp_sev in [RiskSeverity.HIGH.value, RiskSeverity.CRITICAL.value] or (overall_severity == comp_sev and comp_sev != RiskSeverity.LOW.value):
                primary_drivers.append({
                    "risk_type": comp_type,
                    "severity": comp_sev,
                    "summary": comp.get("explanations", ["Operational constraint noted"])[0] if comp.get("explanations") else comp.get("explanation", "Operational constraint"),
                    "mitigation": comp.get("mitigations", ["Review operational plan"])[0] if comp.get("mitigations") else comp.get("mitigation", "Review operational plan")
                })

        # Calculate weather financial cost (hire rate + drift fuel during weather stoppage)
        hourly_hire_and_fuel = (charter_hire_rate_usd_per_day + fuel_drift_cost_usd_per_day) / 24.0
        weather_financial_cost = round(total_weather_delay_hours * hourly_hire_and_fuel, 2)
        total_delay_hours += total_weather_delay_hours

        total_financial_exposure_usd = round(total_demurrage_usd + weather_financial_cost + total_idle_cost_usd, 2)

        return {
            "overall_severity": overall_severity,
            "primary_drivers": primary_drivers,
            "components_count": len(risk_components),
            "total_delay_hours": round(total_delay_hours, 1),
            "financial_exposure": {
                "total_exposure_usd": total_financial_exposure_usd,
                "demurrage_exposure_usd": round(total_demurrage_usd, 2),
                "weather_delay_cost_usd": weather_financial_cost,
                "weather_delay_hours": round(total_weather_delay_hours, 1),
                "idle_cost_usd": round(total_idle_cost_usd, 2),
            },
            "explanations": all_explanations,
            "mitigations": all_mitigations
        }
