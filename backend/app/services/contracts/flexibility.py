from typing import Dict, Any
from pydantic import BaseModel

class FlexibilityEvaluation(BaseModel):
    flexibility_score: float # 0.0 (rigid) to 1.0 (maximum agility)
    duration_factor: float
    volume_commitment_factor: float
    market_volatility_factor: float
    cancellation_optionality_score: float
    explanation: str

class FlexibilityCostModel:
    """
    Evaluates commercial and operational flexibility of chartering strategies.
    Considers:
    - Contract duration (single spot = highest flexibility, 180d = lower)
    - Proportion of total requirement contracted vs spot
    - Market volatility (higher volatility makes flexibility more valuable)
    - Ability to cancel, substitute, or renegotiate laycans
    """

    @staticmethod
    def evaluate(
        contract_duration_days: int,
        contracted_share: float, # 0.0 to 1.0
        volatility_annualized: float = 0.28,
        demand_uncertainty_index: float = 0.15 # 0.0 to 1.0
    ) -> FlexibilityEvaluation:
        contracted_share = max(0.0, min(1.0, contracted_share))
        
        # Duration factor: 0 days = 1.0, 90 days = 0.65, 180 days = 0.40
        duration_factor = max(0.20, 1.0 - (contract_duration_days / 365.0) * 0.80)
        
        # Volume commitment factor: 0% contracted = 1.0, 100% contracted = 0.20
        volume_factor = 1.0 - (contracted_share * 0.80)

        # Volatility & demand uncertainty scaling:
        # When volatility is high, fixed commitment imposes higher inflexibility penalty
        vol_scaling = 1.0 - min(0.20, volatility_annualized * 0.40 * contracted_share)

        # Cancellation optionality: spot retains 100% walkaway optionality
        cancellation_score = 1.0 - (contracted_share * 0.70)

        # Composite flexibility score (0.0 to 1.0)
        score = round((0.40 * volume_factor) + (0.30 * duration_factor) + (0.30 * cancellation_score * vol_scaling), 3)
        score = max(0.05, min(1.0, score))

        if score >= 0.75:
            explanation = "High flexibility: Minimal forward volume encumbrance; agility to exploit spot softening or adjust laycans."
        elif score >= 0.45:
            explanation = "Moderate flexibility: Balanced bilateral commitments with reserved operational optionality."
        else:
            explanation = "Low flexibility: Substantial forward commitment; stringent contractual nomination and performance clauses."

        return FlexibilityEvaluation(
            flexibility_score=score,
            duration_factor=round(duration_factor, 3),
            volume_commitment_factor=round(volume_factor, 3),
            market_volatility_factor=round(vol_scaling, 3),
            cancellation_optionality_score=round(cancellation_score, 3),
            explanation=explanation
        )
