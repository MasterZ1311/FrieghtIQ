import uuid
import json
import pandas as pd
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.freight import FreightForecast, ForecastBacktestResult, FreightRoute
from app.models.enums import ForecastModelType, VesselClass
from app.repositories.freight_repo import FreightRepository
from app.services.forecasting.baseline_models import PersistenceNaiveModel, MovingAverageModel
from app.services.forecasting.tft_model import TemporalFusionForecastModel
from app.services.forecasting.backtester import WalkForwardBacktester

class FreightForecastService:
    def __init__(self, db: Session):
        self.db = db
        self.freight_repo = FreightRepository(db)
        self.backtester = WalkForwardBacktester()

    def get_model(self, model_type: ForecastModelType):
        if model_type == ForecastModelType.PERSISTENCE_NAIVE:
            return PersistenceNaiveModel()
        elif model_type == ForecastModelType.MOVING_AVERAGE_7D:
            return MovingAverageModel(window_days=7)
        elif model_type == ForecastModelType.MOVING_AVERAGE_30D:
            return MovingAverageModel(window_days=30)
        else:
            return TemporalFusionForecastModel()

    def generate_route_forecasts(
        self,
        route_id: str,
        vessel_class: Optional[VesselClass] = None,
        model_type: ForecastModelType = ForecastModelType.TFT,
        horizons: Optional[List[int]] = None
    ) -> List[FreightForecast]:
        if horizons is None:
            horizons = [7, 14, 30, 90]

        route = self.freight_repo.get_route_by_id(route_id)
        if not route:
            raise ValueError(f"Route with id {route_id} not found")

        target_vessel_class = vessel_class or route.default_vessel_class
        observations = self.freight_repo.get_observations(route_id, limit=730)
        
        if not observations or len(observations) < 14:
            raise ValueError(f"Insufficient observation history for route {route_id}")

        obs_dicts = [
            {
                "observation_date": o.observation_date,
                "freight_rate_usd_pmt": o.freight_rate_usd_pmt,
                "bunker_vlsfo_usd": o.bunker_vlsfo_usd,
                "bunker_mgo_usd": o.bunker_mgo_usd,
                "baltic_index_value": o.baltic_index_value,
                "congestion_origin_days": o.congestion_origin_days,
                "congestion_dest_days": o.congestion_dest_days,
            }
            for o in observations
        ]
        df = pd.DataFrame(obs_dicts).sort_values("observation_date")

        model = self.get_model(model_type)
        model.fit(df)

        now = datetime.now(timezone.utc)
        latest_obs_date = df["observation_date"].iloc[-1]
        
        # Clear previous forecasts for this route and model
        self.db.query(FreightForecast).filter(
            FreightForecast.route_id == route_id,
            FreightForecast.model_type == model_type
        ).delete()

        forecast_records = []
        for h in horizons:
            p10, p50, p90, attributions = model.predict(df, horizon_days=h)
            target_date = latest_obs_date + timedelta(days=h)
            
            # Confidence decreases slightly with longer horizons
            conf = round(max(60.0, 92.0 - (h * 0.25)), 1)
            vol = round((p90 - p10) / (p50 or 1.0), 3)

            fc = FreightForecast(
                id=str(uuid.uuid4()),
                route_id=route_id,
                vessel_class=target_vessel_class,
                model_type=model_type,
                horizon_days=h,
                target_date=target_date,
                predicted_p10=p10,
                predicted_p50=p50,
                predicted_p90=p90,
                confidence_pct=conf,
                volatility_index=vol,
                feature_attributions=json.dumps(attributions),
                generated_at=now
            )
            forecast_records.append(fc)

        saved_forecasts = self.freight_repo.save_forecasts(forecast_records)

        # Run walk-forward backtest for standard horizons
        for h in [7, 14, 30]:
            metrics = self.backtester.evaluate(model, df, horizon_days=h)
            
            # Upsert backtest result
            self.db.query(ForecastBacktestResult).filter(
                ForecastBacktestResult.route_id == route_id,
                ForecastBacktestResult.model_type == model_type,
                ForecastBacktestResult.horizon_days == h
            ).delete()

            bt = ForecastBacktestResult(
                id=str(uuid.uuid4()),
                route_id=route_id,
                model_type=model_type,
                horizon_days=h,
                test_start_date=df["observation_date"].iloc[0],
                test_end_date=latest_obs_date,
                sample_count=metrics["sample_count"],
                mae=metrics["mae"],
                rmse=metrics["rmse"],
                mape=metrics["mape"],
                directional_accuracy_pct=metrics["directional_accuracy_pct"],
                pinball_loss_p10=metrics["pinball_loss_p10"],
                pinball_loss_p50=metrics["pinball_loss_p50"],
                pinball_loss_p90=metrics["pinball_loss_p90"],
                evaluated_at=now
            )
            self.freight_repo.save_backtest_result(bt)

        return saved_forecasts
