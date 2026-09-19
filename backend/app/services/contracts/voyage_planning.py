import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class VoyageScheduleItem(BaseModel):
    voyage_number: int
    parcel_mt: float
    is_remainder: bool
    estimated_departure_day: int
    estimated_laycan_window: str

class VoyagePlanningResult(BaseModel):
    total_requirement_mt: float
    voyage_parcel_mt: float
    full_voyages: int
    remainder_mt: float
    expected_voyages: int
    total_planned_mt: float
    voyage_frequency_days: float
    planning_horizon_days: int
    schedule: List[VoyageScheduleItem]

class VoyagePlanningService:
    """
    Service for multi-voyage bulk parcel planning (SIH26006).
    Computes optimal voyage count without discarding cargo remainders:
    expected_voyages = ceil(total_requirement / voyage_parcel)
    """

    @staticmethod
    def plan_voyages(
        total_requirement_mt: float,
        voyage_parcel_mt: float,
        planning_horizon_days: int = 180,
        start_date: Optional[datetime] = None
    ) -> VoyagePlanningResult:
        if total_requirement_mt <= 0:
            raise ValueError("Total cargo requirement must be strictly positive.")
        if voyage_parcel_mt <= 0:
            raise ValueError("Voyage parcel size must be strictly positive.")

        full_voyages = int(math.floor(total_requirement_mt / voyage_parcel_mt))
        remainder_mt = round(total_requirement_mt % voyage_parcel_mt, 2)
        expected_voyages = int(math.ceil(total_requirement_mt / voyage_parcel_mt))

        # Even voyage spacing across horizon
        frequency_days = round(planning_horizon_days / max(expected_voyages, 1), 1)
        base_date = start_date or datetime.now(timezone.utc)

        schedule: List[VoyageScheduleItem] = []
        for i in range(1, expected_voyages + 1):
            is_rem = (i == expected_voyages and remainder_mt > 0 and remainder_mt != voyage_parcel_mt)
            parcel = remainder_mt if is_rem else voyage_parcel_mt
            dep_day = int(round((i - 1) * frequency_days))
            voyage_start = base_date + timedelta(days=dep_day)
            voyage_end = voyage_start + timedelta(days=5) # 5-day standard laycan spread

            schedule.append(VoyageScheduleItem(
                voyage_number=i,
                parcel_mt=parcel,
                is_remainder=is_rem,
                estimated_departure_day=dep_day,
                estimated_laycan_window=f"{voyage_start.strftime('%d %b %Y')} - {voyage_end.strftime('%d %b %Y')}"
            ))

        return VoyagePlanningResult(
            total_requirement_mt=total_requirement_mt,
            voyage_parcel_mt=voyage_parcel_mt,
            full_voyages=full_voyages,
            remainder_mt=remainder_mt,
            expected_voyages=expected_voyages,
            total_planned_mt=total_requirement_mt,
            voyage_frequency_days=frequency_days,
            planning_horizon_days=planning_horizon_days,
            schedule=schedule
        )
