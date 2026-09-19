from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from app.models.freight import FreightRoute, FreightObservation, FreightForecast, ForecastBacktestResult
from app.models.enums import VesselClass, ForecastModelType

class FreightRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_routes(self) -> List[FreightRoute]:
        return (
            self.db.query(FreightRoute)
            .options(
                joinedload(FreightRoute.origin_port),
                joinedload(FreightRoute.destination_port)
            )
            .all()
        )

    def get_route_by_id(self, route_id: str) -> Optional[FreightRoute]:
        return (
            self.db.query(FreightRoute)
            .options(
                joinedload(FreightRoute.origin_port),
                joinedload(FreightRoute.destination_port)
            )
            .filter(FreightRoute.id == route_id)
            .first()
        )

    def get_route_by_code(self, route_code: str) -> Optional[FreightRoute]:
        return (
            self.db.query(FreightRoute)
            .options(
                joinedload(FreightRoute.origin_port),
                joinedload(FreightRoute.destination_port)
            )
            .filter(FreightRoute.route_code == route_code)
            .first()
        )

    def get_observations(self, route_id: str, limit: int = 365) -> List[FreightObservation]:
        return (
            self.db.query(FreightObservation)
            .filter(FreightObservation.route_id == route_id)
            .order_by(FreightObservation.observation_date.asc())
            .limit(limit)
            .all()
        )

    def save_forecasts(self, forecasts: List[FreightForecast]) -> List[FreightForecast]:
        for f in forecasts:
            self.db.add(f)
        self.db.commit()
        return forecasts

    def get_latest_forecasts(self, route_id: str, model_type: Optional[ForecastModelType] = None) -> List[FreightForecast]:
        query = self.db.query(FreightForecast).filter(FreightForecast.route_id == route_id)
        if model_type:
            query = query.filter(FreightForecast.model_type == model_type)
        return query.order_by(FreightForecast.horizon_days.asc()).all()

    def save_backtest_result(self, result: ForecastBacktestResult) -> ForecastBacktestResult:
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result

    def get_backtest_results(self, route_id: str) -> List[ForecastBacktestResult]:
        return (
            self.db.query(ForecastBacktestResult)
            .filter(ForecastBacktestResult.route_id == route_id)
            .order_by(ForecastBacktestResult.horizon_days.asc())
            .all()
        )
