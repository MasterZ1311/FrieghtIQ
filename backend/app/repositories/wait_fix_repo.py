from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.wait_fix import WaitFixAnalysis, WaitFixScenario
from app.models.enums import VesselClass

class WaitFixRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_analysis(self, analysis: WaitFixAnalysis) -> WaitFixAnalysis:
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def save_scenario(self, scenario: WaitFixScenario) -> WaitFixScenario:
        self.db.add(scenario)
        self.db.commit()
        self.db.refresh(scenario)
        return scenario

    def get_analysis_by_id(self, analysis_id: str) -> Optional[WaitFixAnalysis]:
        return self.db.query(WaitFixAnalysis).options(
            joinedload(WaitFixAnalysis.scenarios),
            joinedload(WaitFixAnalysis.origin_port),
            joinedload(WaitFixAnalysis.destination_port),
            joinedload(WaitFixAnalysis.cargo_request)
        ).filter(WaitFixAnalysis.id == analysis_id).first()

    def get_latest_analysis(
        self,
        cargo_request_id: Optional[str] = None,
        origin_port_id: Optional[str] = None,
        destination_port_id: Optional[str] = None,
        vessel_class: Optional[VesselClass] = None
    ) -> Optional[WaitFixAnalysis]:
        query = self.db.query(WaitFixAnalysis).options(
            joinedload(WaitFixAnalysis.scenarios),
            joinedload(WaitFixAnalysis.origin_port),
            joinedload(WaitFixAnalysis.destination_port)
        )
        if cargo_request_id:
            query = query.filter(WaitFixAnalysis.cargo_request_id == cargo_request_id)
        if origin_port_id:
            query = query.filter(WaitFixAnalysis.origin_port_id == origin_port_id)
        if destination_port_id:
            query = query.filter(WaitFixAnalysis.destination_port_id == destination_port_id)
        if vessel_class:
            query = query.filter(WaitFixAnalysis.vessel_class == vessel_class)

        return query.order_by(WaitFixAnalysis.created_at.desc()).first()

    def get_analysis_history(
        self,
        cargo_request_id: Optional[str] = None,
        limit: int = 20
    ) -> List[WaitFixAnalysis]:
        query = self.db.query(WaitFixAnalysis).options(
            joinedload(WaitFixAnalysis.scenarios)
        )
        if cargo_request_id:
            query = query.filter(WaitFixAnalysis.cargo_request_id == cargo_request_id)
        return query.order_by(WaitFixAnalysis.created_at.desc()).limit(limit).all()

    def get_scenarios_by_analysis_id(self, analysis_id: str) -> List[WaitFixScenario]:
        return self.db.query(WaitFixScenario).filter(
            WaitFixScenario.analysis_id == analysis_id
        ).all()
