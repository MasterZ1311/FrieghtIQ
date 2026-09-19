from typing import Dict, Any, Optional

class WaitingCostModel:
    """
    Evaluates the economic downside risks and frictional penalties of postponing a fixture.
    Considers forecast uncertainty spread, adverse rate jump exposure, and deadline proximity.
    Architected to support future additions of vessel availability, port congestion, and repositioning risk.
    """
    @staticmethod
    def calculate_waiting_risk_penalty(
        p10: float,
        p50: float,
        p90: float,
        current_rate: float,
        quantity_mt: float,
        remaining_days: int,
        decision_horizon_days: int
    ) -> Dict[str, Any]:
        """
        Computes the waiting risk adjustment (in USD and USD/MT) to temper raw expected savings.
        """
        # 1. Forecast Uncertainty Spread (Relative Dispersion)
        p50_safe = max(p50, 1.0)
        uncertainty_spread = max(0.0, (p90 - p10) / p50_safe)

        # 2. Adverse Spike Exposure: Potential loss if rate jumps to upper P90 bound
        adverse_rate_jump = max(0.0, p90 - current_rate)
        adverse_cost_exposure = adverse_rate_jump * quantity_mt

        # 3. Deadline Proximity and Urgency Factor
        horizon_safe = max(decision_horizon_days, 1)
        time_elapsed_ratio = max(0.0, min(1.0, 1.0 - (remaining_days / horizon_safe)))
        
        if remaining_days <= 1:
            urgency_multiplier = 3.0 # Critical deadline proximity
        elif remaining_days <= 3:
            urgency_multiplier = 2.0 # High urgency
        elif remaining_days <= 7:
            urgency_multiplier = 1.3 # Moderate urgency
        else:
            urgency_multiplier = 1.0 # Standard decision window

        # 4. Synthesized Risk Penalty ($/MT)
        # Moderate base risk penalty proportional to dispersion and urgency
        risk_penalty_pmt = round(
            float(current_rate * 0.025 * uncertainty_spread * urgency_multiplier),
            2
        )
        total_risk_penalty_usd = round(float(risk_penalty_pmt * quantity_mt), 2)

        return {
            "total_risk_penalty_usd": total_risk_penalty_usd,
            "risk_penalty_pmt": risk_penalty_pmt,
            "uncertainty_spread": round(uncertainty_spread, 3),
            "adverse_cost_exposure_usd": round(adverse_cost_exposure, 2),
            "urgency_multiplier": urgency_multiplier,
            "remaining_days": remaining_days,
            "future_extensions": {
                "vessel_availability_risk": "UNAVAILABLE_PHASE7",
                "port_congestion_risk": "UNAVAILABLE_PHASE7",
                "repositioning_risk": "UNAVAILABLE_PHASE7"
            }
        }
