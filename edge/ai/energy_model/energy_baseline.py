import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

def mean_absolute_percentage_error_safe(y_true, y_pred):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    mask = y_true != 0
    if mask.sum() == 0:
        return None

    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)

def evaluate_baseline_last_7_avg(feature_df: pd.DataFrame):
    """
    Baseline بسيط:
    نتوقع أن target = rolling_mean_7
    """
    y_true = feature_df["target"]
    y_pred = feature_df["rolling_mean_7"]

    split_idx = int(len(feature_df) * 0.8)
    y_test = y_true.iloc[split_idx:]
    pred_test = y_pred.iloc[split_idx:]

    metrics = {
        "mae": float(mean_absolute_error(y_test, pred_test)),
        "rmse": float(mean_squared_error(y_test, pred_test) ** 0.5),
        "r2": float(r2_score(y_test, pred_test)),
        "mape_percent": mean_absolute_percentage_error_safe(y_test, pred_test),
        "test_size": int(len(y_test)),
    }
    return metrics