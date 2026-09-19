from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from app.models.matching import VesselMatchRun, VesselMatchCandidate, VesselMatchRuleResult
from app.models.vessels import Vessel

class MatchingRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_match_run(self, match_run: VesselMatchRun) -> VesselMatchRun:
        self.db.add(match_run)
        self.db.commit()
        self.db.refresh(match_run)
        return self.get_match_run_by_id(match_run.id)

    def get_match_run_by_id(self, run_id: str) -> Optional[VesselMatchRun]:
        return (
            self.db.query(VesselMatchRun)
            .options(
                joinedload(VesselMatchRun.candidates)
                .joinedload(VesselMatchCandidate.vessel)
                .joinedload(Vessel.particulars),
                joinedload(VesselMatchRun.candidates)
                .joinedload(VesselMatchCandidate.vessel)
                .joinedload(Vessel.availability),
                joinedload(VesselMatchRun.candidates)
                .joinedload(VesselMatchCandidate.rule_results),
            )
            .filter(VesselMatchRun.id == run_id)
            .first()
        )

    def get_latest_for_requirement(self, requirement_id: str) -> Optional[VesselMatchRun]:
        return (
            self.db.query(VesselMatchRun)
            .options(
                joinedload(VesselMatchRun.candidates)
                .joinedload(VesselMatchCandidate.vessel)
                .joinedload(Vessel.particulars),
                joinedload(VesselMatchRun.candidates)
                .joinedload(VesselMatchCandidate.vessel)
                .joinedload(Vessel.availability),
                joinedload(VesselMatchRun.candidates)
                .joinedload(VesselMatchCandidate.rule_results),
            )
            .filter(VesselMatchRun.requirement_id == requirement_id)
            .order_by(VesselMatchRun.run_timestamp.desc())
            .first()
        )
