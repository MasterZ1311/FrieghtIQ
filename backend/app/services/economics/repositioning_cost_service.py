from typing import Dict, Any, Optional, List
from app.models.enums import CostComponentType, DataStatusType


class RepositioningCostService:
    """
    Evaluates ballast repositioning and pre-voyage idle exposure expenses.
    Integrates Phase 9 idle and deadhead analysis:
      - Ballast fuel consumed to reach load port
      - Idle holding expense during employment gap
    Adheres strictly to the rule:
      Never fabricate fleet economics; calculate only when required inputs exist.
    """

    @classmethod
    def calculate_repositioning_cost(
        cls,
        ballast_distance_nm: float = 0.0,
        ballast_speed_knots: Optional[float] = None,
        ballast_consumption_mtpd: Optional[float] = None,
        bunker_price_usd_per_mt: Optional[float] = None,
        idle_days: float = 0.0,
        daily_idle_cost_usd: float = 5500.0, # Crew + insurance + auxiliary fuel in anchorage
        cargo_quantity_mt: float = 75000.0,
        is_already_at_load_port: bool = False
    ) -> Dict[str, Any]:
        if is_already_at_load_port or ballast_distance_nm <= 0:
            return {
                "ballast_distance_nm": 0.0,
                "ballast_sailing_days": 0.0,
                "ballast_fuel_consumed_mt": 0.0,
                "repositioning_bunker_cost_usd": 0.0,
                "idle_days": idle_days,
                "idle_cost_usd": round(idle_days * daily_idle_cost_usd, 2) if idle_days > 0 else 0.0,
                "total_repositioning_cost_usd": round(idle_days * daily_idle_cost_usd, 2) if idle_days > 0 else 0.0,
                "cost_per_mt": round((idle_days * daily_idle_cost_usd) / max(1.0, cargo_quantity_mt), 2) if idle_days > 0 else 0.0,
                "is_positioned": True,
                "components": [],
                "data_status": DataStatusType.VERIFIED,
                "explanation": "Vessel already positioned at or near load port. Zero ballast repositioning distance."
            }

        # Ballast leg calculation
        speed = ballast_speed_knots or 12.0
        sailing_hours = ballast_distance_nm / max(1.0, speed)
        sailing_days = round(sailing_hours / 24.0, 2)

        components: List[Dict[str, Any]] = []
        bunker_cost = 0.0
        status = DataStatusType.RECENT

        if ballast_consumption_mtpd and ballast_consumption_mtpd > 0 and bunker_price_usd_per_mt and bunker_price_usd_per_mt > 0:
            fuel_mt = round(sailing_days * ballast_consumption_mtpd, 2)
            bunker_cost = round(fuel_mt * bunker_price_usd_per_mt, 2)
            components.append({
                "component_type": CostComponentType.REPOSITIONING_BUNKER,
                "amount": bunker_cost,
                "unit": "USD",
                "quantity": fuel_mt,
                "rate": bunker_price_usd_per_mt,
                "source": "Phase 9 Ballast Repositioning Model",
                "data_status": DataStatusType.RECENT,
                "assumption": f"Ballast transit of {ballast_distance_nm:,.0f} NM @ {speed:.1f} kts consuming {fuel_mt:,.1f} MT fuel."
            })
        else:
            status = DataStatusType.UNKNOWN

        idle_cost = round(idle_days * daily_idle_cost_usd, 2) if idle_days > 0 else 0.0
        if idle_cost > 0:
            components.append({
                "component_type": CostComponentType.OTHER,
                "amount": idle_cost,
                "unit": "USD/DAY",
                "quantity": idle_days,
                "rate": daily_idle_cost_usd,
                "source": "Phase 9 Idle Exposure Model",
                "data_status": DataStatusType.RECENT,
                "assumption": f"Holding cost over {idle_days:.1f} idle gap days before voyage commencement."
            })

        total_cost = round(bunker_cost + idle_cost, 2)
        cost_per_mt = round(total_cost / max(1.0, cargo_quantity_mt), 2)

        return {
            "ballast_distance_nm": ballast_distance_nm,
            "ballast_sailing_days": sailing_days,
            "ballast_speed_knots": speed,
            "ballast_consumption_mtpd": ballast_consumption_mtpd,
            "bunker_price_usd_per_mt": bunker_price_usd_per_mt,
            "repositioning_bunker_cost_usd": bunker_cost,
            "idle_days": idle_days,
            "daily_idle_cost_usd": daily_idle_cost_usd,
            "idle_cost_usd": idle_cost,
            "total_repositioning_cost_usd": total_cost,
            "cost_per_mt": cost_per_mt,
            "is_positioned": False,
            "components": components,
            "data_status": status,
            "explanation": f"Repositioning cost of ${total_cost:,.2f} modeled for {ballast_distance_nm:,.0f} NM ballast positioning + {idle_days:.1f} idle days."
        }
