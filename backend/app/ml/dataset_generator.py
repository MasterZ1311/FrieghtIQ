"""
FreightIQ ML Dataset Generator
==============================
Deterministic, reproducible synthetic data generator for maritime dry bulk freight forecasting.
Captures key market dynamics:
- Mean-reverting freight rate equilibrium
- Cyclical and seasonal oscillations (monsoon lulls, Q4 energy demand surges)
- Correlated bunker/fuel price random walks
- Port congestion premiums and supply bottle-necks
- Fleet supply / vessel availability and industrial demand indices
- Commodity index proxies

All generated series are deterministic (default seed=42) and explicitly tagged as DEMO/SYNTHETIC.
"""
from __future__ import annotations
import math
import random
from datetime import date, timedelta
from typing import Any, Dict, List, Optional
import pandas as pd


# ─── Reference Route Distances (Nautical Miles) ──────────────────────────────
ROUTE_DISTANCES: Dict[tuple[str, str], float] = {
    ("Australia", "Paradip"): 5100.0,
    ("Australia", "Visakhapatnam"): 5200.0,
    ("Australia", "Gangavaram"): 5200.0,
    ("Australia", "Gopalpur"): 5150.0,
    ("Australia", "Dhamra"): 5250.0,
    ("Australia", "Sagar-Sandheads"): 5350.0,
    ("Australia", "Haldia"): 5400.0,
    ("United States", "Paradip"): 12800.0,
    ("United States", "Visakhapatnam"): 12900.0,
    ("United States", "Gangavaram"): 12900.0,
    ("United States", "Gopalpur"): 12850.0,
    ("United States", "Dhamra"): 12950.0,
    ("United States", "Sagar-Sandheads"): 13050.0,
    ("United States", "Haldia"): 13100.0,
    ("Mozambique", "Paradip"): 4800.0,
    ("Mozambique", "Visakhapatnam"): 4900.0,
    ("Mozambique", "Gangavaram"): 4900.0,
    ("Mozambique", "Gopalpur"): 4850.0,
    ("Mozambique", "Dhamra"): 4950.0,
    ("Mozambique", "Sagar-Sandheads"): 5050.0,
    ("Mozambique", "Haldia"): 5100.0,
    ("Russia", "Paradip"): 9200.0,
    ("Russia", "Visakhapatnam"): 9300.0,
    ("Russia", "Gangavaram"): 9300.0,
    ("Russia", "Gopalpur"): 9250.0,
    ("Russia", "Dhamra"): 9350.0,
    ("Russia", "Sagar-Sandheads"): 9450.0,
    ("Russia", "Haldia"): 9500.0,
    ("Indonesia", "Paradip"): 2900.0,
    ("Indonesia", "Visakhapatnam"): 3000.0,
    ("Indonesia", "Gangavaram"): 3000.0,
    ("Indonesia", "Gopalpur"): 2950.0,
    ("Indonesia", "Dhamra"): 3050.0,
    ("Indonesia", "Sagar-Sandheads"): 3150.0,
    ("Indonesia", "Haldia"): 3200.0,
}

# ─── Base Freight Rates (USD/MT) ─────────────────────────────────────────────
BASE_FREIGHT_RATES: Dict[tuple[str, str], float] = {
    ("Australia", "Handysize"): 18.0,
    ("Australia", "Supramax"): 13.5,
    ("Australia", "Panamax"): 10.5,
    ("Australia", "Capesize"): 7.0,
    ("United States", "Handysize"): 38.0,
    ("United States", "Supramax"): 30.0,
    ("United States", "Panamax"): 24.0,
    ("United States", "Capesize"): 18.0,
    ("Mozambique", "Handysize"): 25.0,
    ("Mozambique", "Supramax"): 19.0,
    ("Mozambique", "Panamax"): 15.5,
    ("Mozambique", "Capesize"): 11.0,
    ("Russia", "Handysize"): 28.0,
    ("Russia", "Supramax"): 22.0,
    ("Russia", "Panamax"): 17.0,
    ("Russia", "Capesize"): 12.5,
    ("Indonesia", "Handysize"): 8.5,
    ("Indonesia", "Supramax"): 6.5,
    ("Indonesia", "Panamax"): 5.0,
    # Indonesia + Capesize omitted (draft/berth incompatible)
}

DEFAULT_COMMODITY_MAP: Dict[str, str] = {
    "Australia": "Coal",
    "United States": "Coal",
    "Mozambique": "Coal",
    "Russia": "Coal",
    "Indonesia": "Coal",
}


def get_distance(origin: str, destination: str) -> float:
    """Return distance in nautical miles with sensible default."""
    return ROUTE_DISTANCES.get((origin, destination), 5500.0)


def generate_route_history(
    origin: str,
    destination: str,
    vessel_class: str,
    commodity: str = "Coal",
    start_date: date = date(2022, 1, 1),
    weeks: int = 156,  # 3 full years of weekly observations
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """
    Generate a deterministic synthetic weekly time series for a single route & vessel combination.
    """
    base = BASE_FREIGHT_RATES.get((origin, vessel_class))
    if base is None:
        # If incompatible (e.g. Indonesia Capesize), return empty
        return []

    # Compute route-specific distance factor
    dist = get_distance(origin, destination)
    distance_factor = (dist / 5000.0) ** 0.35  # mild economies of distance scale

    # Deterministic RNG keyed by route
    rng = random.Random(seed + hash((origin, destination, vessel_class, commodity)) % 100000)

    records: List[Dict[str, Any]] = []
    rate = base * distance_factor
    bunker = 640.0
    congestion = 0.50
    demand = 0.55
    commodity_index = 100.0  # Base 100 commodity price index proxy

    # Destination-specific baseline congestion
    dest_congestion_bias = {
        "Paradip": 0.65,
        "Haldia": 0.75,
        "Visakhapatnam": 0.50,
        "Gangavaram": 0.35,
        "Gopalpur": 0.30,
        "Dhamra": 0.40,
        "Sagar-Sandheads": 0.55,
    }.get(destination, 0.50)

    for w in range(weeks):
        current_date = start_date + timedelta(weeks=w)
        month = current_date.month

        # Seasonal factors:
        # - Monsoon (Jun-Sep): wet season reduces handling capacity and Asian coastal shipping
        # - Q4 (Oct-Dec): pre-winter Indian power plant restocking surge
        seasonal_cycle = 1.0 + 0.14 * math.sin(2 * math.pi * (month - 2) / 12.0)
        if month in (10, 11, 12):
            seasonal_cycle += 0.05
        elif month in (7, 8):
            seasonal_cycle -= 0.04

        # Bunker price stochastic process (mean-reverting geometric walk)
        bunker_shock = rng.gauss(0, 0.018)
        bunker = bunker * (1.0 + bunker_shock) + 0.05 * (630.0 - bunker)
        bunker = max(380.0, min(950.0, bunker))

        # Congestion random walk with destination attractor
        congestion = congestion + 0.10 * (dest_congestion_bias - congestion) + rng.gauss(0, 0.035)
        congestion = max(0.10, min(0.95, congestion))

        # Cargo Demand index (industrial cycle + seasonal pull)
        demand_target = 0.55 + 0.10 * math.sin(2 * math.pi * (month - 3) / 12.0)
        demand = demand + 0.12 * (demand_target - demand) + rng.gauss(0, 0.03)
        demand = max(0.20, min(0.95, demand))

        # Fleet/vessel availability (inversely correlated to demand with lag)
        vessel_availability = max(0.10, min(0.90, 1.0 - demand * 0.9 + rng.gauss(0, 0.04)))

        # Commodity price proxy (e.g. coking/thermal coal benchmark index)
        commodity_index = commodity_index + 0.08 * (105.0 - commodity_index) + rng.gauss(0, 1.8)
        commodity_index = max(60.0, min(180.0, commodity_index))

        # Macroeconomic equilibrium price
        bunker_elasticity = 0.16 * (bunker / 650.0 - 1.0)
        congestion_premium = 0.10 * (congestion - 0.50)
        demand_pull = 0.15 * (demand - 0.55)
        availability_discount = -0.08 * (vessel_availability - 0.50)
        commodity_influence = 0.05 * (commodity_index / 100.0 - 1.0)

        equilibrium = (
            base
            * distance_factor
            * seasonal_cycle
            * (
                1.0
                + bunker_elasticity
                + congestion_premium
                + demand_pull
                + availability_discount
                + commodity_influence
            )
        )

        # Mean-reverting rate process towards equilibrium with idiosyncratic shock
        shock = rng.gauss(0, 0.025)
        rate = rate + 0.20 * (equilibrium - rate) + (base * distance_factor) * shock
        # Physical bounds
        rate = max(base * distance_factor * 0.45, min(base * distance_factor * 2.20, rate))

        # Baltic Panamax Index (BPI) proxy
        bpi_multiplier = {"Handysize": 0.65, "Supramax": 0.85, "Panamax": 1.0, "Capesize": 1.45}
        bpi = (1400.0 + 900.0 * demand + rng.gauss(0, 80)) * bpi_multiplier.get(vessel_class, 1.0)

        # Approximate Time Charter Equivalent (TCE)
        cargo_dwt = {"Handysize": 35000, "Supramax": 58000, "Panamax": 74000, "Capesize": 175000}.get(vessel_class, 70000)
        daily_fuel = {"Handysize": 22.0, "Supramax": 28.0, "Panamax": 34.0, "Capesize": 58.0}.get(vessel_class, 32.0)
        speed = 14.0
        sea_days = dist / (speed * 24.0)
        port_days = 5.0
        total_days = max(1.0, sea_days + port_days)
        voyage_revenue = rate * cargo_dwt
        voyage_expenses = (daily_fuel * sea_days + (daily_fuel * 0.15) * port_days) * bunker + 40000.0
        tce = (voyage_revenue - voyage_expenses) / total_days

        records.append({
            "date": current_date,
            "origin": origin,
            "destination": destination,
            "vessel_class": vessel_class,
            "commodity": commodity,
            "rate_usd_per_mt": round(rate, 2),
            "tce_usd_per_day": round(max(1500.0, tce), 0),
            "bunker_price": round(bunker, 1),
            "congestion_index": round(congestion, 3),
            "vessel_availability": round(vessel_availability, 3),
            "demand_index": round(demand, 3),
            "commodity_index": round(commodity_index, 2),
            "bpi_index": round(bpi, 1),
            "distance_nm": round(dist, 1),
            "is_demo": True,
        })

    return records


def generate_full_synthetic_dataset(
    weeks: int = 156,
    seed: int = 42,
    as_dataframe: bool = True,
) -> pd.DataFrame | List[Dict[str, Any]]:
    """
    Generate the complete synthetic dataset covering all benchmark origins,
    destinations, vessel types, and market proxies.
    """
    origins = ["Australia", "United States", "Mozambique", "Russia", "Indonesia"]
    destinations = ["Paradip", "Visakhapatnam", "Gangavaram", "Gopalpur", "Dhamra", "Sagar-Sandheads", "Haldia"]
    vessel_classes = ["Handysize", "Supramax", "Panamax", "Capesize"]

    all_records: List[Dict[str, Any]] = []

    for origin in origins:
        commodity = DEFAULT_COMMODITY_MAP.get(origin, "Coal")
        for dest in destinations:
            for vc in vessel_classes:
                # Disallow known physically impossible / incompatible pairings
                if origin == "Indonesia" and vc == "Capesize":
                    continue
                # Haldia has 9.5m max draft, cannot take Capesize or fully loaded Panamax
                if dest == "Haldia" and vc in ("Capesize", "Panamax"):
                    continue
                # Gopalpur draft is 11.0m, Capesize incompatible
                if dest == "Gopalpur" and vc in ("Capesize", "Panamax"):
                    continue

                route_records = generate_route_history(
                    origin=origin,
                    destination=dest,
                    vessel_class=vc,
                    commodity=commodity,
                    weeks=weeks,
                    seed=seed,
                )
                all_records.extend(route_records)

    if as_dataframe:
        df = pd.DataFrame(all_records)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(["origin", "destination", "vessel_class", "date"]).reset_index(drop=True)
        return df

    return all_records
