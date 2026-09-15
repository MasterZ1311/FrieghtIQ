"""
Multi-Factor Deterministic Risk Engine Domain Rules
===================================================
Evaluates 6 core deterministic risk components:
1. freight_volatility (Market)
2. port_congestion (Operational)
3. vessel_availability (Market)
4. fuel_bunker_exposure (Cost)
5. schedule_risk (Operational)
6. contract_exposure (Commercial)

Calculates overall risk score via transparent, mathematically weighted formula.
100% deterministic — zero random or pseudo-random calls.
"""
from typing import Dict, Any, List, Optional
from datetime import date
from app.domain.models import RiskFactor, RiskAnalysis, Cargo, Vessel, Port
from app.ml.features import get_distance


RISK_WEIGHTS = {
    "freight_volatility": 0.22,
    "port_congestion": 0.20,
    "vessel_availability": 0.16,
    "fuel_bunker_exposure": 0.14,
    "schedule_risk": 0.16,
    "contract_exposure": 0.12,
}

PORT_CONGESTION_SCORES = {
    "low": 20.0,
    "medium": 50.0,
    "high": 80.0,
}

CONTRACT_STRUCTURE_RISK = {
    "spot": 75.0,
    "3-voyage": 50.0,
    "short-term": 45.0,
    "6-voyage": 35.0,
    "medium-term": 25.0,
    "12-voyage": 18.0,
}

VESSEL_CLASS_SUPPLY_TIGHTNESS = {
    "Handysize": 32.0,   # Plentiful coastal and short-sea tonnage
    "Supramax": 38.0,    # High global liquidity and flexible geartrains
    "Panamax": 52.0,     # Moderate supply on main coal/grain corridors
    "Capesize": 68.0,    # Highly concentrated fleet, long repositioning legs
}

VESSEL_DAILY_BURN_MT = {
    "Handysize": 22.0,
    "Supramax": 28.0,
    "Panamax": 34.0,
    "Capesize": 58.0,
}

ORIGIN_CANAL_CROSSINGS = {
    "United States": True,
    "Russia": True,
    "Australia": False,
    "Mozambique": False,
    "Indonesia": False,
}


def score_risk_dimensions(
    cargo: Cargo,
    vessel: Vessel,
    dest_port: Port,
    contract_type: str = "Spot",
    rate_lower_bound: float = 10.0,
    rate_upper_bound: float = 14.0,
    current_predicted_rate: float = 12.0,
    laycan_date: Optional[date] = None,
    bunker_price_usd: float = 650.0,
) -> RiskAnalysis:
    """
    Computes deterministic multi-factor risk scores and returns explainable risk analysis.
    """
    distance_nm = get_distance(cargo.origin, dest_port.name)
    factors: List[RiskFactor] = []

    # 1. Freight Rate Volatility
    spread_pct = ((rate_upper_bound - rate_lower_bound) / max(current_predicted_rate, 1.0)) * 100.0
    vol_score = round(max(10.0, min(95.0, spread_pct * 2.8)), 1)
    factors.append(RiskFactor(
        category="Market",
        name="Freight Volatility",
        level=_classify_level(vol_score),
        score=vol_score,
        description=f"Forward rate spread spans ${rate_lower_bound:.2f}–${rate_upper_bound:.2f}/MT (±{spread_pct / 2.0:.1f}% confidence interval).",
        mitigation="Hedge spot freight exposure with a fixed-rate COA or establish an index collar.",
    ))

    # 2. Port Congestion
    cong_str = (dest_port.congestion_level or "medium").lower()
    base_cong = PORT_CONGESTION_SCORES.get(cong_str, 50.0)
    turnaround_delta = (dest_port.avg_turnaround_days - 4.0) * 3.5
    cong_score = round(max(15.0, min(95.0, base_cong + turnaround_delta)), 1)
    factors.append(RiskFactor(
        category="Operational",
        name="Port Congestion",
        level=_classify_level(cong_score),
        score=cong_score,
        description=f"Destination port {dest_port.name} exhibits {cong_str} congestion (~{dest_port.avg_turnaround_days:.1f} days turnaround).",
        mitigation="Stipulate Virtual Arrival rights, pre-tender NOR, and include demurrage cap protections.",
    ))

    # 3. Vessel Availability
    vc_name = vessel.vessel_type
    base_avail = VESSEL_CLASS_SUPPLY_TIGHTNESS.get(vc_name, 45.0)
    distance_avail_adj = min(15.0, (distance_nm / 10000.0) * 10.0)
    avail_score = round(max(15.0, min(90.0, base_avail + distance_avail_adj)), 1)
    factors.append(RiskFactor(
        category="Market",
        name="Vessel Availability",
        level=_classify_level(avail_score),
        score=avail_score,
        description=f"Supply tightness for {vc_name} on {cargo.origin} trade lane ({distance_nm:,} NM ballast radius).",
        mitigation="Fix vessel 3–4 weeks prior to laycan window to avoid prompt fixture shortages.",
    ))

    # 4. Fuel / Bunker Exposure
    burn_rate = VESSEL_DAILY_BURN_MT.get(vc_name, 32.0)
    burn_component = (burn_rate / 60.0) * 45.0
    dist_component = (distance_nm / 13000.0) * 35.0
    price_component = (bunker_price_usd / 650.0) * 20.0
    fuel_score = round(max(15.0, min(95.0, burn_component + dist_component + price_component - 10.0)), 1)
    factors.append(RiskFactor(
        category="Cost",
        name="Fuel / Bunker Exposure",
        level=_classify_level(fuel_score),
        score=fuel_score,
        description=f"Bunker fuel at ${bunker_price_usd:.0f}/MT represents substantial voyage expense ({burn_rate:.1f} MT/day burn across {distance_nm:,} NM).",
        mitigation="Utilize bunker price hedging or negotiate a Bunker Adjustment Factor (BAF) clause in contract.",
    ))

    # 5. Schedule Risk (Weather / Canal / Tide / Distance)
    eval_month = (laycan_date or date.today()).month
    if eval_month in [6, 7, 8, 9]:
        wx_component = 30.0
        wx_note = f"Southwest Monsoon season (Month {eval_month}) with high sea swells and cyclone risk."
    elif eval_month in [10, 11]:
        wx_component = 20.0
        wx_note = f"Post-monsoon transition period (Month {eval_month})."
    else:
        wx_component = 10.0
        wx_note = "Benign weather window."

    canal_transit = ORIGIN_CANAL_CROSSINGS.get(cargo.origin, False)
    canal_component = 18.0 if canal_transit else 5.0
    tide_component = 15.0 if dest_port.tide_restricted else 0.0
    dist_sched_component = (distance_nm / 13000.0) * 20.0

    sched_score = round(max(15.0, min(95.0, wx_component + canal_component + tide_component + dist_sched_component)), 1)
    factors.append(RiskFactor(
        category="Operational",
        name="Schedule Risk",
        level=_classify_level(sched_score),
        score=sched_score,
        description=f"Transit schedule exposed to: {wx_note} {'Canal delays. ' if canal_transit else ''}{'Tidal berth windows. ' if dest_port.tide_restricted else ''}",
        mitigation="Build a 3–5 day buffer into laycan dates and verify vessel weather routing protocols.",
    ))

    # 6. Contract Exposure
    c_type_key = contract_type.strip().lower()
    c_score = round(CONTRACT_STRUCTURE_RISK.get(c_type_key, 50.0), 1)
    factors.append(RiskFactor(
        category="Commercial",
        name="Contract Exposure",
        level=_classify_level(c_score),
        score=c_score,
        description=f"{contract_type} procurement: {'100% open exposure to spot freight volatility.' if c_score >= 65 else 'Hedging mechanism in place with volume commitment.'}",
        mitigation="Balance spot fixtures with multi-voyage COA commitments to optimize risk-return profile.",
    ))

    # Transparent mathematical component scores
    component_scores = {
        "freight_volatility": vol_score,
        "port_congestion": cong_score,
        "vessel_availability": avail_score,
        "fuel_bunker_exposure": fuel_score,
        "schedule_risk": sched_score,
        "contract_exposure": c_score,
    }

    # Overall weighted score calculation
    overall_score = round(
        RISK_WEIGHTS["freight_volatility"] * vol_score
        + RISK_WEIGHTS["port_congestion"] * cong_score
        + RISK_WEIGHTS["vessel_availability"] * avail_score
        + RISK_WEIGHTS["fuel_bunker_exposure"] * fuel_score
        + RISK_WEIGHTS["schedule_risk"] * sched_score
        + RISK_WEIGHTS["contract_exposure"] * c_score,
        1,
    )
    overall_level = _classify_level(overall_score)

    sorted_factors = sorted(factors, key=lambda f: f.score, reverse=True)
    top_risks = [f.name for f in sorted_factors[:3]]

    recommended_actions = [
        "Obtain competitive quotes from at least 3 accredited shipbrokers before fixing.",
        "Confirm valid P&I Club Class A entry and vessel vetting under port guidelines.",
        "Check 10-day weather routing forecast prior to laycan commencement.",
    ]
    if cong_str == "high":
        recommended_actions.append(f"Negotiate port-call agreement at {dest_port.name} to mitigate demurrage.")
    if canal_transit:
        recommended_actions.append("Book canal transit booking slot early to bypass bottleneck delays.")

    return RiskAnalysis(
        overall_risk_score=overall_score,
        overall_risk_level=overall_level,
        risk_factors=factors,
        top_risks=top_risks,
        recommended_actions=recommended_actions,
        component_scores=component_scores,
    )


def _classify_level(score: float) -> str:
    if score < 30.0:
        return "Low"
    elif score < 55.0:
        return "Medium"
    elif score < 75.0:
        return "High"
    return "Critical"
