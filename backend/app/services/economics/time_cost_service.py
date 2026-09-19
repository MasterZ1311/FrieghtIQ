from typing import Dict, Any, Optional
from app.models.enums import CostComponentType, DataStatusType


class TimeCostService:
    """
    Evaluates vessel time-based capital, hire, and operational expenditure.
    Adheres strictly to the rule:
      Never fabricate daily vessel hire rates.
      If hire rates are missing, returns UNKNOWN.
    """

    BENCHMARK_HIRE_RATES: Dict[str, float] = {
        "CAPESIZE": 26500.0,
        "PANAMAX": 16200.0,
        "SUPRAMAX": 14500.0,
        "HANDYSIZE": 11800.0,
    }

    @classmethod
    def calculate_time_cost(
        cls,
        sailing_days: float,
        port_days: float,
        waiting_days: float = 0.0,
        daily_charter_rate_usd: Optional[float] = None,
        daily_opex_usd: Optional[float] = None,
        vessel_class: Optional[str] = None,
        cargo_quantity_mt: float = 75000.0,
        allow_benchmark_fallback: bool = True
    ) -> Dict[str, Any]:
        total_days = round(sailing_days + port_days + waiting_days, 3)

        effective_rate = daily_charter_rate_usd
        rate_source = "User Specified / Contract Rate"
        rate_status = DataStatusType.RECENT

        if effective_rate is None or effective_rate <= 0:
            if allow_benchmark_fallback and vessel_class:
                class_key = vessel_class.upper().strip()
                if class_key in cls.BENCHMARK_HIRE_RATES:
                    effective_rate = cls.BENCHMARK_HIRE_RATES[class_key]
                    rate_source = f"Baltic Dry Index Class Benchmark ({class_key})"
                    rate_status = DataStatusType.RECENT
            
        if effective_rate is None or effective_rate <= 0:
            return {
                "sailing_days": sailing_days,
                "port_days": port_days,
                "waiting_days": waiting_days,
                "total_voyage_days": total_days,
                "daily_charter_rate_usd": None,
                "charter_hire_cost_usd": None,
                "opex_cost_usd": None,
                "total_time_cost_usd": None,
                "cost_per_mt": None,
                "is_calculable": False,
                "data_status": DataStatusType.UNKNOWN,
                "rate_source": "UNAVAILABLE",
                "explanation": "Daily vessel charter hire rate is unavailable. Vessel time cost cannot be calculated without assuming hire rate."
            }

        charter_cost = round(total_days * effective_rate, 2)
        opex_cost = round(total_days * (daily_opex_usd or 0.0), 2)
        total_time_cost = round(charter_cost + opex_cost, 2)
        cost_per_mt = round(total_time_cost / max(1.0, cargo_quantity_mt), 2)

        components = [
            {
                "component_type": CostComponentType.TIME_CHARTER,
                "amount": charter_cost,
                "unit": "USD/DAY",
                "quantity": total_days,
                "rate": effective_rate,
                "source": rate_source,
                "data_status": rate_status,
                "assumption": f"Vessel hire calculated over {total_days:.2f} total days ({sailing_days:.1f} sailing, {port_days:.1f} port, {waiting_days:.1f} waiting)."
            }
        ]
        if opex_cost > 0:
            components.append({
                "component_type": CostComponentType.TIME_OPPORTUNITY,
                "amount": opex_cost,
                "unit": "USD/DAY",
                "quantity": total_days,
                "rate": daily_opex_usd,
                "source": "Documented Technical OPEX",
                "data_status": DataStatusType.VERIFIED,
                "assumption": "Owner technical operational expenses during voyage duration."
            })

        return {
            "sailing_days": sailing_days,
            "port_days": port_days,
            "waiting_days": waiting_days,
            "total_voyage_days": total_days,
            "daily_charter_rate_usd": effective_rate,
            "daily_opex_usd": daily_opex_usd,
            "charter_hire_cost_usd": charter_cost,
            "opex_cost_usd": opex_cost,
            "total_time_cost_usd": total_time_cost,
            "cost_per_mt": cost_per_mt,
            "components": components,
            "rate_source": rate_source,
            "data_status": rate_status,
            "is_calculable": True,
            "explanation": f"Time cost of ${total_time_cost:,.2f} modeled across {total_days:.1f} days @ ${effective_rate:,.0f}/day."
        }
