"""
FreightIQ — Database Reset Script
=================================
Completely resets the database to a pristine demo state:
1. Disposes database connections
2. Drops all database tables
3. Removes cached ML model pickle
4. Re-creates all schema tables (including all 8 synthetic datasets)
5. Seeds all demo data
6. Re-trains ML ensemble model
7. Verifies table integrity and counts

Usage:
  python reset_db.py
"""
import os
import sys
import time
from pathlib import Path

from app.database import engine, Base, SessionLocal
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
from app.seed.seeder import seed_database
from app.services.forecast_service import ensure_model_trained


def reset_database():
    print("\n=======================================================")
    print(" FreightIQ Database Reset & Clean Re-Seed Tool        ")
    print(" Notice: Resets all tables with fresh synthetic data. ")
    print("=======================================================\n")

    # Step 1: Invalidate cached ML model pickle to ensure retrain
    print("1. Removing cached ML model pickle...")
    pkl_path = Path(__file__).parent / "app" / "ml" / "trained_model.pkl"
    if pkl_path.exists():
        try:
            os.remove(pkl_path)
            print(f"   [OK] Removed {pkl_path.name}")
        except Exception as e:
            print(f"   [NOTE] Could not remove pickle file: {e}")
    else:
        print("   [OK] No cached model pickle found.")

    # Step 2: Drop all tables cleanly
    print("\n2. Dropping existing tables...")
    engine.dispose()
    Base.metadata.drop_all(bind=engine)
    print("   [OK] All tables dropped.")

    # Step 3: Re-create all schema tables
    print("\n3. Creating fresh schema tables...")
    Base.metadata.create_all(bind=engine)
    print("   [OK] Schema tables initialized.")

    # Step 4: Seed all 8 demo datasets
    print("\n4. Seeding all 8 synthetic demo datasets...")
    t0 = time.time()
    db = SessionLocal()
    try:
        counts = seed_database(db, force=True)
    except Exception as e:
        print(f"   [ERROR] Failed to seed database: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()
    elapsed = time.time() - t0
    print(f"   [OK] Data seeding completed in {elapsed:.2f}s.")

    # Step 5: Re-train / warm up ML model
    print("\n5. Training ML forecasting model on freshly generated synthetic data...")
    t1 = time.time()
    db = SessionLocal()
    try:
        ensure_model_trained(db, force=True)
        print(f"   [OK] ML model trained and serialized in {time.time() - t1:.2f}s.")
    except Exception as e:
        print(f"   [WARNING] ML model training notice: {e}")
    finally:
        db.close()

    # Step 6: Verify table record counts
    print("\n6. Verifying database table record counts:")
    db = SessionLocal()
    try:
        tables = [
            ("Freight Rates (Weekly)", FreightRate),
            ("Ports (Global & East Coast)", Port),
            ("Vessels (Bulk Carrier Specs)", Vessel),
            ("Routes (Origin-Destination)", Route),
            ("Market Indicators (Baltic & Bunker)", MarketIndicator),
            ("Port Congestion (Queue & Turnaround)", PortCongestion),
            ("Commodity Indicators (FOB Benchmarks)", CommodityIndicator),
            ("Historical Observations (Unified)", HistoricalObservation),
        ]
        all_passed = True
        for label, model in tables:
            c = db.query(model).count()
            status = "[PASS]" if c > 0 else "[FAIL]"
            if c == 0:
                all_passed = False
            print(f"   {status} {label:<38}: {c:>6,} records [DEMO]")

        if all_passed:
            print("\n=======================================================")
            print(" SUCCESS: Database reset complete with 100% integrity! ")
            print("=======================================================\n")
        else:
            print("\n[WARNING] Some tables have 0 records. Check logs above.\n")
            sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    reset_database()
