from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.ports import Port, Berth, PortConstraint, BerthConstraint

class PortRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_ports(self) -> List[Port]:
        return self.db.query(Port).order_by(Port.name).all()

    def get_port_by_id(self, port_id: str) -> Optional[Port]:
        return (
            self.db.query(Port)
            .options(
                joinedload(Port.berths).joinedload(Berth.constraints),
                joinedload(Port.constraints),
                joinedload(Port.data_sources),
            )
            .filter(Port.id == port_id)
            .first()
        )

    def get_port_by_unlocode(self, unlocode: str) -> Optional[Port]:
        return (
            self.db.query(Port)
            .options(
                joinedload(Port.berths).joinedload(Berth.constraints),
                joinedload(Port.constraints),
                joinedload(Port.data_sources),
            )
            .filter(Port.unlocode == unlocode)
            .first()
        )

    def get_berths_for_port(self, port_id: str) -> List[Berth]:
        return (
            self.db.query(Berth)
            .options(joinedload(Berth.constraints))
            .filter(Berth.port_id == port_id)
            .order_by(Berth.berth_code)
            .all()
        )
