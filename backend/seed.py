"""
FreightIQ — Standalone Database Seeder CLI
=========================================
Populates SQLite with clearly labelled DEMO/SYNTHETIC datasets for all 8 categories:
1. Freight rates
2. Ports
3. Vessels
4. Routes
5. Market indicators
6. Congestion
7. Commodity indicators
8. Historical observations

Usage:
  python seed.py [--force] [--retrain]
"""
import argparse
import sys
import time
from app.database import engine, Base, SessionLocal
from app.seed.seeder import seed_database
from app.services.forecast_service import ensure_model_trained


def main():
    parser = argparse.ArgumentParser(description="FreightIQ Synthetic Database Seeder")
    parser.add_argument("--force", action="store_true", help="Force clear existing tables and re-seed from scratch")
    parser.add_argument("--retrain", action="store_true", help="Re-train ML models after seeding")
    args = parser.parse_args()

    print("\n=======================================================")
    print(" FreightIQ Database Seeder [DEMO MODE]                ")
    print(" Notice: All datasets are synthetic / demonstration    ")
    print("=======================================================\n")

    # Ensure tables exist
    print("Step 1: Creating database tables if not existing...")
    Base.metadata.create_all(bind=engine)
    print("        [OK] Database schema initialized.")

    # Seed data
    print(f"Step 2: Seeding demo datasets (force={args.force})...")
    start_time = time.time()
    db = SessionLocal()
    try:
        counts = seed_database(db, force=args.force)
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

    elapsed = time.time() - start_time
    print(f"        [OK] Seeding finished in {elapsed:.2f} seconds.\n")

    print("--- Seed Summary Table ---")
    for category, count in counts.items():
        print(f"  * {category.replace('_', ' ').title():<28}: {count:>6,} records [DEMO]")

    # Warm up ML model
    print("\nStep 3: Verifying / training ML forecasting model on synthetic series...")
    db = SessionLocal()
    try:
        ensure_model_trained(db, force=args.retrain)
        print("        [OK] ML model trained and ready.")
    except Exception as e:
        print(f"        [WARNING] ML model warm-up encountered: {e}")
    finally:
        db.close()

    print("\n=======================================================")
    print(" Database ready for development and scenario analysis. ")
    print("=======================================================\n")


if __name__ == "__main__":
    main()
