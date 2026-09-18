"""
FreightIQ — Market Intelligence Models
New SQLAlchemy ORM tables for:
  - MarketRegime      : HMM-detected BDI market regime snapshots
  - PortCongestionAIS : AIS-derived live port congestion scores
  - TidalWindow       : INCOIS tidal gate entry predictions
  - NewsSentiment     : NLP-classified news sentiment feed
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base


class MarketRegime(Base):
    __tablename__ = "market_regimes"

    id = Column(Integer, primary_key=True, index=True)
    detected_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Regime classification (4 states)
    regime_name = Column(String(30), nullable=False)
    # SUPERCYCLE_BULL | SEASONAL_LIFT | NEUTRAL | BEAR_DISTRESS

    confidence = Column(Float, nullable=False)                 # 0.0–1.0
    bci_avg_30d = Column(Float, nullable=True)                 # BCI 30-day average used
    transition_probabilities = Column(JSON, nullable=True)
    # e.g. {"SUPERCYCLE_BULL": 0.08, "SEASONAL_LIFT": 0.73, "NEUTRAL": 0.15, "BEAR_DISTRESS": 0.04}

    primary_driver = Column(String(200), nullable=True)
    regime_duration_estimate_days = Column(Integer, nullable=True)

    # Decision outputs
    contract_recommendation = Column(String(30), nullable=True)
    # SPOT_ONLY | MIXED_SPOT_COA | SHORT_COA_3V | TIME_CHARTER_6M
    urgency = Column(String(30), nullable=True)
    # NO_RUSH | EVALUATE_WEEKLY | WITHIN_2_WEEKS | IMMEDIATE

    is_demo = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<MarketRegime id={self.id} regime={self.regime_name} conf={self.confidence:.2f}>"


class PortCongestionAIS(Base):
    __tablename__ = "port_congestion_ais"

    id = Column(Integer, primary_key=True, index=True)
    port_code = Column(String(15), nullable=False, index=True)
    snapshot_time = Column(DateTime, server_default=func.now(), nullable=False)

    # AIS-derived metrics
    anchor_count = Column(Integer, nullable=True)        # Vessels at anchor within 10 NM
    drifting_count = Column(Integer, nullable=True)      # Vessels near-stopped (SOG < 0.5)
    berthed_count = Column(Integer, nullable=True)
    avg_approach_speed_knots = Column(Float, nullable=True)

    # Derived score
    congestion_score = Column(Integer, nullable=True)    # 0–100
    # 0-25=CLEAR, 26-50=MODERATE, 51-75=CONGESTED, 76-100=CRITICAL

    estimated_wait_days = Column(Float, nullable=True)
    demurrage_exposure_usd = Column(Float, nullable=True)
    virtual_arrival_saving_usd = Column(Float, nullable=True)

    source = Column(String(30), default="AISHub", nullable=False)
    # "AISHub Live" | "DEMO"

    is_demo = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<PortCongestionAIS port={self.port_code} score={self.congestion_score}>"


class TidalWindow(Base):
    __tablename__ = "tidal_windows"

    id = Column(Integer, primary_key=True, index=True)
    port_code = Column(String(15), nullable=False, index=True)
    # Only tide-gated ports: haldia, gopalpur, sagar

    window_start = Column(DateTime, nullable=False)
    window_end = Column(DateTime, nullable=False)
    window_duration_hrs = Column(Float, nullable=True)

    tide_height_m = Column(Float, nullable=True)
    channel_depth_m = Column(Float, nullable=True)
    available_draft_m = Column(Float, nullable=True)    # channel_depth + tide_height
    vessel_classes_feasible = Column(JSON, nullable=True)
    # e.g. ["Handysize", "Supramax"] — which classes can enter this window

    source = Column(String(20), default="INCOIS", nullable=False)
    fetched_at = Column(DateTime, server_default=func.now())
    is_demo = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<TidalWindow port={self.port_code} start={self.window_start} draft={self.available_draft_m}m>"


class NewsSentiment(Base):
    __tablename__ = "news_sentiment"

    id = Column(Integer, primary_key=True, index=True)
    fetched_at = Column(DateTime, server_default=func.now(), nullable=False)

    headline = Column(String(500), nullable=False)
    source = Column(String(50), nullable=True)          # Reuters, TradeWinds, etc.
    published_at = Column(DateTime, nullable=True)
    article_url = Column(String(500), nullable=True)

    # NLP classification
    category = Column(String(30), nullable=True)
    # Geopolitical | Weather | Demand | Supply | Port | Regulatory

    sentiment_score = Column(Float, nullable=True)      # -1.0 (bearish) → +1.0 (bullish)
    relevance_score = Column(Float, nullable=True)      # 0.0–1.0 relevance to SAIL trade lanes
    rate_impact = Column(String(20), nullable=True)     # bullish | bearish | neutral
    lag_days_estimate = Column(Integer, nullable=True)  # Estimated days until BDI reacts
    relevant_routes = Column(JSON, nullable=True)
    # e.g. ["Australia_India", "USA_India"]

    is_demo = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<NewsSentiment id={self.id} sentiment={self.sentiment_score:.2f} '{self.headline[:40]}...'>"
