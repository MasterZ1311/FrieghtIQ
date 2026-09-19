import numpy as np
import pandas as pd
from typing import List, Tuple

def create_forecasting_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Transforms raw market observation series into feature matrix.
    Ensures strict chronological sorting to prevent lookahead data leakage.
    """
    data = df.sort_values("observation_date").copy()
    
    # Target variable
    target_col = "freight_rate_usd_pmt"
    
    # Fill missing values if any
    data[target_col] = data[target_col].ffill().bfill()
    if "bunker_vlsfo_usd" in data.columns:
        data["bunker_vlsfo_usd"] = data["bunker_vlsfo_usd"].ffill().bfill()
    if "baltic_index_value" in data.columns:
        data["baltic_index_value"] = data["baltic_index_value"].ffill().bfill()
    if "congestion_origin_days" in data.columns:
        data["congestion_origin_days"] = data["congestion_origin_days"].fillna(2.0)
    if "congestion_dest_days" in data.columns:
        data["congestion_dest_days"] = data["congestion_dest_days"].fillna(3.0)

    # 1. Autoregressive Lags
    data["lag_1"] = data[target_col].shift(1)
    data["lag_7"] = data[target_col].shift(7)
    data["lag_14"] = data[target_col].shift(14)
    data["lag_30"] = data[target_col].shift(30)

    # 2. Rolling Momentum and Volatility
    data["rolling_mean_7"] = data[target_col].shift(1).rolling(window=7, min_periods=3).mean()
    data["rolling_std_7"] = data[target_col].shift(1).rolling(window=7, min_periods=3).std().fillna(0.5)
    data["rolling_mean_30"] = data[target_col].shift(1).rolling(window=30, min_periods=7).mean()
    data["rolling_std_30"] = data[target_col].shift(1).rolling(window=30, min_periods=7).std().fillna(1.0)

    # 3. Rate Returns (Momentum)
    data["rate_change_7d"] = (data["lag_1"] - data["lag_7"]).fillna(0.0)
    data["rate_change_14d"] = (data["lag_1"] - data["lag_14"]).fillna(0.0)

    # 4. Exogenous Drivers
    if "bunker_vlsfo_usd" in data.columns:
        data["bunker_lag_1"] = data["bunker_vlsfo_usd"].shift(1)
        data["bunker_pct_change_7"] = data["bunker_vlsfo_usd"].pct_change(7).shift(1).fillna(0.0)
    else:
        data["bunker_lag_1"] = 620.0
        data["bunker_pct_change_7"] = 0.0

    if "baltic_index_value" in data.columns:
        data["baltic_lag_1"] = data["baltic_index_value"].shift(1)
    else:
        data["baltic_lag_1"] = 1500.0

    data["total_congestion"] = data["congestion_origin_days"].shift(1) + data["congestion_dest_days"].shift(1)

    # 5. Seasonality (Sin/Cos Day of Year)
    if "observation_date" in data.columns:
        dates = pd.to_datetime(data["observation_date"])
        day_of_year = dates.dt.dayofyear
        data["sin_day_of_year"] = np.sin(2 * np.pi * day_of_year / 365.25)
        data["cos_day_of_year"] = np.cos(2 * np.pi * day_of_year / 365.25)
        data["month"] = dates.dt.month

    feature_cols = [
        "lag_1", "lag_7", "lag_14", "lag_30",
        "rolling_mean_7", "rolling_std_7",
        "rolling_mean_30", "rolling_std_30",
        "rate_change_7d", "rate_change_14d",
        "bunker_lag_1", "bunker_pct_change_7",
        "baltic_lag_1", "total_congestion",
        "sin_day_of_year", "cos_day_of_year"
    ]

    return data, feature_cols
