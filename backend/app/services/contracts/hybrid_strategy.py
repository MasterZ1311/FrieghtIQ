from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class CoverageTierResult(BaseModel):
    coverage_percentage: float # 0.0, 25.0, 50.0, 75.0, 100.0
    contracted_quantity_mt: float
    spot_quantity_mt: float
    blended_expected_rate: float
    expected_cost: float
    p10_cost: float
    p90_cost: float
    cost_range_usd: float
    market_exposure: float # 0.0 - 1.0
    flexibility_measure: float # 0.0 - 1.0
    risk_adjusted_cost: float
    summary_label: str

class HybridContractStrategy:
    """
    Evaluates hybrid contract portfolio coverage spectrum:
    0% (pure spot), 25%, 50%, 75%, 100% (fully contracted).
    Guarantees: contracted_quantity + spot_quantity == total_requirement
    """

    @staticmethod
    def evaluate_coverage(
        total_requirement_mt: float,
        coverage_percentage: float, # e.g. 75.0
        contract_rate: float,
        spot_expected_rate: float,
        spot_p10_rate: float,
        spot_p90_rate: float,
        volatility_annualized: float = 0.28,
        planning_horizon_days: int = 180
    ) -> CoverageTierResult:
        if total_requirement_mt <= 0:
            raise ValueError("Total cargo requirement must be positive.")
        if coverage_percentage < 0.0 or coverage_percentage > 100.0:
            raise ValueError("Coverage percentage must be between 0 and 100.")

        cov_frac = coverage_percentage / 100.0
        contracted_mt = round(total_requirement_mt * cov_frac, 2)
        spot_mt = round(total_requirement_mt - contracted_mt, 2)

        # Expected freight cost
        contract_exp_cost = contracted_mt * contract_rate
        spot_exp_cost = spot_mt * spot_expected_rate
        expected_total_cost = round(contract_exp_cost + spot_exp_cost, 2)

        # Cost range: contracted is fixed, spot varies with P10/P90
        p10_total_cost = round(contract_exp_cost + (spot_mt * spot_p10_rate), 2)
        p90_total_cost = round(contract_exp_cost + (spot_mt * spot_p90_rate), 2)
        cost_range = round(p90_total_cost - p10_total_cost, 2)

        blended_rate = round(expected_total_cost / total_requirement_mt, 2)

        # Market exposure: proportion exposed to spot rate variance
        # When 100% contracted, exposure is near zero (0.05 residual counterparty/operational risk).
        # When 0% contracted (100% spot), exposure is 1.0 * volatility scaling.
        market_exp = round((1.0 - cov_frac) * min(1.0, volatility_annualized / 0.25), 3)
        market_exp = max(0.05, min(1.0, market_exp)) if cov_frac < 1.0 else 0.05

        # Flexibility measure: proportion uncommitted allowing operational/route changes
        # Pure spot = 0.95 flexibility. Fully committed COA = 0.20 flexibility.
        flexibility = round(0.20 + (1.0 - cov_frac) * 0.75, 3)

        # Risk-adjusted cost: expected cost + adverse spot variance penalty + commitment penalty
        # Adverse variance penalty on spot MT: 0.5 * (p90 - p50) * spot_mt
        adverse_spot_penalty = 0.5 * max(0.0, spot_p90_rate - spot_expected_rate) * spot_mt
        # Commitment penalty on contracted MT: commitment to fixed tonnage in changing demand
        commitment_penalty = 0.02 * contract_exp_cost * (planning_horizon_days / 180.0)
        risk_adjusted_cost = round(expected_total_cost + adverse_spot_penalty + commitment_penalty, 2)

        summary_label = f"{coverage_percentage:.0f}% Contracted / {100 - coverage_percentage:.0f}% Spot"

        return CoverageTierResult(
            coverage_percentage=coverage_percentage,
            contracted_quantity_mt=contracted_mt,
            spot_quantity_mt=spot_mt,
            blended_expected_rate=blended_rate,
            expected_cost=expected_total_cost,
            p10_cost=p10_total_cost,
            p90_cost=p90_total_cost,
            cost_range_usd=cost_range,
            market_exposure=market_exp,
            flexibility_measure=flexibility,
            risk_adjusted_cost=risk_adjusted_cost,
            summary_label=summary_label
        )

    @classmethod
    def generate_standard_tiers(
        cls,
        total_requirement_mt: float,
        contract_rate: float,
        spot_expected_rate: float,
        spot_p10_rate: float,
        spot_p90_rate: float,
        volatility_annualized: float = 0.28,
        planning_horizon_days: int = 180
    ) -> List[CoverageTierResult]:
        tiers = [0.0, 25.0, 50.0, 75.0, 100.0]
        return [
            cls.evaluate_coverage(
                total_requirement_mt=total_requirement_mt,
                coverage_percentage=t,
                contract_rate=contract_rate,
                spot_expected_rate=spot_expected_rate,
                spot_p10_rate=spot_p10_rate,
                spot_p90_rate=spot_p90_rate,
                volatility_annualized=volatility_annualized,
                planning_horizon_days=planning_horizon_days
            )
            for t in tiers
        ]
