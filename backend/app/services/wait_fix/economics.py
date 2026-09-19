from typing import Tuple

class FreightEconomicImpactService:
    """
    Calculates voyage-level freight economics and cost deltas.
    Strictly preserves unit integrity: rates in USD/MT, quantities in MT, total amounts in USD.
    Does not convert or mix with daily time-charter rates (USD/day) without explicit charter voyage conversion.
    """
    @staticmethod
    def calculate_total_freight_cost(rate_usd_pmt: float, quantity_mt: float) -> float:
        """
        Total Freight Cost (USD) = Freight Rate (USD/MT) × Cargo Quantity (MT)
        """
        if quantity_mt <= 0:
            raise ValueError(f"Cargo quantity must be strictly positive, received {quantity_mt} MT")
        if rate_usd_pmt < 0:
            raise ValueError(f"Freight rate cannot be negative, received ${rate_usd_pmt}/MT")
        return round(float(rate_usd_pmt * quantity_mt), 2)

    @staticmethod
    def calculate_cost_difference(current_fix_cost: float, expected_wait_cost: float) -> float:
        """
        Modeled Freight Cost Difference = Current Fix Cost - Expected Wait Cost
        Positive value: Expected modeled saving by waiting.
        Negative value: Modeled saving by fixing now (waiting expected to cost more).
        """
        return round(float(current_fix_cost - expected_wait_cost), 2)

    @staticmethod
    def calculate_savings_percentage(modeled_difference: float, current_fix_cost: float) -> float:
        """
        Relative percentage advantage compared to prompt fixture cost.
        """
        if current_fix_cost <= 0:
            return 0.0
        return round(float((modeled_difference / current_fix_cost) * 100), 2)
