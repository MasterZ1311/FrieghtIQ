"""
Port Repository
===============
Data access abstraction for Seaport specifications.
Queries SQLAlchemy DB with deterministic demo fallbacks.
"""
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models import Port as PortModel
from app.domain.models import Port
from app.seed.seed_data import PORTS

logger = logging.getLogger(__name__)


# Quick in-memory demo lookup index
DEMO_PORTS_BY_NAME = {p["name"].lower(): p for p in PORTS}


class PortRepository:
    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def get_by_name(self, name: str) -> Optional[Port]:
        """
        Retrieves port by name. First checks DB, then falls back to demo seed data.
        """
        clean_name = name.strip()
        # 1. Try DB query
        if self.db:
            try:
                row = self.db.query(PortModel).filter(PortModel.name.ilike(clean_name)).first()
                if row:
                    return Port(
                        name=row.name,
                        country=row.country,
                        region=row.region,
                        max_loa=row.max_loa_m or 280.0,
                        max_beam=row.max_beam_m or 45.0,
                        max_draft=row.max_draft_m or 14.5,
                        handling_rate=row.handling_rate_mt_day or 25000.0,
                        berth_constraints=[c for c in [
                            "Tide-restricted operational window" if row.tide_restricted else None,
                            f"{row.congestion_level.capitalize()} anchorage congestion" if row.congestion_level else None,
                        ] if c],
                        max_dwt=float(row.max_dwt or 180000),
                        berths=row.berths or 6,
                        tide_restricted=bool(row.tide_restricted),
                        congestion_level=row.congestion_level or "medium",
                        avg_turnaround_days=float(row.avg_turnaround_days or 4.0),
                        port_dues_usd=float(row.port_dues_usd_per_call or 25000.0),
                        suitable_commodities=row.suitable_commodities or ["Coal", "Iron Ore", "Grain"],
                        notes=row.notes or "",
                        is_demo=True,
                    )
            except Exception as e:
                logger.warning(f"DB lookup for port '{name}' failed: {e}. Falling back to demo data.")

        # 2. Demo Seed Fallback
        demo_port = DEMO_PORTS_BY_NAME.get(clean_name.lower())
        if demo_port:
            return Port(
                name=demo_port["name"],
                country=demo_port["country"],
                region=demo_port["region"],
                max_loa=demo_port.get("max_loa_m", 280.0),
                max_beam=demo_port.get("max_beam_m", 45.0),
                max_draft=demo_port.get("max_draft_m", 14.5),
                handling_rate=float(demo_port.get("handling_rate_mt_day", 25000)),
                berth_constraints=[c for c in [
                    "Tide-restricted operational window" if demo_port.get("tide_restricted") else None,
                    f"{demo_port.get('congestion_level', 'medium').capitalize()} anchorage congestion",
                ] if c],
                max_dwt=float(demo_port.get("max_dwt", 180000)),
                berths=demo_port.get("berths", 6),
                tide_restricted=bool(demo_port.get("tide_restricted", False)),
                congestion_level=demo_port.get("congestion_level", "medium"),
                avg_turnaround_days=float(demo_port.get("avg_turnaround_days", 4.0)),
                port_dues_usd=float(demo_port.get("port_dues_usd_per_call", 25000)),
                suitable_commodities=demo_port.get("suitable_commodities", ["Coal", "Iron Ore"]),
                notes=demo_port.get("notes", ""),
                is_demo=True,
            )

        # 3. Deterministic Generic Fallback for unknown ports
        return Port(
            name=name,
            country="India" if "par" in clean_name.lower() or "vis" in clean_name.lower() else "International",
            region="destination",
            max_loa=260.0,
            max_beam=42.0,
            max_draft=14.0,
            handling_rate=22000.0,
            berth_constraints=["Standard commercial berth"],
            max_dwt=90000.0,
            berths=4,
            tide_restricted=False,
            congestion_level="medium",
            avg_turnaround_days=4.5,
            port_dues_usd=25000.0,
            suitable_commodities=["Coal", "Iron Ore", "Grain", "Fertilizer", "Bauxite"],
            notes="[DEMO] Generic synthetic fallback port profile.",
            is_demo=True,
        )

    def list_all(self, region: Optional[str] = None) -> List[Port]:
        """Lists all ports from DB or demo seed."""
        ports = []
        if self.db:
            try:
                q = self.db.query(PortModel)
                if region:
                    q = q.filter(PortModel.region == region)
                rows = q.all()
                if rows:
                    for r in rows:
                        ports.append(self.get_by_name(r.name))
                    return ports
            except Exception as e:
                logger.warning(f"Failed to list ports from DB: {e}")

        # Fallback to seed
        for p in PORTS:
            if not region or p.get("region") == region:
                ports.append(self.get_by_name(p["name"]))
        return ports
