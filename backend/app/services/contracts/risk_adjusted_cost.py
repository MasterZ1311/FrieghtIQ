from typing import Dict, Any
from pydantic import BaseModel

class RiskAdjustedCostBreakdown(BaseModel):
    expected_freight_cost: float
    uncertainty_adjustment_usd: float
    commitment_adjustment_usd: float
    total_risk_adjusted_cost: float
    risk_adjusted_rate_pmt: float
    uncertainty_coefficient: float
    commitment_coefficient: float
    assumptions_summary: str

class RiskAdjustedCostService:
    """
    Computes risk-adjusted total procurement freight cost (SIH26006):
    Risk-adjusted Cost = Expected Freight Cost + Uncertainty Adjustment + Commitment Adjustment
    Exposes full parametric breakdown without hidden or arbitrary coefficients.
    """

    @staticmethod
    def calculate_risk_adjusted_cost(
        expected_freight_cost: float,
        total_quantity_mt: float,
        spot_quantity_mt: float,
        contracted_quantity_mt: float,
        p50_spot_rate: float,
        p90_spot_rate: float,
        contract_duration_days: int = 180,
        uncertainty_coefficient: float = 0.50, # weight on adverse (P90 - P50) spread
        commitment_coefficient: float = 0.02 # 2% annual commitment drag on fixed volume
    ) -> RiskAdjustedCostBreakdown:
        if total_quantity_mt <= 0:
            raise ValueError("Total quantity must be strictly positive.")

        # 1. Uncertainty adjustment: penalizes open spot tonnage exposed to upside freight spike (P90 - P50)
        adverse_spread = max(0.0, p90_spot_rate - p50_spot_rate)
        uncertainty_adj = round(uncertainty_coefficient * adverse_spread * spot_quantity_mt, 2)

        # 2. Commitment adjustment: penalizes rigid multi-voyage lock-in (loss of optionality)
        duration_ratio = contract_duration_days / 365.0
        contracted_share = contracted_quantity_mt / total_quantity_mt
        commitment_adj = round(commitment_coefficient * expected_freight_cost * contracted_share * (1.0 + duration_ratio), 2)

        total_risk_adjusted = round(expected_freight_cost + uncertainty_adj + commitment_adj, 2)
        rate_pmt = round(total_risk_adjusted / total_quantity_mt, 2)

        summary = (
            f"Uncertainty adjustment (${uncertainty_adj:,.0f}) reflects {uncertainty_coefficient*100:.0f}% of adverse (P90-P50) "
            f"spread on open spot tonnage. Commitment adjustment (${commitment_adj:,.0f}) reflects {commitment_coefficient*100:.1f}% "
            f"liquidity lock-in over {contract_duration_days} days."
        )

        return RiskAdjustedCostBreakdown(
            expected_freight_cost=round(expected_freight_cost, 2),
            uncertainty_adjustment_usd=uncertainty_adj,
            commitment_adjustment_usd=commitment_adj,
            total_risk_adjusted_cost=total_risk_adjusted,
            risk_adjusted_rate_pmt=rate_pmt,
            uncertainty_coefficient=uncertainty_coefficient,
            commitment_coefficient=commitment_coefficient,
            assumptions_summary=summary
        )
