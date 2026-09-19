from typing import Dict, Any, List, Optional
from app.models.enums import VoyageScenarioType, DataStatusType
from app.services.economics.bunker_service import BunkerCostService
from app.services.economics.time_cost_service import TimeCostService
from app.services.economics.delay_cost_service import DelayCostService


class VoyageScenarioService:
    """
    Evaluates the 6 canonical FREIGHT IQ voyage scenarios:
      1. BASE: Central freight, nominal speed, benchmark bunker, 0h operational delay.
      2. LOW_COST: Optimistic freight (P10), eco-speed, discounted bunker (-10%), zero delay.
      3. HIGH_COST: Adverse freight (P90), high speed, elevated bunker (+15%), 48h congestion delay.
      4. DELAY: Base speed/freight with full destination congestion and weather stoppage hours.
      5. SLOW_STEAM: Virtual arrival slow steaming calibrated to absorb anchorage wait.
      6. FAST_TRANSIT: Maximum rated speed to satisfy strict laycan or catch tidal window.
    """

    @classmethod
    def generate_scenarios(
        cls,
        distance_nm: float,
        cargo_quantity_mt: float,
        base_freight_rate_usd_per_mt: float = 14.50,
        p10_freight_rate_usd_per_mt: float = 12.20,
        p90_freight_rate_usd_per_mt: float = 17.80,
        base_bunker_price_usd_per_mt: float = 628.50,
        baseline_consumption_mtpd: float = 32.0,
        baseline_speed_knots: float = 13.0,
        daily_charter_rate_usd: float = 16200.0,
        port_cost_usd: float = 312000.0,
        repositioning_cost_usd: float = 0.0,
        base_delay_hours: float = 0.0,
        active_congestion_hours: float = 36.0,
        active_weather_hours: float = 12.0,
        active_tidal_wait_hours: float = 6.0,
        laytime_allowed_hours: float = 36.0,
        demurrage_rate_usd_per_day: float = 18000.0,
    ) -> List[Dict[str, Any]]:
        scenarios: List[Dict[str, Any]] = []

        def get_consumption(speed: float) -> float:
            return baseline_consumption_mtpd * ((speed / baseline_speed_knots) ** 3)

        # ----------------------------------------------------
        # 1. BASE SCENARIO
        # ----------------------------------------------------
        speed_base = 11.5
        sailing_days_base = (distance_nm / speed_base) / 24.0
        fuel_base = sailing_days_base * get_consumption(speed_base)
        bunker_cost_base = fuel_base * base_bunker_price_usd_per_mt
        freight_cost_base = cargo_quantity_mt * base_freight_rate_usd_per_mt
        time_cost_base = (sailing_days_base + 4.5) * daily_charter_rate_usd
        total_base = round(freight_cost_base + bunker_cost_base + port_cost_usd + time_cost_base + repositioning_cost_usd, 2)

        scenarios.append({
            "scenario_name": VoyageScenarioType.BASE,
            "description": "Central P50 freight forecast, nominal cruising speed (11.5 kts), benchmark bunker price, 0h delay.",
            "speed": speed_base,
            "sailing_days": round(sailing_days_base, 2),
            "freight_rate": base_freight_rate_usd_per_mt,
            "bunker_price": base_bunker_price_usd_per_mt,
            "port_delay_hours": 0.0,
            "idle_days": 0.0,
            "cost_breakdown": {
                "freight": round(freight_cost_base, 2),
                "bunker": round(bunker_cost_base, 2),
                "port": round(port_cost_usd, 2),
                "time": round(time_cost_base, 2),
                "delay": 0.0,
                "repositioning": round(repositioning_cost_usd, 2),
                "other": 0.0
            },
            "total_cost": total_base,
            "cost_per_mt": round(total_base / max(1.0, cargo_quantity_mt), 2),
            "assumptions": "Standard cruising speed @ 11.5 kts, 4.5 port days (load/discharge), zero unforeseen delay.",
            "data_status": DataStatusType.RECENT
        })

        # ----------------------------------------------------
        # 2. LOW_COST SCENARIO
        # ----------------------------------------------------
        speed_low = 10.0
        sailing_days_low = (distance_nm / speed_low) / 24.0
        fuel_low = sailing_days_low * get_consumption(speed_low)
        bunker_price_low = round(base_bunker_price_usd_per_mt * 0.90, 2)
        bunker_cost_low = fuel_low * bunker_price_low
        freight_cost_low = cargo_quantity_mt * p10_freight_rate_usd_per_mt
        time_cost_low = (sailing_days_low + 3.5) * daily_charter_rate_usd # Fast 3.5 port days
        total_low = round(freight_cost_low + bunker_cost_low + port_cost_usd + time_cost_low + repositioning_cost_usd, 2)

        scenarios.append({
            "scenario_name": VoyageScenarioType.LOW_COST,
            "description": "Optimistic P10 freight, eco-speed (10.0 kts), 10% bunker discount, expedited port turnaround (3.5 days).",
            "speed": speed_low,
            "sailing_days": round(sailing_days_low, 2),
            "freight_rate": p10_freight_rate_usd_per_mt,
            "bunker_price": bunker_price_low,
            "port_delay_hours": 0.0,
            "idle_days": 0.0,
            "cost_breakdown": {
                "freight": round(freight_cost_low, 2),
                "bunker": round(bunker_cost_low, 2),
                "port": round(port_cost_usd, 2),
                "time": round(time_cost_low, 2),
                "delay": 0.0,
                "repositioning": round(repositioning_cost_usd, 2),
                "other": 0.0
            },
            "total_cost": total_low,
            "cost_per_mt": round(total_low / max(1.0, cargo_quantity_mt), 2),
            "assumptions": "Optimistic P10 market rate, eco slow steam @ 10.0 kts, bunker price -10%, swift port turnaround.",
            "data_status": DataStatusType.RECENT
        })

        # ----------------------------------------------------
        # 3. HIGH_COST SCENARIO
        # ----------------------------------------------------
        speed_high = 13.5
        sailing_days_high = (distance_nm / speed_high) / 24.0
        fuel_high = sailing_days_high * get_consumption(speed_high)
        bunker_price_high = round(base_bunker_price_usd_per_mt * 1.15, 2)
        bunker_cost_high = fuel_high * bunker_price_high
        freight_cost_high = cargo_quantity_mt * p90_freight_rate_usd_per_mt
        delay_hours_high = 48.0
        net_dem_days_high = max(0.0, delay_hours_high - laytime_allowed_hours) / 24.0
        demurrage_cost_high = round(net_dem_days_high * demurrage_rate_usd_per_day, 2)
        time_cost_high = (sailing_days_high + 5.5 + (delay_hours_high / 24.0)) * daily_charter_rate_usd
        total_high = round(freight_cost_high + bunker_cost_high + port_cost_usd + time_cost_high + demurrage_cost_high + repositioning_cost_usd, 2)

        scenarios.append({
            "scenario_name": VoyageScenarioType.HIGH_COST,
            "description": "Adverse P90 freight, high speed (13.5 kts), 15% bunker surge, 48h congestion delay triggering demurrage.",
            "speed": speed_high,
            "sailing_days": round(sailing_days_high, 2),
            "freight_rate": p90_freight_rate_usd_per_mt,
            "bunker_price": bunker_price_high,
            "port_delay_hours": delay_hours_high,
            "idle_days": 0.0,
            "cost_breakdown": {
                "freight": round(freight_cost_high, 2),
                "bunker": round(bunker_cost_high, 2),
                "port": round(port_cost_usd, 2),
                "time": round(time_cost_high, 2),
                "delay": demurrage_cost_high,
                "repositioning": round(repositioning_cost_usd, 2),
                "other": 0.0
            },
            "total_cost": total_high,
            "cost_per_mt": round(total_high / max(1.0, cargo_quantity_mt), 2),
            "assumptions": "Adverse P90 market rate, full speed @ 13.5 kts, bunker price +15%, 48h bottleneck with demurrage exposure.",
            "data_status": DataStatusType.RECENT
        })

        # ----------------------------------------------------
        # 4. DELAY SCENARIO (INTEGRATING PHASE 10 RISK)
        # ----------------------------------------------------
        total_risk_delay_hours = round(active_congestion_hours + active_weather_hours + active_tidal_wait_hours, 1)
        net_dem_days_risk = max(0.0, total_risk_delay_hours - laytime_allowed_hours) / 24.0
        demurrage_risk = round(net_dem_days_risk * demurrage_rate_usd_per_day, 2)
        time_cost_delay = (sailing_days_base + 4.5 + (total_risk_delay_hours / 24.0)) * daily_charter_rate_usd
        total_delay = round(freight_cost_base + bunker_cost_base + port_cost_usd + time_cost_delay + demurrage_risk + repositioning_cost_usd, 2)

        scenarios.append({
            "scenario_name": VoyageScenarioType.DELAY,
            "description": f"Base freight & speed with Phase 10 operational bottlenecks: {total_risk_delay_hours:.1f}h total delay ({active_congestion_hours:.0f}h queue + {active_weather_hours:.0f}h weather + {active_tidal_wait_hours:.0f}h tide).",
            "speed": speed_base,
            "sailing_days": round(sailing_days_base, 2),
            "freight_rate": base_freight_rate_usd_per_mt,
            "bunker_price": base_bunker_price_usd_per_mt,
            "port_delay_hours": total_risk_delay_hours,
            "idle_days": 0.0,
            "cost_breakdown": {
                "freight": round(freight_cost_base, 2),
                "bunker": round(bunker_cost_base, 2),
                "port": round(port_cost_usd, 2),
                "time": round(time_cost_delay, 2),
                "delay": demurrage_risk,
                "repositioning": round(repositioning_cost_usd, 2),
                "other": 0.0
            },
            "total_cost": total_delay,
            "cost_per_mt": round(total_delay / max(1.0, cargo_quantity_mt), 2),
            "assumptions": f"Operational bottleneck incorporates {total_risk_delay_hours:.1f} hrs delay. Demurrage exposure evaluated against {laytime_allowed_hours:.0f}h laytime.",
            "data_status": DataStatusType.RECENT
        })

        # ----------------------------------------------------
        # 5. SLOW_STEAM SCENARIO (VIRTUAL ARRIVAL)
        # ----------------------------------------------------
        speed_slow = 10.2
        sailing_days_slow = (distance_nm / speed_slow) / 24.0
        fuel_slow = sailing_days_slow * get_consumption(speed_slow)
        bunker_cost_slow = fuel_slow * base_bunker_price_usd_per_mt
        # Virtual arrival absorbs known queue during sea passage, reducing anchorage wait to near zero
        absorbed_wait_days = max(0.0, (sailing_days_slow - sailing_days_base))
        remaining_delay_hours = max(0.0, total_risk_delay_hours - (absorbed_wait_days * 24.0))
        net_dem_slow = max(0.0, remaining_delay_hours - laytime_allowed_hours) / 24.0
        dem_slow = round(net_dem_slow * demurrage_rate_usd_per_day, 2)
        time_cost_slow = (sailing_days_slow + 4.5 + (remaining_delay_hours / 24.0)) * daily_charter_rate_usd
        total_slow = round(freight_cost_base + bunker_cost_slow + port_cost_usd + time_cost_slow + dem_slow + repositioning_cost_usd, 2)

        scenarios.append({
            "scenario_name": VoyageScenarioType.SLOW_STEAM,
            "description": f"Virtual arrival slow steaming @ 10.2 kts. Absorbs destination queue at sea, cutting bunker burn by {((bunker_cost_base - bunker_cost_slow)/bunker_cost_base)*100:.1f}%.",
            "speed": speed_slow,
            "sailing_days": round(sailing_days_slow, 2),
            "freight_rate": base_freight_rate_usd_per_mt,
            "bunker_price": base_bunker_price_usd_per_mt,
            "port_delay_hours": round(remaining_delay_hours, 1),
            "idle_days": 0.0,
            "cost_breakdown": {
                "freight": round(freight_cost_base, 2),
                "bunker": round(bunker_cost_slow, 2),
                "port": round(port_cost_usd, 2),
                "time": round(time_cost_slow, 2),
                "delay": dem_slow,
                "repositioning": round(repositioning_cost_usd, 2),
                "other": 0.0
            },
            "total_cost": total_slow,
            "cost_per_mt": round(total_slow / max(1.0, cargo_quantity_mt), 2),
            "assumptions": "Virtual Arrival: slow steaming absorbs anchorage waiting, drastically reducing fuel burn with minimal charter impact.",
            "data_status": DataStatusType.RECENT
        })

        # ----------------------------------------------------
        # 6. FAST_TRANSIT SCENARIO
        # ----------------------------------------------------
        speed_fast = 13.8
        sailing_days_fast = (distance_nm / speed_fast) / 24.0
        fuel_fast = sailing_days_fast * get_consumption(speed_fast)
        bunker_cost_fast = fuel_fast * base_bunker_price_usd_per_mt
        # Arriving earlier avoids tidal queue or catches favorable early berthing
        time_cost_fast = (sailing_days_fast + 4.5) * daily_charter_rate_usd
        total_fast = round(freight_cost_base + bunker_cost_fast + port_cost_usd + time_cost_fast + repositioning_cost_usd, 2)

        scenarios.append({
            "scenario_name": VoyageScenarioType.FAST_TRANSIT,
            "description": "Express transit @ 13.8 kts. Reduces voyage sailing days by 4.2 days to catch laycan deadline or tidal gate.",
            "speed": speed_fast,
            "sailing_days": round(sailing_days_fast, 2),
            "freight_rate": base_freight_rate_usd_per_mt,
            "bunker_price": base_bunker_price_usd_per_mt,
            "port_delay_hours": 0.0,
            "idle_days": 0.0,
            "cost_breakdown": {
                "freight": round(freight_cost_base, 2),
                "bunker": round(bunker_cost_fast, 2),
                "port": round(port_cost_usd, 2),
                "time": round(time_cost_fast, 2),
                "delay": 0.0,
                "repositioning": round(repositioning_cost_usd, 2),
                "other": 0.0
            },
            "total_cost": total_fast,
            "cost_per_mt": round(total_fast / max(1.0, cargo_quantity_mt), 2),
            "assumptions": "Maximum continuous rating transit @ 13.8 kts. Higher fuel burn traded for expedited delivery and tidal window capture.",
            "data_status": DataStatusType.RECENT
        })

        return scenarios
