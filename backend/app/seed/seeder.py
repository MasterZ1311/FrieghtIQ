"""
Database seeder — populates SQLite with all 8 demo/synthetic datasets on startup or CLI trigger.
Clearly labelled synthetic data for development and demonstration.
"""
import logging
from sqlalchemy.orm import Session
from app.models import (
    FreightRate,
    Vessel,
    Port,
    Route,
    MarketIndicator,
    PortCongestion,
    CommodityIndicator,
    HistoricalObservation,
)
from app.seed.seed_data import (
    PORTS,
    VESSELS,
    generate_routes,
    generate_all_history,
    generate_market_indicators,
    generate_port_congestion_history,
    generate_commodity_indicators,
    generate_historical_observations,
)

logger = logging.getLogger(__name__)


def seed_database(db: Session, force: bool = False) -> dict:
    """
    Seed all 8 DEMO/SYNTHETIC datasets into the database.
    If force=True, clears all existing records first.
    Returns counts of all seeded entities.
    """
    if not force and db.query(Port).count() > 0:
        logger.info("Database already seeded, skipping.")
        return {
            "ports": db.query(Port).count(),
            "vessels": db.query(Vessel).count(),
            "routes": db.query(Route).count(),
            "freight_rates": db.query(FreightRate).count(),
            "market_indicators": db.query(MarketIndicator).count(),
            "port_congestion": db.query(PortCongestion).count(),
            "commodity_indicators": db.query(CommodityIndicator).count(),
            "historical_observations": db.query(HistoricalObservation).count(),
        }

    if force:
        logger.info("Force re-seeding: clearing all existing tables...")
        db.query(HistoricalObservation).delete()
        db.query(CommodityIndicator).delete()
        db.query(PortCongestion).delete()
        db.query(MarketIndicator).delete()
        db.query(FreightRate).delete()
        db.query(Route).delete()
        db.query(Vessel).delete()
        db.query(Port).delete()
        db.commit()

    logger.info("=========================================================")
    logger.info("  SEEDING FREIGHTIQ DEMO DATASETS (SYNTHETIC BENCHMARK)  ")
    logger.info("=========================================================")

    # 1. Ports (7 origins + 7 East Coast destinations)
    for p in PORTS:
        db.add(Port(**p))
    db.commit()
    ports_count = len(PORTS)
    logger.info(f"  [1/8] Ports: Added {ports_count} port profiles")

    # 2. Vessels (Handysize, Supramax, Panamax, Capesize)
    for v in VESSELS:
        db.add(Vessel(**v))
    db.commit()
    vessels_count = len(VESSELS)
    logger.info(f"  [2/8] Vessels: Added {vessels_count} vessel classes")

    # 3. Routes (5 origins x 7 destinations = 35 routes)
    routes = generate_routes()
    for r in routes:
        db.add(Route(**r))
    db.commit()
    routes_count = len(routes)
    logger.info(f"  [3/8] Routes: Added {routes_count} route definitions")

    # 4. Market Indicators (Baltic indices BDI/BCI/BPI/BSI/BHSI + Bunker VLSFO/IFO/MGO)
    market_indicators = generate_market_indicators()
    for chunk_start in range(0, len(market_indicators), 500):
        chunk = market_indicators[chunk_start:chunk_start + 500]
        db.bulk_insert_mappings(MarketIndicator, chunk)
    db.commit()
    market_count = len(market_indicators)
    logger.info(f"  [4/8] Market Indicators: Added {market_count} weekly Baltic & Bunker observations")

    # 5. Port Congestion (Weekly queue, waiting days, berth occupancy)
    congestion_records = generate_port_congestion_history()
    for chunk_start in range(0, len(congestion_records), 500):
        chunk = congestion_records[chunk_start:chunk_start + 500]
        db.bulk_insert_mappings(PortCongestion, chunk)
    db.commit()
    congestion_count = len(congestion_records)
    logger.info(f"  [5/8] Port Congestion: Added {congestion_count} port-week congestion metrics")

    # 6. Commodity Indicators (Benchmark prices FOB/CFR + Indian demand)
    commodity_records = generate_commodity_indicators()
    for chunk_start in range(0, len(commodity_records), 500):
        chunk = commodity_records[chunk_start:chunk_start + 500]
        db.bulk_insert_mappings(CommodityIndicator, chunk)
    db.commit()
    commodity_count = len(commodity_records)
    logger.info(f"  [6/8] Commodity Indicators: Added {commodity_count} commodity benchmark records")

    # 7. Freight Rate Time-Series (~17,290 observations across 5 origins x 7 destinations)
    logger.info("  Generating freight rate historical series...")
    history = generate_all_history()
    for chunk_start in range(0, len(history), 1000):
        chunk = history[chunk_start:chunk_start + 1000]
        db.bulk_insert_mappings(FreightRate, chunk)
    db.commit()
    history_count = len(history)
    logger.info(f"  [7/8] Freight Rates: Added {history_count} weekly freight observations")

    # 8. Unified Historical Observations
    logger.info("  Generating unified multi-factor historical observations...")
    obs = generate_historical_observations(history)
    for chunk_start in range(0, len(obs), 1000):
        chunk = obs[chunk_start:chunk_start + 1000]
        db.bulk_insert_mappings(HistoricalObservation, chunk)
    db.commit()
    obs_count = len(obs)
    logger.info(f"  [8/8] Historical Observations: Added {obs_count} unified multi-factor records")

    logger.info("=========================================================")
    logger.info("  DEMO SEEDING COMPLETE: ALL 8 SYNTHETIC DATASETS ACTIVE  ")
    logger.info("=========================================================")

    return {
        "ports": ports_count,
        "vessels": vessels_count,
        "routes": routes_count,
        "freight_rates": history_count,
        "market_indicators": market_count,
        "port_congestion": congestion_count,
        "commodity_indicators": commodity_count,
        "historical_observations": obs_count,
    }
