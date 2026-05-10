import pandas as pd

def convert_daily_to_weekly(daily_df: pd.DataFrame) -> pd.DataFrame:
    df = daily_df.copy()
    df["reading_date"] = pd.to_datetime(df["reading_date"])
    df = df.sort_values("reading_date").reset_index(drop=True)

    df["week_start"] = df["reading_date"] - pd.to_timedelta(df["reading_date"].dt.dayofweek, unit="D")

    weekly = (
        df.groupby("week_start")["consumption_kwh"]
        .sum()
        .reset_index()
    )

    weekly = weekly.rename(columns={
        "week_start": "reading_date",
        "consumption_kwh": "consumption_kwh"
    })

    weekly["reading_date"] = weekly["reading_date"].astype(str)
    return weekly