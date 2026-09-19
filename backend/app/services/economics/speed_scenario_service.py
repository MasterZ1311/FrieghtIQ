from typing import Dict, Any, List, Optional
import math

from app.models.enums import SpeedScenarioStatus, DataStatusType


class SpeedScenarioService:
    """
    Generates configurable speed scenarios across valid operational ranges.
    Utilizes hydrodynamic cubic Admiralty coefficient relationship:
      F(V) = F_0 * (V / V_0)^3
    Strictly adheres to:
      - Only evaluate speeds physically valid for the vessel
      - Do not claim a speed is optimal unless underlying inputs support it
      - Wording: 'Economically preferred speed under available assumptions'
      - Never fabricate baseline consumption rates
    """

    DEFAULT_CANDIDATE_SPEEDS = [8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0]

    @classmethod
    def evaluate_speed_scenarios(
        cls,
        distance_nm: float,
        cargo_quantity_mt: float = 75000.0,
        baseline_speed_knots: Optional[float] = 13.0,
        baseline_consumption_mtpd: Optional[float] = 32.0,
        bunker_price_usd_per_mt: Optional[float] = 628.50,
        daily_charter_rate_usd: Optional[float] = 16200.0,
        port_cost_usd: float = 0.0,
        port_days: float = 4.5, # 2 days load + 2.5 days discharge
        fixed_delay_hours: float = 0.0,
        candidate_speeds: Optional[List[float]] = None,
        max_vessel_speed_knots: Optional[float] = 14.5,
        min_vessel_speed_knots: Optional[float] = 7.5,
    ) -> Dict[str, Any]:
        speeds = candidate_speeds or cls.DEFAULT_CANDIDATE_SPEEDS
        speeds = sorted(list(set(speeds)))

        has_fuel_model = (
            baseline_speed_knots is not None and baseline_speed_knots > 0 and
            baseline_consumption_mtpd is not None and baseline_consumption_mtpd > 0
        )
        has_bunker_price = bunker_price_usd_per_mt is not None and bunker_price_usd_per_mt > 0
        has_hire_rate = daily_charter_rate_usd is not None and daily_charter_rate_usd > 0

        scenarios: List[Dict[str, Any]] = []
        preferred_speed = None
        min_total_cost = float("inf")

        for spd in speeds:
            sailing_hours = round(distance_nm / spd, 2)
            sailing_days = round(sailing_hours / 24.0, 3)
            total_voyage_days = round(sailing_days + port_days + (fixed_delay_hours / 24.0), 3)

            # Operational speed boundary validation
            if max_vessel_speed_knots and spd > max_vessel_speed_knots:
                scenarios.append({
                    "speed_knots": spd,
                    "sailing_hours": sailing_hours,
                    "sailing_days": sailing_days,
                    "fuel_consumption_mtpd": None,
                    "fuel_consumed_mt": None,
                    "bunker_cost_usd": None,
                    "time_cost_usd": None,
                    "delay_exposure_usd": None,
                    "port_cost_usd": port_cost_usd,
                    "total_cost_usd": None,
                    "cost_per_mt": None,
                    "status": SpeedScenarioStatus.SPEED_EXCEEDS_RATING,
                    "assumption": f"Speed {spd:.1f} kts exceeds vessel maximum certified continuous rating ({max_vessel_speed_knots:.1f} kts)."
                })
                continue

            if min_vessel_speed_knots and spd < min_vessel_speed_knots:
                scenarios.append({
                    "speed_knots": spd,
                    "sailing_hours": sailing_hours,
                    "sailing_days": sailing_days,
                    "fuel_consumption_mtpd": None,
                    "fuel_consumed_mt": None,
                    "bunker_cost_usd": None,
                    "time_cost_usd": None,
                    "delay_exposure_usd": None,
                    "port_cost_usd": port_cost_usd,
                    "total_cost_usd": None,
                    "cost_per_mt": None,
                    "status": SpeedScenarioStatus.SUBOPTIMAL,
                    "assumption": f"Speed {spd:.1f} kts below minimum safe engine governor maneuvering speed ({min_vessel_speed_knots:.1f} kts)."
                })
                continue

            # Fuel Consumption: Hydrodynamic Cubic Admiralty Law
            fuel_rate = None
            fuel_consumed = None
            bunker_cost = None
            if has_fuel_model:
                # F = F_0 * (V / V_0)^3
                speed_ratio = spd / baseline_speed_knots
                fuel_rate = round(baseline_consumption_mtpd * (speed_ratio ** 3), 2)
                fuel_consumed = round(sailing_days * fuel_rate, 2)
                if has_bunker_price:
                    bunker_cost = round(fuel_consumed * bunker_price_usd_per_mt, 2)

            # Time Cost
            time_cost = None
            if has_hire_rate:
                time_cost = round(total_voyage_days * daily_charter_rate_usd, 2)

            # Total Cost
            total_cost = None
            cost_per_mt = None
            if bunker_cost is not None and time_cost is not None:
                total_cost = round(bunker_cost + time_cost + port_cost_usd, 2)
                cost_per_mt = round(total_cost / max(1.0, cargo_quantity_mt), 2)

                if total_cost < min_total_cost:
                    min_total_cost = total_cost
                    preferred_speed = spd

            status = SpeedScenarioStatus.EVALUATED
            if not has_fuel_model or not has_bunker_price or not has_hire_rate:
                status = SpeedScenarioStatus.INSUFFICIENT_DATA

            scenarios.append({
                "speed_knots": spd,
                "sailing_hours": sailing_hours,
                "sailing_days": sailing_days,
                "total_voyage_days": total_voyage_days,
                "fuel_consumption_mtpd": fuel_rate,
                "fuel_consumed_mt": fuel_consumed,
                "bunker_price_usd_per_mt": bunker_price_usd_per_mt if has_bunker_price else None,
                "bunker_cost_usd": bunker_cost,
                "daily_hire_usd": daily_charter_rate_usd if has_hire_rate else None,
                "time_cost_usd": time_cost,
                "port_cost_usd": port_cost_usd,
                "delay_exposure_usd": 0.0,
                "total_cost_usd": total_cost,
                "cost_per_mt": cost_per_mt,
                "status": status,
                "assumption": f"Admiralty cubic law: {fuel_rate:.1f} MT/day @ {spd:.1f} kts based on baseline {baseline_consumption_mtpd:.1f} MT/day @ {baseline_speed_knots:.1f} kts." if has_fuel_model else "Missing baseline fuel consumption."
            })

        # Mark the economically preferred speed
        if preferred_speed is not None:
            for sc in scenarios:
                if sc["speed_knots"] == preferred_speed and sc["total_cost_usd"] is not None:
                    sc["status"] = SpeedScenarioStatus.ECONOMICALLY_PREFERRED

        can_determine_optimum = (preferred_speed is not None and has_fuel_model and has_bunker_price and has_hire_rate)

        return {
            "distance_nm": distance_nm,
            "cargo_quantity_mt": cargo_quantity_mt,
            "baseline_speed_knots": baseline_speed_knots,
            "baseline_consumption_mtpd": baseline_consumption_mtpd,
            "bunker_price_usd_per_mt": bunker_price_usd_per_mt,
            "daily_charter_rate_usd": daily_charter_rate_usd,
            "scenarios": scenarios,
            "can_determine_optimum": can_determine_optimum,
            "economically_preferred_speed_knots": preferred_speed if can_determine_optimum else None,
            "min_total_cost_usd": min_total_cost if can_determine_optimum else None,
            "verdict_label": "Economically preferred speed under available assumptions" if can_determine_optimum else "Insufficient data to determine economic speed.",
            "data_status": DataStatusType.RECENT if can_determine_optimum else DataStatusType.UNKNOWN,
            "explanation": (
                f"Economically preferred speed under available assumptions is {preferred_speed:.1f} knots "
                f"(Total Cost: ${min_total_cost:,.2f} / ${min_total_cost/max(1.0, cargo_quantity_mt):.2f}/MT)."
                if can_determine_optimum
                else "Insufficient data to determine economic speed. Baseline fuel consumption, bunker price, or charter hire rate is unavailable."
            )
        }
