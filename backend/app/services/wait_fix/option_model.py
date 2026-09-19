import math
from typing import Optional, Dict, Any
from scipy.stats import norm
from app.schemas.wait_fix import OptionValueResult

class WaitOptionModel:
    """
    Real-option-inspired flexibility valuation for charter party postponement.
    Evaluates the managerial option value of holding open the fixing decision.
    
    Analytical Framing:
    Does NOT treat physical freight as an exchange-traded equity option.
    Framed strictly as "Real-option-inspired decision-support analysis" to measure
    the economic value of operational timing flexibility under uncertainty.
    """
    @classmethod
    def calculate_wait_option_value(
        cls,
        current_freight_rate: Optional[float],
        reference_fix_rate: Optional[float],
        cargo_quantity_mt: Optional[float],
        remaining_days: Optional[int],
        annualized_volatility: Optional[float] = 0.28,
        discount_rate: float = 0.05
    ) -> OptionValueResult:
        """
        Calculates flexibility option value using Black-76 adapted formulation.
        Returns OptionValueResult with status and full parameter traceability.
        """
        # Input validation
        if (
            current_freight_rate is None or current_freight_rate <= 0 or
            reference_fix_rate is None or reference_fix_rate <= 0 or
            cargo_quantity_mt is None or cargo_quantity_mt <= 0 or
            remaining_days is None or remaining_days <= 0 or
            annualized_volatility is None or annualized_volatility <= 0
        ):
            reason = "Missing or non-positive parameter (requires valid spot rate, fix rate, quantity, positive window, and volatility)."
            if remaining_days is not None and remaining_days <= 0:
                reason = "Decision window has expired (remaining days <= 0). Flexibility option value has decayed to zero."
            
            return OptionValueResult(
                option_value_usd=None,
                option_value_pmt=None,
                methodology="Real-Option Decision-Support (Black-Scholes / Black-76 Framework)",
                parameters={
                    "S_current_rate": current_freight_rate,
                    "K_reference_rate": reference_fix_rate,
                    "T_years": round(remaining_days / 365.25, 4) if remaining_days else None,
                    "sigma_volatility": annualized_volatility,
                    "r_discount_rate": discount_rate
                },
                status="OPTION_VALUE_UNAVAILABLE",
                rationale=reason
            )

        # 1. Map Parameters
        S = float(current_freight_rate) # Spot freight rate ($/MT)
        K = float(reference_fix_rate)   # Reference benchmark fix rate ($/MT)
        T = max(0.001, remaining_days / 365.25) # Decision window in annualized years
        sigma = float(annualized_volatility)    # Annualized freight volatility
        r = float(discount_rate)               # Cost of capital / discount rate

        try:
            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)

            # Option value per MT ($/MT)
            option_pmt = (S * norm.cdf(d1)) - (K * math.exp(-r * T) * norm.cdf(d2))
            option_pmt = max(0.0, round(float(option_pmt), 2))

            # Total Option Flexibility Value across cargo lot (USD)
            total_option_usd = round(float(option_pmt * cargo_quantity_mt), 2)

            return OptionValueResult(
                option_value_usd=total_option_usd,
                option_value_pmt=option_pmt,
                methodology="Real-Option Decision-Support (Black-Scholes / Black-76 Framework)",
                parameters={
                    "S_current_rate": S,
                    "K_reference_rate": K,
                    "T_years": round(T, 4),
                    "sigma_volatility": sigma,
                    "r_discount_rate": r,
                    "d1": round(float(d1), 3),
                    "d2": round(float(d2), 3)
                },
                status="AVAILABLE",
                rationale=f"Flexibility premium estimated at ${option_pmt}/MT (${total_option_usd:,.0f} aggregate lot value) over a {remaining_days}-day decision window."
            )
        except Exception as e:
            return OptionValueResult(
                option_value_usd=None,
                option_value_pmt=None,
                methodology="Real-Option Decision-Support (Black-Scholes / Black-76 Framework)",
                parameters={"error": str(e)},
                status="OPTION_VALUE_UNAVAILABLE",
                rationale=f"Numerical option evaluation failed: {str(e)}"
            )
