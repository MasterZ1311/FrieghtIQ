from typing import List, Dict, Any, Tuple
from app.schemas.wait_fix import ScenarioItem
from app.services.wait_fix.economics import FreightEconomicImpactService

class WaitFixScenarioService:
    """
    Constructs discrete economic outcome scenarios (LOW, CENTRAL, HIGH)
    derived from Phase 5 probabilistic quantile forecasts (P10, P50, P90).
    
    Methodology:
    Employs the documented Extended Swanson-Megill 3-point approximation
    for quantile-derived distributions:
      - LOW (P10 Rate): 30% probability weight (softening market / favorable entry)
      - CENTRAL (P50 Rate): 40% probability weight (median expected trajectory)
      - HIGH (P90 Rate): 30% probability weight (adverse spike / tightening tonnage)
      Normalized sum: 0.30 + 0.40 + 0.30 = 1.00.
    """
    DEFAULT_WEIGHTS = {
        "LOW": 0.30,
        "CENTRAL": 0.40,
        "HIGH": 0.30
    }

    @classmethod
    def generate_scenarios(
        cls,
        p10: float,
        p50: float,
        p90: float,
        quantity_mt: float,
        reference_fix_rate: float
    ) -> Tuple[List[ScenarioItem], float, float, float, float]:
        """
        Generates LOW, CENTRAL, HIGH scenario outcomes and computes overall expected wait economics.
        
        Returns:
            (scenarios_list, expected_wait_rate, expected_fix_cost, expected_wait_cost, expected_modeled_difference)
        """
        if not (p10 <= p50 <= p90):
            # Guard against corrupted quantile inversion
            p10 = min(p10, p50, p90)
            p90 = max(p10, p50, p90)
            p50 = max(p10, min(p50, p90))

        current_fix_cost = FreightEconomicImpactService.calculate_total_freight_cost(reference_fix_rate, quantity_mt)

        raw_scenarios = [
            ("LOW", round(p10, 2), cls.DEFAULT_WEIGHTS["LOW"]),
            ("CENTRAL", round(p50, 2), cls.DEFAULT_WEIGHTS["CENTRAL"]),
            ("HIGH", round(p90, 2), cls.DEFAULT_WEIGHTS["HIGH"])
        ]

        scenario_items: List[ScenarioItem] = []
        expected_wait_rate = 0.0

        for name, rate, prob in raw_scenarios:
            f_cost = FreightEconomicImpactService.calculate_total_freight_cost(rate, quantity_mt)
            diff = FreightEconomicImpactService.calculate_cost_difference(current_fix_cost, f_cost)
            expected_wait_rate += rate * prob

            scenario_items.append(ScenarioItem(
                scenario_name=name,
                rate=rate,
                probability=prob,
                freight_cost=f_cost,
                difference_vs_fix=diff
            ))

        expected_wait_rate = round(expected_wait_rate, 2)
        expected_wait_cost = FreightEconomicImpactService.calculate_total_freight_cost(expected_wait_rate, quantity_mt)
        expected_modeled_diff = FreightEconomicImpactService.calculate_cost_difference(current_fix_cost, expected_wait_cost)

        return (
            scenario_items,
            expected_wait_rate,
            current_fix_cost,
            expected_wait_cost,
            expected_modeled_diff
        )
