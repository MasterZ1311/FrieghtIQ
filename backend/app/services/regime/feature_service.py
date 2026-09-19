import numpy as np
import pandas as pd
from typing import List, Tuple, Optional, Dict, Any

class MarketRegimeFeatureService:
    """
    Transforms verified market observations and forecast parameters into
    chronologically indexed multi-signal feature matrices for regime classification.
    
    Adheres strictly to the Data Integrity policy:
    Only calculates signals from fields that genuinely exist in the database.
    Does not fabricate missing external indicators.
    """
    @staticmethod
    def extract_features(
        observations: List[Any],
        forecasts: Optional[List[Any]] = None
    ) -> Tuple[pd.DataFrame, List[str]]:
        if not observations or len(observations) < 14:
            raise ValueError("Insufficient observation history to construct regime feature matrix (min 14 days required)")

        # Convert observation models to sorted DataFrame
        records = [
            {
                "observation_date": o.observation_date,
                "freight_rate": float(o.freight_rate_usd_pmt),
                "bunker_price": float(o.bunker_vlsfo_usd) if o.bunker_vlsfo_usd is not None else None,
                "baltic_index": float(o.baltic_index_value) if o.baltic_index_value is not None else None,
                "congestion_origin": float(o.congestion_origin_days) if o.congestion_origin_days is not None else 0.0,
                "congestion_dest": float(o.congestion_dest_days) if o.congestion_dest_days is not None else 0.0,
            }
            for o in observations
        ]
        df = pd.DataFrame(records).sort_values("observation_date").reset_index(drop=True)

        # 1. Freight Returns (Momentum)
        df["rate_return_1d"] = df["freight_rate"].pct_change(1).fillna(0.0)
        df["rate_return_7d"] = df["freight_rate"].pct_change(7).fillna(0.0)
        df["rate_return_30d"] = df["freight_rate"].pct_change(30).fillna(0.0)

        # 2. Volatility Clustering
        df["rolling_volatility_7d"] = df["rate_return_1d"].rolling(window=7, min_periods=3).std().fillna(0.01)
        df["rolling_volatility_14d"] = df["rate_return_1d"].rolling(window=14, min_periods=5).std().fillna(0.015)
        df["rolling_volatility_30d"] = df["rate_return_1d"].rolling(window=30, min_periods=7).std().fillna(0.02)

        # 3. Bunker Fuel Signals (if available)
        if df["bunker_price"].notnull().any():
            df["bunker_price"] = df["bunker_price"].ffill().bfill()
            df["bunker_change_7d"] = df["bunker_price"].pct_change(7).fillna(0.0)
            df["bunker_volatility_14d"] = df["bunker_price"].pct_change(1).rolling(14, min_periods=5).std().fillna(0.01)
        else:
            df["bunker_change_7d"] = 0.0
            df["bunker_volatility_14d"] = 0.0

        # 4. Baltic Index Signals (if available)
        if df["baltic_index"].notnull().any():
            df["baltic_index"] = df["baltic_index"].ffill().bfill()
            df["baltic_change_7d"] = df["baltic_index"].pct_change(7).fillna(0.0)
        else:
            df["baltic_change_7d"] = 0.0

        # 5. Port Congestion Signals
        df["congestion_index"] = df["congestion_origin"] + df["congestion_dest"]
        df["congestion_change_7d"] = df["congestion_index"].diff(7).fillna(0.0)

        # 6. Seasonality Harmonics
        dates = pd.to_datetime(df["observation_date"])
        day_of_year = dates.dt.dayofyear
        df["month"] = dates.dt.month
        df["quarter"] = dates.dt.quarter
        df["seasonal_signal"] = np.sin(2 * np.pi * (day_of_year - 60) / 365.25)
        df["seasonal_sin"] = np.sin(2 * np.pi * day_of_year / 365.25)
        df["seasonal_cos"] = np.cos(2 * np.pi * day_of_year / 365.25)

        # 7. Forward Forecast Features (Phase 5 integration)
        forecast_slope = 0.0
        forecast_spread = 0.0
        forecast_p50_val = None
        if forecasts and len(forecasts) >= 2:
            sorted_fc = sorted(forecasts, key=lambda f: f.horizon_days)
            f_near = sorted_fc[0] # e.g. 7d
            f_far = sorted_fc[-1] # e.g. 30d or 90d
            h_delta = max(1, f_far.horizon_days - f_near.horizon_days)
            forecast_slope = (f_far.predicted_p50 - f_near.predicted_p50) / h_delta
            forecast_spread = (f_far.predicted_p90 - f_far.predicted_p10) / (f_far.predicted_p50 or 1.0)
            forecast_p50_val = f_near.predicted_p50

        df["forecast_slope"] = forecast_slope
        df["forecast_spread"] = forecast_spread

        feature_cols = [
            "rate_return_7d",
            "rolling_volatility_14d",
            "rate_return_30d",
            "seasonal_signal",
            "bunker_change_7d",
            "congestion_change_7d",
            "forecast_slope"
        ]

        return df, feature_cols
