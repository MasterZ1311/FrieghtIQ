from typing import Dict, Any, List, Optional
from app.models.enums import DataStatusType


class SensitivityService:
    """
    Multidimensional economic sensitivity and elasticity engine.
    Calculates dynamic variations across key maritime operational levers:
      - Bunker fuel price (USD/MT)
      - Freight rate (USD/MT)
      - Vessel cruising speed (knots)
      - Cargo quantity (MT)
      - Port congestion / delay (hours)
      - Daily vessel hire / charter rate (USD/day)
    Strictly adheres to:
      Do not hardcode sensitivity tables; recalculate dynamically from physical models.
    """

    @classmethod
    def calculate_sensitivities(
        cls,
        distance_nm: float,
        base_cargo_quantity_mt: float = 75000.0,
        base_freight_rate_usd_per_mt: float = 14.50,
        base_bunker_price_usd_per_mt: float = 628.50,
        base_speed_knots: float = 11.5,
        base_daily_charter_rate_usd: float = 16200.0,
        base_port_cost_usd: float = 312000.0,
        base_port_delay_hours: float = 0.0,
        baseline_consumption_mtpd: float = 32.0,
        baseline_speed_knots: float = 13.0,
        laytime_allowed_hours: float = 36.0,
        demurrage_rate_usd_per_day: float = 18000.0,
        port_days: float = 4.5,
        repositioning_cost_usd: float = 0.0,
    ) -> Dict[str, Any]:
        
        def run_single(
            cargo_mt: float,
            freight_rate: float,
            bunker_price: float,
            speed: float,
            daily_hire: float,
            delay_hours: float,
        ) -> Dict[str, Any]:
            sailing_days = (distance_nm / speed) / 24.0
            fuel_rate = baseline_consumption_mtpd * ((speed / baseline_speed_knots) ** 3)
            fuel_consumed = sailing_days * fuel_rate
            bunker_cost = fuel_consumed * bunker_price
            freight_cost = cargo_mt * freight_rate
            total_days = sailing_days + port_days + (delay_hours / 24.0)
            time_cost = total_days * daily_hire

            net_dem_days = max(0.0, delay_hours - laytime_allowed_hours) / 24.0
            delay_cost = net_dem_days * demurrage_rate_usd_per_day

            total = round(freight_cost + bunker_cost + base_port_cost_usd + time_cost + delay_cost + repositioning_cost_usd, 2)
            cost_per_mt = round(total / max(1.0, cargo_mt), 2)

            return {
                "total_cost": total,
                "cost_per_mt": cost_per_mt,
                "freight_cost": round(freight_cost, 2),
                "bunker_cost": round(bunker_cost, 2),
                "port_cost": round(base_port_cost_usd, 2),
                "time_cost": round(time_cost, 2),
                "delay_cost": round(delay_cost, 2),
                "repositioning_cost": round(repositioning_cost_usd, 2),
                "fuel_consumed_mt": round(fuel_consumed, 1),
                "sailing_days": round(sailing_days, 2)
            }

        base_res = run_single(
            base_cargo_quantity_mt,
            base_freight_rate_usd_per_mt,
            base_bunker_price_usd_per_mt,
            base_speed_knots,
            base_daily_charter_rate_usd,
            base_port_delay_hours
        )

        # 1. Bunker Price Sensitivity (-20%, -10%, Base, +10%, +20%)
        bunker_variations = [0.80, 0.90, 1.00, 1.10, 1.20]
        bunker_curve = []
        for factor in bunker_variations:
            p = round(base_bunker_price_usd_per_mt * factor, 2)
            r = run_single(base_cargo_quantity_mt, base_freight_rate_usd_per_mt, p, base_speed_knots, base_daily_charter_rate_usd, base_port_delay_hours)
            bunker_curve.append({
                "delta_pct": f"{(factor - 1.0) * 100:+.0f}%",
                "bunker_price_usd": p,
                "total_cost_usd": r["total_cost"],
                "cost_per_mt": r["cost_per_mt"],
                "bunker_cost_usd": r["bunker_cost"],
                "delta_total_usd": round(r["total_cost"] - base_res["total_cost"], 2)
            })

        # 2. Freight Rate Sensitivity (P10, Base P50, P90, and steps)
        freight_variations = [round(base_freight_rate_usd_per_mt * f, 2) for f in [0.80, 0.90, 1.00, 1.10, 1.20]]
        freight_curve = []
        for fr in freight_variations:
            r = run_single(base_cargo_quantity_mt, fr, base_bunker_price_usd_per_mt, base_speed_knots, base_daily_charter_rate_usd, base_port_delay_hours)
            freight_curve.append({
                "freight_rate_usd_per_mt": fr,
                "total_cost_usd": r["total_cost"],
                "cost_per_mt": r["cost_per_mt"],
                "freight_cost_usd": r["freight_cost"],
                "delta_total_usd": round(r["total_cost"] - base_res["total_cost"], 2)
            })

        # 3. Speed Sensitivity (9 to 14 kts)
        speeds = [9.0, 10.0, 11.0, 11.5, 12.0, 13.0, 14.0]
        speed_curve = []
        for spd in speeds:
            r = run_single(base_cargo_quantity_mt, base_freight_rate_usd_per_mt, base_bunker_price_usd_per_mt, spd, base_daily_charter_rate_usd, base_port_delay_hours)
            speed_curve.append({
                "speed_knots": spd,
                "sailing_days": r["sailing_days"],
                "bunker_cost_usd": r["bunker_cost"],
                "time_cost_usd": r["time_cost"],
                "total_cost_usd": r["total_cost"],
                "cost_per_mt": r["cost_per_mt"],
                "delta_total_usd": round(r["total_cost"] - base_res["total_cost"], 2)
            })

        # 4. Port Delay Sensitivity (0h to 120h)
        delays = [0.0, 24.0, 48.0, 72.0, 96.0, 120.0]
        delay_curve = []
        for d in delays:
            r = run_single(base_cargo_quantity_mt, base_freight_rate_usd_per_mt, base_bunker_price_usd_per_mt, base_speed_knots, base_daily_charter_rate_usd, d)
            delay_curve.append({
                "delay_hours": d,
                "delay_cost_usd": r["delay_cost"],
                "time_cost_usd": r["time_cost"],
                "total_cost_usd": r["total_cost"],
                "cost_per_mt": r["cost_per_mt"],
                "delta_total_usd": round(r["total_cost"] - base_res["total_cost"], 2)
            })

        # 5. Cargo Quantity Sensitivity (e.g. 60k, 70k, 75k, 80k, 85k MT)
        cargo_steps = [round(base_cargo_quantity_mt * f, 0) for f in [0.80, 0.90, 1.00, 1.10, 1.15]]
        cargo_curve = []
        for cq in cargo_steps:
            r = run_single(cq, base_freight_rate_usd_per_mt, base_bunker_price_usd_per_mt, base_speed_knots, base_daily_charter_rate_usd, base_port_delay_hours)
            cargo_curve.append({
                "cargo_quantity_mt": cq,
                "total_cost_usd": r["total_cost"],
                "cost_per_mt": r["cost_per_mt"],
                "freight_cost_usd": r["freight_cost"],
                "delta_cost_per_mt": round(r["cost_per_mt"] - base_res["cost_per_mt"], 2)
            })

        # 6. Daily Charter Rate Sensitivity (-25%, Base, +25%)
        hire_rates = [round(base_daily_charter_rate_usd * f, 0) for f in [0.75, 0.90, 1.00, 1.10, 1.25]]
        hire_curve = []
        for hr in hire_rates:
            r = run_single(base_cargo_quantity_mt, base_freight_rate_usd_per_mt, base_bunker_price_usd_per_mt, base_speed_knots, hr, base_port_delay_hours)
            hire_curve.append({
                "daily_charter_rate_usd": hr,
                "time_cost_usd": r["time_cost"],
                "total_cost_usd": r["total_cost"],
                "cost_per_mt": r["cost_per_mt"],
                "delta_total_usd": round(r["total_cost"] - base_res["total_cost"], 2)
            })

        return {
            "baseline": base_res,
            "bunker_sensitivity": bunker_curve,
            "freight_sensitivity": freight_curve,
            "speed_sensitivity": speed_curve,
            "delay_sensitivity": delay_curve,
            "cargo_sensitivity": cargo_curve,
            "hire_rate_sensitivity": hire_curve,
            "data_status": DataStatusType.RECENT
        }
