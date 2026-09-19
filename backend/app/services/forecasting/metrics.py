import numpy as np
from typing import Union, List

def calculate_mae(y_true: Union[np.ndarray, List[float]], y_pred: Union[np.ndarray, List[float]]) -> float:
    y_t = np.array(y_true, dtype=float)
    y_p = np.array(y_pred, dtype=float)
    return float(np.mean(np.abs(y_t - y_p)))

def calculate_rmse(y_true: Union[np.ndarray, List[float]], y_pred: Union[np.ndarray, List[float]]) -> float:
    y_t = np.array(y_true, dtype=float)
    y_p = np.array(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_t - y_p) ** 2)))

def calculate_mape(y_true: Union[np.ndarray, List[float]], y_pred: Union[np.ndarray, List[float]]) -> float:
    y_t = np.array(y_true, dtype=float)
    y_p = np.array(y_pred, dtype=float)
    # Avoid zero division
    mask = y_t != 0
    if not np.any(mask):
        return 0.0
    return float(np.mean(np.abs((y_t[mask] - y_p[mask]) / y_t[mask])) * 100.0)

def calculate_directional_accuracy(
    y_true: Union[np.ndarray, List[float]],
    y_pred: Union[np.ndarray, List[float]],
    y_base: Union[np.ndarray, List[float]]
) -> float:
    y_t = np.array(y_true, dtype=float)
    y_p = np.array(y_pred, dtype=float)
    y_b = np.array(y_base, dtype=float)
    
    actual_direction = np.sign(y_t - y_b)
    predicted_direction = np.sign(y_p - y_b)
    
    correct = (actual_direction == predicted_direction) | (actual_direction == 0)
    return float(np.mean(correct) * 100.0)

def calculate_pinball_loss(
    y_true: Union[np.ndarray, List[float]],
    y_pred_quantile: Union[np.ndarray, List[float]],
    quantile: float
) -> float:
    """
    Pinball loss for quantile evaluation:
    L_q(y, y_hat) = max(q * (y - y_hat), (q - 1) * (y - y_hat))
    """
    y_t = np.array(y_true, dtype=float)
    y_q = np.array(y_pred_quantile, dtype=float)
    err = y_t - y_q
    return float(np.mean(np.maximum(quantile * err, (quantile - 1.0) * err)))
