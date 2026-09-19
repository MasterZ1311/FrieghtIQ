from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.economics import (
    VoyageEconomicAnalysis,
    VoyageCostComponent,
    SpeedScenario,
    VoyageScenario,
)


class VoyageEconomicsRepository:
    """
    Data repository for managing voyage economic analyses, itemized financial ledgers,
    speed curves, and multi-scenario evaluations.
    """

    @staticmethod
    def get_by_id(db: Session, analysis_id: str) -> Optional[VoyageEconomicAnalysis]:
        return db.query(VoyageEconomicAnalysis).filter(VoyageEconomicAnalysis.id == analysis_id).first()

    @staticmethod
    def get_latest(db: Session) -> Optional[VoyageEconomicAnalysis]:
        return db.query(VoyageEconomicAnalysis).order_by(desc(VoyageEconomicAnalysis.created_at)).first()

    @staticmethod
    def list_analyses(
        db: Session,
        limit: int = 20,
        cargo_request_id: Optional[str] = None,
        vessel_id: Optional[str] = None
    ) -> List[VoyageEconomicAnalysis]:
        q = db.query(VoyageEconomicAnalysis)
        if cargo_request_id:
            q = q.filter(VoyageEconomicAnalysis.cargo_request_id == cargo_request_id)
        if vessel_id:
            q = q.filter(VoyageEconomicAnalysis.vessel_id == vessel_id)
        return q.order_by(desc(VoyageEconomicAnalysis.created_at)).limit(limit).all()

    @staticmethod
    def get_components(db: Session, analysis_id: str) -> List[VoyageCostComponent]:
        return db.query(VoyageCostComponent).filter(VoyageCostComponent.analysis_id == analysis_id).all()

    @staticmethod
    def get_scenarios(db: Session, analysis_id: str) -> List[VoyageScenario]:
        return db.query(VoyageScenario).filter(VoyageScenario.analysis_id == analysis_id).all()

    @staticmethod
    def get_speed_scenarios(db: Session, analysis_id: str) -> List[SpeedScenario]:
        return db.query(SpeedScenario).filter(SpeedScenario.analysis_id == analysis_id).order_by(SpeedScenario.speed_knots.asc()).all()
