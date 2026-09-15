"""
FreightIQ Single End-to-End Decision Workflow Service
====================================================
Integrates all core modules into a single synchronized decision flow:
Cargo Input
-> Forecast
-> Vessel Feasibility
-> Vessel Ranking
-> Economics
-> Contract Comparison
-> Risk
-> Final Recommendation
"""
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.ml.features import get_distance
from app.services.forecast_service import forecast
from app.services.vessel_service import recommend_vessels
from app.services.port_service import check_compatibility
from app.services.economics_service import calculate_economics
from app.services.market_entry_service import generate_signal
from app.services.risk_service import score_risk
from app.services.contract_service import compare_contracts

VESSEL_CLASSES = ["Handysize", "Supramax", "Panamax", "Capesize"]

logger = logging.getLogger(__name__)



def run_end_to_end_flow(
    db: Session,
    origin: str = "Australia",
    destination: str = "Paradip",
    commodity: str = "Coal",
    cargo_mt: float = 70000.0,
    vessel_class: str = None,
    urgency_days: int = 30,
    annual_volume_mt: float = 500000.0,
    planning_horizon_months: int = 12,
    bunker_price_usd_per_mt: float = 650.0,
) -> dict:
    """
    Executes the complete 8-stage FreightIQ Decision Pipeline.
    """
    # 1. Cargo Input & Geometry
    # Support general 'bulk cargo' by mapping to default dry bulk commodity (Coal)
    comm_normalized = commodity
    if commodity.lower() in ["bulk cargo", "dry bulk", "bulk"]:
        comm_normalized = "Coal"

    distance = get_distance(origin, destination)

    # 2. Vessel Recommendation & Feasibility across all 4 classes
    vessel_rec_result = recommend_vessels(
        db=db,
        origin=origin,
        destination=destination,
        commodity=comm_normalized,
        cargo_mt=cargo_mt,
    )

    all_options = vessel_rec_result.get("alternatives", [])
    recommended_class = vessel_rec_result.get("recommended_class", "Panamax")

    # If caller specifically asked to focus on a particular vessel class:
    target_class = vessel_class if vessel_class in VESSEL_CLASSES else recommended_class

    # Port compatibility check for all classes
    all_ports_comp: Dict[str, Any] = {}
    for vc in VESSEL_CLASSES:
        comp = check_compatibility(db, destination, vc, cargo_mt, comm_normalized)
        all_ports_comp[vc] = comp

    # Ensure each option in alternatives has enriched feasibility attributes
    for opt in all_options:
        vc = opt["vessel_class"]
        p_comp = all_ports_comp.get(vc, {})
        opt["port_compatible"] = p_comp.get("compatible", True)
        opt["is_feasible"] = p_comp.get("compatible", True)
        opt["feasibility_status"] = "Feasible" if opt["is_feasible"] else "Infeasible"

    target_port_comp = all_ports_comp.get(target_class, all_ports_comp.get(recommended_class, {}))

    # 3. Forecast for the selected vessel class
    fc = forecast(
        db=db,
        origin=origin,
        destination=destination,
        vessel_class=target_class,
        commodity=comm_normalized,
        horizon_days=urgency_days,
    )

    # 4. Market Entry Timing Signal
    me = generate_signal(
        db=db,
        origin=origin,
        destination=destination,
        vessel_class=target_class,
        commodity=comm_normalized,
        cargo_mt=cargo_mt,
        urgency_days=urgency_days,
    )

    # 5. Voyage Economics
    econ = calculate_economics(
        db=db,
        origin=origin,
        destination=destination,
        vessel_class=target_class,
        commodity=comm_normalized,
        cargo_mt=cargo_mt,
        freight_rate_usd_per_mt=fc["predicted_rate_usd_per_mt"],
        bunker_price_usd_per_mt=bunker_price_usd_per_mt,
    )

    # 6. Contract Comparison
    contracts = compare_contracts(
        db=db,
        origin=origin,
        destination=destination,
        vessel_class=target_class,
        commodity=comm_normalized,
        cargo_mt=cargo_mt,
        annual_volume_mt=annual_volume_mt,
        planning_horizon_months=planning_horizon_months,
    )

    # 7. Risk Engine Scoring
    risk_out = score_risk(
        db=db,
        origin=origin,
        destination=destination,
        vessel_class=target_class,
        commodity=comm_normalized,
        cargo_mt=cargo_mt,
        contract_type="Spot",
    )

    # 8. Synthesis & Executive Recommendation
    # Find rank & fit score of target vessel
    fit_score = 85.0
    for opt in all_options:
        if opt["vessel_class"] == target_class:
            fit_score = opt.get("fit_score", 85.0)
            break

    port_status_str = "Compatible" if target_port_comp.get("compatible", True) else "Restricted"
    rate_val = fc.get("predicted_rate_usd_per_mt", 12.0)
    total_cost = econ.get("total_cost_usd", 500000.0)
    tce_val = econ.get("tce_usd_per_day", 15000.0)
    margin_val = econ.get("margin_pct", 15.0)
    breakeven_val = econ.get("breakeven_rate_usd_per_mt", 8.0)

    # Action items based on timing and port conditions
    actions: List[str] = []
    if me["signal"] in ["WAIT"]:
        actions.append(f"Hold spot fixtures for 7-14 days: Rates projected to decline ({fc['trend'].upper()}) with est. savings of ${me['estimated_savings_usd']:,.0f}.")
    elif me["signal"] in ["BUY_NOW", "CHARTER_NOW"]:
        actions.append(f"Fix prompt tonnage immediately: Bullish rate pressure detected ({fc['trend'].upper()}).")
    else:
        actions.append(f"Monitor tonnage availability: {me['recommendation']}")

    actions.append(f"Vessel Selection: Deploy {target_class} ({cargo_mt:,.0f} MT) — Fit score {fit_score}/100.")
    if not target_port_comp.get("compatible", True):
        actions.append(f"WARNING: Port restriction detected at {destination} for {target_class}. Consider lightering or alternative berth.")
    else:
        actions.append(f"Port Clearance: {destination} berth clearance confirmed. Projected turnaround: {target_port_comp.get('turnaround_days', 5.0)} days.")

    actions.append(f"Contract Strategy: Recommended {contracts.get('recommended_contract', 'Spot')} for {planning_horizon_months}-month horizon.")
    actions.append(f"Operational Protection: Total congestion exposure ${risk_out.get('overall_risk_score', 50):.0f} risk rating. Implement slow-steaming buffer if arrival delays exceed 3 days.")

    # High-level narrative explanation
    infeasible_vessels = [v["vessel_class"] for v in all_options if not v.get("port_compatible", True)]
    infeasible_str = f" Meanwhile, {', '.join(infeasible_vessels)} is restricted at {destination} due to physical draft/LOA constraints." if infeasible_vessels else ""

    explanation = (
        f"For the {origin} → {destination} route handling {cargo_mt:,.0f} MT of {commodity}, {target_class} "
        f"emerges as the optimal vessel selection with an overall fit score of {fit_score}/100. "
        f"{explanation_port_detail(target_class, destination, target_port_comp)}{infeasible_str} "
        f"The predictive freight engine projects rates at ${rate_val:.2f}/MT with a {fc['trend'].upper()} trend ({fc['confidence_pct']}% confidence). "
        f"Based on rate momentum and a {urgency_days}-day horizon, the platform issues a '{me['signal']}' timing signal ({me['best_entry_window']}). "
        f"Voyage economics indicate an estimated total voyage cost of ${total_cost:,.0f} yielding a TCE of ${tce_val:,.0f}/day "
        f"({margin_val:.1f}% operating margin, breakeven at ${breakeven_val:.2f}/MT). "
        f"For procurement strategy, {contracts.get('recommended_contract', 'Spot')} contracts deliver optimal risk-adjusted savings. "
        f"Overall voyage risk is scored at {risk_out.get('overall_risk_score', 45):.1f}/100 ({risk_out.get('overall_risk_level', 'Medium')})."
    )

    final_summary = {
        "recommended_vessel": target_class,
        "optimal_timing_signal": me["signal"],
        "recommended_contract": contracts.get("recommended_contract", "Spot"),
        "port_status": port_status_str,
        "overall_risk_level": str(risk_out.get("overall_risk_level", "Medium")),
        "overall_fit_score": round(fit_score, 1),
        "estimated_freight_usd_per_mt": round(rate_val, 2),
        "total_voyage_cost_usd": round(total_cost, 0),
        "tce_usd_per_day": round(tce_val, 0),
        "breakeven_rate_usd_per_mt": round(breakeven_val, 2),
        "margin_pct": round(margin_val, 1),
        "action_items": actions,
    }

    return {
        "origin": origin,
        "destination": destination,
        "commodity": commodity,
        "cargo_mt": cargo_mt,
        "distance_nm": round(distance, 1),
        "forecast": fc,
        "vessel_feasibility": all_options,
        "recommended_vessel": target_class,
        "port_compatibility": target_port_comp,
        "all_ports_compatibility": all_ports_comp,
        "market_entry": me,
        "economics": econ,
        "contracts": contracts,
        "risk": risk_out,
        "final_recommendation": final_summary,
        "explanation": explanation,
        "disclaimer": "[DEMO] All calculations use synthetic dry bulk models for SIH hackathon demonstration.",
    }


def explanation_port_detail(vessel_class: str, port: str, comp: dict) -> str:
    if comp.get("compatible", True):
        return f"{vessel_class} is fully compatible with {port} navigational limits, with draft and LOA within certified safety tolerances."
    else:
        fails = [c["detail"] for c in comp.get("constraints", []) if c.get("status") == "FAIL"]
        fail_str = "; ".join(fails) if fails else "draft or dimension limits"
        return f"{vessel_class} faces physical clearance restrictions at {port} ({fail_str})."
