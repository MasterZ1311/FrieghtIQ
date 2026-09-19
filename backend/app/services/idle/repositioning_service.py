"""
Repositioning Service
Evaluates ballast transit feasibility, sailing duration, bunker economics, and laycan timing.

STRICT DATA INTEGRITY:
- Sailing Days = Distance / (Speed × 24)
- Speed must be an explicit assumption or sourced vessel speed: "Speed assumption: X knots".
- Bunker Cost = (Fuel Consumption MT/day × Sailing Days) × Bunker Price $/MT.
- If consumption or price is unavailable: bunker_cost = None (UNAVAILABLE).
- Outputs: REPOSITION, DO_NOT_REPOSITION, UNKNOWN.
"""
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone

from app.models.vessels import Vessel
from app.models.ports import Port
from app.models.cargo import CargoRequirement
from app.models.enums import RepositioningDecision, FeasibilityStatus


class RepositioningService:
    @staticmethod
    def calculate_sailing_time(
        distance_nm: Optional[float],
        speed_knots: Optional[float]
    ) -> Tuple[Optional[float], Optional[str]]:
        """
        Calculates sailing time in days.
        Returns:
            (sailing_days, speed_assumption_label)
        """
        if distance_nm is None or distance_nm <= 0:
            return (0.0 if distance_nm == 0.0 else None, None)

        if speed_knots is None or speed_knots <= 0:
            return (None, "Speed assumption: UNAVAILABLE")

        # 24 hours per day
        sailing_days = round(distance_nm / (speed_knots * 24.0), 2)
        speed_label = f"Speed assumption: {speed_knots:.1f} knots"
        return (sailing_days, speed_label)

    @staticmethod
    def calculate_bunker_cost(
        sailing_days: Optional[float],
        fuel_consumption_mtpd: Optional[float],
        bunker_price_usd_per_mt: Optional[float]
    ) -> Tuple[Optional[float], str]:
        """
        Calculates total bunker expenditure for repositioning leg.
        If either consumption or price is missing: returns (None, 'Bunker Cost: UNAVAILABLE').
        """
        if sailing_days is None:
            return (None, "Bunker Cost: UNAVAILABLE (Sailing duration uncomputed)")

        if fuel_consumption_mtpd is None or fuel_consumption_mtpd <= 0:
            return (None, "Bunker Cost: UNAVAILABLE (Fuel consumption parameter unrecorded)")

        if bunker_price_usd_per_mt is None or bunker_price_usd_per_mt <= 0:
            return (None, "Bunker Cost: UNAVAILABLE (Bunker fuel price unrecorded)")

        total_bunker_mt = round(sailing_days * fuel_consumption_mtpd, 2)
        total_cost = round(total_bunker_mt * bunker_price_usd_per_mt, 2)
        return (
            total_cost,
            f"Bunker cost: ${total_cost:,.2f} ({total_bunker_mt:.1f} MT @ ${bunker_price_usd_per_mt:,.2f}/MT VLSFO)"
        )

    @staticmethod
    def evaluate_timing(
        available_date: Optional[datetime],
        sailing_days: Optional[float],
        laycan_start: Optional[datetime],
        laycan_end: Optional[datetime]
    ) -> Tuple[str, Optional[datetime], str]:
        """
        Evaluates whether repositioning vessel can make the cargo laycan.
        Returns:
            (timing_status, estimated_eta, narrative)
            timing_status: 'ON_TIME', 'TIGHT', 'MISSED_LAYCAN', 'UNKNOWN'
        """
        if available_date is None or sailing_days is None or laycan_end is None:
            return ("UNKNOWN", None, "Availability date, sailing duration, or laycan canceling date is unknown.")

        avail_dt = available_date if available_date.tzinfo else available_date.replace(tzinfo=timezone.utc)
        lay_start_dt = (laycan_start if laycan_start.tzinfo else laycan_start.replace(tzinfo=timezone.utc)) if laycan_start else None
        lay_end_dt = laycan_end if laycan_end.tzinfo else laycan_end.replace(tzinfo=timezone.utc)

        eta = avail_dt + timedelta(days=sailing_days)

        if lay_start_dt and eta < lay_start_dt:
            margin = (lay_start_dt - eta).total_seconds() / 86400.0
            return (
                "ON_TIME",
                eta,
                f"Vessel arrives {round(margin, 1)} days ahead of laycan opening ({eta.strftime('%Y-%m-%d')})."
            )

        if eta <= lay_end_dt:
            margin = (lay_end_dt - eta).total_seconds() / 86400.0
            if margin < 1.5:
                return (
                    "TIGHT",
                    eta,
                    f"Vessel arrives {round(margin, 1)} days before canceling date ({eta.strftime('%Y-%m-%d')}). Tight buffer."
                )
            return (
                "ON_TIME",
                eta,
                f"Vessel arrives comfortably within laycan ({eta.strftime('%Y-%m-%d')}, {round(margin, 1)} days buffer)."
            )

        missed = (eta - lay_end_dt).total_seconds() / 86400.0
        return (
            "MISSED_LAYCAN",
            eta,
            f"Vessel ETA ({eta.strftime('%Y-%m-%d')}) misses laycan canceling date by {round(missed, 1)} days."
        )

    @classmethod
    def evaluate_repositioning_option(
        cls,
        vessel: Vessel,
        target_port: Port,
        target_cargo: Optional[CargoRequirement],
        distance_nm: Optional[float],
        distance_method: str,
        speed_knots: Optional[float] = 12.5,
        port_compatibility: str = "PASS",
        bunker_price_usd: Optional[float] = None,
        daily_vessel_cost: Optional[float] = None,
        now: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Fully evaluates a ballast repositioning leg.
        """
        # Determine vessel availability date
        avail_date = None
        if vessel.availability and vessel.availability.open_date_start:
            avail_date = vessel.availability.open_date_start

        # Sailing time
        sailing_days, speed_label = cls.calculate_sailing_time(distance_nm, speed_knots)

        # Laycan Timing
        laycan_start = target_cargo.laycan_start if target_cargo else None
        laycan_end = target_cargo.laycan_end if target_cargo else None
        timing_status, eta, timing_narrative = cls.evaluate_timing(
            avail_date, sailing_days, laycan_start, laycan_end
        )

        # Bunker consumption
        consumption_mtpd = None
        if vessel.particulars:
            consumption_mtpd = (
                getattr(vessel.particulars, "consumption_ballast_mtpd", None) or
                getattr(vessel.particulars, "consumption_laden_mtpd", None)
            )

        bunker_cost, bunker_narrative = cls.calculate_bunker_cost(
            sailing_days, consumption_mtpd, bunker_price_usd
        )

        # Total cost (bunker + daily vessel cost during transit if available)
        total_cost = None
        if bunker_cost is not None and daily_vessel_cost is not None and sailing_days is not None:
            charter_transit_cost = sailing_days * daily_vessel_cost
            total_cost = round(bunker_cost + charter_transit_cost, 2)
        elif bunker_cost is not None:
            total_cost = bunker_cost

        # Overall Recommendation
        if port_compatibility == "FAIL" or timing_status == "MISSED_LAYCAN":
            status = RepositioningDecision.DO_NOT_REPOSITION
            rec_reason = "Repositioning unviable: Violates port constraints or misses cargo laycan."
        elif port_compatibility == "PASS" and timing_status in ["ON_TIME", "TIGHT"]:
            status = RepositioningDecision.REPOSITION
            rec_reason = "Feasible repositioning: Vessel meets port constraints and laycan schedule."
        elif distance_nm is None or sailing_days is None:
            status = RepositioningDecision.UNKNOWN
            rec_reason = "Distance or sailing speed is unknown; feasibility undetermined."
        else:
            status = RepositioningDecision.UNKNOWN
            rec_reason = "Port clearance or timing window requires verification."

        return {
            "vessel_id": vessel.id,
            "target_port_id": target_port.id,
            "target_cargo_request_id": target_cargo.id if target_cargo else None,
            "distance_nm": distance_nm,
            "distance_method": distance_method,
            "speed_knots": speed_knots,
            "speed_label": speed_label or "Speed assumption: UNAVAILABLE",
            "sailing_days": sailing_days,
            "estimated_eta": eta.isoformat() if eta else None,
            "port_compatibility": port_compatibility,
            "timing_compatibility": timing_status,
            "timing_narrative": timing_narrative,
            "estimated_bunker_cost": bunker_cost,
            "bunker_narrative": bunker_narrative,
            "estimated_total_cost": total_cost,
            "decision": status.value,
            "recommendation_reason": rec_reason,
            "data_status": "RECENT" if (bunker_cost is not None and distance_method == "NAUTICAL_CHART") else "SYNTHETIC"
        }
