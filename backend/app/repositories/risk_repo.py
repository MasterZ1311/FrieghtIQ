from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone

from app.models.risk import (
    PortCongestion,
    WeatherObservation,
    TidalWindow,
    RiskEvent,
)
from app.models.enums import RiskSeverity, RiskType, RiskStatus


class RiskRepository:
    def __init__(self, db: Session):
        self.db = db

    # ----------------------------------------------------
    # Port Congestion
    # ----------------------------------------------------
    def get_latest_congestion_for_port(self, port_id: str) -> Optional[PortCongestion]:
        return (
            self.db.query(PortCongestion)
            .filter(PortCongestion.port_id == port_id)
            .order_by(PortCongestion.observed_at.desc())
            .first()
        )

    def get_congestion_history_for_port(self, port_id: str, limit: int = 14) -> List[PortCongestion]:
        return (
            self.db.query(PortCongestion)
            .filter(PortCongestion.port_id == port_id)
            .order_by(PortCongestion.observed_at.desc())
            .limit(limit)
            .all()
        )

    def get_all_latest_port_congestions(self) -> List[PortCongestion]:
        # Distinct by port_id ordered by observed_at desc
        all_records = (
            self.db.query(PortCongestion)
            .order_by(PortCongestion.observed_at.desc())
            .all()
        )
        seen_ports = set()
        latest = []
        for rec in all_records:
            if rec.port_id not in seen_ports:
                seen_ports.add(rec.port_id)
                latest.append(rec)
        return latest

    def save_congestion(self, record: PortCongestion) -> PortCongestion:
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    # ----------------------------------------------------
    # Weather Observations
    # ----------------------------------------------------
    def get_latest_weather_for_port(self, port_id: str) -> Optional[WeatherObservation]:
        return (
            self.db.query(WeatherObservation)
            .filter(WeatherObservation.location_id == port_id)
            .order_by(WeatherObservation.observed_at.desc())
            .first()
        )

    def get_weather_history_for_port(self, port_id: str, limit: int = 24) -> List[WeatherObservation]:
        return (
            self.db.query(WeatherObservation)
            .filter(WeatherObservation.location_id == port_id)
            .order_by(WeatherObservation.observed_at.desc())
            .limit(limit)
            .all()
        )

    def save_weather(self, record: WeatherObservation) -> WeatherObservation:
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    # ----------------------------------------------------
    # Tidal Windows
    # ----------------------------------------------------
    def get_tidal_windows_for_port(self, port_id: str, limit: int = 30) -> List[TidalWindow]:
        return (
            self.db.query(TidalWindow)
            .filter(TidalWindow.port_id == port_id)
            .order_by(TidalWindow.window_start.asc())
            .limit(limit)
            .all()
        )

    def get_tidal_windows_for_berth(self, berth_id: str, limit: int = 20) -> List[TidalWindow]:
        return (
            self.db.query(TidalWindow)
            .filter(TidalWindow.berth_id == berth_id)
            .order_by(TidalWindow.window_start.asc())
            .limit(limit)
            .all()
        )

    def save_tidal_window(self, record: TidalWindow) -> TidalWindow:
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    # ----------------------------------------------------
    # Risk Events
    # ----------------------------------------------------
    def get_risk_events(
        self,
        severity: Optional[str] = None,
        risk_type: Optional[str] = None,
        status: Optional[str] = None,
        port_id: Optional[str] = None,
        vessel_id: Optional[str] = None,
        voyage_id: Optional[str] = None,
        limit: int = 100
    ) -> List[RiskEvent]:
        query = self.db.query(RiskEvent)

        if severity:
            query = query.filter(RiskEvent.severity == severity)
        if risk_type:
            query = query.filter(RiskEvent.risk_type == risk_type)
        if status:
            query = query.filter(RiskEvent.status == status)
        if port_id:
            query = query.filter(RiskEvent.entity_id == port_id)
        if vessel_id:
            query = query.filter(RiskEvent.entity_id == vessel_id)
        if voyage_id:
            query = query.filter(RiskEvent.voyage_id == voyage_id)

        return query.order_by(RiskEvent.created_at.desc()).limit(limit).all()

    def get_risk_event_by_id(self, event_id: str) -> Optional[RiskEvent]:
        return self.db.query(RiskEvent).filter(RiskEvent.id == event_id).first()

    def create_risk_event(self, event: RiskEvent) -> RiskEvent:
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def update_risk_event_status(self, event_id: str, status: RiskStatus) -> Optional[RiskEvent]:
        event = self.get_risk_event_by_id(event_id)
        if event:
            event.status = status
            self.db.commit()
            self.db.refresh(event)
        return event
