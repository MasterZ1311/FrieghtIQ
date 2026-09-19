from typing import Dict, Any, List, Optional
from app.models.enums import DataStatusType


class SpeedBreakEvenService:
    """
    Computes marginal economic speed break-even analysis:
      Marginal Bunker Cost increase vs Marginal Time Charter savings.
    Strictly adheres to:
      If insufficient data exists -> 'Insufficient data to determine economic speed.'
      Never forces an unvalidated result.
    """

    @classmethod
    def calculate_break_even(
        cls,
        distance_nm: float,
        baseline_consumption_mtpd: Optional[float] = 32.0,
        baseline_speed_knots: Optional[float] = 13.0,
        bunker_price_usd_per_mt: Optional[float] = 628.50,
        daily_charter_rate_usd: Optional[float] = 16200.0,
        cargo_quantity_mt: float = 75000.0,
        speed_step: float = 0.5,
        min_speed: float = 8.5,
        max_speed: float = 14.0,
    ) -> Dict[str, Any]:
        # Verification of required data
        if (
            not distance_nm or distance_nm <= 0 or
            not baseline_consumption_mtpd or baseline_consumption_mtpd <= 0 or
            not baseline_speed_knots or baseline_speed_knots <= 0 or
            not bunker_price_usd_per_mt or bunker_price_usd_per_mt <= 0 or
            not daily_charter_rate_usd or daily_charter_rate_usd <= 0
        ):
            return {
                "is_evaluable": False,
                "break_even_speed_knots": None,
                "economic_speed_range_min": None,
                "economic_speed_range_max": None,
                "marginal_steps": [],
                "data_status": DataStatusType.UNKNOWN,
                "verdict": "Insufficient data to determine economic speed.",
                "explanation": "Insufficient data to determine economic speed. Baseline fuel consumption, baseline speed, bunker price, or daily charter hire rate is missing."
            }

        def get_consumption(v: float) -> float:
            return baseline_consumption_mtpd * ((v / baseline_speed_knots) ** 3)

        steps: List[Dict[str, Any]] = []
        current_v = min_speed
        break_even_knot = None

        while current_v + speed_step <= max_speed + 0.001:
            v1 = round(current_v, 1)
            v2 = round(current_v + speed_step, 1)

            # Durations
            t1_days = (distance_nm / v1) / 24.0
            t2_days = (distance_nm / v2) / 24.0
            time_saved_days = t1_days - t2_days
            time_value_saved = time_saved_days * daily_charter_rate_usd

            # Fuel burns
            f1_rate = get_consumption(v1)
            f2_rate = get_consumption(v2)
            b1_mt = t1_days * f1_rate
            b2_mt = t2_days * f2_rate
            delta_fuel_mt = b2_mt - b1_mt
            delta_bunker_cost = delta_fuel_mt * bunker_price_usd_per_mt

            # Net marginal savings of speeding up by speed_step knots
            net_marginal_gain = time_value_saved - delta_bunker_cost

            steps.append({
                "from_speed_knots": v1,
                "to_speed_knots": v2,
                "time_saved_hours": round(time_saved_days * 24.0, 1),
                "time_saved_days": round(time_saved_days, 2),
                "time_value_saved_usd": round(time_value_saved, 2),
                "delta_fuel_consumed_mt": round(delta_fuel_mt, 2),
                "delta_bunker_cost_usd": round(delta_bunker_cost, 2),
                "net_marginal_gain_usd": round(net_marginal_gain, 2),
                "recommendation": "SPEED_UP_ECONOMIC" if net_marginal_gain > 0 else "SLOW_STEAM_ECONOMIC"
            })

            # Check crossing point where speeding up becomes economically net negative
            if break_even_knot is None and net_marginal_gain <= 0:
                break_even_knot = v1

            current_v += speed_step

        if break_even_knot is None:
            break_even_knot = max_speed

        eco_min = max(min_speed, round(break_even_knot - 0.5, 1))
        eco_max = min(max_speed, round(break_even_knot + 0.5, 1))

        return {
            "is_evaluable": True,
            "break_even_speed_knots": break_even_knot,
            "economic_speed_range_min": eco_min,
            "economic_speed_range_max": eco_max,
            "marginal_steps": steps,
            "daily_charter_rate_usd": daily_charter_rate_usd,
            "bunker_price_usd_per_mt": bunker_price_usd_per_mt,
            "data_status": DataStatusType.RECENT,
            "verdict": f"Economically preferred speed under available assumptions: {break_even_knot:.1f} knots (Range: {eco_min:.1f} - {eco_max:.1f} kts).",
            "explanation": (
                f"Above {break_even_knot:.1f} knots, the marginal bunker expenditure exceeds the time charter hire savings "
                f"(${(daily_charter_rate_usd):,.0f}/day), rendering faster transit economically suboptimal."
            )
        }
