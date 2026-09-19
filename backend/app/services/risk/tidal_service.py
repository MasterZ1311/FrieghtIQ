"""
Tidal Gate Scheduler Service
Evaluates tidal windows, draft clearances, and Under Keel Clearance (UKC) constraints.

STRICT DATA INTEGRITY & PHYSICAL FORMULAS:
- available_depth = berth_draft (or channel_draft) + predicted_tide_height
- required_depth = vessel_draft + required_ukc
- ukc_margin = available_depth - required_depth
- Status:
  - PASS: available_depth >= required_depth across the entire tidal cycle or planned transit window.
  - CONDITIONAL: clearance is only achievable during High Water tidal window (e.g. HW ± 2 hrs).
  - FAIL: available_depth < required_depth even at maximum astronomical high tide.
  - UNKNOWN: missing vessel_draft, missing berth_draft, or unrecorded tidal predictions.
- STRICT PROHIBITION: Never infer vessel draft from DWT or cargo volume!
"""
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone, timedelta
import math

from app.models.enums import TidalWindowStatus


class TidalGateScheduler:
    """
    Computes tidal predictions and evaluates vessel passage feasibility for tidal ports.
    """
    # Known tidal ranges (mean high water springs, mean low water) in meters for key bulk ports
    PORT_TIDAL_CONSTANTS = {
        "HALDIA": {"mhw": 5.8, "mlw": 1.1, "cycle_hours": 12.4, "channel_depth_cd": 7.5, "is_strongly_tidal": True},
        "PARADIP": {"mhw": 2.8, "mlw": 0.4, "cycle_hours": 12.4, "channel_depth_cd": 17.1, "is_strongly_tidal": False},
        "DHAMRA": {"mhw": 4.5, "mlw": 0.8, "cycle_hours": 12.4, "channel_depth_cd": 18.0, "is_strongly_tidal": True},
        "VISAKHAPATNAM": {"mhw": 1.9, "mlw": 0.3, "cycle_hours": 12.4, "channel_depth_cd": 18.5, "is_strongly_tidal": False},
        "PORT_HEDLAND": {"mhw": 7.2, "mlw": 1.2, "cycle_hours": 12.2, "channel_depth_cd": 14.5, "is_strongly_tidal": True},
        "NEWCASTLE": {"mhw": 1.8, "mlw": 0.2, "cycle_hours": 12.5, "channel_depth_cd": 15.2, "is_strongly_tidal": False},
    }

    @classmethod
    def get_port_constants(cls, port_id: str, port_name: Optional[str] = None) -> Dict[str, Any]:
        key = (port_name or port_id or "").upper().replace(" ", "_")
        for k, v in cls.PORT_TIDAL_CONSTANTS.items():
            if k in key:
                return v
        return {"mhw": 2.5, "mlw": 0.5, "cycle_hours": 12.4, "channel_depth_cd": 14.0, "is_strongly_tidal": False}

    @classmethod
    def calculate_predicted_tide(
        cls,
        port_id: str,
        target_time: datetime,
        port_name: Optional[str] = None
    ) -> float:
        """
        Calculates harmonic sinusoidal tide height above Chart Datum (CD) at a specific time.
        """
        constants = cls.get_port_constants(port_id, port_name)
        mhw = constants["mhw"]
        mlw = constants["mlw"]
        mean_level = (mhw + mlw) / 2.0
        amplitude = (mhw - mlw) / 2.0
        
        # Semi-diurnal cycle (approx 12.4h per high tide)
        epoch = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        hours_since_epoch = (target_time - epoch).total_seconds() / 3600.0
        phase = (hours_since_epoch % constants["cycle_hours"]) / constants["cycle_hours"] * 2.0 * math.pi
        
        # Predicted height
        height = mean_level + amplitude * math.cos(phase)
        return round(height, 2)

    @classmethod
    def generate_tidal_windows(
        cls,
        port_id: str,
        start_time: datetime,
        days: int = 3,
        port_name: Optional[str] = None,
        berth_id: Optional[str] = None,
        berth_name: Optional[str] = None,
        berth_draft: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Generates high and low water tidal windows for planning over the given days.
        """
        constants = cls.get_port_constants(port_id, port_name)
        cycle_hours = constants["cycle_hours"]
        half_cycle = cycle_hours / 2.0
        windows = []

        total_hours = days * 24
        current_time = start_time

        step = 0
        while step * half_cycle < total_hours:
            event_time = start_time + timedelta(hours=step * half_cycle)
            is_high_water = (step % 2 == 0)
            
            tide_height = cls.calculate_predicted_tide(port_id, event_time, port_name)
            
            # Window duration for high water transit (approx 3 to 4 hours around HW)
            window_start = event_time - timedelta(hours=1.75)
            window_end = event_time + timedelta(hours=1.75)

            windows.append({
                "port_id": port_id,
                "port_name": port_name,
                "berth_id": berth_id,
                "berth_name": berth_name,
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
                "peak_water_time": event_time.isoformat(),
                "event_type": "HIGH_WATER" if is_high_water else "LOW_WATER",
                "predicted_tide_height_m": tide_height,
                "berth_depth_cd_m": berth_draft,
                "total_available_depth_m": round(berth_draft + tide_height, 2) if berth_draft is not None else None,
                "tidal_range_m": round(constants["mhw"] - constants["mlw"], 2),
                "is_strongly_tidal": constants["is_strongly_tidal"]
            })
            step += 1

        return windows

    @classmethod
    def evaluate_ukc_feasibility(
        cls,
        vessel_draft_m: Optional[float],
        berth_draft_m: Optional[float],
        port_id: str,
        arrival_time: Optional[datetime] = None,
        required_ukc_m: float = 0.5,
        port_name: Optional[str] = None,
        channel_draft_m: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluates UKC feasibility strictly according to physical depth rules.
        Never infers vessel draft from DWT or cargo!
        """
        # Strict UNKNOWN if either draft is missing
        if vessel_draft_m is None or vessel_draft_m <= 0:
            return {
                "status": TidalWindowStatus.UNKNOWN.value,
                "vessel_draft_m": None,
                "berth_draft_m": berth_draft_m,
                "required_depth_m": None,
                "available_depth_m": None,
                "ukc_margin_m": None,
                "high_water_slots": [],
                "explanation": "Vessel draft is unrecorded. Under Keel Clearance cannot be determined. In accordance with maritime safety rules, draft will not be inferred from DWT.",
                "mitigation": "Input verified hydrostatic arrival draft from vessel master or charter party."
            }

        effective_base_draft = berth_draft_m or channel_draft_m
        if effective_base_draft is None or effective_base_draft <= 0:
            return {
                "status": TidalWindowStatus.UNKNOWN.value,
                "vessel_draft_m": vessel_draft_m,
                "berth_draft_m": None,
                "required_depth_m": round(vessel_draft_m + required_ukc_m, 2),
                "available_depth_m": None,
                "ukc_margin_m": None,
                "high_water_slots": [],
                "explanation": "Port / Berth authorized chart datum draft is unrecorded. Cannot calculate tidal clearance.",
                "mitigation": "Confirm latest soundings and dredged chart depth with Port Harbor Master."
            }

        required_depth = round(vessel_draft_m + required_ukc_m, 2)
        constants = cls.get_port_constants(port_id, port_name)
        mhw = constants["mhw"]
        mlw = constants["mlw"]

        eval_time = arrival_time or datetime.now(timezone.utc)
        current_tide = cls.calculate_predicted_tide(port_id, eval_time, port_name)
        available_depth_current = round(effective_base_draft + current_tide, 2)
        ukc_margin_current = round(available_depth_current - required_depth, 2)

        available_depth_peak = round(effective_base_draft + mhw, 2)
        available_depth_low = round(effective_base_draft + mlw, 2)

        # Generate HW slots for the next 48 hours
        hw_windows = cls.generate_tidal_windows(
            port_id=port_id,
            start_time=eval_time,
            days=2,
            port_name=port_name,
            berth_draft=effective_base_draft
        )
        hw_slots = [w for w in hw_windows if w["event_type"] == "HIGH_WATER"]

        # 1. FAIL: Vessel draft exceeds maximum astronomical tide depth
        if available_depth_peak < required_depth:
            max_ukc_margin = round(available_depth_peak - required_depth, 2)
            return {
                "status": TidalWindowStatus.FAIL.value,
                "vessel_draft_m": vessel_draft_m,
                "berth_draft_m": effective_base_draft,
                "required_ukc_m": required_ukc_m,
                "required_depth_m": required_depth,
                "available_depth_m": available_depth_peak,
                "ukc_margin_m": max_ukc_margin,
                "high_water_slots": hw_slots,
                "explanation": (
                    f"Physical depth failure: Required depth {required_depth}m (draft {vessel_draft_m}m + UKC {required_ukc_m}m) "
                    f"exceeds maximum spring high water depth {available_depth_peak}m (base {effective_base_draft}m + MHW {mhw}m) "
                    f"by {abs(max_ukc_margin)}m. Vessel cannot berth or transit at this draft."
                ),
                "mitigation": "Lighter cargo at outer anchorage or nominate deep-water alternative terminal."
            }

        # 2. PASS: All-tide accessible (even at Mean Low Water)
        if available_depth_low >= required_depth:
            return {
                "status": TidalWindowStatus.PASS.value,
                "vessel_draft_m": vessel_draft_m,
                "berth_draft_m": effective_base_draft,
                "required_ukc_m": required_ukc_m,
                "required_depth_m": required_depth,
                "available_depth_m": available_depth_current,
                "ukc_margin_m": ukc_margin_current,
                "high_water_slots": hw_slots,
                "explanation": (
                    f"All-tide accessibility confirmed. At lowest water ({mlw}m CD), available depth {available_depth_low}m "
                    f"clears required depth {required_depth}m with {round(available_depth_low - required_depth, 2)}m UKC safety buffer."
                ),
                "mitigation": "Proceed with standard unconstrained pilotage booking."
            }

        # 3. CONDITIONAL: Tidal Gate required
        # Accessible only during High Water window
        next_passable_slot = None
        for slot in hw_slots:
            if slot["total_available_depth_m"] and slot["total_available_depth_m"] >= required_depth:
                next_passable_slot = slot
                break

        slot_label = f"{next_passable_slot['window_start'][11:16]} - {next_passable_slot['window_end'][11:16]} UTC" if next_passable_slot else "Next HW window"

        return {
            "status": TidalWindowStatus.CONDITIONAL.value,
            "vessel_draft_m": vessel_draft_m,
            "berth_draft_m": effective_base_draft,
            "required_ukc_m": required_ukc_m,
            "required_depth_m": required_depth,
            "available_depth_m": available_depth_current,
            "ukc_margin_m": ukc_margin_current,
            "high_water_slots": hw_slots,
            "recommended_window": next_passable_slot,
            "explanation": (
                f"Tidal gate dependency: Vessel draft {vessel_draft_m}m requires High Water tide assistance. "
                f"Low tide depth ({available_depth_low}m) is insufficient. "
                f"Transit clearance is CONDITIONAL upon riding high water slot ({slot_label})."
            ),
            "mitigation": f"Schedule pilot boarding strictly for High Water window ({slot_label}); alert vessel master to stand by engine."
        }
