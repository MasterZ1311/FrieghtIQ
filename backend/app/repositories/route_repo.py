"""
Route Repository
================
Data access for trade lane routes, nautical mile distances, and canal transit requirements.
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Route as RouteModel
from app.ml.features import get_distance, ROUTE_DISTANCES

logger = logging.getLogger(__name__)


class RouteRepository:
    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def get_distance_nm(self, origin: str, destination: str) -> float:
        """
        Retrieves nautical distance in NM between origin and destination.
        """
        # 1. Try DB
        if self.db:
            try:
                row = self.db.query(RouteModel).filter(
                    RouteModel.origin.ilike(origin.strip()),
                    RouteModel.destination.ilike(destination.strip()),
                ).first()
                if row and row.distance_nm:
                    return float(row.distance_nm)
            except Exception as e:
                logger.debug(f"DB route query for {origin}->{destination}: {e}")

        # 2. Fall back to maritime distance table
        dist = get_distance(origin, destination)
        return float(dist)
