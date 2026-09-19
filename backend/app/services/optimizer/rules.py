from typing import Tuple, Optional
from app.models.enums import FeasibilityStatus
from app.models.vessels import Vessel
from app.models.ports import Berth, Port

class BerthFeasibilityRule:
    rule_name: str
    is_blocking: bool
    unit: str = "m"

    def evaluate(self, vessel: Vessel, berth: Berth, port: Port) -> Tuple[FeasibilityStatus, Optional[float], Optional[float], Optional[float], str]:
        """
        Returns: (status, limit_value, vessel_value, margin, narrative)
        """
        raise NotImplementedError


class DraftConstraintRule(BerthFeasibilityRule):
    rule_name = "MAX_PERMISSIBLE_DRAFT"
    is_blocking = True
    unit = "m"

    def evaluate(self, vessel: Vessel, berth: Berth, port: Port) -> Tuple[FeasibilityStatus, Optional[float], Optional[float], Optional[float], str]:
        # Governing limit is the minimum of berth permissible draft and approach channel depth
        limits = [lim for lim in [berth.max_draft_m, port.channel_max_draft_m] if lim is not None]
        if not limits:
            return FeasibilityStatus.UNKNOWN, None, None, None, "Berth and channel permissible drafts are unrecorded."
        
        governing_limit = min(limits)
        
        if not vessel.particulars or vessel.particulars.summer_draft_m is None:
            return FeasibilityStatus.UNKNOWN, governing_limit, None, None, "Vessel laden/summer draft is not verified in particulars database."

        vessel_draft = vessel.particulars.summer_draft_m
        margin = governing_limit - vessel_draft

        if margin >= 0.5:
            return (
                FeasibilityStatus.PASS,
                governing_limit,
                vessel_draft,
                round(margin, 2),
                f"Full clearance of {margin:.2f}m complies with mandatory Under Keel Clearance (UKC ≥ 0.5m)."
            )
        elif margin >= 0.0:
            return (
                FeasibilityStatus.CONDITIONAL,
                governing_limit,
                vessel_draft,
                round(margin, 2),
                f"Marginal clearance ({margin:.2f}m). Requires high-tide entry (+{port.tide_range_m or 1.5:.1f}m tidal assistance) or partial lighterage."
            )
        else:
            return (
                FeasibilityStatus.FAIL,
                governing_limit,
                vessel_draft,
                round(margin, 2),
                f"Overdraft violation: Vessel draft ({vessel_draft:.2f}m) exceeds governing limit ({governing_limit:.2f}m) by {abs(margin):.2f}m."
            )


class LoaConstraintRule(BerthFeasibilityRule):
    rule_name = "MAX_PERMISSIBLE_LOA"
    is_blocking = True
    unit = "m"

    def evaluate(self, vessel: Vessel, berth: Berth, port: Port) -> Tuple[FeasibilityStatus, Optional[float], Optional[float], Optional[float], str]:
        limits = [lim for lim in [berth.max_loa_m, port.channel_max_loa_m] if lim is not None]
        if not limits:
            return FeasibilityStatus.UNKNOWN, None, None, None, "Max LOA limit not defined for berth/channel."

        governing_limit = min(limits)
        if not vessel.particulars or vessel.particulars.loa_m is None:
            return FeasibilityStatus.UNKNOWN, governing_limit, None, None, "Vessel LOA is unrecorded."

        vessel_loa = vessel.particulars.loa_m
        margin = governing_limit - vessel_loa

        if margin >= 0.0:
            return (
                FeasibilityStatus.PASS,
                governing_limit,
                vessel_loa,
                round(margin, 2),
                f"Vessel LOA ({vessel_loa:.1f}m) safely berths within quay limit ({governing_limit:.1f}m)."
            )
        else:
            return (
                FeasibilityStatus.FAIL,
                governing_limit,
                vessel_loa,
                round(margin, 2),
                f"LOA violation: Vessel length ({vessel_loa:.1f}m) exceeds berth mooring pocket ({governing_limit:.1f}m) by {abs(margin):.1f}m."
            )


class BeamConstraintRule(BerthFeasibilityRule):
    rule_name = "MAX_PERMISSIBLE_BEAM"
    is_blocking = True
    unit = "m"

    def evaluate(self, vessel: Vessel, berth: Berth, port: Port) -> Tuple[FeasibilityStatus, Optional[float], Optional[float], Optional[float], str]:
        limits = [lim for lim in [berth.max_beam_m, port.channel_max_beam_m] if lim is not None]
        if not limits:
            return FeasibilityStatus.UNKNOWN, None, None, None, "Max beam limit not defined."

        governing_limit = min(limits)
        if not vessel.particulars or vessel.particulars.beam_m is None:
            return FeasibilityStatus.UNKNOWN, governing_limit, None, None, "Vessel beam width is unrecorded."

        vessel_beam = vessel.particulars.beam_m
        margin = governing_limit - vessel_beam

        if margin >= 0.0:
            return (
                FeasibilityStatus.PASS,
                governing_limit,
                vessel_beam,
                round(margin, 2),
                f"Vessel beam ({vessel_beam:.1f}m) is within shore unloader outreach ({governing_limit:.1f}m)."
            )
        else:
            return (
                FeasibilityStatus.FAIL,
                governing_limit,
                vessel_beam,
                round(margin, 2),
                f"Beam violation: Vessel width ({vessel_beam:.1f}m) exceeds crane outreach limit ({governing_limit:.1f}m)."
            )


class BerthCargoCompatibilityRule(BerthFeasibilityRule):
    rule_name = "BERTH_CARGO_TYPE"
    is_blocking = True
    unit = "type"

    def evaluate(self, vessel: Vessel, berth: Berth, port: Port) -> Tuple[FeasibilityStatus, Optional[float], Optional[float], Optional[float], str]:
        b_type = berth.berth_type.upper()
        if any(term in b_type for term in ["COAL", "BULK", "MULTIPURPOSE", "GENERAL"]):
            return (
                FeasibilityStatus.PASS,
                None,
                None,
                None,
                f"Berth facility '{berth.berth_type}' is designated for dry bulk & coking coal operations."
            )
        else:
            return (
                FeasibilityStatus.FAIL,
                None,
                None,
                None,
                f"Berth type '{berth.berth_type}' is not equipped for dry bulk/coal discharge."
            )
