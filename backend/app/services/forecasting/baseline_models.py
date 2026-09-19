import numpy as np
import pandas as pd
from typing import Tuple, Dict
from app.services.forecasting.base_model import BaseForecastModel
from app.models.enums import ForecastModelType

class PersistenceNaiveModel(BaseForecastModel):
    def __init__(self):
        super().__init__(ForecastModelType.PERSISTENCE_NAIVE)
        self.last_rate = None
        self.historical_volatility = 1.0

    def fit(self, df: pd.DataFrame, target_col: str = "freight_rate_usd_pmt") -> "PersistenceNaiveModel":
        sorted_df = df.sort_values("observation_date")
        rates = sorted_df[target_col].dropna().values
        if len(rates) > 0:
            self.last_rate = float(rates[-1])
            diffs = np.diff(rates)
            self.historical_volatility = float(np.std(diffs)) if len(diffs) > 1 else 1.0
        return self

    def predict(
        self,
        df: pd.DataFrame,
        horizon_days: int,
        target_col: str = "freight_rate_usd_pmt"
    ) -> Tuple[float, float, float, Dict[str, float]]:
        self.fit(df, target_col)
        p50 = round(self.last_rate if self.last_rate is not None else 25.0, 2)
        # Uncertainty widens with square root of time horizon
        dispersion = self.historical_volatility * np.sqrt(horizon_days / 7.0) * 1.28
        p10 = round(max(5.0, p50 - dispersion), 2)
        p90 = round(p50 + dispersion, 2)
        
        attributions = {
            "Latest Spot Observation": 1.0
        }
        return p10, p50, p90, attributions


class MovingAverageModel(BaseForecastModel):
    def __init__(self, window_days: int = 7):
        model_type = ForecastModelType.MOVING_AVERAGE_7D if window_days == 7 else ForecastModelType.MOVING_AVERAGE_30D
        super().__init__(model_type)
        self.window_days = window_days
        self.ma_rate = None
        self.std_rate = 1.0

    def fit(self, df: pd.DataFrame, target_col: str = "freight_rate_usd_pmt") -> "MovingAverageModel":
        sorted_df = df.sort_values("observation_date")
        rates = sorted_df[target_col].dropna().values
        if len(rates) >= self.window_days:
            window_slice = rates[-self.window_days:]
            self.ma_rate = float(np.mean(window_slice))
            self.std_rate = float(np.std(window_slice)) if len(window_slice) > 1 else 1.0
        elif len(rates) > 0:
            self.ma_rate = float(np.mean(rates))
            self.std_rate = float(np.std(rates)) if len(rates) > 1 else 1.0
        return self

    def predict(
        self,
        df: pd.DataFrame,
        horizon_days: int,
        target_col: str = "freight_rate_usd_pmt"
    ) -> Tuple[float, float, float, Dict[str, float]]:
        self.fit(df, target_col)
        p50 = round(self.ma_rate if self.ma_rate is not None else 25.0, 2)
        dispersion = max(0.5, self.std_rate * np.sqrt(horizon_days / 7.0) * 1.28)
        p10 = round(max(5.0, p50 - dispersion), 2)
        p90 = round(p50 + dispersion, 2)
        
        attributions = {
            f"Rolling {self.window_days}d Moving Average": 0.85,
            "Historical Variance": 0.15
        }
        return p10, p50, p90, attributions
