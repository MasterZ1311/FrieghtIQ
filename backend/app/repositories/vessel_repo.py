from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.vessels import Vessel, VesselParticulars, VesselAvailability, OperationalSnapshotVessel
from app.models.enums import VesselClass, VesselStatus

class VesselRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_vessels(
        self,
        vessel_class: Optional[VesselClass] = None,
        status: Optional[VesselStatus] = None,
        is_snapshot_only: Optional[bool] = None
    ) -> List[Vessel]:
        query = (
            self.db.query(Vessel)
            .options(
                joinedload(Vessel.particulars),
                joinedload(Vessel.availability),
                joinedload(Vessel.snapshot_records)
            )
        )
        if vessel_class:
            query = query.filter(Vessel.vessel_class == vessel_class)
        if status:
            query = query.join(Vessel.availability).filter(VesselAvailability.current_status == status)
        if is_snapshot_only is not None:
            query = query.filter(Vessel.is_snapshot_vessel == is_snapshot_only)
        
        return query.order_by(Vessel.vessel_name).all()

    def get_vessel_by_id(self, vessel_id: str) -> Optional[Vessel]:
        return (
            self.db.query(Vessel)
            .options(
                joinedload(Vessel.particulars),
                joinedload(Vessel.availability),
                joinedload(Vessel.snapshot_records)
            )
            .filter(Vessel.id == vessel_id)
            .first()
        )

    def get_vessel_by_imo(self, imo_number: str) -> Optional[Vessel]:
        return (
            self.db.query(Vessel)
            .options(
                joinedload(Vessel.particulars),
                joinedload(Vessel.availability),
                joinedload(Vessel.snapshot_records)
            )
            .filter(Vessel.imo_number == imo_number)
            .first()
        )
