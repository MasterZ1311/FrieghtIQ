from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from app.models.optimizer import FeasibilityRun, FeasibilityBerthResult, FeasibilityRuleEvaluation
from app.models.ports import Berth, Port
from app.models.vessels import Vessel

class OptimizerRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_feasibility_run(self, run: FeasibilityRun) -> FeasibilityRun:
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return self.get_feasibility_run_by_id(run.id)

    def get_feasibility_run_by_id(self, run_id: str) -> Optional[FeasibilityRun]:
        return (
            self.db.query(FeasibilityRun)
            .options(
                joinedload(FeasibilityRun.vessel).joinedload(Vessel.particulars),
                joinedload(FeasibilityRun.port).joinedload(Port.berths),
                joinedload(FeasibilityRun.berth_results)
                .joinedload(FeasibilityBerthResult.berth)
                .joinedload(Berth.constraints),
                joinedload(FeasibilityRun.berth_results)
                .joinedload(FeasibilityBerthResult.rule_evaluations),
            )
            .filter(FeasibilityRun.id == run_id)
            .first()
        )

    def get_latest_run(self, vessel_id: str, port_id: str) -> Optional[FeasibilityRun]:
        return (
            self.db.query(FeasibilityRun)
            .options(
                joinedload(FeasibilityRun.vessel).joinedload(Vessel.particulars),
                joinedload(FeasibilityRun.port).joinedload(Port.berths),
                joinedload(FeasibilityRun.berth_results)
                .joinedload(FeasibilityBerthResult.berth)
                .joinedload(Berth.constraints),
                joinedload(FeasibilityRun.berth_results)
                .joinedload(FeasibilityBerthResult.rule_evaluations),
            )
            .filter(FeasibilityRun.vessel_id == vessel_id, FeasibilityRun.port_id == port_id)
            .order_by(FeasibilityRun.run_timestamp.desc())
            .first()
        )
