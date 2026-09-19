from typing import Dict, Any, Optional
from pydantic import BaseModel

class MarketExposureEvaluation(BaseModel):
    exposure_score: float # 0.0 to 1.0
    uncommitted_volume_pct: float # 0.0% to 100.0%
    volatility_multiplier: float
    regime_risk_multiplier: float
    at_risk_freight_usd: float
    explanation: str

class MarketExposureModel:
    """
    Evaluates exposure to future spot freight market volatility.
    Methodology:
    Market Exposure = (Spot Quantity / Total Quantity) * Volatility Multiplier * Regime Risk Multiplier
    Exposes transparent quantitative components without arbitrary opaque scores.
    """

    @staticmethod
    def evaluate(
        spot_quantity_mt: float,
        total_quantity_mt: float,
        expected_spot_rate: float,
        volatility_annualized: float = 0.28,
        regime_type: str = "NEUTRAL",
        bull_transition_prob: float = 0.20
    ) -> MarketExposureEvaluation:
        if total_quantity_mt <= 0:
            raise ValueError("Total quantity must be strictly positive.")

        uncommitted_share = max(0.0, min(1.0, spot_quantity_mt / total_quantity_mt))

        # Volatility multiplier: benchmarked against 25% annualized volatility
        vol_multiplier = round(min(1.50, max(0.60, volatility_annualized / 0.25)), 3)

        # Regime risk multiplier: higher if market is Bull or transition into Bull is high
        if regime_type == "BULL":
            regime_mult = 1.25
        elif regime_type == "BEAR":
            regime_mult = 0.85
        else: # NEUTRAL / SEASONAL
            regime_mult = 1.0 + (bull_transition_prob * 0.40)
        regime_mult = round(regime_mult, 3)

        # Raw exposure
        raw_exposure = uncommitted_share * vol_multiplier * (regime_mult / 1.0)
        exposure_score = round(max(0.05, min(1.0, raw_exposure)), 3)

        at_risk_freight = round(spot_quantity_mt * expected_spot_rate, 2)

        if exposure_score >= 0.70:
            exp_text = "High market exposure: Open spot volume subject to full freight curve appreciation and spike risk."
        elif exposure_score >= 0.35:
            exp_text = "Moderate market exposure: Balanced hedging with partial containment of freight curve volatility."
        else:
            exp_text = "Low market exposure: Procurement cost locked via multi-voyage contract coverage."

        return MarketExposureEvaluation(
            exposure_score=exposure_score,
            uncommitted_volume_pct=round(uncommitted_share * 100, 1),
            volatility_multiplier=vol_multiplier,
            regime_risk_multiplier=regime_mult,
            at_risk_freight_usd=at_risk_freight,
            explanation=exp_text
        )
