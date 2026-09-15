from sqlalchemy import Column, Integer, String, Float, Date, DateTime, JSON, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base


class FreightRate(Base):
    """
    Weekly freight rate historical series.
    All records are clearly labelled synthetic demo data.
    """
    __tablename__ = "freight_rates"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    origin = Column(String(100), nullable=False, index=True)
    destination = Column(String(100), nullable=False, index=True)
    vessel_class = Column(String(50), nullable=False, index=True)
    commodity = Column(String(100), nullable=False)
    rate_usd_per_mt = Column(Float, nullable=False)
    tce_usd_per_day = Column(Float, nullable=True)
    bpi_index = Column(Float, nullable=True)       # Baltic Panamax Index proxy
    bunker_price = Column(Float, nullable=True)    # IFO380 USD/MT proxy
    congestion_index = Column(Float, nullable=True)  # 0-1
    vessel_availability = Column(Float, nullable=True)  # 0-1
    demand_index = Column(Float, nullable=True)    # 0-1
    is_demo = Column(Boolean, default=True, nullable=False)
    data_label = Column(String(100), default="[DEMO] Synthetic Freight Rate", nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Vessel(Base):
    """
    Vessel specifications and operational economics for dry bulk carriers.
    """
    __tablename__ = "vessels"

    id = Column(Integer, primary_key=True, index=True)
    vessel_class = Column(String(50), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    dwt_min = Column(Integer, nullable=False)
    dwt_max = Column(Integer, nullable=False)
    loa_m = Column(Float, nullable=False)          # Length Overall in meters
    beam_m = Column(Float, nullable=False)
    draft_m = Column(Float, nullable=False)        # Max draft in meters
    daily_opex_usd = Column(Float, nullable=False) # OPEX per day
    daily_hire_usd = Column(Float, nullable=True)  # Time charter hire
    speed_kn = Column(Float, nullable=False)       # Service speed in knots
    fuel_consumption_mt_day = Column(Float, nullable=False)
    suitable_commodities = Column(JSON, nullable=True)
    is_demo = Column(Boolean, default=True, nullable=False)
    data_label = Column(String(100), default="[DEMO] Synthetic Vessel Spec", nullable=False)


class Port(Base):
    """
    Port specifications, physical constraints, handling metrics, and dues.
    """
    __tablename__ = "ports"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    country = Column(String(100), nullable=False)
    region = Column(String(50), nullable=False)    # origin/destination
    max_dwt = Column(Integer, nullable=False)
    max_draft_m = Column(Float, nullable=False)
    max_loa_m = Column(Float, nullable=True)
    max_beam_m = Column(Float, nullable=True)
    berths = Column(Integer, nullable=True)
    tide_restricted = Column(Boolean, default=False)
    congestion_level = Column(String(20), default="medium")  # low/medium/high
    avg_turnaround_days = Column(Float, nullable=False)
    handling_rate_mt_day = Column(Float, nullable=False)
    port_dues_usd_per_call = Column(Float, nullable=True)
    suitable_commodities = Column(JSON, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    is_demo = Column(Boolean, default=True, nullable=False)
    data_label = Column(String(100), default="[DEMO] Synthetic Port Profile", nullable=False)


class Route(Base):
    """
    Shipping routes between origin export ports and Indian East Coast destination ports.
    """
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    origin = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False)
    distance_nm = Column(Float, nullable=False)     # Nautical miles
    typical_vessel_classes = Column(JSON, nullable=True)
    typical_commodities = Column(JSON, nullable=True)
    canal_transit = Column(String(100), nullable=True)
    is_demo = Column(Boolean, default=True, nullable=False)
    data_label = Column(String(100), default="[DEMO] Synthetic Route Table", nullable=False)


class MarketIndicator(Base):
    """
    Baltic dry index proxies, bunker benchmark prices, and global fleet utilization.
    """
    __tablename__ = "market_indicators"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    bdi_index = Column(Float, nullable=False)              # Baltic Dry Index proxy
    bci_index = Column(Float, nullable=False)              # Baltic Capesize Index
    bpi_index = Column(Float, nullable=False)              # Baltic Panamax Index
    bsi_index = Column(Float, nullable=False)              # Baltic Supramax Index
    bhsi_index = Column(Float, nullable=False)             # Baltic Handysize Index
    bunker_vlsfo_usd = Column(Float, nullable=False)       # VLSFO 0.5% S USD/MT
    bunker_ifo380_usd = Column(Float, nullable=False)      # IFO 380 USD/MT
    bunker_mgo_usd = Column(Float, nullable=False)         # Marine Gas Oil USD/MT
    fleet_utilization_pct = Column(Float, nullable=False)  # Global fleet active %
    orderbook_to_fleet_pct = Column(Float, nullable=False) # Orderbook ratio %
    is_demo = Column(Boolean, default=True, nullable=False)
    data_label = Column(String(100), default="[DEMO] Synthetic Baltic & Bunker Indicator", nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class PortCongestion(Base):
    """
    Port congestion time series, queue metrics, waiting days, and berth turnaround.
    """
    __tablename__ = "port_congestion"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    port_name = Column(String(100), nullable=False, index=True)
    vessels_waiting_count = Column(Integer, nullable=False) # Number of vessels at anchorage
    avg_waiting_days = Column(Float, nullable=False)        # Days waiting for berth
    berth_occupancy_pct = Column(Float, nullable=False)     # Berth occupancy rate
    congestion_index = Column(Float, nullable=False)        # 0.0 - 1.0 index
    weather_delay_factor = Column(Float, default=0.0)       # 0.0 - 1.0 delay impact
    status = Column(String(50), default="medium")           # low/medium/high/severe
    is_demo = Column(Boolean, default=True, nullable=False)
    data_label = Column(String(100), default="[DEMO] Synthetic Port Congestion Metric", nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class CommodityIndicator(Base):
    """
    Benchmark commodity FOB/CFR pricing and Indian demand indices.
    """
    __tablename__ = "commodity_indicators"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    commodity = Column(String(100), nullable=False, index=True)
    origin = Column(String(100), nullable=False, index=True)
    price_index_usd_per_mt = Column(Float, nullable=False)       # Benchmark price proxy
    india_import_demand_index = Column(Float, nullable=False)    # 0.0 - 1.0
    steel_production_index = Column(Float, nullable=False)       # 0.0 - 1.0
    power_generation_demand_index = Column(Float, nullable=False)# 0.0 - 1.0
    is_demo = Column(Boolean, default=True, nullable=False)
    data_label = Column(String(100), default="[DEMO] Synthetic Commodity Market Indicator", nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class HistoricalObservation(Base):
    """
    Unified multi-factor historical observations linking route, vessel class,
    freight rates, voyage economics, congestion, and demand.
    """
    __tablename__ = "historical_observations"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    origin = Column(String(100), nullable=False, index=True)
    destination = Column(String(100), nullable=False, index=True)
    vessel_class = Column(String(50), nullable=False, index=True)
    commodity = Column(String(100), nullable=False)
    distance_nm = Column(Float, nullable=False)
    freight_rate_usd_per_mt = Column(Float, nullable=False)
    tce_usd_per_day = Column(Float, nullable=True)
    bunker_price_usd_per_mt = Column(Float, nullable=False)
    congestion_index = Column(Float, nullable=False)
    vessel_availability_index = Column(Float, nullable=False)
    demand_index = Column(Float, nullable=False)
    bpi_index = Column(Float, nullable=True)
    is_demo = Column(Boolean, default=True, nullable=False)
    data_label = Column(String(100), default="[DEMO] Synthetic Historical Observation", nullable=False)
    created_at = Column(DateTime, server_default=func.now())
