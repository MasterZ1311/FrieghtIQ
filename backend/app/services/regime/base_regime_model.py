from abc import ABC, abstractmethod
from typing import Tuple, Dict, List, Any
import numpy as np
import pandas as pd
from app.models.enums import MarketRegimeType

class MarketRegimeModel(ABC):
    """
    Abstract modular base class for maritime freight market regime detection.
    Decouples regime classification and API surfaces from specific underlying
    machine learning or statistical models.
    """
    def __init__(self, model_name: str, version: str, number_of_states: int = 4):
        self.model_name = model_name
        self.version = version
        self.number_of_states = number_of_states
        self.is_fitted = False

    @abstractmethod
    def fit(self, features_df: pd.DataFrame) -> "MarketRegimeModel":
        """
        Fit the regime model on chronological feature matrix.
        """
        pass

    @abstractmethod
    def predict(self, features_df: pd.DataFrame) -> Tuple[List[MarketRegimeType], np.ndarray]:
        """
        Decode the most probable regime sequence and return posterior probabilities matrix.
        Returns: (regime_sequence, posterior_probabilities_matrix)
        """
        pass

    @abstractmethod
    def predict_current_proba(self, features_df: pd.DataFrame) -> Dict[MarketRegimeType, float]:
        """
        Predict normalized posterior probabilities for the latest observation:
        { MarketRegimeType.BULL: 0.78, MarketRegimeType.BEAR: 0.02, ... }
        """
        pass
