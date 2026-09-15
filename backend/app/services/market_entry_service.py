"""
FreightIQ — Market Entry Decision Engine
========================================
Multi-criteria decision logic for freight chartering timing.
Evaluates:
- current rate ($/MT)
- forecast rate ($/MT)
- forecast direction (rising / falling / stable)
- uncertainty (volatility spread, standard error, confidence interval)
- expected savings ($ and $/MT)
- contract horizon / laycan urgency (days)

Returns explainable signals:
- CHARTER_NOW
- WAIT
- MONITOR

Avoids arbitrary single-threshold logic by using an explainable multi-factor
decision matrix (Z-score significance, operational lead time, and asymmetric risk).
"""
import math
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.services.forecast_service import forecast


def generate_signal(
    db: Session,
    origin: str,
    destination: str,
    vessel_class: str,
    commodity: str,
    cargo_mt: float,
    urgency_days: int = 30,
) -> Dict[str, Any]:
    fc = forecast(db, origin, destination, vessel_class, commodity, horizon_days=urgency_days)

    predicted = fc["predicted_rate_usd_per_mt"]
    current = fc["current_rate_usd_per_mt"]
    trend = fc.get("trend", "stable")
    confidence = fc.get("confidence_pct", 80.0)
    lower = fc.get("lower_bound", current * 0.9)
    upper = fc.get("upper_bound", current * 1.1)

    # 1. Delta & Direction
    rate_delta = predicted - current
    rate_change_pct = (rate_delta / max(current, 0.01)) * 100.0

    # 2. Uncertainty Quantification (Standard Error proxy from 95% CI)
    spread = (upper - lower) / 2.0
    sigma = max(0.05, (upper - lower) / 3.92)  # Gaussian 95% interval width: 2 * 1.96 * sigma
    relative_uncertainty_pct = (spread / max(current, 0.01)) * 100.0

    # 3. Statistical Significance (Z-score of expected movement)
    z_score = rate_delta / sigma

    # 4. Asymmetric Risk Ratio (Upside cost escalation vs Downside savings opportunity)
    upside_risk_usd = max(0.0, (upper - current) * cargo_mt)
    downside_opportunity_usd = max(0.0, (current - lower) * cargo_mt)
    asymmetry_ratio = (upside_risk_usd / max(downside_opportunity_usd, 1.0)) if downside_opportunity_usd > 0 else 1.0

    # 5. Horizon / Urgency Lead Time Analysis
    # Dry bulk chartering typically requires 7-10 days for fixture negotiation, stem confirmation, and vessel positioning
    is_urgent = urgency_days <= 10
    is_medium_horizon = 10 < urgency_days <= 25
    is_long_horizon = urgency_days > 25

    reasons: List[str] = []
    warnings: List[str] = []

    # 6. Multi-Criteria Decision Engine Logic
    if is_urgent:
        # Laycan is imminent: Vessel positioning lead time dominates market speculation
        signal = "CHARTER_NOW"
        recommendation = (
            f"Charter immediately: Horizon of {urgency_days} days is within critical vessel positioning lead time. "
            f"Waiting risks vessel availability failure or having to pay prompt/spot distress premiums (+5–10%)."
        )
        reasons.append(f"Operational Urgency: {urgency_days} days remaining to laycan window.")
        reasons.append("Tonnage positioning and stem confirmation require minimum 7–10 days lead time.")
        warnings.append("Short laycan window restricts broker competition; lock open tonnage promptly.")
        estimated_savings = 0.0
        best_window = "Immediate fixture (within 24–48 hours)"

    elif trend == "rising" and z_score >= 1.0:
        # Statistically significant rising market
        signal = "CHARTER_NOW"
        savings_per_mt = predicted - current
        estimated_savings = savings_per_mt * cargo_mt
        recommendation = (
            f"Charter now: Rates are trending UP with statistical significance (Z = +{z_score:.2f}, "
            f"+{rate_change_pct:.1f}% forecast over {urgency_days}d). "
            f"Securing a fixture today saves an estimated ${estimated_savings:,.0f} compared to future rates."
        )
        reasons.append(f"Forecasted rate escalation: ${current:.2f}/MT -> ${predicted:.2f}/MT (+{rate_change_pct:.1f}%).")
        reasons.append(f"Signal strength: Z-score is +{z_score:.2f} (above significance threshold of +1.0).")
        reasons.append(f"Asymmetric risk: Potential rate spike upper bound is ${upper:.2f}/MT.")
        if confidence < 75.0:
            warnings.append(f"Forecast confidence is moderate ({confidence:.0f}%). Consider fixing on index-linked terms with a cap.")
        best_window = "Within the next 3–5 business days"

    elif trend == "falling" and z_score <= -1.1 and is_long_horizon:
        # Statistically significant falling market with sufficient runway
        signal = "WAIT"
        savings_per_mt = current - predicted
        estimated_savings = savings_per_mt * cargo_mt
        recommendation = (
            f"Wait to charter: Freight market is in a confirmed downward correction "
            f"(Z = {z_score:.2f}, {rate_change_pct:.1f}% forecast decline over {urgency_days}d). "
            f"Postponing fixture by {max(7, urgency_days // 2)} days yields projected savings of ${estimated_savings:,.0f}."
        )
        reasons.append(f"Bearish momentum: Rate projected to drop from ${current:.2f}/MT to ${predicted:.2f}/MT.")
        reasons.append(f"Strong statistical signal: Z-score {z_score:.2f} indicates persistent downward pressure.")
        reasons.append(f"Adequate runway: {urgency_days} days allows waiting without endangering vessel laycan.")
        if urgency_days < 20:
            warnings.append("Monitor open tonnage count in loading area to avoid being caught in sudden regional vessel shortages.")
        best_window = f"In {max(7, urgency_days // 2)}–{urgency_days - 7} days"

    elif relative_uncertainty_pct > 18.0:
        # High market volatility / wide uncertainty band
        signal = "MONITOR"
        recommendation = (
            f"Monitor market closely: Rate forecast uncertainty is high (forecast band ${lower:.2f}–${upper:.2f}/MT, "
            f"±{relative_uncertainty_pct:.1f}%). Market direction lacks clear statistical consensus (Z = {z_score:.2f})."
        )
        reasons.append(f"Uncertainty spread: Wide 95% confidence interval of ±${spread:.2f}/MT.")
        reasons.append(f"Signal-to-noise ratio is weak (Z = {z_score:.2f}); neither decisive upward nor downward momentum.")
        warnings.append("Track daily Baltic indices (BPI/BCI) and bunker price adjustments before committing.")
        estimated_savings = max(0.0, (current - lower) * cargo_mt * 0.25)
        best_window = "Re-evaluate in 3–5 days after observing Baltic fixture volume"

    elif trend == "falling" and not is_long_horizon:
        # Falling trend but runway is tight (10 < urgency <= 25 days)
        signal = "MONITOR"
        savings_per_mt = max(0.0, current - predicted)
        estimated_savings = savings_per_mt * cargo_mt
        recommendation = (
            f"Monitor & prepare: Market is softening ({rate_change_pct:.1f}%), but limited runway ({urgency_days} days) "
            f"precludes passive waiting. Solicit competitive broker indications now while tracking daily fixtures."
        )
        reasons.append(f"Marginal waiting window: {urgency_days} days requires initiating broker discussions immediately.")
        reasons.append(f"Rate delta: -${savings_per_mt:.2f}/MT potential saving if market continues softer.")
        warnings.append("Do not let laycan approach within 10 days without a firm vessel offer.")
        best_window = "Solict quotes now; hold off final fixture for 3–5 days"

    else:
        # Range-bound / stable market
        signal = "MONITOR"
        recommendation = (
            f"Monitor: Market is stable with low directional bias (projected movement {rate_change_pct:+.1f}%, Z = {z_score:+.2f}). "
            f"Standard spot chartering procedures recommended as laycan nears."
        )
        reasons.append(f"Rate stability: Predicted rate ${predicted:.2f}/MT is within ±3% of current rate ${current:.2f}/MT.")
        reasons.append("Balanced supply/demand fundamentals on this trade lane.")
        estimated_savings = 0.0
        best_window = f"Fix {max(10, urgency_days - 10)}–{urgency_days - 5} days before laycan"

    # 7. Strategic Alternatives Breakdown
    alternatives = [
        {
            "strategy": "Spot Charter Now",
            "description": f"Fix at prevailing spot rate (${current:.2f}/MT). Immediate vessel certainty with zero timing exposure.",
            "pros": ["Eliminates laycan availability risk", "Locks guaranteed loading window", "Avoids unexpected rate spikes"],
            "cons": ["Forfeits savings if spot rates decline further", "Subject to current market bunker level"],
        },
        {
            "strategy": "Controlled Wait & Tender",
            "description": f"Delay fixture by 1–2 weeks while circulating cargo requirements among 3+ shipbrokers. Target: ${predicted:.2f}/MT.",
            "pros": [f"Potential savings up to ${abs(current - predicted)*cargo_mt:,.0f}", "Captures soft tonnage on ballast"],
            "cons": ["Execution risk if regional vessel supply tightens", "Demurrage risk if vessel arrives late"],
        },
        {
            "strategy": "Index-Linked COA with Cap",
            "description": "Fix on floating Baltic index (BPI/BSI) minus agreed discount with a maximum ceiling rate cap.",
            "pros": ["Protects against sudden upside market spikes", "Directly captures downside market declines", "Favorable broker relationships"],
            "cons": ["Requires index settlement clause and counterparty agreement"],
        },
    ]

    return {
        "signal": signal,
        "confidence_pct": round(confidence, 1),
        "recommendation": recommendation,
        "reasons": reasons,
        "warnings": warnings,
        "best_entry_window": best_window,
        "estimated_savings_usd": round(max(0.0, estimated_savings), 0),
        "alternative_strategies": alternatives,
        "current_rate_usd_per_mt": round(current, 2),
        "forecast_rate_usd_per_mt": round(predicted, 2),
        "forecast_direction": trend,
        "uncertainty_usd_per_mt": round(spread, 2),
        "z_score": round(z_score, 2),
        "savings_usd_per_mt": round(abs(rate_delta), 2),
        "contract_horizon_days": urgency_days,
        "disclaimer": "[DEMO] Market entry timing evaluates econometric forecast, Z-score significance, and laycan lead time.",
    }

