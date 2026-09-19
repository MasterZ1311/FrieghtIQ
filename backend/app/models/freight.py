from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.enums import VesselClass, ForecastModelType

class FreightRoute(Base):
    __tablename__ = "freight_routes"

    id = Column(String(36), primary_key=True, index=True)
    route_code = Column(String(50), unique=True, index=True, nullable=False) # e.g. "NEWCASTLE_PARADIP_CAPESIZE"
    origin_port_id = Column(String(36), ForeignKey("ports.id"), nullable=False)
    destination_port_id = Column(String(36), ForeignKey("ports.id"), nullable=False)
    default_vessel_class = Column(SQLEnum(VesselClass), nullable=False)
    distance_nm = Column(Float, nullable=False)
    typical_duration_days = Column(Float, nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    origin_port = relationship("Port", foreign_keys=[origin_port_id])
    destination_port = relationship("Port", foreign_keys=[destination_port_id])
    observations = relationship("FreightObservation", back_populates="route", cascade="all, delete-orphan")
    forecasts = relationship("FreightForecast", back_populates="route", cascade="all, delete-orphan")


class FreightObservation(Base):
    __tablename__ = "freight_observations"

    id = Column(String(36), primary_key=True, index=True)
    route_id = Column(String(36), ForeignKey("freight_routes.id", ondelete="CASCADE"), nullable=False, index=True)
    observation_date = Column(DateTime, nullable=False, index=True)
    
    freight_rate_usd_pmt = Column(Float, nullable=False)
    bunker_vlsfo_usd = Column(Float, nullable=True)
    bunker_mgo_usd = Column(Float, nullable=True)
    baltic_index_value = Column(Float, nullable=True)
    congestion_origin_days = Column(Float, nullable=True)
    congestion_dest_days = Column(Float, nullable=True)
    
    is_interpolated = Column(Boolean, default=False)
    source_type = Column(String(50), default="SYNTHETIC_DERIVED")

    route = relationship("FreightRoute", back_populates="observations")


class FreightForecast(Base):
    __tablename__ = "freight_forecasts"

    id = Column(String(36), primary_key=True, index=True)
    route_id = Column(String(36), ForeignKey("freight_routes.id", ondelete="CASCADE"), nullable=False, index=True)
    vessel_class = Column(SQLEnum(VesselClass), nullable=False)
    model_type = Column(SQLEnum(ForecastModelType), nullable=False)
    
    horizon_days = Column(Integer, nullable=False) # 7, 14, 30, 90
    target_date = Column(DateTime, nullable=False, index=True)
    
    # Quantile Predictions
    predicted_p10 = Column(Float, nullable=False) # Lower bound
    predicted_p50 = Column(Float, nullable=False) # Median / Expected rate
    predicted_p90 = Column(Float, nullable=False) # Upper bound
    
    confidence_pct = Column(Float, default=85.0)
    volatility_index = Column(Float, nullable=True)
    feature_attributions = Column(Text, nullable=True) # JSON representation of top driver weights
    
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    route = relationship("FreightRoute", back_populates="forecasts")


class ForecastBacktestResult(Base):
    __tablename__ = "forecast_backtest_results"

    id = Column(String(36), primary_key=True, index=True)
    route_id = Column(String(36), ForeignKey("freight_routes.id", ondelete="CASCADE"), nullable=False, index=True)
    model_type = Column(SQLEnum(ForecastModelType), nullable=False)
    horizon_days = Column(Integer, nullable=False)
    
    test_start_date = Column(DateTime, nullable=False)
    test_end_date = Column(DateTime, nullable=False)
    sample_count = Column(Integer, nullable=False)
    
    mae = Column(Float, nullable=False)
    rmse = Column(Float, nullable=False)
    mape = Column(Float, nullable=False)
    directional_accuracy_pct = Column(Float, nullable=False)
    pinball_loss_p10 = Column(Float, nullable=False)
    pinball_loss_p50 = Column(Float, nullable=False)
    pinball_loss_p90 = Column(Float, nullable=False)
    
    evaluated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
