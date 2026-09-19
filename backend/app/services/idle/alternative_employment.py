"""
Alternative Employment Service
Identifies and evaluates verified cargo opportunities from cargo_requirements
to resolve idle exposure or ballast positioning.

STRICT INTEGRITY & INTEGRATION:
- Integrates Phase 3 Vessel Matching Rules (Capacity, Laycan, Vessel Class, Gear, Age).
- Integrates Phase 4 Vessel-Port Validation (Draft, LOA, Beam, Berth Facilities) for both load and discharge ports.
- Candidate states: COMPATIBLE, PARTIAL, NOT_COMPATIBLE, UNKNOWN.
- Never treats UNKNOWN as PASS.
- Never creates fake cargo opportunities.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.vessels import Vessel
from app.models.cargo import CargoRequirement
from app.models.ports import Port
from app.models.enums import EmploymentCompatibility, MatchStatus, FeasibilityStatus
from app.services.matching.rules import (
    CapacityRule,
    LaycanTimingRule,
    VesselClassPreferenceRule,
    VesselAgeRule,
    GearRequirementRule,
)
from app.services.optimizer.service import VesselPortOptimizerService
from app.services.idle.distance_service import RouteDistanceService


class AlternativeEmploymentCandidate:
    def __init__(
        self,
        cargo_requirement: CargoRequirement,
        compatibility_status: EmploymentCompatibility,
        matching_status: MatchStatus,
        origin_port_status: FeasibilityStatus,
        destination_port_status: FeasibilityStatus,
        repositioning_required: bool,
        repositioning_distance_nm: Optional[float],
        distance_method: str,
        matching_summary: str,
        port_validation_summary: str,
        is_data_complete: bool,
        missing_fields: Optional[str] = None
    ):
        self.cargo_requirement = cargo_requirement
        self.compatibility_status = compatibility_status
        self.matching_status = matching_status
        self.origin_port_status = origin_port_status
        self.destination_port_status = destination_port_status
        self.repositioning_required = repositioning_required
        self.repositioning_distance_nm = repositioning_distance_nm
        self.distance_method = distance_method
        self.matching_summary = matching_summary
        self.port_validation_summary = port_validation_summary
        self.is_data_complete = is_data_complete
        self.missing_fields = missing_fields

    def to_dict(self) -> Dict[str, Any]:
        cr = self.cargo_requirement
        return {
            "cargo_id": cr.id,
            "cargo_name": cr.cargo_type.value if hasattr(cr.cargo_type, "value") else str(cr.cargo_type),
            "quantity_mt": cr.quantity_mt,
            "origin_port_id": cr.load_port_id,
            "origin_port_name": cr.load_port.name if cr.load_port else "Unknown",
            "destination_port_id": cr.discharge_port_id,
            "destination_port_name": cr.discharge_port.name if cr.discharge_port else "Unknown",
            "laycan_start": cr.laycan_start.isoformat() if cr.laycan_start else None,
            "laycan_end": cr.laycan_end.isoformat() if cr.laycan_end else None,
            "compatibility_status": self.compatibility_status.value,
            "matching_status": self.matching_status.value,
            "origin_port_status": self.origin_port_status.value,
            "destination_port_status": self.destination_port_status.value,
            "repositioning_required": self.repositioning_required,
            "repositioning_distance_nm": self.repositioning_distance_nm,
            "distance_method": self.distance_method,
            "matching_summary": self.matching_summary,
            "port_validation_summary": self.port_validation_summary,
            "is_data_complete": self.is_data_complete,
            "missing_fields": self.missing_fields,
            "data_status": "RECENT" if self.is_data_complete else "SYNTHETIC"
        }


class AlternativeEmploymentService:
    def __init__(self, db: Session):
        self.db = db
        self.port_optimizer = VesselPortOptimizerService(db)
        self.distance_service = RouteDistanceService()
        self.matching_rules = [
            CapacityRule(),
            LaycanTimingRule(),
            VesselClassPreferenceRule(),
            VesselAgeRule(),
            GearRequirementRule(),
        ]

    def find_candidates_for_vessel(
        self,
        vessel_id: str,
        current_port_id: Optional[str] = None
    ) -> List[AlternativeEmploymentCandidate]:
        vessel = self.db.query(Vessel).filter(Vessel.id == vessel_id).first()
        if not vessel:
            raise ValueError(f"Vessel with id {vessel_id} not found.")

        # Resolve current port if not passed
        curr_port = None
        if current_port_id:
            curr_port = self.db.query(Port).filter(Port.id == current_port_id).first()
        elif vessel.availability and vessel.availability.open_port_name:
            curr_port = self.db.query(Port).filter(
                Port.name.ilike(f"%{vessel.availability.open_port_name.split()[0]}%")
            ).first()

        # Query actual cargo requirements
        open_cargos = self.db.query(CargoRequirement).all()
        candidates: List[AlternativeEmploymentCandidate] = []

        missing_fields = []
        if not vessel.particulars or vessel.particulars.summer_dwt is None:
            missing_fields.append("summer_dwt")
        if not vessel.particulars or vessel.particulars.summer_draft_m is None:
            missing_fields.append("summer_draft_m")
        if not vessel.particulars or vessel.particulars.loa_m is None:
            missing_fields.append("loa_m")
        if not vessel.availability or not vessel.availability.open_date_start:
            missing_fields.append("open_window")

        for req in open_cargos:
            # 1. Phase 3 Matching Rules Evaluation
            has_blocking_matching_failure = False
            has_unknown_matching = False
            has_partial_matching = False

            for rule in self.matching_rules:
                status, _, _, _ = rule.evaluate(vessel, req)
                if status == MatchStatus.NOT_RELEVANT and rule.is_blocking:
                    has_blocking_matching_failure = True
                elif status == MatchStatus.UNKNOWN:
                    has_unknown_matching = True
                elif status == MatchStatus.PARTIAL:
                    has_partial_matching = True

            if has_blocking_matching_failure:
                match_status = MatchStatus.NOT_RELEVANT
                match_summary = "Disqualified: Vessel violates cargo technical or laycan constraints."
            elif has_unknown_matching or len(missing_fields) > 0:
                match_status = MatchStatus.UNKNOWN
                match_summary = f"Cannot confirm compatibility due to unverified vessel particulars: {', '.join(missing_fields)}."
            elif has_partial_matching:
                match_status = MatchStatus.PARTIAL
                match_summary = "Operational or schedule tolerances required for cargo fixture."
            else:
                match_status = MatchStatus.RELEVANT
                match_summary = "Fully compatible with cargo tonnage, laycan, and class specifications."

            # 2. Phase 4 Port Feasibility Check (Load Port & Discharge Port)
            origin_port = req.load_port
            dest_port = req.discharge_port

            # Check Origin Port (Load Port)
            orig_status = FeasibilityStatus.UNKNOWN
            if origin_port:
                orig_run = self.port_optimizer.evaluate_feasibility(
                    vessel_id=vessel.id,
                    port_id=origin_port.id,
                    cargo_quantity_mt=req.quantity_mt
                )
                orig_status = orig_run.overall_status

            # Check Destination Port (Discharge Port)
            dest_status = FeasibilityStatus.UNKNOWN
            if dest_port:
                dest_run = self.port_optimizer.evaluate_feasibility(
                    vessel_id=vessel.id,
                    port_id=dest_port.id,
                    cargo_quantity_mt=req.quantity_mt
                )
                dest_status = dest_run.overall_status

            # 3. Synthesize Candidate Status
            port_reasons = []
            if orig_status == FeasibilityStatus.FAIL:
                port_reasons.append(f"Load port ({origin_port.name if origin_port else 'Origin'}) rejects vessel constraints.")
            if dest_status == FeasibilityStatus.FAIL:
                port_reasons.append(f"Discharge port ({dest_port.name if dest_port else 'Destination'}) rejects vessel constraints.")

            if orig_status == FeasibilityStatus.UNKNOWN or dest_status == FeasibilityStatus.UNKNOWN:
                port_reasons.append("Port berth particulars unverified for vessel dimensions.")

            port_summary = " ".join(port_reasons) if port_reasons else "Both load and discharge ports pass physical berth clearances."

            # Determine Overall Candidate Compatibility
            if (
                match_status == MatchStatus.NOT_RELEVANT or
                orig_status == FeasibilityStatus.FAIL or
                dest_status == FeasibilityStatus.FAIL
            ):
                overall_compat = EmploymentCompatibility.NOT_COMPATIBLE
            elif (
                match_status == MatchStatus.UNKNOWN or
                orig_status == FeasibilityStatus.UNKNOWN or
                dest_status == FeasibilityStatus.UNKNOWN
            ):
                overall_compat = EmploymentCompatibility.UNKNOWN
            elif (
                match_status == MatchStatus.PARTIAL or
                orig_status == FeasibilityStatus.CONDITIONAL or
                dest_status == FeasibilityStatus.CONDITIONAL
            ):
                overall_compat = EmploymentCompatibility.PARTIAL
            else:
                overall_compat = EmploymentCompatibility.COMPATIBLE

            # 4. Ballast Repositioning Requirement
            repo_required = False
            dist_nm = None
            dist_method = "UNAVAILABLE"

            if curr_port and origin_port:
                if curr_port.id != origin_port.id:
                    repo_required = True
                    dist_nm, dist_method, _ = self.distance_service.get_distance(
                        curr_port, origin_port, db=self.db
                    )
                else:
                    repo_required = False
                    dist_nm = 0.0
                    dist_method = "SAME_PORT"
            elif origin_port:
                repo_required = True
                dist_method = "UNKNOWN_ORIGIN"

            candidate = AlternativeEmploymentCandidate(
                cargo_requirement=req,
                compatibility_status=overall_compat,
                matching_status=match_status,
                origin_port_status=orig_status,
                destination_port_status=dest_status,
                repositioning_required=repo_required,
                repositioning_distance_nm=dist_nm,
                distance_method=dist_method,
                matching_summary=match_summary,
                port_validation_summary=port_summary,
                is_data_complete=(len(missing_fields) == 0 and dist_nm is not None),
                missing_fields=", ".join(missing_fields) if missing_fields else None
            )
            candidates.append(candidate)

        return candidates
