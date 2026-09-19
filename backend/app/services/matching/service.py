import uuid
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.matching import VesselMatchRun, VesselMatchCandidate, VesselMatchRuleResult
from app.models.vessels import Vessel
from app.models.cargo import CargoRequirement
from app.models.enums import MatchStatus
from app.services.matching.rules import (
    CapacityRule,
    LaycanTimingRule,
    VesselClassPreferenceRule,
    VesselAgeRule,
    GearRequirementRule,
)
from app.repositories.matching_repo import MatchingRepository
from app.repositories.vessel_repo import VesselRepository
from app.repositories.cargo_repo import CargoRepository

class VesselMatchingService:
    def __init__(self, db: Session):
        self.db = db
        self.matching_repo = MatchingRepository(db)
        self.vessel_repo = VesselRepository(db)
        self.cargo_repo = CargoRepository(db)
        
        # Instantiate rules
        self.rules = [
            CapacityRule(),
            LaycanTimingRule(),
            VesselClassPreferenceRule(),
            VesselAgeRule(),
            GearRequirementRule(),
        ]

    def execute_matching_run(
        self,
        requirement_id: str,
        candidate_vessel_ids: Optional[List[str]] = None
    ) -> VesselMatchRun:
        requirement = self.cargo_repo.get_requirement_by_id(requirement_id)
        if not requirement:
            raise ValueError(f"Requirement with id {requirement_id} not found")

        # Fetch candidate vessels
        if candidate_vessel_ids and len(candidate_vessel_ids) > 0:
            vessels = [
                self.vessel_repo.get_vessel_by_id(vid)
                for vid in candidate_vessel_ids
                if self.vessel_repo.get_vessel_by_id(vid)
            ]
        else:
            vessels = self.vessel_repo.get_all_vessels()

        run_id = str(uuid.uuid4())
        match_run = VesselMatchRun(
            id=run_id,
            requirement_id=requirement_id,
            run_timestamp=datetime.now(timezone.utc),
            total_evaluated=len(vessels),
            relevant_count=0,
            partial_count=0,
            not_relevant_count=0,
            unknown_count=0,
        )

        candidates = []
        for vessel in vessels:
            candidate_id = str(uuid.uuid4())
            rule_results = []
            
            has_blocking_failure = False
            has_unknown = False
            has_partial = False
            missing_fields = []
            
            if not vessel.particulars or vessel.particulars.summer_dwt is None:
                missing_fields.append("summer_dwt")
            if not vessel.availability or not vessel.availability.open_date_start:
                missing_fields.append("open_window")

            for rule in self.rules:
                status, eval_val, req_val, expl = rule.evaluate(vessel, requirement)
                
                if status == MatchStatus.NOT_RELEVANT and rule.is_blocking:
                    has_blocking_failure = True
                elif status == MatchStatus.UNKNOWN:
                    has_unknown = True
                elif status == MatchStatus.PARTIAL:
                    has_partial = True

                rule_res = VesselMatchRuleResult(
                    id=str(uuid.uuid4()),
                    candidate_id=candidate_id,
                    rule_name=rule.rule_name,
                    rule_category=rule.rule_category,
                    status=status,
                    evaluated_value=eval_val,
                    required_value=req_val,
                    explanation=expl,
                    is_blocking=rule.is_blocking
                )
                rule_results.append(rule_res)

            # Overall status synthesis
            if has_blocking_failure:
                overall_status = MatchStatus.NOT_RELEVANT
                match_run.not_relevant_count += 1
                summary = "Disqualified by blocking technical or commercial constraints."
            elif has_unknown and ("summer_dwt" in missing_fields or "open_window" in missing_fields):
                overall_status = MatchStatus.UNKNOWN
                match_run.unknown_count += 1
                summary = f"Cannot confirm feasibility due to unverified vessel parameters: {', '.join(missing_fields)}."
            elif has_partial:
                overall_status = MatchStatus.PARTIAL
                match_run.partial_count += 1
                summary = "Candidate satisfies core parameters with minor operational or schedule variances."
            else:
                overall_status = MatchStatus.RELEVANT
                match_run.relevant_count += 1
                summary = "Full technical, volumetric, and laycan alignment with requisition."

            candidate = VesselMatchCandidate(
                id=candidate_id,
                match_run_id=run_id,
                vessel_id=vessel.id,
                overall_status=overall_status,
                summary_explanation=summary,
                is_data_complete=(len(missing_fields) == 0),
                missing_fields=", ".join(missing_fields) if missing_fields else None,
                rule_results=rule_results
            )
            candidates.append(candidate)

        match_run.candidates = candidates
        return self.matching_repo.save_match_run(match_run)
