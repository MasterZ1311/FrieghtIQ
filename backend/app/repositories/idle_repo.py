from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone

from app.models.idle_repositioning import (
    VesselEmploymentEvent,
    IdleScenario,
    RepositioningOption,
)


class IdleRepository:
    def __init__(self, db: Session):
        self.db = db

    # 1. Employment Events
    def get_events_for_vessel(self, vessel_id: str) -> List[VesselEmploymentEvent]:
        return (
            self.db.query(VesselEmploymentEvent)
            .filter(VesselEmploymentEvent.vessel_id == vessel_id)
            .options(
                joinedload(VesselEmploymentEvent.origin_port),
                joinedload(VesselEmploymentEvent.destination_port),
                joinedload(VesselEmploymentEvent.cargo_request),
            )
            .order_by(VesselEmploymentEvent.event_start.asc())
            .all()
        )

    def create_event(self, event: VesselEmploymentEvent) -> VesselEmploymentEvent:
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    # 2. Idle Scenarios
    def get_all_scenarios(self) -> List[IdleScenario]:
        return (
            self.db.query(IdleScenario)
            .options(
                joinedload(IdleScenario.vessel),
                joinedload(IdleScenario.repositioning_options),
            )
            .order_by(IdleScenario.created_at.desc())
            .all()
        )

    def get_scenario_by_id(self, scenario_id: str) -> Optional[IdleScenario]:
        return (
            self.db.query(IdleScenario)
            .filter(IdleScenario.id == scenario_id)
            .options(
                joinedload(IdleScenario.vessel),
                joinedload(IdleScenario.repositioning_options),
            )
            .first()
        )

    def get_latest_scenario_for_vessel(self, vessel_id: str) -> Optional[IdleScenario]:
        return (
            self.db.query(IdleScenario)
            .filter(IdleScenario.vessel_id == vessel_id)
            .options(
                joinedload(IdleScenario.vessel),
                joinedload(IdleScenario.repositioning_options),
            )
            .order_by(IdleScenario.created_at.desc())
            .first()
        )

    def save_scenario(self, scenario: IdleScenario) -> IdleScenario:
        self.db.add(scenario)
        self.db.commit()
        self.db.refresh(scenario)
        return scenario

    # 3. Repositioning Options
    def get_repositioning_options_for_vessel(self, vessel_id: str) -> List[RepositioningOption]:
        return (
            self.db.query(RepositioningOption)
            .filter(RepositioningOption.vessel_id == vessel_id)
            .options(
                joinedload(RepositioningOption.target_port),
                joinedload(RepositioningOption.target_cargo_request),
            )
            .order_by(RepositioningOption.distance.asc())
            .all()
        )

    def save_repositioning_option(self, option: RepositioningOption) -> RepositioningOption:
        self.db.add(option)
        self.db.commit()
        self.db.refresh(option)
        return option
