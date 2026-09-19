from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.regime import MarketRegime, MarketRegimeTransition
from app.models.enums import MarketRegimeType, CargoType, VesselClass

class RegimeRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_regime(self, regime: MarketRegime) -> MarketRegime:
        self.db.add(regime)
        self.db.commit()
        self.db.refresh(regime)
        return regime

    def get_latest_regime(
        self,
        origin_port_id: str,
        destination_port_id: str,
        cargo_type: Optional[CargoType] = None,
        vessel_class: Optional[VesselClass] = None
    ) -> Optional[MarketRegime]:
        query = self.db.query(MarketRegime).filter(
            MarketRegime.origin_port_id == origin_port_id,
            MarketRegime.destination_port_id == destination_port_id
        )
        if cargo_type:
            query = query.filter(MarketRegime.cargo_type == cargo_type)
        if vessel_class:
            query = query.filter(MarketRegime.vessel_class == vessel_class)

        return query.order_by(MarketRegime.detected_at.desc()).first()

    def get_regime_history(
        self,
        origin_port_id: Optional[str] = None,
        destination_port_id: Optional[str] = None,
        trade_lane: Optional[str] = None,
        vessel_class: Optional[VesselClass] = None,
        limit: int = 180
    ) -> List[MarketRegime]:
        query = self.db.query(MarketRegime)
        if trade_lane:
            query = query.filter(MarketRegime.trade_lane == trade_lane)
        if origin_port_id and destination_port_id:
            query = query.filter(
                MarketRegime.origin_port_id == origin_port_id,
                MarketRegime.destination_port_id == destination_port_id
            )
        if vessel_class:
            query = query.filter(MarketRegime.vessel_class == vessel_class)

        return query.order_by(MarketRegime.detected_at.asc()).limit(limit).all()

    def save_transition(self, transition: MarketRegimeTransition) -> MarketRegimeTransition:
        self.db.add(transition)
        self.db.commit()
        self.db.refresh(transition)
        return transition

    def get_transitions(
        self,
        trade_lane: Optional[str] = None,
        limit: int = 20
    ) -> List[MarketRegimeTransition]:
        query = self.db.query(MarketRegimeTransition)
        if trade_lane:
            query = query.join(MarketRegimeTransition.market_regime).filter(
                MarketRegime.trade_lane == trade_lane
            )
        return query.order_by(MarketRegimeTransition.transition_date.desc()).limit(limit).all()
