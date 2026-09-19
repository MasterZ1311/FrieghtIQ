from typing import List, Optional
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from app.models.cargo import CargoRequirement, CargoHandlingLog
from app.schemas.cargo import CargoRequirementCreate
from app.models.enums import RequirementStatus

class CargoRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_requirements(self) -> List[CargoRequirement]:
        return (
            self.db.query(CargoRequirement)
            .options(
                joinedload(CargoRequirement.load_port),
                joinedload(CargoRequirement.discharge_port)
            )
            .order_by(CargoRequirement.created_at.desc())
            .all()
        )

    def get_requirement_by_id(self, requirement_id: str) -> Optional[CargoRequirement]:
        return (
            self.db.query(CargoRequirement)
            .options(
                joinedload(CargoRequirement.load_port),
                joinedload(CargoRequirement.discharge_port),
                joinedload(CargoRequirement.handling_logs)
            )
            .filter(CargoRequirement.id == requirement_id)
            .first()
        )

    def create_requirement(self, req_in: CargoRequirementCreate) -> CargoRequirement:
        # Generate code e.g. CR-2026-XXXX
        count = self.db.query(CargoRequirement).count()
        code = f"CR-2026-{count + 1:03d}"
        
        req = CargoRequirement(
            id=str(uuid.uuid4()),
            requirement_code=code,
            title=req_in.title,
            cargo_type=req_in.cargo_type,
            quantity_mt=req_in.quantity_mt,
            tolerance_pct=req_in.tolerance_pct,
            load_port_id=req_in.load_port_id,
            discharge_port_id=req_in.discharge_port_id,
            laycan_start=req_in.laycan_start,
            laycan_end=req_in.laycan_end,
            target_freight_usd_pmt=req_in.target_freight_usd_pmt,
            max_vessel_age_years=req_in.max_vessel_age_years,
            preferred_vessel_classes=req_in.preferred_vessel_classes,
            gear_requirement=req_in.gear_requirement,
            status=RequirementStatus.MARKET_SCAN,
            notes=req_in.notes
        )
        self.db.add(req)
        self.db.commit()
        self.db.refresh(req)
        return self.get_requirement_by_id(req.id)
