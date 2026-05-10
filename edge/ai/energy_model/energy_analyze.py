import pandas as pd
from .energy_weekly import convert_daily_to_weekly

def analyze_energy_usage(daily_df: pd.DataFrame, forecast_month_kwh: float) -> dict:
    """
    يحلل الاستهلاك الأسبوعي بدل اليومي.
    """
    weekly_df = convert_daily_to_weekly(daily_df)
    weekly_df["reading_date"] = pd.to_datetime(weekly_df["reading_date"])
    weekly_df = weekly_df.sort_values("reading_date").reset_index(drop=True)

    last_1_week = weekly_df.tail(1)["consumption_kwh"].mean()
    last_4_weeks = weekly_df.tail(4)["consumption_kwh"].mean()
    overall_weekly_avg = weekly_df["consumption_kwh"].mean()

    weekly_trend = "stable"
    if last_1_week > last_4_weeks * 1.10:
        weekly_trend = "up"
    elif last_1_week < last_4_weeks * 0.90:
        weekly_trend = "down"

    expected_weekly_next_month = forecast_month_kwh / 4.0

    return {
        "last_1_week_kwh": float(last_1_week),
        "last_4_weeks_avg_kwh": float(last_4_weeks),
        "overall_weekly_avg_kwh": float(overall_weekly_avg),
        "weekly_trend": weekly_trend,
        "expected_weekly_next_month_kwh": float(expected_weekly_next_month),
        "predicted_month_total_kwh": float(forecast_month_kwh)
    }