import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.optimizer import FeasibilityRun, FeasibilityBerthResult, FeasibilityRuleEvaluation
from app.models.enums import FeasibilityStatus
from app.models.vessels import Vessel
from app.models.ports import Port, Berth
from app.services.optimizer.rules import (
    DraftConstraintRule,
    LoaConstraintRule,
    BeamConstraintRule,
    BerthCargoCompatibilityRule,
)
from app.repositories.optimizer_repo import OptimizerRepository
from app.repositories.vessel_repo import VesselRepository
from app.repositories.port_repo import PortRepository

class VesselPortOptimizerService:
    def __init__(self, db: Session):
        self.db = db
        self.optimizer_repo = OptimizerRepository(db)
        self.vessel_repo = VesselRepository(db)
        self.port_repo = PortRepository(db)
        
        self.rules = [
            DraftConstraintRule(),
            LoaConstraintRule(),
            BeamConstraintRule(),
            BerthCargoCompatibilityRule(),
        ]

    def evaluate_feasibility(
        self,
        vessel_id: str,
        port_id: str,
        cargo_quantity_mt: Optional[float] = 75000.0
    ) -> FeasibilityRun:
        vessel = self.vessel_repo.get_vessel_by_id(vessel_id)
        if not vessel:
            raise ValueError(f"Vessel with id {vessel_id} not found")

        port = self.port_repo.get_port_by_id(port_id)
        if not port:
            raise ValueError(f"Port with id {port_id} not found")

        run_id = str(uuid.uuid4())
        feasibility_run = FeasibilityRun(
            id=run_id,
            vessel_id=vessel_id,
            port_id=port_id,
            run_timestamp=datetime.now(timezone.utc),
            evaluated_berths_count=len(port.berths),
            passing_berths_count=0,
            overall_status=FeasibilityStatus.UNKNOWN
        )

        berth_results = []
        has_passing = False
        has_conditional = False
        has_unknown = False

        for berth in port.berths:
            b_res_id = str(uuid.uuid4())
            rule_evals = []
            
            b_failed = False
            b_unknown = False
            b_conditional = False
            
            draft_clearance = None
            loa_clearance = None
            beam_clearance = None

            for rule in self.rules:
                status, lim_val, ves_val, margin, narrative = rule.evaluate(vessel, berth, port)
                
                if rule.rule_name == "MAX_PERMISSIBLE_DRAFT":
                    draft_clearance = margin
                elif rule.rule_name == "MAX_PERMISSIBLE_LOA":
                    loa_clearance = margin
                elif rule.rule_name == "MAX_PERMISSIBLE_BEAM":
                    beam_clearance = margin

                if status == FeasibilityStatus.FAIL and rule.is_blocking:
                    b_failed = True
                elif status == FeasibilityStatus.UNKNOWN:
                    b_unknown = True
                elif status == FeasibilityStatus.CONDITIONAL:
                    b_conditional = True

                eval_record = FeasibilityRuleEvaluation(
                    id=str(uuid.uuid4()),
                    berth_result_id=b_res_id,
                    rule_name=rule.rule_name,
                    status=status,
                    limit_value=lim_val,
                    vessel_value=ves_val,
                    unit=rule.unit,
                    margin=margin,
                    is_blocking=rule.is_blocking,
                    narrative=narrative
                )
                rule_evals.append(eval_record)

            # Determine berth status
            if b_failed:
                berth_status = FeasibilityStatus.FAIL
                expl = "Berth rejected due to draft, LOA, or equipment limitations."
            elif b_unknown:
                berth_status = FeasibilityStatus.UNKNOWN
                expl = "Feasibility unverified: Vessel particulars lack verified dimension records."
            elif b_conditional:
                berth_status = FeasibilityStatus.CONDITIONAL
                expl = "Conditional acceptance: Tidal window scheduling or lighterage required."
                has_conditional = True
            else:
                berth_status = FeasibilityStatus.PASS
                expl = "Full operational clearance across draft, LOA, beam, and cargo handling facilities."
                has_passing = True
                feasibility_run.passing_berths_count += 1

            # Turnaround estimation
            est_days = None
            if cargo_quantity_mt and berth.discharge_rate_tpd and berth.discharge_rate_tpd > 0:
                est_days = round((cargo_quantity_mt / berth.discharge_rate_tpd) + 0.5, 1)

            berth_result = FeasibilityBerthResult(
                id=b_res_id,
                feasibility_run_id=run_id,
                berth_id=berth.id,
                status=berth_status,
                draft_clearance_m=draft_clearance,
                loa_clearance_m=loa_clearance,
                beam_clearance_m=beam_clearance,
                estimated_turnaround_days=est_days,
                summary_explanation=expl,
                rule_evaluations=rule_evals
            )
            berth_results.append(berth_result)

        # Port level status
        if has_passing:
            feasibility_run.overall_status = FeasibilityStatus.PASS
            feasibility_run.summary_narrative = f"Vessel is fully compatible with {feasibility_run.passing_berths_count} berth(s) at {port.name}."
        elif has_conditional:
            feasibility_run.overall_status = FeasibilityStatus.CONDITIONAL
            feasibility_run.summary_narrative = f"Vessel requires tidal high-water window or lighterage at {port.name}."
        elif all(b.status == FeasibilityStatus.FAIL for b in berth_results):
            feasibility_run.overall_status = FeasibilityStatus.FAIL
            feasibility_run.summary_narrative = f"Vessel exceeds permissible physical constraints at all berths in {port.name}."
        else:
            feasibility_run.overall_status = FeasibilityStatus.UNKNOWN
            feasibility_run.summary_narrative = f"Vessel-port feasibility cannot be verified without complete technical particulars."

        feasibility_run.berth_results = berth_results
        return self.optimizer_repo.save_feasibility_run(feasibility_run)
