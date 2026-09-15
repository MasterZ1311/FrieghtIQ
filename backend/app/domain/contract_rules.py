"""
Contract Comparison & Procurement Domain Rules
==============================================
Pure domain rules for evaluating chartering structures: Spot, 3-Voyage, 6-Voyage,
and 12-Voyage commitments across trade volume horizons and forward rate curves.
"""
import math
from typing import Dict, Any, List
from app.domain.models import Contract


CONTRACT_DISCOUNTS = {
    "Spot": 0.00,        # No discount; full spot volatility
    "3-Voyage": 0.035,   # ~3.5% discount for 3-voyage quarterly commitment
    "6-Voyage": 0.075,   # ~7.5% discount for semi-annual COA commitment
    "12-Voyage": 0.125,  # ~12.5% discount for annual 12-voyage baseload commitment
}

CONTRACT_DURATIONS = {
    "Spot": "Per voyage (Spot single fixture)",
    "3-Voyage": "3 voyages (Quarterly commitment)",
    "6-Voyage": "6 voyages (Semi-annual COA)",
    "12-Voyage": "12 voyages (Annual COA / Period TC)",
}

CONTRACT_EXPOSURE_PCT = {
    "Spot": 100.0,
    "3-Voyage": 75.0,
    "6-Voyage": 50.0,
    "12-Voyage": 0.0,
}

CONTRACT_FLEXIBILITY = {
    "Spot": 95.0,
    "3-Voyage": 70.0,
    "6-Voyage": 50.0,
    "12-Voyage": 25.0,
}


def evaluate_contracts(
    spot_rate_usd_per_mt: float,
    future_rate_usd_per_mt: float,
    cargo_quantity_mt: float,
    annual_volume_mt: float = 500000.0,
    planning_horizon_months: int = 12,
    trend: str = "stable",
) -> Dict[str, Any]:
    """
    Evaluates 4 contract options across volume, discount elasticity, and forward rate trends.
    """
    months = max(1, min(36, planning_horizon_months))
    effective_program_volume = annual_volume_mt * (months / 12.0)
    program_voyages = max(1, math.ceil(effective_program_volume / max(cargo_quantity_mt, 1000.0)))

    # Spot rate calculation
    spot_effective_rate = round(spot_rate_usd_per_mt * 0.40 + future_rate_usd_per_mt * 0.60, 2)
    spot_total_cost = round(spot_effective_rate * effective_program_volume, 0)

    contract_types = ["Spot", "3-Voyage", "6-Voyage", "12-Voyage"]
    options: List[Dict[str, Any]] = []

    for ctype in contract_types:
        disc = CONTRACT_DISCOUNTS[ctype]
        contract_rate = round(spot_rate_usd_per_mt * (1.0 - disc), 2)
        total_cost = round(contract_rate * effective_program_volume, 0)
        savings_usd = max(0.0, spot_total_cost - total_cost) if ctype != "Spot" else 0.0
        savings_pct = round((savings_usd / max(spot_total_cost, 1.0)) * 100.0, 1)

        exposure_pct = CONTRACT_EXPOSURE_PCT[ctype]
        flexibility = CONTRACT_FLEXIBILITY[ctype]

        if ctype == "Spot":
            risk_score = 75.0 if trend != "falling" else 60.0
            voyages_num = program_voyages
            pros = [
                "Zero commitment: Cargo parcel volume and timing can adapt to market demand",
                "Captures lower rates immediately if freight market enters a downturn",
                "No counterparty lock-in or default risk across long contract periods",
            ]
            cons = [
                "Maximum price volatility: Budget is 100% exposed to unexpected freight spikes",
                "No tonnage guarantee: Tonnage availability subject to regional spot supply",
                f"Highest projected baseline cost: ${total_cost:,.0f} (${spot_effective_rate:.2f}/MT)",
            ]
        elif ctype == "3-Voyage":
            risk_score = 55.0
            voyages_num = min(3, program_voyages)
            pros = [
                f"Secures {disc*100:.1f}% discount (${savings_usd:,.0f} total saving vs spot)",
                "Guaranteed vessel capacity across next 3 laycan windows",
                "Low commitment duration: Re-negotiate terms after 1 quarter",
            ]
            cons = [
                "Partial exposure: 75% of annual volume remains subject to spot volatility",
                "Requires committing to 3 parcels with laycan windows",
                "Moderate renegotiation overhead every 90 days",
            ]
        elif ctype == "6-Voyage":
            risk_score = 35.0
            voyages_num = min(6, program_voyages)
            pros = [
                f"Solid {disc*100:.1f}% discount (${savings_usd:,.0f} savings vs spot baseline)",
                "Half of annual volume insulated against freight escalation",
                "Priority vessel allocation during peak congested seasons",
            ]
            cons = [
                "6-month volume commitment with agreed cancellation / laycan windows",
                "Partial penalty if downstream industrial demand decreases by >20%",
                "Some missed opportunity if spot rates experience sharp collapse",
            ]
        else:  # 12-Voyage
            risk_score = 20.0
            voyages_num = min(12, program_voyages)
            pros = [
                f"Maximum rate discount of {disc*100:.1f}% (${savings_usd:,.0f} savings vs spot)",
                "Complete budget predictability: 0% open freight price exposure",
                "Dedicated shipowner partnership with agreed laytime and priority loading",
            ]
            cons = [
                "Rigid schedule: Minimum monthly volume lifting obligation (deadfreight liability)",
                "No benefit from sudden spot rate declines over the 12-month horizon",
                "Counterparty credit risk over 12 consecutive voyages",
            ]

        risk_label = "High" if risk_score >= 65 else ("Medium" if risk_score >= 35 else "Low")

        options.append({
            "contract_type": ctype,
            "duration": CONTRACT_DURATIONS[ctype],
            "rate_usd_per_mt": contract_rate,
            "cost_per_mt": contract_rate,
            "total_cost_usd": total_cost,
            "estimated_cost": total_cost,
            "savings_vs_spot_usd": savings_usd,
            "estimated_savings": savings_usd,
            "savings_vs_spot_pct": savings_pct,
            "exposure_pct": exposure_pct,
            "flexibility_score": flexibility,
            "risk_score": risk_score,
            "risk": risk_label,
            "recommended": False,
            "voyages": voyages_num,
            "voyages_count": voyages_num,
            "pros": pros,
            "cons": cons,
        })

    # Recommendation
    opt_12 = next(o for o in options if o["contract_type"] == "12-Voyage")
    opt_6 = next(o for o in options if o["contract_type"] == "6-Voyage")

    if trend == "rising":
        recommended = "12-Voyage"
        expected_saving = opt_12["savings_vs_spot_usd"]
        reasoning = (
            f"Bullish freight outlook: Forward curve indicates rising rates. "
            f"Locking in a 12-Voyage COA at ${opt_12['cost_per_mt']:.2f}/MT delivers "
            f"maximum cost insulation and saves ${expected_saving:,.0f} ({opt_12['savings_vs_spot_pct']:.1f}%) vs spot."
        )
        blended = "Optimal Blended Allocation: 70% 12-Voyage COA (baseload) + 30% Spot (operational buffer)."
    elif trend == "falling":
        recommended = "Spot"
        expected_saving = 0.0
        reasoning = (
            f"Bearish freight outlook: Spot rates are projected to soften. "
            f"Retaining Spot procurement captures forward rate declines without locking into fixed commitments. "
            f"Consider 3-Voyage COA only if cargo supply security is critical."
        )
        blended = "Optimal Blended Allocation: 75% Spot (riding market decline) + 25% 3-Voyage COA (supply guarantee)."
    else:
        recommended = "6-Voyage"
        expected_saving = opt_6["savings_vs_spot_usd"]
        reasoning = (
            f"Balanced freight market: A 6-Voyage COA strikes the optimal Pareto trade-off, "
            f"securing a {opt_6['savings_vs_spot_pct']:.1f}% discount (${expected_saving:,.0f} saving) "
            f"while maintaining flexibility for the second half of the year."
        )
        blended = "Optimal Blended Allocation: 50% 6-Voyage COA + 30% 3-Voyage + 20% Spot buffer."

    for opt in options:
        opt["recommended"] = (opt["contract_type"] == recommended)

    return {
        "contracts": options,
        "options": options,
        "recommended_contract": recommended,
        "blended_strategy": blended,
        "expected_saving_vs_spot": round(expected_saving, 0),
        "reasoning": reasoning,
        "disclaimer": "[DEMO] Contract optimization evaluates volume discount elasticity, forward curve, and open exposure.",
    }
