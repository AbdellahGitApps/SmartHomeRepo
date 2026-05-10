import pandas as pd
import numpy as np

def build_energy_features(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["reading_date"] = pd.to_datetime(data["reading_date"])
    data = data.sort_values("reading_date").reset_index(drop=True)

    data["day_of_week"] = data["reading_date"].dt.dayofweek
    data["day_of_month"] = data["reading_date"].dt.day
    data["month"] = data["reading_date"].dt.month
    data["day_of_year"] = data["reading_date"].dt.dayofyear
    data["week_of_year"] = data["reading_date"].dt.isocalendar().week.astype(int)
    data["is_weekend"] = data["day_of_week"].isin([4, 5]).astype(int)

    data["dow_sin"] = np.sin(2 * np.pi * data["day_of_week"] / 7)
    data["dow_cos"] = np.cos(2 * np.pi * data["day_of_week"] / 7)
    data["month_sin"] = np.sin(2 * np.pi * data["month"] / 12)
    data["month_cos"] = np.cos(2 * np.pi * data["month"] / 12)

    for lag in [1, 2, 3, 7, 14, 21, 30]:
        data[f"lag_{lag}"] = data["consumption_kwh"].shift(lag)

    for window in [3, 7, 14, 30]:
        data[f"rolling_mean_{window}"] = data["consumption_kwh"].rolling(window).mean().shift(1)
        data[f"rolling_std_{window}"] = data["consumption_kwh"].rolling(window).std().shift(1)
        data[f"rolling_min_{window}"] = data["consumption_kwh"].rolling(window).min().shift(1)
        data[f"rolling_max_{window}"] = data["consumption_kwh"].rolling(window).max().shift(1)

    data["diff_1"] = data["consumption_kwh"].diff(1).shift(1)
    data["diff_7"] = data["consumption_kwh"].diff(7).shift(1)

    data["target"] = data["consumption_kwh"]

    data = data.dropna().reset_index(drop=True)
    return data