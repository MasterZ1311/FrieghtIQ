from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, List
import pandas as pd
from app.models.enums import ForecastModelType

class BaseForecastModel(ABC):
    def __init__(self, model_type: ForecastModelType):
        self.model_type = model_type

    @abstractmethod
    def fit(self, df: pd.DataFrame, target_col: str = "freight_rate_usd_pmt") -> "BaseForecastModel":
        """
        Fit model on historical observation dataframe.
        """
        pass

    @abstractmethod
    def predict(
        self,
        df: pd.DataFrame,
        horizon_days: int,
        target_col: str = "freight_rate_usd_pmt"
    ) -> Tuple[float, float, float, Dict[str, float]]:
        """
        Returns: (predicted_p10, predicted_p50, predicted_p90, feature_attributions)
        """
        pass
