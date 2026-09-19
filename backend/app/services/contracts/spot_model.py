from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class VoyageCostItem(BaseModel):
    voyage_number: int
    quantity_mt: float
    spot_rate_usd_pmt: float
    freight_cost_usd: float

class SpotCostResult(BaseModel):
    expected_rate: float
    expected_cost: float
    p10_rate: float
    p10_cost: float
    p50_rate: float
    p50_cost: float
    p90_rate: float
    p90_cost: float
    total_quantity_mt: float
    voyage_breakdown: List[VoyageCostItem]

class SpotContractCostModel:
    """
    Evaluates scenario-based spot market exposure across single or repeated voyages.
    Total Spot Cost = SUM(voyage freight rate * voyage quantity)
    Uses Phase 5 forward curve quantiles (P10, P50, P90) and Phase 6 market regimes.
    """

    @staticmethod
    def calculate_spot_exposure(
        voyages: List[Dict[str, Any]], # list of {"voyage_number": int, "parcel_mt": float, "departure_day": int}
        current_spot_rate: float,
        p10_rate: float,
        p50_rate: float,
        p90_rate: float,
        regime_type: str = "NEUTRAL",
        volatility_annualized: float = 0.28
    ) -> SpotCostResult:
        if current_spot_rate <= 0:
            raise ValueError("Current spot rate must be strictly positive.")
        if not voyages:
            raise ValueError("At least one voyage must be provided.")

        total_quantity = sum(v.get("parcel_mt", 0.0) for v in voyages)
        if total_quantity <= 0:
            raise ValueError("Total parcel quantity must be strictly positive.")

        # Extended forward rate estimation per voyage based on forward horizon and regime
        # For prompt voyage (day ~0), rate is current spot.
        # For subsequent voyages, rate converges toward forward forecast curve.
        total_p10_cost = 0.0
        total_p50_cost = 0.0
        total_p90_cost = 0.0
        total_expected_cost = 0.0
        breakdown: List[VoyageCostItem] = []

        for v in voyages:
            qty = float(v.get("parcel_mt", 0.0))
            dep_day = int(v.get("departure_day", 0))

            # Forward weighting: prompt is spot, later voyages reflect forward distribution
            weight_forward = min(1.0, dep_day / 30.0) if dep_day > 0 else 0.0
            
            v_p10 = (1.0 - weight_forward) * current_spot_rate + weight_forward * p10_rate
            v_p50 = (1.0 - weight_forward) * current_spot_rate + weight_forward * p50_rate
            v_p90 = (1.0 - weight_forward) * current_spot_rate + weight_forward * p90_rate

            # Swanson-Megill 3-point expected rate for the voyage
            v_expected = 0.30 * v_p10 + 0.40 * v_p50 + 0.30 * v_p90

            v_exp_cost = v_expected * qty
            total_expected_cost += v_exp_cost
            total_p10_cost += v_p10 * qty
            total_p50_cost += v_p50 * qty
            total_p90_cost += v_p90 * qty

            breakdown.append(VoyageCostItem(
                voyage_number=int(v.get("voyage_number", len(breakdown) + 1)),
                quantity_mt=qty,
                spot_rate_usd_pmt=round(v_expected, 2),
                freight_cost_usd=round(v_exp_cost, 2)
            ))

        return SpotCostResult(
            expected_rate=round(total_expected_cost / total_quantity, 2),
            expected_cost=round(total_expected_cost, 2),
            p10_rate=round(total_p10_cost / total_quantity, 2),
            p10_cost=round(total_p10_cost, 2),
            p50_rate=round(total_p50_cost / total_quantity, 2),
            p50_cost=round(total_p50_cost, 2),
            p90_rate=round(total_p90_cost / total_quantity, 2),
            p90_cost=round(total_p90_cost, 2),
            total_quantity_mt=round(total_quantity, 2),
            voyage_breakdown=breakdown
        )
