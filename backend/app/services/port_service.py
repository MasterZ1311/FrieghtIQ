"""
Port Compatibility Service
==========================
Orchestrates port compatibility evaluations using domain rules and repository access.
Provides deterministic fallback behavior for missing or unseeded port records.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.domain.models import Cargo, Port
from app.domain.port_rules import evaluate_port_compatibility
from app.repositories.port_repo import PortRepository
from app.repositories.vessel_repo import VesselRepository


def check_compatibility(
    db: Optional[Session],
    port_name: str,
    vessel_class: str,
    cargo_mt: float,
    commodity: str,
) -> Dict[str, Any]:
    """
    Checks port compatibility by coordinating the repositories and domain rules.
    """
    port_repo = PortRepository(db)
    vessel_repo = VesselRepository(db)

    port = port_repo.get_by_name(port_name)
    vessel = vessel_repo.get_by_class(vessel_class)
    cargo = Cargo(
        commodity=commodity,
        quantity_mt=cargo_mt,
        origin="Default",
        destination=port_name,
    )

    result = evaluate_port_compatibility(port=port, vessel=vessel, cargo=cargo)
    return result


def list_ports(db: Optional[Session], region: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lists all ports, optionally filtered by region.
    """
    port_repo = PortRepository(db)
    ports = port_repo.list_all(region=region)
    return [
        {
            "name": p.name,
            "country": p.country,
            "region": p.region,
            "max_dwt": p.max_dwt,
            "max_draft_m": p.max_draft,
            "max_loa_m": p.max_loa,
            "max_beam_m": p.max_beam,
            "berths": p.berths,
            "tide_restricted": p.tide_restricted,
            "congestion_level": p.congestion_level,
            "avg_turnaround_days": p.avg_turnaround_days,
            "handling_rate_mt_day": p.handling_rate,
            "handling_rate": p.handling_rate,
            "suitable_commodities": p.suitable_commodities,
            "notes": p.notes,
        }
        for p in ports
    ]
