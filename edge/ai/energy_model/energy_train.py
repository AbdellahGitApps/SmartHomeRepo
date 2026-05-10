import json
import joblib
import numpy as np

from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from app.core.config import ENERGY_MODEL_PATH, ENERGY_FEATURES_PATH

def mean_absolute_percentage_error_safe(y_true, y_pred):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    mask = y_true != 0
    if mask.sum() == 0:
        return None

    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)

def train_energy_model(feature_df):
    feature_columns = [
        "day_of_week",
        "day_of_month",
        "month",
        "day_of_year",
        "week_of_year",
        "is_weekend",
        "dow_sin",
        "dow_cos",
        "month_sin",
        "month_cos",
        "lag_1",
        "lag_2",
        "lag_3",
        "lag_7",
        "lag_14",
        "lag_21",
        "lag_30",
        "rolling_mean_3",
        "rolling_mean_7",
        "rolling_mean_14",
        "rolling_mean_30",
        "rolling_std_3",
        "rolling_std_7",
        "rolling_std_14",
        "rolling_std_30",
        "rolling_min_3",
        "rolling_min_7",
        "rolling_min_14",
        "rolling_min_30",
        "rolling_max_3",
        "rolling_max_7",
        "rolling_max_14",
        "rolling_max_30",
        "diff_1",
        "diff_7",
    ]

    X = feature_df[feature_columns]
    y = feature_df["target"]

    split_idx = int(len(feature_df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    model = HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.03,
        max_iter=500,
        max_depth=6,
        min_samples_leaf=10,
        l2_regularization=0.1,
        random_state=42
    )

    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    mae = float(mean_absolute_error(y_test, preds))
    rmse = float(mean_squared_error(y_test, preds) ** 0.5)
    r2 = float(r2_score(y_test, preds))
    mape = mean_absolute_percentage_error_safe(y_test, preds)

    metrics = {
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "mape_percent": mape,
        "test_size": int(len(X_test)),
    }

    joblib.dump(model, ENERGY_MODEL_PATH)

    with open(ENERGY_FEATURES_PATH, "w", encoding="utf-8") as f:
        json.dump(feature_columns, f, ensure_ascii=False, indent=2)

    return model, metrics