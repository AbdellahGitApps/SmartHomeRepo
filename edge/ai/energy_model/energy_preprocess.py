import pandas as pd

def preprocess_raw_to_daily(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()

    df["datetime"] = pd.to_datetime(
        df["Date"] + " " + df["Time"],
        format="%d/%m/%Y %H:%M:%S",
        errors="coerce"
    )

    df = df.dropna(subset=["datetime"])

    df["Global_active_power"] = pd.to_numeric(df["Global_active_power"], errors="coerce")
    df = df.dropna(subset=["Global_active_power"])

    df["reading_date"] = df["datetime"].dt.date.astype(str)

    daily = (
        df.groupby("reading_date")["Global_active_power"]
        .sum()
        .reset_index()
    )

    daily["consumption_kwh"] = daily["Global_active_power"] / 60.0
    daily = daily.drop(columns=["Global_active_power"])

    return daily