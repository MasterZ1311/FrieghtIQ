"""
Port Compatibility Domain Rules
===============================
Pure business rules for evaluating physical, navigational, and operational
compatibility between a vessel/cargo and a seaport.
"""
from typing import Dict, Any, List
from app.domain.models import Port, Vessel, Cargo


def evaluate_port_compatibility(
    port: Port,
    vessel: Vessel,
    cargo: Cargo,
) -> Dict[str, Any]:
    """
    Evaluates physical and operational constraints between port and vessel.
    Returns explainable constraint checks, overall compatibility status,
    and operational turnaround estimates.
    """
    constraints: List[Dict[str, str]] = []
    berth_constraints: List[str] = list(port.berth_constraints)

    # 1. Draft Check
    port_draft = port.max_draft if port.max_draft > 0 else 99.0
    vessel_draft = vessel.draft
    if vessel_draft > port_draft:
        constraints.append({
            "constraint": "Draft",
            "status": "FAIL",
            "detail": f"Vessel draft {vessel_draft:.1f}m exceeds port maximum permissible draft of {port_draft:.1f}m. Vessel cannot berth fully laden.",
        })
        berth_constraints.append(f"Exceeds max channel/berth draft ({port_draft:.1f}m)")
    elif vessel_draft > port_draft * 0.90:
        constraints.append({
            "constraint": "Draft",
            "status": "WARNING",
            "detail": f"Vessel draft {vessel_draft:.1f}m is close to port limit ({port_draft:.1f}m). High-tide window and under-keel clearance protocol required.",
        })
        berth_constraints.append("High-tide transit window required")
    else:
        constraints.append({
            "constraint": "Draft",
            "status": "OK",
            "detail": f"Vessel draft {vessel_draft:.1f}m is well within port limit of {port_draft:.1f}m.",
        })

    # 2. LOA (Length Overall) Check
    port_loa = port.max_loa if port.max_loa > 0 else 999.0
    vessel_loa = vessel.loa
    if vessel_loa > port_loa:
        constraints.append({
            "constraint": "Length (LOA)",
            "status": "FAIL",
            "detail": f"Vessel LOA {vessel_loa:.1f}m exceeds port quay limit of {port_loa:.1f}m.",
        })
        berth_constraints.append(f"Exceeds maximum berth LOA ({port_loa:.1f}m)")
    else:
        constraints.append({
            "constraint": "Length (LOA)",
            "status": "OK",
            "detail": f"Vessel LOA {vessel_loa:.1f}m is within quay limit of {port_loa:.1f}m.",
        })

    # 3. Beam Check
    port_beam = port.max_beam if port.max_beam > 0 else 999.0
    vessel_beam = vessel.beam
    if vessel_beam > port_beam:
        constraints.append({
            "constraint": "Beam",
            "status": "FAIL",
            "detail": f"Vessel beam {vessel_beam:.1f}m exceeds channel/lock limit of {port_beam:.1f}m.",
        })
        berth_constraints.append(f"Exceeds crane outreach / channel beam ({port_beam:.1f}m)")
    else:
        constraints.append({
            "constraint": "Beam",
            "status": "OK",
            "detail": f"Vessel beam {vessel_beam:.1f}m complies with port limit of {port_beam:.1f}m.",
        })

    # 4. Cargo / DWT Capacity Check
    port_max_dwt = port.max_dwt if port.max_dwt > 0 else 999999.0
    if cargo.quantity_mt > port_max_dwt:
        constraints.append({
            "constraint": "Cargo Weight",
            "status": "FAIL",
            "detail": f"Cargo quantity {cargo.quantity_mt:,.0f} MT exceeds port maximum DWT handling capability of {port_max_dwt:,.0f} MT.",
        })
    else:
        constraints.append({
            "constraint": "Cargo Weight",
            "status": "OK",
            "detail": f"Cargo {cargo.quantity_mt:,.0f} MT is within port displacement capacity of {port_max_dwt:,.0f} MT.",
        })

    # 5. Commodity Handling
    if port.suitable_commodities and cargo.commodity not in port.suitable_commodities:
        constraints.append({
            "constraint": "Commodity Handling",
            "status": "WARNING",
            "detail": f"{cargo.commodity} is not listed among primary dedicated terminal commodities at {port.name}. Dedicated conveyor/hopper availability must be verified.",
        })
    else:
        constraints.append({
            "constraint": "Commodity Handling",
            "status": "OK",
            "detail": f"Port {port.name} routinely handles dry bulk {cargo.commodity}.",
        })

    # 6. Tidal Restrictions
    if port.tide_restricted:
        constraints.append({
            "constraint": "Tide Restriction",
            "status": "WARNING",
            "detail": f"{port.name} is tidal-dependent. Vessel navigation restricted to 4-hour high-water windows twice daily.",
        })
        berth_constraints.append("Tidal navigation window restriction (HW ±2 hrs)")
    else:
        constraints.append({
            "constraint": "Tide Restriction",
            "status": "OK",
            "detail": "Non-tidal or deepwater approaches; 24/7 navigation permitted under pilotage.",
        })

    # 7. Congestion & Waiting Buffer
    congestion_map = {
        "low": ("OK", "Low anchorage waiting. Average turnaround on schedule."),
        "medium": ("WARNING", "Moderate queue. Add 1.5 to 2.5 days operational buffer."),
        "high": ("WARNING", "High queue at outer anchorage. Add 3 to 6 days buffer; demurrage risk elevated."),
    }
    status, detail = congestion_map.get(port.congestion_level.lower(), ("OK", "Normal operational conditions."))
    constraints.append({
        "constraint": "Congestion Level",
        "status": status,
        "detail": detail,
    })

    # Handling rate and turnaround calculation
    handling_rate = port.handling_rate if port.handling_rate > 0 else 20000.0
    discharge_days = cargo.quantity_mt / handling_rate
    turnaround_days = round(discharge_days + port.avg_turnaround_days, 1)

    is_compatible = all(c["status"] != "FAIL" for c in constraints)

    return {
        "port": port.name,
        "vessel_class": vessel.vessel_type,
        "compatible": is_compatible,
        "constraints": constraints,
        "berth_constraints": berth_constraints,
        "turnaround_days": turnaround_days,
        "port_dues_usd": port.port_dues_usd,
        "handling_rate": handling_rate,
        "handling_rate_mt_day": handling_rate,
        "notes": port.notes or f"Compatibility check performed against {port.name} standard navigational limits.",
    }
