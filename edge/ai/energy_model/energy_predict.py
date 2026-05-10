import json
import joblib
import pandas as pd
from app.core.config import ENERGY_MODEL_PATH, ENERGY_FEATURES_PATH
from .energy_features import build_energy_features
from .energy_weekly import convert_daily_to_weekly

def load_energy_model():
    model = joblib.load(ENERGY_MODEL_PATH)
    with open(ENERGY_FEATURES_PATH, "r", encoding="utf-8") as f:
        feature_columns = json.load(f)
    return model, feature_columns

def forecast_next_weeks(daily_df: pd.DataFrame, weeks: int = 4) -> pd.DataFrame:
    """
    يحوّل البيانات اليومية إلى أسبوعية ثم يتنبأ بالأسابيع القادمة.
    """
    model, feature_columns = load_energy_model()

    weekly_df = convert_daily_to_weekly(daily_df)
    weekly_df["reading_date"] = pd.to_datetime(weekly_df["reading_date"])
    weekly_df = weekly_df.sort_values("reading_date").reset_index(drop=True)

    forecasts = []

    for _ in range(weeks):
        feature_df = build_energy_features(weekly_df)
        last_row = feature_df.iloc[[-1]].copy()

        next_date = weekly_df["reading_date"].max() + pd.Timedelta(days=7)

        next_input = last_row.copy()
        next_input["day_of_week"] = next_date.dayofweek
        next_input["day_of_month"] = next_date.day
        next_input["month"] = next_date.month
        next_input["day_of_year"] = next_date.dayofyear
        next_input["week_of_year"] = int(next_date.isocalendar().week)
        next_input["is_weekend"] = int(next_date.dayofweek in [4, 5])

        # circular features
        import numpy as np
        next_input["dow_sin"] = np.sin(2 * np.pi * next_input["day_of_week"] / 7)
        next_input["dow_cos"] = np.cos(2 * np.pi * next_input["day_of_week"] / 7)
        next_input["month_sin"] = np.sin(2 * np.pi * next_input["month"] / 12)
        next_input["month_cos"] = np.cos(2 * np.pi * next_input["month"] / 12)

        pred = float(model.predict(next_input[feature_columns])[0])

        forecasts.append({
            "forecast_week_start": next_date.strftime("%Y-%m-%d"),
            "predicted_kwh": pred
        })

        weekly_df = pd.concat([
            weekly_df,
            pd.DataFrame([{
                "reading_date": next_date,
                "consumption_kwh": pred
            }])
        ], ignore_index=True)

    return pd.DataFrame(forecasts)

def forecast_next_month_total(daily_df: pd.DataFrame, weeks: int = 4) -> dict:
    """
    يتنبأ بـ 4 أسابيع قادمة ويحسب مجموعها كتقدير للشهر القادم.
    """
    forecast_df = forecast_next_weeks(daily_df, weeks=weeks)
    total_kwh = float(forecast_df["predicted_kwh"].sum())

    return {
        "forecast_weeks": forecast_df,
        "predicted_month_total_kwh": total_kwh
    }