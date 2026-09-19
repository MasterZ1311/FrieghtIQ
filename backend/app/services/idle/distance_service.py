"""
Route Distance Service & Providers
Calculates ballast repositioning and trade route distances between global maritime ports.

STRICT DATA INTEGRITY:
- Sourced routes: labeled "NAUTICAL_CHART"
- Geodesic fallback: explicitly labeled "GEODESIC_APPROXIMATION"
- Missing coordinates: labeled "UNAVAILABLE"
"""
import math
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.ports import Port
from app.models.freight import FreightRoute


class RouteDistanceProvider(ABC):
    @abstractmethod
    def get_distance(
        self,
        origin_port: Port,
        destination_port: Port,
        db: Optional[Session] = None
    ) -> Tuple[Optional[float], str, str]:
        """
        Returns:
            (distance_nm, distance_method, explanation)
        """
        pass


class StaticDemoDistanceProvider(RouteDistanceProvider):
    """
    Looks up distance from certified FreightRoute entities in the database.
    If unavailable, calculates geodesic Haversine distance with explicit 'GEODESIC_APPROXIMATION' label.
    """
    def __init__(self):
        # In-memory cache for speed
        self._cache: Dict[str, Tuple[Optional[float], str, str]] = {}

    def get_distance(
        self,
        origin_port: Port,
        destination_port: Port,
        db: Optional[Session] = None
    ) -> Tuple[Optional[float], str, str]:
        if not origin_port or not destination_port:
            return (None, "UNAVAILABLE", "One or both port entities are null.")

        if origin_port.id == destination_port.id:
            return (0.0, "SAME_PORT", f"Vessel already stationed at {origin_port.name}.")

        cache_key = f"{origin_port.id}::{destination_port.id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 1. Attempt lookup in DB freight_routes
        if db:
            route = db.query(FreightRoute).filter(
                or_(
                    and_(FreightRoute.origin_port_id == origin_port.id, FreightRoute.destination_port_id == destination_port.id),
                    and_(FreightRoute.origin_port_id == destination_port.id, FreightRoute.destination_port_id == origin_port.id),
                )
            ).first()

            if route and route.distance_nm:
                res = (
                    round(route.distance_nm, 1),
                    "NAUTICAL_CHART",
                    f"Verified standard maritime distance ({route.distance_nm:,.1f} NM) from route record '{route.route_code}'."
                )
                self._cache[cache_key] = res
                return res

        # 2. Geodesic Approximation Fallback
        if (
            origin_port.latitude is not None and origin_port.longitude is not None and
            destination_port.latitude is not None and destination_port.longitude is not None
        ):
            lat1, lon1 = origin_port.latitude, origin_port.longitude
            lat2, lon2 = destination_port.latitude, destination_port.longitude

            # Haversine great-circle formula
            r_nm = 3440.065 # Earth radius in nautical miles
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)

            a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
            c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
            dist_nm = round(r_nm * c, 1)

            res = (
                dist_nm,
                "GEODESIC_APPROXIMATION",
                f"Calculated {dist_nm:,.1f} NM via great-circle Haversine formula (GEODESIC APPROXIMATION). Not a certified nautical sailing distance."
            )
            self._cache[cache_key] = res
            return res

        res = (
            None,
            "UNAVAILABLE",
            f"Geographic coordinates unavailable for {origin_port.name} or {destination_port.name}."
        )
        self._cache[cache_key] = res
        return res


class RouteDistanceService:
    def __init__(self, provider: Optional[RouteDistanceProvider] = None):
        self.provider = provider or StaticDemoDistanceProvider()

    def get_distance(
        self,
        origin_port: Port,
        destination_port: Port,
        db: Optional[Session] = None
    ) -> Tuple[Optional[float], str, str]:
        return self.provider.get_distance(origin_port, destination_port, db=db)
