"""
Vessel Employment State Machine
States:
- EMPLOYED: Vessel under active charter party / laden voyage transit.
- VOYAGE_COMPLETING: Vessel approaching discharge port or actively discharging.
- AVAILABLE: Vessel open for employment; charter completed.
- NEXT_EMPLOYMENT_PENDING: Vessel fixed or scheduled for next fixture.
- IDLE_RISK: Vessel open or completing without verified next employment within prompt window.
- IDLE: Vessel idle beyond prompt threshold without commercial employment.
- REPOSITIONING: Vessel in ballast transit repositioning toward load port / market area.
- ALTERNATIVE_EMPLOYMENT: Vessel evaluating or engaged in alternative mitigating cargo.
- UNKNOWN: Insufficient evidence or unverified vessel records.
"""
from typing import Optional, Set, Tuple
from datetime import datetime, timezone
from app.models.enums import VesselEmploymentState, VesselStatus

VALID_TRANSITIONS: dict[VesselEmploymentState, Set[VesselEmploymentState]] = {
    VesselEmploymentState.EMPLOYED: {
        VesselEmploymentState.VOYAGE_COMPLETING,
        VesselEmploymentState.UNKNOWN,
    },
    VesselEmploymentState.VOYAGE_COMPLETING: {
        VesselEmploymentState.AVAILABLE,
        VesselEmploymentState.UNKNOWN,
    },
    VesselEmploymentState.AVAILABLE: {
        VesselEmploymentState.NEXT_EMPLOYMENT_PENDING,
        VesselEmploymentState.IDLE_RISK,
        VesselEmploymentState.IDLE,
        VesselEmploymentState.REPOSITIONING,
        VesselEmploymentState.ALTERNATIVE_EMPLOYMENT,
        VesselEmploymentState.UNKNOWN,
    },
    VesselEmploymentState.NEXT_EMPLOYMENT_PENDING: {
        VesselEmploymentState.REPOSITIONING,
        VesselEmploymentState.EMPLOYED,
        VesselEmploymentState.AVAILABLE,
        VesselEmploymentState.IDLE_RISK,
        VesselEmploymentState.UNKNOWN,
    },
    VesselEmploymentState.IDLE_RISK: {
        VesselEmploymentState.IDLE,
        VesselEmploymentState.NEXT_EMPLOYMENT_PENDING,
        VesselEmploymentState.REPOSITIONING,
        VesselEmploymentState.ALTERNATIVE_EMPLOYMENT,
        VesselEmploymentState.UNKNOWN,
    },
    VesselEmploymentState.IDLE: {
        VesselEmploymentState.NEXT_EMPLOYMENT_PENDING,
        VesselEmploymentState.REPOSITIONING,
        VesselEmploymentState.ALTERNATIVE_EMPLOYMENT,
        VesselEmploymentState.UNKNOWN,
    },
    VesselEmploymentState.REPOSITIONING: {
        VesselEmploymentState.EMPLOYED,
        VesselEmploymentState.AVAILABLE,
        VesselEmploymentState.IDLE,
        VesselEmploymentState.UNKNOWN,
    },
    VesselEmploymentState.ALTERNATIVE_EMPLOYMENT: {
        VesselEmploymentState.REPOSITIONING,
        VesselEmploymentState.EMPLOYED,
        VesselEmploymentState.AVAILABLE,
        VesselEmploymentState.UNKNOWN,
    },
    VesselEmploymentState.UNKNOWN: {
        VesselEmploymentState.EMPLOYED,
        VesselEmploymentState.VOYAGE_COMPLETING,
        VesselEmploymentState.AVAILABLE,
        VesselEmploymentState.NEXT_EMPLOYMENT_PENDING,
        VesselEmploymentState.IDLE_RISK,
        VesselEmploymentState.IDLE,
        VesselEmploymentState.REPOSITIONING,
        VesselEmploymentState.ALTERNATIVE_EMPLOYMENT,
    },
}


class EmploymentStateMachine:
    @staticmethod
    def is_transition_valid(
        current_state: VesselEmploymentState,
        target_state: VesselEmploymentState
    ) -> bool:
        if current_state == target_state:
            return True
        allowed = VALID_TRANSITIONS.get(current_state, set())
        return target_state in allowed

    @staticmethod
    def evaluate_state(
        vessel_status: Optional[VesselStatus],
        is_verified_particulars: bool,
        has_current_voyage: bool,
        voyage_completion_date: Optional[datetime],
        next_employment_confirmed: bool,
        idle_days_observed: Optional[float],
        is_ballasting_for_cargo: bool = False,
        now: Optional[datetime] = None
    ) -> Tuple[VesselEmploymentState, str]:
        """
        Determines the evidence-driven employment state for a vessel.
        Never infers state without supporting evidence.
        """
        if now is None:
            now = datetime.now(timezone.utc)

        # Incomplete or unverified records must resolve to UNKNOWN
        if not is_verified_particulars and vessel_status == VesselStatus.WAITING_ORDERS:
            return (
                VesselEmploymentState.UNKNOWN,
                "Vessel particulars unverified and status lacks confirmed schedule records."
            )

        if vessel_status is None:
            return (
                VesselEmploymentState.UNKNOWN,
                "Vessel tracking status is not available."
            )

        # Repositioning check
        if is_ballasting_for_cargo or (vessel_status == VesselStatus.BALLAST_TRANSIT and next_employment_confirmed):
            return (
                VesselEmploymentState.REPOSITIONING,
                "Vessel is steaming under ballast to position for scheduled loading."
            )

        # Active Voyage Check
        if has_current_voyage or vessel_status == VesselStatus.LADEN_TRANSIT:
            if voyage_completion_date:
                # Normalize tz
                v_comp = voyage_completion_date if voyage_completion_date.tzinfo else voyage_completion_date.replace(tzinfo=timezone.utc)
                remaining_hours = (v_comp - now).total_seconds() / 3600.0
                if remaining_hours <= 72.0:
                    return (
                        VesselEmploymentState.VOYAGE_COMPLETING,
                        f"Laden transit completing within {round(remaining_hours, 1)} hours."
                    )
            return (
                VesselEmploymentState.EMPLOYED,
                "Vessel under active laden voyage transit."
            )

        # Discharging / At Berth
        if vessel_status == VesselStatus.BERTHED_DISCHARGING:
            return (
                VesselEmploymentState.VOYAGE_COMPLETING,
                "Vessel currently at berth discharging cargo."
            )

        # Anchorage Waiting
        if vessel_status == VesselStatus.AT_ANCHORAGE:
            if next_employment_confirmed:
                return (
                    VesselEmploymentState.NEXT_EMPLOYMENT_PENDING,
                    "Vessel at anchorage awaiting next scheduled loading orders."
                )
            if idle_days_observed is not None and idle_days_observed > 3.0:
                return (
                    VesselEmploymentState.IDLE,
                    f"Vessel idle at anchorage for {round(idle_days_observed, 1)} days without employment."
                )
            return (
                VesselEmploymentState.IDLE_RISK,
                "Vessel at anchorage without confirmed subsequent employment."
            )

        # Available / Open
        if next_employment_confirmed:
            return (
                VesselEmploymentState.NEXT_EMPLOYMENT_PENDING,
                "Vessel open with confirmed next employment fixture pending."
            )

        if idle_days_observed is not None and idle_days_observed > 3.0:
            return (
                VesselEmploymentState.IDLE,
                f"Vessel has exceeded prompt availability threshold by {round(idle_days_observed, 1)} days."
            )

        return (
            VesselEmploymentState.IDLE_RISK,
            "Vessel available or approaching availability with no confirmed next charter party."
        )
