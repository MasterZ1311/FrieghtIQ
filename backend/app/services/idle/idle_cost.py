"""
Idle Cost Service
Calculates economic holding loss of idle exposure.

STRICT DATA INTEGRITY:
Idle Cost = Idle Days × Daily Vessel Cost
Daily Vessel Cost must originate from sourced data, configured assumption, or explicit input.
If unavailable: idle_cost = None (UNAVAILABLE).
Never fabricate a vessel daily cost.
"""
from typing import Optional, Tuple


class IdleCostService:
    @staticmethod
    def calculate_idle_cost(
        idle_days: Optional[float],
        daily_vessel_cost: Optional[float],
        cost_source_label: Optional[str] = None
    ) -> Tuple[Optional[float], str]:
        """
        Calculates total idle cost.
        Returns:
            (idle_cost_usd, explanation)
        """
        if idle_days is None:
            return (
                None,
                "Idle exposure days is UNKNOWN; cost cannot be computed."
            )

        if daily_vessel_cost is None or daily_vessel_cost <= 0:
            return (
                None,
                "DAILY VESSEL COST: NOT AVAILABLE. No sourced charter rate or calibrated OPEX assumption recorded."
            )

        source_info = f" ({cost_source_label})" if cost_source_label else ""
        cost = round(idle_days * daily_vessel_cost, 2)
        return (
            cost,
            f"Idle holding cost: ${cost:,.2f} based on {idle_days:.1f} idle days @ ${daily_vessel_cost:,.2f}/day{source_info}."
        )
