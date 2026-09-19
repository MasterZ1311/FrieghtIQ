from datetime import datetime, timezone
from typing import Tuple, Optional, List
from app.models.enums import MatchStatus, VesselClass
from app.models.vessels import Vessel
from app.models.cargo import CargoRequirement

class MatchingRule:
    rule_name: str
    rule_category: str
    is_blocking: bool

    def evaluate(self, vessel: Vessel, requirement: CargoRequirement) -> Tuple[MatchStatus, Optional[str], Optional[str], str]:
        """
        Returns: (status, evaluated_value, required_value, explanation)
        """
        raise NotImplementedError


class CapacityRule(MatchingRule):
    rule_name = "CARGO_CAPACITY"
    rule_category = "CAPACITY"
    is_blocking = True

    def evaluate(self, vessel: Vessel, requirement: CargoRequirement) -> Tuple[MatchStatus, Optional[str], Optional[str], str]:
        req_qty = requirement.quantity_mt
        req_val_str = f"{req_qty:,.0f} MT (±{requirement.tolerance_pct}%)"
        
        if not vessel.particulars or vessel.particulars.summer_dwt is None:
            return (
                MatchStatus.UNKNOWN,
                "UNKNOWN",
                req_val_str,
                "Vessel deadweight (DWT) is not verified in master database. Observed handling records reflect parcel size, not vessel capacity."
            )
        
        dwt = vessel.particulars.summer_dwt
        eval_str = f"{dwt:,.0f} DWT"
        
        # Lower bound: vessel must accommodate minimum cargo parcel
        min_cargo = req_qty * (1.0 - requirement.tolerance_pct / 100.0)
        # Upper bound: vessel should not be disproportionately oversized (e.g. Capesize for a 50k parcel)
        max_economic_dwt = req_qty * 1.50
        
        if dwt < min_cargo:
            return (
                MatchStatus.NOT_RELEVANT,
                eval_str,
                req_val_str,
                f"Vessel summer DWT ({dwt:,.0f} MT) is insufficient for required parcel ({min_cargo:,.0f} MT min)."
            )
        elif dwt > max_economic_dwt:
            return (
                MatchStatus.PARTIAL,
                eval_str,
                req_val_str,
                f"Vessel DWT ({dwt:,.0f} MT) is significantly larger than parcel requirement ({req_qty:,.0f} MT). Partial parcel or deadfreight risk."
            )
        else:
            return (
                MatchStatus.RELEVANT,
                eval_str,
                req_val_str,
                f"Vessel DWT ({dwt:,.0f} MT) is well matched to required shipment parcel ({req_qty:,.0f} MT)."
            )


class VesselClassPreferenceRule(MatchingRule):
    rule_name = "VESSEL_CLASS_FIT"
    rule_category = "CLASSIFICATION"
    is_blocking = False

    def evaluate(self, vessel: Vessel, requirement: CargoRequirement) -> Tuple[MatchStatus, Optional[str], Optional[str], str]:
        preferred_classes = [c.strip().upper() for c in requirement.preferred_vessel_classes.split(",") if c.strip()]
        vessel_class_str = vessel.vessel_class.value if vessel.vessel_class else "UNKNOWN"
        pref_str = ", ".join(preferred_classes)

        if not preferred_classes or vessel_class_str in preferred_classes:
            return (
                MatchStatus.RELEVANT,
                vessel_class_str,
                pref_str,
                f"Vessel class {vessel_class_str} strictly matches chartering requisition preferences."
            )
        else:
            # Adjacent classes may be partially relevant
            return (
                MatchStatus.PARTIAL,
                vessel_class_str,
                pref_str,
                f"Vessel class {vessel_class_str} is acceptable as an operational alternate, but not in primary target classes ({pref_str})."
            )


class LaycanTimingRule(MatchingRule):
    rule_name = "LAYCAN_TIMING"
    rule_category = "TIMING"
    is_blocking = True

    def evaluate(self, vessel: Vessel, requirement: CargoRequirement) -> Tuple[MatchStatus, Optional[str], Optional[str], str]:
        laycan_start = requirement.laycan_start
        laycan_end = requirement.laycan_end
        req_str = f"{laycan_start.strftime('%d %b %Y')} – {laycan_end.strftime('%d %b %Y')}"
        
        if not vessel.availability or not vessel.availability.open_date_start:
            return (
                MatchStatus.UNKNOWN,
                "UNKNOWN",
                req_str,
                "Vessel open window/ETA is unconfirmed in market reports."
            )
        
        open_start = vessel.availability.open_date_start
        open_end = vessel.availability.open_date_end or open_start
        eval_str = f"{open_start.strftime('%d %b %Y')} – {open_end.strftime('%d %b %Y')}"
        
        # If open window overlaps with laycan window
        if open_start <= laycan_end and open_end >= laycan_start:
            return (
                MatchStatus.RELEVANT,
                eval_str,
                req_str,
                "Vessel open readiness overlaps directly with charterers' laycan window."
            )
        
        # Calculate deviation in days
        start_delta = abs((open_start - laycan_start).days)
        if start_delta <= 4:
            return (
                MatchStatus.PARTIAL,
                eval_str,
                req_str,
                f"Vessel ETA is within ±{start_delta} days of laycan window. Subject to voyage speed adjustment."
            )
        else:
            return (
                MatchStatus.NOT_RELEVANT,
                eval_str,
                req_str,
                f"Vessel open readiness deviates substantially ({start_delta} days) from required laycan."
            )


class VesselAgeRule(MatchingRule):
    rule_name = "VESSEL_AGE"
    rule_category = "VETTING"
    is_blocking = False

    def evaluate(self, vessel: Vessel, requirement: CargoRequirement) -> Tuple[MatchStatus, Optional[str], Optional[str], str]:
        max_age = requirement.max_vessel_age_years
        req_str = f"≤ {max_age} Years"
        
        if not vessel.year_built:
            return (
                MatchStatus.UNKNOWN,
                "UNKNOWN",
                req_str,
                "Vessel build year is not recorded in vessel database."
            )
        
        current_year = datetime.now(timezone.utc).year
        age = current_year - vessel.year_built
        eval_str = f"{age} Years ({vessel.year_built})"
        
        if age <= max_age:
            return (
                MatchStatus.RELEVANT,
                eval_str,
                req_str,
                f"Vessel age ({age} yrs) complies with SAIL vetting policy (≤ {max_age} yrs)."
            )
        elif age <= max_age + 5:
            return (
                MatchStatus.PARTIAL,
                eval_str,
                req_str,
                f"Vessel age ({age} yrs) exceeds standard limit ({max_age} yrs). Over-age insurance premium (OAP) required."
            )
        else:
            return (
                MatchStatus.NOT_RELEVANT,
                eval_str,
                req_str,
                f"Vessel age ({age} yrs) severely exceeds commercial vetting limits."
            )


class GearRequirementRule(MatchingRule):
    rule_name = "GEAR_SPECIFICATION"
    rule_category = "EQUIPMENT"
    is_blocking = False

    def evaluate(self, vessel: Vessel, requirement: CargoRequirement) -> Tuple[MatchStatus, Optional[str], Optional[str], str]:
        req_gear = requirement.gear_requirement.upper()
        req_str = req_gear
        
        if req_gear in ["ANY", "NONE"]:
            return (
                MatchStatus.RELEVANT,
                vessel.particulars.gear_summary if vessel.particulars else "Gearless",
                req_str,
                "Charterer accepts both geared and gearless tonnage."
            )
        
        if not vessel.particulars or not vessel.particulars.gear_summary:
            return (
                MatchStatus.UNKNOWN,
                "UNKNOWN",
                req_str,
                "Vessel onboard gear particulars are unverified."
            )
        
        gear_str = vessel.particulars.gear_summary.upper()
        is_geared = "CRANE" in gear_str or "DERRICK" in gear_str
        
        if req_gear == "GEARED" and is_geared:
            return (
                MatchStatus.RELEVANT,
                vessel.particulars.gear_summary,
                req_str,
                "Vessel is equipped with self-discharging cranes/grabs as requested."
            )
        elif req_gear == "GEARLESS" and not is_geared:
            return (
                MatchStatus.RELEVANT,
                "Gearless",
                req_str,
                "Vessel is gearless, optimal for shore grab unloader discharge."
            )
        elif req_gear == "GEARED" and not is_geared:
            return (
                MatchStatus.NOT_RELEVANT,
                "Gearless",
                req_str,
                "Requisition strictly requires self-geared vessel for unequipped berths."
            )
        else:
            return (
                MatchStatus.PARTIAL,
                vessel.particulars.gear_summary,
                req_str,
                "Vessel gear configuration partially differs from requisition baseline."
            )
