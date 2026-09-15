"""
FreightIQ — Idle Scenario Management Service
=============================================
Calculates anchorage waiting costs, laytime & demurrage exposure,
slow-steaming bunker optimization trade-offs, and port diversion economics
for dry bulk cargo arriving at East Coast Indian ports.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models import Port
from app.ml.features import get_distance

DEFAULT_DEMURRAGE = {
    "Handysize": 14000.0,
    "Supramax": 18000.0,
    "Panamax": 24000.0,
    "Capesize": 38000.0,
}

IDLE_AUX_FUEL = {
    "Handysize": 2.2,  # MT/day auxiliary generator
    "Supramax": 2.8,
    "Panamax": 3.5,
    "Capesize": 5.2,
}

VESSEL_HIRE_DAILY = {
    "Handysize": 11000.0,
    "Supramax": 15000.0,
    "Panamax": 18000.0,
    "Capesize": 28000.0,
}

VESSEL_SPEEDS = {
    "Handysize": 13.5,
    "Supramax": 14.0,
    "Panamax": 14.5,
    "Capesize": 14.5,
}

VESSEL_SEA_FUEL = {
    "Handysize": 22.0,
    "Supramax": 28.0,
    "Panamax": 34.0,
    "Capesize": 58.0,
}

PORT_CONGESTION_DAYS = {
    "Paradip": 5.5,
    "Visakhapatnam": 3.0,
    "Gangavaram": 1.5,
    "Gopalpur": 2.5,
    "Dhamra": 1.5,
    "Sagar-Sandheads": 4.0,
    "Haldia": 7.0,
}

EAST_COAST_DIVERSIONS = {
    "Paradip": ["Dhamra", "Gangavaram"],
    "Haldia": ["Dhamra", "Sagar-Sandheads"],
    "Sagar-Sandheads": ["Dhamra", "Paradip"],
    "Visakhapatnam": ["Gangavaram", "Dhamra"],
    "Gopalpur": ["Gangavaram", "Paradip"],
    "Dhamra": ["Paradip", "Gangavaram"],
    "Gangavaram": ["Visakhapatnam", "Dhamra"],
}


def calculate_idle_scenario(
    db: Session,
    origin: str,
    destination: str,
    vessel_class: str,
    commodity: str,
    cargo_mt: float,
    waiting_days: Optional[float] = None,
    demurrage_rate_usd_day: Optional[float] = None,
    bunker_price_usd_per_mt: float = 650.0,
    slow_steaming_knots: float = 11.5,
) -> Dict[str, Any]:
    port = db.query(Port).filter(Port.name == destination).first()
    handling_rate = port.handling_rate_mt_day if port and port.handling_rate_mt_day else 25000.0

    # Determine waiting days
    if waiting_days is None:
        waiting_days = PORT_CONGESTION_DAYS.get(destination, 4.0)

    # Demurrage rate
    if demurrage_rate_usd_day is None:
        demurrage_rate_usd_day = DEFAULT_DEMURRAGE.get(vessel_class, 22000.0)

    # Laytime calculation: allowed discharge time = (cargo / handling_rate) + allowance (1.5 days)
    berth_discharge_days = cargo_mt / max(handling_rate, 5000.0)
    laytime_allowed_days = round(berth_discharge_days + 1.5, 1)
    actual_port_days = round(waiting_days + berth_discharge_days, 1)

    # Waiting costs at anchorage
    aux_fuel = IDLE_AUX_FUEL.get(vessel_class, 3.2)
    daily_hire = VESSEL_HIRE_DAILY.get(vessel_class, 16000.0)

    anchorage_idle_bunker = waiting_days * aux_fuel * bunker_price_usd_per_mt
    anchorage_vessel_cost = waiting_days * daily_hire
    total_waiting_cost = anchorage_idle_bunker + anchorage_vessel_cost

    # Demurrage vs Dispatch
    excess_days = max(0.0, actual_port_days - laytime_allowed_days)
    saved_days = max(0.0, laytime_allowed_days - actual_port_days)

    demurrage_incurred = excess_days * demurrage_rate_usd_day
    dispatch_earned = saved_days * (demurrage_rate_usd_day * 0.5)

    total_congestion_exposure = total_waiting_cost + demurrage_incurred - dispatch_earned

    # Slow Steaming Analysis
    distance = get_distance(origin, destination)
    normal_speed = VESSEL_SPEEDS.get(vessel_class, 14.0)
    normal_fuel_rate = VESSEL_SEA_FUEL.get(vessel_class, 32.0)

    normal_sea_days = distance / (normal_speed * 24.0)
    normal_sea_bunker = normal_sea_days * normal_fuel_rate * bunker_price_usd_per_mt

    slow_speed = min(normal_speed - 0.5, max(8.5, slow_steaming_knots))
    # Cubic law for fuel consumption: F_slow = F_normal * (V_slow / V_normal)^3
    slow_fuel_rate = normal_fuel_rate * ((slow_speed / normal_speed) ** 3)
    slow_sea_days = distance / (slow_speed * 24.0)
    slow_sea_bunker = slow_sea_days * slow_fuel_rate * bunker_price_usd_per_mt

    bunker_savings = max(0.0, normal_sea_bunker - slow_sea_bunker)
    absorbed_waiting_days = min(waiting_days, max(0.0, slow_sea_days - normal_sea_days))
    remaining_waiting_days = max(0.0, waiting_days - absorbed_waiting_days)

    net_economic_benefit = bunker_savings + (absorbed_waiting_days * (demurrage_rate_usd_day * 0.5))

    slow_steaming = {
        "normal_speed_kn": round(normal_speed, 1),
        "normal_sea_days": round(normal_sea_days, 1),
        "normal_sea_bunker_cost_usd": round(normal_sea_bunker, 0),
        "slow_speed_kn": round(slow_speed, 1),
        "slow_sea_days": round(slow_sea_days, 1),
        "slow_sea_bunker_cost_usd": round(slow_sea_bunker, 0),
        "bunker_savings_usd": round(bunker_savings, 0),
        "absorbed_waiting_days": round(absorbed_waiting_days, 1),
        "remaining_waiting_days": round(remaining_waiting_days, 1),
        "net_economic_benefit_usd": round(net_economic_benefit, 0),
    }

    # Diversion Options
    diversion_options: List[Dict[str, Any]] = []
    diversion_candidates = EAST_COAST_DIVERSIONS.get(destination, ["Dhamra", "Visakhapatnam"])

    for cand_name in diversion_candidates:
        cand_port = db.query(Port).filter(Port.name == cand_name).first()
        if not cand_port:
            continue
        cand_dist = get_distance(origin, cand_name)
        dist_delta = cand_dist - distance
        cand_waiting = PORT_CONGESTION_DAYS.get(cand_name, 2.0)
        waiting_saved = max(0.0, waiting_days - cand_waiting)

        port_dues_cand = cand_port.port_dues_usd_per_call or 20000.0
        port_dues_curr = port.port_dues_usd_per_call if port else 22000.0
        port_dues_delta = port_dues_cand - port_dues_curr

        steaming_fuel_delta = (abs(dist_delta) / (normal_speed * 24.0)) * normal_fuel_rate * bunker_price_usd_per_mt
        waiting_cost_saved = waiting_saved * (daily_hire + aux_fuel * bunker_price_usd_per_mt + demurrage_rate_usd_day)

        net_savings = waiting_cost_saved - port_dues_delta - (steaming_fuel_delta if dist_delta > 0 else -steaming_fuel_delta * 0.5)

        if net_savings > 15000:
            rec = f"Highly Recommended: Divert to {cand_name} to save ~{waiting_saved:.1f} days waiting."
        elif net_savings > 0:
            rec = f"Viable Alternative: Marginally favorable if berth ready on arrival."
        else:
            rec = f"Stay at {destination}: Diversion costs exceed congestion savings."

        diversion_options.append({
            "alternative_port": cand_name,
            "distance_delta_nm": round(dist_delta, 0),
            "turnaround_days": round(cand_port.avg_turnaround_days or 4.0, 1),
            "congestion_level": cand_port.congestion_level or "low",
            "port_dues_delta_usd": round(port_dues_delta, 0),
            "net_savings_usd": round(net_savings, 0),
            "recommendation": rec,
        })

    # Strategy synthesis
    recommendations = []
    if waiting_days >= 3.0 and bunker_savings > 10000:
        optimal_strategy = "VIRTUAL_ARRIVAL_SLOW_STEAM"
        recommendations.append(
            f"Slow steam at {slow_speed:.1f} knots to absorb {absorbed_waiting_days:.1f} days of anchorage waiting at sea. "
            f"This saves ${bunker_savings:,.0f} in bunker fuel without delaying overall cargo discharge."
        )
    elif any(d["net_savings_usd"] > 25000 for d in diversion_options):
        best_div = max(diversion_options, key=lambda x: x["net_savings_usd"])
        optimal_strategy = "PORT_DIVERSION"
        recommendations.append(
            f"Divert shipment to {best_div['alternative_port']}. Projected net savings of "
            f"${best_div['net_savings_usd']:,.0f} by avoiding {waiting_days:.1f} days congestion at {destination}."
        )
    else:
        optimal_strategy = "STANDARD_BERTH_WAIT"
        recommendations.append(
            f"Maintain normal speed and tender NOR (Notice of Readiness) immediately to enter the queue. "
            f"Ensure charterparty laytime terms include prompt berth clause to limit demurrage exposure."
        )

    recommendations.append(
        f"Anchorage idling burns ~{aux_fuel} MT/day fuel (${aux_fuel * bunker_price_usd_per_mt:,.0f}/day). "
        f"Total idle expense over {waiting_days:.1f} days is ${total_waiting_cost:,.0f}."
    )

    if demurrage_incurred > 0:
        recommendations.append(
            f"Demurrage risk: Estimated ${demurrage_incurred:,.0f} for {excess_days:.1f} days over allowed laytime ({laytime_allowed_days:.1f} days)."
        )

    # ── Deterministic 6-Scenario Simulation Matrix ────────────────────────────
    # 1. Low Demand Scenario
    low_demand_delay_days = 6.0
    low_demand_cost = round(low_demand_delay_days * daily_hire + low_demand_delay_days * aux_fuel * bunker_price_usd_per_mt, 0)
    low_demand_mitig_benefit = round(bunker_savings + low_demand_cost * 0.45, 0)
    scen_low_demand = {
        "scenario_type": "low_demand",
        "scenario_name": "Downstream Low Demand & Receiver Delay",
        "description": "Receiver storage facilities at capacity; cargo discharge off-take delayed by ~6 days.",
        "financial_impact_usd": low_demand_cost,
        "suggested_mitigation": "Slow steam to absorb transit time (super eco-speed 9.0–10.5 kn) and convert vessel into floating storage on agreed discounted daily rate.",
        "mitigation_benefit_usd": low_demand_mitig_benefit,
        "net_exposure_usd": max(0.0, low_demand_cost - low_demand_mitig_benefit),
        "operational_action": "Execute addendum for floating storage at 60% standard hire rate; reduce main engine rpm to minimum safe load.",
    }

    # 2. Port Congestion Scenario
    scen_port_congestion = {
        "scenario_type": "port_congestion",
        "scenario_name": "Anchorage Queue & Terminal Congestion",
        "description": f"Destination port {destination} has {waiting_days:.1f} days anchorage queue with {int(waiting_days*1.5)} vessels waiting.",
        "financial_impact_usd": round(total_congestion_exposure, 0),
        "suggested_mitigation": "Implement Virtual Arrival protocol: agree with terminal on scheduled unberthing slot and adjust passage speed to arrive just-in-time.",
        "mitigation_benefit_usd": round(bunker_savings, 0),
        "net_exposure_usd": max(0.0, round(total_congestion_exposure - bunker_savings, 0)),
        "operational_action": "Tender electronic NOR under BIMCO Virtual Arrival clause; reduce speed from 14.5 to 11.5 knots.",
    }

    # 3. Delayed Berth Scenario
    berth_delay_days = 3.0
    berth_delay_demurrage = round(berth_delay_days * demurrage_rate_usd_day, 0)
    berth_mitig_benefit = round(berth_delay_demurrage * 0.70, 0)
    scen_delayed_berth = {
        "scenario_type": "delayed_berth",
        "scenario_name": "Delayed Berth & Tidal Window Constraints",
        "description": f"Berth occupied by previous vessel or tide window missed at {destination}; 3.0 days berthing delay.",
        "financial_impact_usd": berth_delay_demurrage,
        "suggested_mitigation": "Enforce 'Whether In Berth Or Not' (WIBON) charterparty clause so laytime continues counting; tender NOR immediately upon pilot station arrival.",
        "mitigation_benefit_usd": berth_mitig_benefit,
        "net_exposure_usd": max(0.0, berth_delay_demurrage - berth_mitig_benefit),
        "operational_action": "Verify charterer counter-signature on NOR; demand terminal priority berthing in next high-tide slot.",
    }

    # 4. Vessel Waiting Scenario
    waiting_direct_cost = round(total_waiting_cost, 0)
    waiting_mitig_benefit = round(waiting_direct_cost * 0.40, 0)
    scen_vessel_waiting = {
        "scenario_type": "vessel_waiting",
        "scenario_name": "Anchorage Waiting & Auxiliary Fuel Consumption",
        "description": f"Vessel at anchor for {waiting_days:.1f} days burning {aux_fuel} MT/day auxiliary generator fuel plus daily hire.",
        "financial_impact_usd": waiting_direct_cost,
        "suggested_mitigation": "Switch auxiliary generators to economy eco-mode; pre-clear customs, immigration, and maritime health declarations prior to anchoring.",
        "mitigation_benefit_usd": waiting_mitig_benefit,
        "net_exposure_usd": max(0.0, waiting_direct_cost - waiting_mitig_benefit),
        "operational_action": "Pre-arrange bunker delivery and underwater hull cleaning at anchorage during waiting window if permitted.",
    }

    # 5. Alternate Employment Scenario
    best_div_savings = max([d["net_savings_usd"] for d in diversion_options], default=0.0)
    best_alt_port = diversion_options[0]["alternative_port"] if diversion_options else "Dhamra"
    alt_employ_cost = round(total_congestion_exposure, 0)
    alt_employ_benefit = round(max(15000.0, best_div_savings), 0)
    scen_alt_employment = {
        "scenario_type": "alternate_employment",
        "scenario_name": "Alternative Discharge Port / Transhipment",
        "description": f"Prolonged congestion or equipment breakdown at {destination}; alternate discharge port evaluation.",
        "financial_impact_usd": alt_employ_cost,
        "suggested_mitigation": f"Exercise Liberty clause to divert vessel to {best_alt_port} with faster turnaround and lower anchorage waiting.",
        "mitigation_benefit_usd": alt_employ_benefit,
        "net_exposure_usd": max(0.0, alt_employ_cost - alt_employ_benefit),
        "operational_action": f"Request charterer consent to reroute to {best_alt_port}; arrange coastal rail/barge logistics for final inland delivery.",
    }

    # 6. Repositioning Scenario
    reposition_days = 2.5
    reposition_fuel_cost = round(reposition_days * VESSEL_SEA_FUEL.get(vessel_class, 32.0) * bunker_price_usd_per_mt * 0.85, 0)
    reposition_opex = round(reposition_days * daily_hire, 0)
    reposition_total_cost = round(reposition_fuel_cost + reposition_opex, 0)
    reposition_benefit = round(reposition_total_cost * 0.65, 0)
    scen_repositioning = {
        "scenario_type": "repositioning",
        "scenario_name": "Ballast Repositioning & Backhaul Employment",
        "description": f"Post-discharge repositioning from {destination} to next regional loading zone (~{reposition_days:.1f} ballast days).",
        "financial_impact_usd": reposition_total_cost,
        "suggested_mitigation": "Secure coastal or backhaul parcel (e.g. Indian coastal coal to Western India or iron ore fines to China) to monetize ballast transit.",
        "mitigation_benefit_usd": reposition_benefit,
        "net_exposure_usd": max(0.0, reposition_total_cost - reposition_benefit),
        "operational_action": "Instruct regional broker to circularize vessel for short-haul cabotage fixture before completion of discharge.",
    }

    simulated_scenarios = [
        scen_low_demand,
        scen_port_congestion,
        scen_delayed_berth,
        scen_vessel_waiting,
        scen_alt_employment,
        scen_repositioning,
    ]

    return {
        "destination": destination,
        "vessel_class": vessel_class,
        "waiting_days": round(waiting_days, 1),
        "demurrage_rate_usd_day": round(demurrage_rate_usd_day, 0),
        "laytime_allowed_days": round(laytime_allowed_days, 1),
        "actual_port_days": round(actual_port_days, 1),
        "anchorage_idle_bunker_usd": round(anchorage_idle_bunker, 0),
        "anchorage_vessel_cost_usd": round(anchorage_vessel_cost, 0),
        "total_waiting_cost_usd": round(total_waiting_cost, 0),
        "demurrage_incurred_usd": round(demurrage_incurred, 0),
        "dispatch_earned_usd": round(dispatch_earned, 0),
        "total_congestion_exposure_usd": round(total_congestion_exposure, 0),
        "slow_steaming": slow_steaming,
        "diversion_options": diversion_options,
        "simulated_scenarios": simulated_scenarios,
        "optimal_strategy": optimal_strategy,
        "actionable_recommendations": recommendations,
        "disclaimer": "[DEMO] Idle scenario calculations use synthetic operational parameters.",
    }
