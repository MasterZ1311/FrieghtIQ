"""
FreightIQ — Custom Real-World Data Loader
==========================================
Loads sanitized real logistics fixture data from CSV into the FreightIQ database.
See TEAM_DOCS/08_DATA_ACQUISITION_MASTER_GUIDE.md for full data acquisition guide.

Usage:
    # From e:/SIH21006/backend with venv active:
    python -m app.seed.custom_loader
    # Or with a custom CSV path:
    python -m app.seed.custom_loader path/to/your/fixtures.csv
"""

import csv
import sys
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def load_real_fixtures(csv_path: str = None) -> int:
    """
    Load sanitized real-world fixture data into FreightIQ database.

    Args:
        csv_path: Path to sanitized CSV fixture file. Defaults to
                  backend/app/seed/data/real_fixtures.csv

    Returns:
        Number of fixture records successfully inserted.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If required CSV columns are missing.
    """
    # Default to the bundled seed CSV
    if csv_path is None:
        csv_path = Path(__file__).parent / "data" / "real_fixtures.csv"

    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Fixture CSV not found: {csv_path}\n"
            "Please create the file per TEAM_DOCS/08_DATA_ACQUISITION_MASTER_GUIDE.md"
        )

    # Required columns
    required_cols = {
        "fixture_id", "route_code", "origin_port", "destination_port",
        "vessel_class", "cargo_type", "cargo_mt", "rate_usd_per_mt",
        "fixture_month", "source"
    }

    inserted = 0
    skipped = 0
    records = []

    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        # Read all rows first so we can skip comment rows
        all_rows = list(reader)
        # Filter out comment/blank rows before column validation
        data_rows = [
            r for r in all_rows
            if not r.get(reader.fieldnames[0] if reader.fieldnames else "", "").strip().startswith("#")
        ]

        # Validate columns
        missing = required_cols - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"CSV missing required columns: {missing}\n"
                f"Found columns: {reader.fieldnames}"
            )

        for row in data_rows:
            # Skip comment rows (fixture_id starts with #)
            if row.get("fixture_id", "").strip().startswith("#"):
                continue

            try:
                record = {
                    "fixture_id": row["fixture_id"].strip(),
                    "route_code": row["route_code"].strip(),
                    "origin_port": row["origin_port"].strip(),
                    "destination_port": row["destination_port"].strip(),
                    "vessel_class": row["vessel_class"].strip().lower(),
                    "cargo_type": row["cargo_type"].strip().lower(),
                    "cargo_mt": float(row["cargo_mt"]),
                    "rate_usd_per_mt": float(row["rate_usd_per_mt"]),
                    "fixture_month": row["fixture_month"].strip(),
                    "source": row["source"].strip(),
                }
                records.append(record)
                inserted += 1

            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping row {row.get('fixture_id', '?')}: {e}")
                skipped += 1

    # Print summary (can be extended to write to DB when models are connected)
    print(f"\n[OK] Real Fixture Loader Summary")
    print(f"   CSV file:        {csv_path}")
    print(f"   Records loaded:  {inserted}")
    print(f"   Records skipped: {skipped}")
    print(f"\n   Routes loaded:")
    for r in records:
        print(f"   -> {r['route_code']}: ${r['rate_usd_per_mt']}/MT | "
              f"{r['cargo_mt']:,.0f} MT {r['cargo_type']} | "
              f"Source: {r['source']}")

    print(f"\n   To integrate with DB, extend this function with SQLAlchemy session.")
    print(f"   See TEAM_DOCS/08_DATA_ACQUISITION_MASTER_GUIDE.md section 4 for full guide.\n")

    return inserted


def print_data_collection_checklist():
    """Print the data collection status checklist to terminal."""
    items = [
        "[ ] Father's company fixtures (min 15 records)",
        "[ ] Exim India Sep 11 fixture data extracted",
        "[ ] Global Timex Sep 18 fixture data extracted",
        "[ ] VOCPA 15,000 MT/day gazette confirmed",
        "[ ] Chennai JD-2 pig iron handling rate confirmed",
        "[ ] BDI 365-day historical CSV (FRED)",
        "[ ] Thoothukudi tidal data (INCOIS 30-day)",
        "[ ] Chennai tidal data (INCOIS 30-day)",
        "[ ] MV Vishva Vijay AIS snapshot captured",
        "[ ] MV Supra Monarch AIS snapshot captured",
        "[ ] verify_all.py still passing 12/12 after data load",
    ]
    print("\n" + "=" * 60)
    print("  FreightIQ Data Collection Checklist")
    print("  See TEAM_DOCS/08_DATA_ACQUISITION_MASTER_GUIDE.md")
    print("=" * 60)
    for item in items:
        print(f"  {item}")
    print("=" * 60 + "\n")




if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Accept optional CSV path argument
    csv_file = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        count = load_real_fixtures(csv_file)
        print_data_collection_checklist()
        sys.exit(0 if count > 0 else 1)
    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\nCSV format error: {e}")
        sys.exit(1)
