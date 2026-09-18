"""
FreightIQ ML Preprocessing & Feature Engineering
================================================
Handles data cleaning, time-series lag/rolling feature extraction, cyclical
seasonality encoding, and strict chronological train/test splitting to prevent lookahead leakage.
"""
from __future__ import annotations
import math
from datetime import date
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from app.ml.dataset_generator import ROUTE_DISTANCES, get_distance


VESSEL_CLASS_ENCODING: Dict[str, int] = {
    "Handysize": 0,
    "Supramax": 1,
    "Panamax": 2,
    "Capesize": 3,
}

ORIGIN_ENCODING: Dict[str, int] = {
    "Australia": 0,
    "United States": 1,
    "Mozambique": 2,
    "Russia": 3,
    "Indonesia": 4,
}

DESTINATION_ENCODING: Dict[str, int] = {
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

COMMODITY_ENCODING: Dict[str, int] = {
    "Coal": 0,
    "Iron Ore": 1,
    "Grain": 2,
    "Fertilizer": 3,
    "Bauxite": 4,
}

CANAL_TRANSIT_ROUTES = {
    ("United States", "Thoothukudi"),
    ("United States", "Chennai"),
    ("United States", "Kamarajar"),
    ("United States", "Paradip"),
    ("United States", "Visakhapatnam"),
    ("United States", "Gangavaram"),
    ("United States", "Gopalpur"),
    ("United States", "Dhamra"),
    ("United States", "Sagar-Sandheads"),
    ("United States", "Haldia"),
    ("Russia", "Thoothukudi"),
    ("Russia", "Chennai"),
    ("Russia", "Kamarajar"),
    ("Russia", "Paradip"),
    ("Russia", "Visakhapatnam"),
    ("Russia", "Gangavaram"),
    ("Russia", "Gopalpur"),
    ("Russia", "Dhamra"),
    ("Russia", "Sagar-Sandheads"),
    ("Russia", "Haldia"),
}

FEATURE_NAMES: List[str] = [
    "origin_enc",
    "destination_enc",
    "vessel_class_enc",
    "commodity_enc",
    "distance_norm",
    "canal_transit_flag",
    "bunker_price_norm",
    "congestion_index",
    "vessel_availability",
    "demand_index",
    "commodity_index_norm",
    "lag_rate_1w",
    "lag_rate_2w",
    "lag_rate_4w",
    "lag_rate_12w",
    "rolling_mean_4w",
    "rolling_mean_12w",
    "rolling_std_4w",
    "sin_annual",
    "cos_annual",
    "q4_demand_flag",
    "q1_demand_flag",
    "monsoon_flag",
]


def extract_seasonality_features(ref_date: date) -> Dict[str, float]:
    """Compute cyclical harmonics and seasonal flags for a given date."""
    day_of_year = ref_date.timetuple().tm_yday
    month = ref_date.month

    # Continuous annual Fourier cycle
    sin_annual = math.sin(2.0 * math.pi * day_of_year / 365.25)
    cos_annual = math.cos(2.0 * math.pi * day_of_year / 365.25)

    # Seasonal Indian Ocean and East Coast India freight flags
    q4_flag = 1.0 if month in (10, 11, 12) else 0.0
    q1_flag = 1.0 if month in (1, 2, 3) else 0.0
    monsoon_flag = 1.0 if month in (6, 7, 8, 9) else 0.0

    return {
        "sin_annual": sin_annual,
        "cos_annual": cos_annual,
        "month": float(month),
        "q4_demand_flag": q4_flag,
        "q1_demand_flag": q1_flag,
        "monsoon_flag": monsoon_flag,
    }


def build_single_feature_vector(
    origin: str,
    destination: str,
    vessel_class: str,
    commodity: str,
    ref_date: date,
    bunker_price: float = 640.0,
    congestion_index: float = 0.50,
    vessel_availability: float = 0.50,
    demand_index: float = 0.55,
    commodity_index: float = 100.0,
    lag_rate_1w: float = 0.0,
    lag_rate_2w: float = 0.0,
    lag_rate_4w: float = 0.0,
    lag_rate_12w: float = 0.0,
    rolling_mean_4w: float = 0.0,
    rolling_mean_12w: float = 0.0,
    rolling_std_4w: float = 0.0,
) -> np.ndarray:
    """
    Construct the normalized feature vector (1D np.ndarray) for a single inference call.
    """
    dist = get_distance(origin, destination)
    dist_norm = dist / 15000.0
    canal_flag = 1.0 if (origin, destination) in CANAL_TRANSIT_ROUTES else 0.0
    seasonal = extract_seasonality_features(ref_date)

    features = [
        ORIGIN_ENCODING.get(origin, 0) / 4.0,
        DESTINATION_ENCODING.get(destination, 0) / 6.0,
        VESSEL_CLASS_ENCODING.get(vessel_class, 1) / 3.0,
        COMMODITY_ENCODING.get(commodity, 0) / 4.0,
        dist_norm,
        canal_flag,
        bunker_price / 1000.0,
        congestion_index,
        vessel_availability,
        demand_index,
        commodity_index / 150.0,
        lag_rate_1w,
        lag_rate_2w,
        lag_rate_4w,
        lag_rate_12w,
        rolling_mean_4w,
        rolling_mean_12w,
        rolling_std_4w,
        seasonal["sin_annual"],
        seasonal["cos_annual"],
        seasonal["q4_demand_flag"],
        seasonal["q1_demand_flag"],
        seasonal["monsoon_flag"],
    ]
    return np.array(features, dtype=np.float32)


def process_tabular_dataset(
    data: pd.DataFrame | List[Dict[str, Any]],
) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Clean raw time-series records, compute chronological lags/rolling stats per route,
    and return (feature_df, X, y).
    """
    if isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data.copy()

    if df.empty:
        return pd.DataFrame(), np.zeros((0, len(FEATURE_NAMES))), np.zeros(0)

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["origin", "destination", "vessel_class", "commodity", "date"]).reset_index(drop=True)

    # Impute missing proxies if not present
    if "bunker_price" not in df.columns:
        df["bunker_price"] = 640.0
    if "congestion_index" not in df.columns:
        df["congestion_index"] = 0.50
    if "vessel_availability" not in df.columns:
        df["vessel_availability"] = 0.50
    if "demand_index" not in df.columns:
        df["demand_index"] = 0.55
    if "commodity_index" not in df.columns:
        df["commodity_index"] = 100.0

    feature_rows: List[np.ndarray] = []
    target_values: List[float] = []
    meta_rows: List[Dict[str, Any]] = []

    group_keys = ["origin", "destination", "vessel_class", "commodity"]
    for key, group in df.groupby(group_keys):
        origin, destination, vessel_class, commodity = key
        rates = group["rate_usd_per_mt"].values
        dates = group["date"].values
        bunkers = group["bunker_price"].values
        congestions = group["congestion_index"].values
        availabilities = group["vessel_availability"].values
        demands = group["demand_index"].values
        commodity_indices = group["commodity_index"].values

        base_mean = float(np.mean(rates)) if len(rates) > 0 else 10.0
        if base_mean <= 0:
            base_mean = 10.0

        # We need at least 12 weeks of historical context for full lag expansion
        min_lags = 12
        n = len(group)
        if n <= min_lags:
            continue

        for i in range(min_lags, n):
            ref_dt = pd.Timestamp(dates[i]).date()
            rate_t = rates[i]

            # Normalized relative lags (returns relative to route baseline)
            lag_1 = float(rates[i - 1] / base_mean - 1.0)
            lag_2 = float(rates[i - 2] / base_mean - 1.0)
            lag_4 = float(rates[i - 4] / base_mean - 1.0)
            lag_12 = float(rates[i - 12] / base_mean - 1.0)

            # Rolling stats over preceding window
            window_4 = rates[max(0, i - 4):i]
            window_12 = rates[max(0, i - 12):i]
            roll_mean_4 = float(np.mean(window_4) / base_mean - 1.0)
            roll_mean_12 = float(np.mean(window_12) / base_mean - 1.0)
            roll_std_4 = float(np.std(window_4) / base_mean) if len(window_4) > 1 else 0.0

            feat_vec = build_single_feature_vector(
                origin=origin,
                destination=destination,
                vessel_class=vessel_class,
                commodity=commodity,
                ref_date=ref_dt,
                bunker_price=float(bunkers[i]),
                congestion_index=float(congestions[i]),
                vessel_availability=float(availabilities[i]),
                demand_index=float(demands[i]),
                commodity_index=float(commodity_indices[i]),
                lag_rate_1w=lag_1,
                lag_rate_2w=lag_2,
                lag_rate_4w=lag_4,
                lag_rate_12w=lag_12,
                rolling_mean_4w=roll_mean_4,
                rolling_mean_12w=roll_mean_12,
                rolling_std_4w=roll_std_4,
            )

            feature_rows.append(feat_vec)
            target_values.append(rate_t)
            meta_rows.append({
                "date": dates[i],
                "origin": origin,
                "destination": destination,
                "vessel_class": vessel_class,
                "commodity": commodity,
                "rate_usd_per_mt": rate_t,
                "lag_1_rate": rates[i - 1],
                "roll_4_rate": float(np.mean(window_4)),
            })

    if not feature_rows:
        return pd.DataFrame(), np.zeros((0, len(FEATURE_NAMES))), np.zeros(0)

    feat_df = pd.DataFrame(meta_rows)
    X = np.array(feature_rows, dtype=np.float32)
    y = np.array(target_values, dtype=np.float32)

    return feat_df, X, y


def train_test_chronological_split(
    feat_df: pd.DataFrame,
    X: np.ndarray,
    y: np.ndarray,
    test_ratio: float = 0.20,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, pd.DataFrame, pd.DataFrame]:
    """
    Split time-series data chronologically by date cutoff to strictly prevent lookahead leakage.
    Ensures:
      train_dates.max() < test_dates.min()
    """
    if len(feat_df) == 0:
        raise ValueError("Cannot split empty dataframe.")

    dates = pd.to_datetime(feat_df["date"])
    unique_dates = sorted(dates.unique())
    cutoff_idx = int(len(unique_dates) * (1.0 - test_ratio))
    cutoff_date = unique_dates[cutoff_idx]

    train_mask = dates < cutoff_date
    test_mask = dates >= cutoff_date

    X_train = X[train_mask]
    y_train = y[train_mask]
    X_test = X[test_mask]
    y_test = y[test_mask]

    train_meta = feat_df[train_mask].reset_index(drop=True)
    test_meta = feat_df[test_mask].reset_index(drop=True)

    return X_train, y_train, X_test, y_test, train_meta, test_meta
