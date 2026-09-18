"""
FreightIQ ML Feature Engineering
=================================
Deterministic, explainable feature extraction for freight rate prediction.
"""
import math
import numpy as np
import pandas as pd
from datetime import date


VESSEL_CLASS_ENCODING = {
    "Handysize": 0,
    "Supramax": 1,
    "Panamax": 2,
    "Capesize": 3,
}

ORIGIN_ENCODING = {
    "Australia": 0,
    "United States": 1,
    "Mozambique": 2,
    "Russia": 3,
    "Indonesia": 4,
}

DESTINATION_ENCODING = {
    "Paradip": 0,
    "Visakhapatnam": 1,
    "Gangavaram": 2,
    "Gopalpur": 3,
    "Dhamra": 4,
    "Sagar-Sandheads": 5,
    "Haldia": 6,
    "Thoothukudi": 7,
    "Chennai": 8,
    "Kamarajar": 9,
}

COMMODITY_ENCODING = {
    "Coal": 0,
    "Iron Ore": 1,
    "Grain": 2,
    "Fertilizer": 3,
    "Bauxite": 4,
}

ROUTE_DISTANCES = {
    ("Australia", "Thoothukudi"): 4850,
    ("Australia", "Chennai"): 5050,
    ("Australia", "Kamarajar"): 5060,
    ("Australia", "Paradip"): 5100,
    ("Australia", "Visakhapatnam"): 5200,
    ("Australia", "Gangavaram"): 5200,
    ("Australia", "Gopalpur"): 5150,
    ("Australia", "Dhamra"): 5250,
    ("Australia", "Sagar-Sandheads"): 5350,
    ("Australia", "Haldia"): 5400,
    ("United States", "Thoothukudi"): 12100,
    ("United States", "Chennai"): 12300,
    ("United States", "Kamarajar"): 12310,
    ("United States", "Paradip"): 12800,
    ("United States", "Visakhapatnam"): 12900,
    ("United States", "Gangavaram"): 12900,
    ("United States", "Gopalpur"): 12850,
    ("United States", "Dhamra"): 12950,
    ("United States", "Sagar-Sandheads"): 13050,
    ("United States", "Haldia"): 13100,
    ("Mozambique", "Thoothukudi"): 3400,
    ("Mozambique", "Chennai"): 3700,
    ("Mozambique", "Kamarajar"): 3720,
    ("Mozambique", "Paradip"): 4800,
    ("Mozambique", "Visakhapatnam"): 4900,
    ("Mozambique", "Gangavaram"): 4900,
    ("Mozambique", "Gopalpur"): 4850,
    ("Mozambique", "Dhamra"): 4950,
    ("Mozambique", "Sagar-Sandheads"): 5050,
    ("Mozambique", "Haldia"): 5100,
    ("Russia", "Thoothukudi"): 8800,
    ("Russia", "Chennai"): 9000,
    ("Russia", "Kamarajar"): 9020,
    ("Russia", "Paradip"): 9200,
    ("Russia", "Visakhapatnam"): 9300,
    ("Russia", "Gangavaram"): 9300,
    ("Russia", "Gopalpur"): 9250,
    ("Russia", "Dhamra"): 9350,
    ("Russia", "Sagar-Sandheads"): 9450,
    ("Russia", "Haldia"): 9500,
    ("Indonesia", "Thoothukudi"): 1850,
    ("Indonesia", "Chennai"): 1650,
    ("Indonesia", "Kamarajar"): 1660,
    ("Indonesia", "Paradip"): 2900,
    ("Indonesia", "Visakhapatnam"): 3000,
    ("Indonesia", "Gangavaram"): 3000,
    ("Indonesia", "Gopalpur"): 2950,
    ("Indonesia", "Dhamra"): 3050,
    ("Indonesia", "Sagar-Sandheads"): 3150,
    ("Indonesia", "Haldia"): 3200,
}


def get_distance(origin: str, destination: str) -> float:
    return ROUTE_DISTANCES.get((origin, destination), 5500)


def seasonality_features(ref_date: date) -> dict:
    """Return deterministic seasonal features for a given date."""
    day_of_year = ref_date.timetuple().tm_yday
    month = ref_date.month
    # Fourier seasonal components
    sin_annual = math.sin(2 * math.pi * day_of_year / 365)
    cos_annual = math.cos(2 * math.pi * day_of_year / 365)
    # Q4 peak demand factor (Indian power demand + weather)
    q4_flag = 1 if month in [10, 11, 12] else 0
    # Q1 post-monsoon flag
    q1_flag = 1 if month in [1, 2, 3] else 0
    # Monsoon (Jun–Sep reduces shipping activity in Indian Ocean)
    monsoon_flag = 1 if month in [6, 7, 8, 9] else 0
    return {
        "sin_annual": sin_annual,
        "cos_annual": cos_annual,
        "q4_demand_flag": q4_flag,
        "q1_demand_flag": q1_flag,
        "monsoon_flag": monsoon_flag,
        "month": month,
    }


def build_feature_vector(
    origin: str,
    destination: str,
    vessel_class: str,
    commodity: str,
    ref_date: date,
    bunker_price: float = 650.0,
    congestion_index: float = 0.5,
    vessel_availability: float = 0.5,
    demand_index: float = 0.55,
    lag_rate_1w: float = 0.0,    # Rate 1 week ago (normalized)
    lag_rate_4w: float = 0.0,    # Rate 4 weeks ago (normalized)
    lag_rate_12w: float = 0.0,   # Rate 12 weeks ago (normalized)
) -> np.ndarray:
    """Build the full feature vector for a single prediction."""
    distance = get_distance(origin, destination) / 15000.0  # Normalize by max distance

    seasonal = seasonality_features(ref_date)

    features = [
        ORIGIN_ENCODING.get(origin, 0) / 4.0,
        DESTINATION_ENCODING.get(destination, 0) / 6.0,
        VESSEL_CLASS_ENCODING.get(vessel_class, 1) / 3.0,
        COMMODITY_ENCODING.get(commodity, 0) / 4.0,
        distance,
        bunker_price / 1000.0,
        congestion_index,
        vessel_availability,
        demand_index,
        lag_rate_1w,
        lag_rate_4w,
        lag_rate_12w,
        seasonal["sin_annual"],
        seasonal["cos_annual"],
        float(seasonal["q4_demand_flag"]),
        float(seasonal["q1_demand_flag"]),
        float(seasonal["monsoon_flag"]),
    ]
    return np.array(features, dtype=np.float32)


FEATURE_NAMES = [
    "origin_enc",
    "destination_enc",
    "vessel_class_enc",
    "commodity_enc",
    "distance_norm",
    "bunker_price_norm",
    "congestion_index",
    "vessel_availability",
    "demand_index",
    "lag_rate_1w",
    "lag_rate_4w",
    "lag_rate_12w",
    "sin_annual",
    "cos_annual",
    "q4_demand_flag",
    "q1_demand_flag",
    "monsoon_flag",
]


def build_training_dataset(records: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    """Build X, y arrays from a list of freight rate records."""
    df = pd.DataFrame(records)
    df = df.sort_values(["origin", "destination", "vessel_class", "date"]).reset_index(drop=True)

    rows = []
    targets = []

    for key, group in df.groupby(["origin", "destination", "vessel_class", "commodity"]):
        origin, dest, vc, comm = key
        rates = group["rate_usd_per_mt"].values
        base = rates.mean()

        for i in range(12, len(group)):
            row = group.iloc[i]
            ref_date = row["date"] if hasattr(row["date"], "month") else pd.Timestamp(row["date"]).date()

            lag_1 = rates[i - 1] / base - 1.0
            lag_4 = rates[i - 4] / base - 1.0
            lag_12 = rates[i - 12] / base - 1.0

            feat = build_feature_vector(
                origin=origin,
                destination=dest,
                vessel_class=vc,
                commodity=comm,
                ref_date=ref_date,
                bunker_price=row.get("bunker_price", 650.0),
                congestion_index=row.get("congestion_index", 0.5),
                vessel_availability=row.get("vessel_availability", 0.5),
                demand_index=row.get("demand_index", 0.55),
                lag_rate_1w=lag_1,
                lag_rate_4w=lag_4,
                lag_rate_12w=lag_12,
            )
            rows.append(feat)
            targets.append(row["rate_usd_per_mt"])

    if not rows:
        return np.zeros((0, len(FEATURE_NAMES))), np.zeros(0)

    return np.array(rows), np.array(targets)
