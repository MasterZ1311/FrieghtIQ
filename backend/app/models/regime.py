from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.enums import MarketRegimeType, DataStatusType, CargoType, VesselClass

class MarketRegime(Base):
    __tablename__ = "market_regimes"

    id = Column(String(36), primary_key=True, index=True)
    origin_port_id = Column(String(36), ForeignKey("ports.id"), nullable=False, index=True)
    destination_port_id = Column(String(36), ForeignKey("ports.id"), nullable=False, index=True)
    trade_lane = Column(String(100), nullable=False, index=True)
    cargo_type = Column(SQLEnum(CargoType), nullable=False)
    vessel_class = Column(SQLEnum(VesselClass), nullable=False)
    
    # Detected Regime & Probabilities
    regime = Column(SQLEnum(MarketRegimeType), nullable=False, index=True)
    regime_probability = Column(Float, nullable=False)
    bull_probability = Column(Float, nullable=False)
    bear_probability = Column(Float, nullable=False)
    neutral_probability = Column(Float, nullable=False)
    seasonal_probability = Column(Float, nullable=False)
    
    # Timing & Provenance
    regime_start_date = Column(DateTime, nullable=False)
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    model_version_id = Column(String(50), nullable=False, default="HMM_GAUSSIAN_V1.0")
    dataset_version_id = Column(String(50), nullable=False, default="SYNTHETIC_BALTIC_V2026")
    data_status = Column(SQLEnum(DataStatusType), nullable=False, default=DataStatusType.SYNTHETIC)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    origin_port = relationship("Port", foreign_keys=[origin_port_id])
    destination_port = relationship("Port", foreign_keys=[destination_port_id])
    transitions = relationship("MarketRegimeTransition", back_populates="market_regime", cascade="all, delete-orphan")


class MarketRegimeTransition(Base):
    __tablename__ = "market_regime_transitions"

    id = Column(String(36), primary_key=True, index=True)
    market_regime_id = Column(String(36), ForeignKey("market_regimes.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_regime = Column(SQLEnum(MarketRegimeType), nullable=False)
    new_regime = Column(SQLEnum(MarketRegimeType), nullable=False)
    transition_date = Column(DateTime, nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    trigger_features = Column(Text, nullable=True) # JSON string of leading features causing transition
    model_version_id = Column(String(50), nullable=False, default="HMM_GAUSSIAN_V1.0")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    market_regime = relationship("MarketRegime", back_populates="transitions")
