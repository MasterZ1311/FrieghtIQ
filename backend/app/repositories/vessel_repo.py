"""
Vessel Repository
=================
Data access abstraction for Vessel class specifications.
Provides vessel specs with deterministic demo fallbacks.
"""
import logging
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from app.models import Vessel as VesselModel
from app.domain.models import Vessel
from app.seed.seed_data import VESSELS

logger = logging.getLogger(__name__)

# Standard maritime baseline specs
STANDARD_VESSEL_SPECS: Dict[str, Dict] = {
    "Handysize": {
        "vessel_type": "Handysize",
        "capacity_mt": 35000.0,
        "dwt_min": 25000.0,
        "dwt_max": 40000.0,
        "loa": 180.0,
        "beam": 28.0,
        "draft": 10.5,
        "speed": 13.5,
        "daily_cost": 7000.0,
        "fuel_consumption_mt_day": 22.0,
    },
    "Supramax": {
        "vessel_type": "Supramax",
        "capacity_mt": 58000.0,
        "dwt_min": 50000.0,
        "dwt_max": 65000.0,
        "loa": 200.0,
        "beam": 32.2,
        "draft": 12.8,
        "speed": 14.0,
        "daily_cost": 8500.0,
        "fuel_consumption_mt_day": 28.0,
    },
    "Panamax": {
        "vessel_type": "Panamax",
        "capacity_mt": 75000.0,
        "dwt_min": 65000.0,
        "dwt_max": 82000.0,
        "loa": 225.0,
        "beam": 32.26,
        "draft": 14.0,
        "speed": 14.5,
        "daily_cost": 9500.0,
        "fuel_consumption_mt_day": 34.0,
    },
    "Capesize": {
        "vessel_type": "Capesize",
        "capacity_mt": 180000.0,
        "dwt_min": 150000.0,
        "dwt_max": 200000.0,
        "loa": 295.0,
        "beam": 45.0,
        "draft": 18.0,
        "speed": 14.5,
        "daily_cost": 13000.0,
        "fuel_consumption_mt_day": 58.0,
    },
}


class VesselRepository:
    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def get_by_class(self, vessel_class: str) -> Vessel:
        """
        Retrieves vessel specs by class name. First checks DB, then falls back to demo specs.
        """
        clean_class = vessel_class.strip().capitalize()
        # Normalization for common aliases
        if "handy" in clean_class.lower():
            clean_class = "Handysize"
        elif "supra" in clean_class.lower() or "ultra" in clean_class.lower():
            clean_class = "Supramax"
        elif "pana" in clean_class.lower() or "kamsar" in clean_class.lower():
            clean_class = "Panamax"
        elif "cape" in clean_class.lower() or "newcastle" in clean_class.lower():
            clean_class = "Capesize"

        if self.db:
            try:
                row = self.db.query(VesselModel).filter(VesselModel.vessel_class.ilike(clean_class)).first()
                if row:
                    return Vessel(
                        vessel_type=row.vessel_class,
                        capacity_mt=float(row.dwt_max or 75000),
                        loa=float(row.loa_m or 225.0),
                        beam=float(row.beam_m or 32.2),
                        draft=float(row.draft_m or 14.0),
                        speed=float(row.speed_kn or 14.5),
                        daily_cost=float(row.daily_opex_usd or 9500.0),
                        dwt_min=float(row.dwt_min or 65000),
                        dwt_max=float(row.dwt_max or 82000),
                        fuel_consumption_mt_day=float(row.fuel_consumption_mt_day or 34.0),
                        is_demo=True,
                    )
            except Exception as e:
                logger.warning(f"DB vessel query error for '{vessel_class}': {e}. Using fallback specs.")

        spec = STANDARD_VESSEL_SPECS.get(clean_class, STANDARD_VESSEL_SPECS["Panamax"])
        return Vessel(
            vessel_type=spec["vessel_type"],
            capacity_mt=spec["capacity_mt"],
            loa=spec["loa"],
            beam=spec["beam"],
            draft=spec["draft"],
            speed=spec["speed"],
            daily_cost=spec["daily_cost"],
            dwt_min=spec["dwt_min"],
            dwt_max=spec["dwt_max"],
            fuel_consumption_mt_day=spec["fuel_consumption_mt_day"],
            is_demo=True,
        )

    def list_classes(self) -> List[Vessel]:
        """Returns all standard dry bulk vessel classes."""
        return [self.get_by_class(c) for c in ["Handysize", "Supramax", "Panamax", "Capesize"]]
