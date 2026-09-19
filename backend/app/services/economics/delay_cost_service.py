from typing import Dict, Any, Optional, List
from app.models.enums import CostComponentType, DataStatusType


class DelayCostService:
    """
    Evaluates expected delay and demurrage exposure from operational bottlenecks
    (port congestion, weather handling stoppages, and tidal gate waits).

    CRITICAL SEMANTIC INTEGRITY:
      Never present an estimated delay cost as actual contractual demurrage.
      This engine strictly computes EXPECTED DEMURRAGE EXPOSURE.
    """

    DEFAULT_DEMURRAGE_RATES: Dict[str, float] = {
        "CAPESIZE": 28000.0,
        "PANAMAX": 18000.0,
        "SUPRAMAX": 15000.0,
        "HANDYSIZE": 12000.0,
    }

    @classmethod
    def calculate_delay_exposure(
        cls,
        congestion_wait_hours: float = 0.0,
        weather_stoppage_hours: float = 0.0,
        tidal_wait_hours: float = 0.0,
        laytime_allowed_hours: float = 36.0,
        demurrage_rate_usd_per_day: Optional[float] = None,
        vessel_class: Optional[str] = "PANAMAX",
        cargo_quantity_mt: float = 75000.0,
    ) -> Dict[str, Any]:
        total_delay_hours = round(congestion_wait_hours + weather_stoppage_hours + tidal_wait_hours, 2)
        
        rate = demurrage_rate_usd_per_day
        rate_source = "Contractual Laytime / Charter Party Rate"
        rate_status = DataStatusType.RECENT

        if rate is None or rate <= 0:
            if vessel_class:
                class_key = vessel_class.upper().strip()
                rate = cls.DEFAULT_DEMURRAGE_RATES.get(class_key, 18000.0)
                rate_source = f"Industry Standard Benchmark Demurrage ({class_key})"
                rate_status = DataStatusType.DEMO
            else:
                rate = 18000.0
                rate_source = "Standard Panamax Demurrage Benchmark"
                rate_status = DataStatusType.DEMO

        # Laytime absorption: Demurrage only commences once allowable laytime is exceeded
        net_demurrage_hours = max(0.0, round(total_delay_hours - laytime_allowed_hours, 2))
        demurrage_days = net_demurrage_hours / 24.0
        exposure_usd = round(demurrage_days * rate, 2)
        cost_per_mt = round(exposure_usd / max(1.0, cargo_quantity_mt), 2)

        components: List[Dict[str, Any]] = []
        if exposure_usd > 0:
            components.append({
                "component_type": CostComponentType.DELAY_DEMURRAGE,
                "amount": exposure_usd,
                "unit": "USD/DAY",
                "quantity": round(demurrage_days, 3),
                "rate": rate,
                "source": rate_source,
                "data_status": rate_status,
                "assumption": f"Expected demurrage exposure: total operational delay ({total_delay_hours:.1f}h) exceeds agreed laytime ({laytime_allowed_hours:.1f}h) by {net_demurrage_hours:.1f}h."
            })

        evidence_notes = []
        if congestion_wait_hours > 0:
            evidence_notes.append(f"Port congestion queue: {congestion_wait_hours:.1f} hrs")
        if weather_stoppage_hours > 0:
            evidence_notes.append(f"Bulk cargo rain/sea-state stoppage: {weather_stoppage_hours:.1f} hrs")
        if tidal_wait_hours > 0:
            evidence_notes.append(f"Tidal gate high-water waiting: {tidal_wait_hours:.1f} hrs")

        return {
            "total_delay_hours": total_delay_hours,
            "congestion_wait_hours": congestion_wait_hours,
            "weather_stoppage_hours": weather_stoppage_hours,
            "tidal_wait_hours": tidal_wait_hours,
            "laytime_allowed_hours": laytime_allowed_hours,
            "net_demurrage_hours": net_demurrage_hours,
            "demurrage_days": round(demurrage_days, 2),
            "demurrage_rate_usd_per_day": rate,
            "demurrage_exposure_usd": exposure_usd,
            "cost_per_mt": cost_per_mt,
            "is_actual_demurrage": False,
            "exposure_classification": "EXPECTED_DEMURRAGE_EXPOSURE",
            "evidence_notes": evidence_notes,
            "components": components,
            "data_status": rate_status,
            "explanation": f"Expected demurrage exposure of ${exposure_usd:,.2f} modeled over {net_demurrage_hours:.1f} net demurrage hours (agreed laytime: {laytime_allowed_hours:.0f}h)."
        }
