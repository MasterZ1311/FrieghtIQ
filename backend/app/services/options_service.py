"""
Black-Scholes-Merton Options Pricing applied to freight chartering decisions.
=============================================================================
Models the "Wait vs. Fix Now" chartering decision as a real put option:

  - Underlying (S) : current freight rate ($/MT)
  - Strike (K)     : target / budget rate the charterer wants to lock in
  - Waiting = holding the option open
  - Fixing now     = exercising the option at S
  - σ              : historical freight rate volatility (annualised)
  - r              : risk-free rate (RBI repo rate ≈ 6.5%)
  - T              : time to cargo need (years)

A put option value > threshold ⟹ WAIT (rates likely to fall toward K).
A put option value ≤ threshold ⟹ FIX_NOW (locking in S is optimal).
"""

import math
import logging
from scipy.stats import norm

logger = logging.getLogger(__name__)

# Annualised freight rate volatility by route cluster (from historical BDI analysis)
ROUTE_VOLATILITY: dict[str, float] = {
    "australia_india":   0.38,
    "usa_india":         0.42,
    "indonesia_india":   0.33,
    "mozambique_india":  0.40,
    "russia_india":      0.45,
    "default":           0.40,
}

# If option value exceeds this fraction of fix-now cost, recommend WAIT
WAIT_THRESHOLD_FRACTION = 0.018   # 1.8% of total fix-now voyage cost


def _resolve_volatility(route: str) -> float:
    route_lower = route.lower().replace(" ", "_").replace("-", "_")
    for key, vol in ROUTE_VOLATILITY.items():
        if key.split("_")[0] in route_lower:
            return vol
    return ROUTE_VOLATILITY["default"]


def calculate_wait_or_fix(
    current_rate: float,
    target_rate: float,
    days_until_needed: int,
    cargo_mt: float,
    route: str = "default",
    risk_free_rate: float = 0.065,
) -> dict:
    """
    Calculate the Black-Scholes put option value for the freight timing decision.

    Args:
        current_rate      : Current spot freight rate ($/MT).
        target_rate       : Charterer's budget/target rate ($/MT). Should be ≤ current_rate
                            for a put option to have value (i.e. waiting for rates to fall).
        days_until_needed : Days until the vessel is required.
        cargo_mt          : Cargo size in metric tonnes.
        route             : Route identifier string (used to look up historical σ).
        risk_free_rate    : Annual risk-free rate (default 6.5% RBI repo rate).

    Returns:
        dict with decision, option value, probability, saving estimates, and reasoning.
    """
    sigma = _resolve_volatility(route)
    T = max(days_until_needed, 1) / 365.0
    S, K, r = float(current_rate), float(target_rate), float(risk_free_rate)

    # ── Black-Scholes-Merton put formula ──
    try:
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        # Put value per MT (right to sell at K, i.e. wait for rate to reach K)
        put_value_per_mt = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        put_value_total = max(0.0, put_value_per_mt * cargo_mt)

        delta = float(norm.cdf(d1))                    # Sensitivity to rate move
        prob_below_target = float(norm.cdf(-d2))       # P(rate ≤ K at expiry)
        prob_rises_10pct  = float(1 - norm.cdf(         # P(rate rises ≥ 10%)
            (math.log(S * 1.10 / S) - (r - 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        ))

    except (ValueError, ZeroDivisionError) as exc:
        logger.warning("BSM calculation error: %s — using simple heuristic", exc)
        put_value_total = 0.0
        delta = 0.5
        prob_below_target = 0.5
        prob_rises_10pct = 0.2

    fix_now_cost = S * cargo_mt
    threshold = fix_now_cost * WAIT_THRESHOLD_FRACTION

    # Decision
    decision = "WAIT" if put_value_total > threshold else "FIX_NOW"

    # Expected saving if WAIT and correct
    expected_saving = put_value_total if decision == "WAIT" else 0.0

    # Downside if WAIT and wrong (rate rises 10%)
    risk_if_wrong = abs(S * 0.10 * cargo_mt)

    # Break-even rate at expiry
    breakeven_rate = K * math.exp(-r * T)

    # Confidence in the decision
    if decision == "WAIT":
        confidence = min(0.95, prob_below_target + 0.25)
    else:
        confidence = min(0.95, (1 - prob_below_target) + 0.25)

    # Build human-readable reasoning
    if decision == "WAIT":
        reasoning = (
            f"Rate σ={sigma * 100:.0f}%/yr. "
            f"Prob rate falls to ${target_rate:.2f}/MT in {days_until_needed}d: "
            f"{prob_below_target * 100:.1f}%. "
            f"Option value: ${put_value_total:,.0f} — WAIT {days_until_needed} days "
            f"to save ~${expected_saving:,.0f}."
        )
    else:
        reasoning = (
            f"Rate σ={sigma * 100:.0f}%/yr. "
            f"Prob rate falls to target: {prob_below_target * 100:.1f}% — too low. "
            f"Option value ${put_value_total:,.0f} below threshold ${threshold:,.0f}. "
            f"FIX NOW at ${current_rate:.2f}/MT to lock in certainty."
        )

    return {
        "current_rate_usd_mt": round(S, 2),
        "target_rate_usd_mt": round(K, 2),
        "cargo_mt": int(cargo_mt),
        "days_until_needed": days_until_needed,
        "route": route,

        # Financial outputs
        "option_value_usd": round(put_value_total, 0),
        "fix_now_total_cost_usd": round(fix_now_cost, 0),
        "expected_saving_usd": round(expected_saving, 0),
        "risk_if_wrong_usd": round(risk_if_wrong, 0),
        "breakeven_rate_usd_mt": round(breakeven_rate, 2),

        # Statistical outputs
        "delta": round(delta, 3),
        "probability_below_target": round(prob_below_target, 3),
        "probability_rises_10pct": round(prob_rises_10pct, 3),
        "annualized_volatility": sigma,

        # Decision
        "decision": decision,
        "days_to_wait": days_until_needed if decision == "WAIT" else 0,
        "confidence": round(confidence, 2),
        "reasoning": reasoning,
    }
