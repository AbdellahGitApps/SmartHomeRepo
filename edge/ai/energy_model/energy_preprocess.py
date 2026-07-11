import pandas as pd

def preprocess_raw_to_daily(raw_df: pd.DataFrame, energy_profile: str = "Residential Type A") -> pd.DataFrame:
    df = raw_df.copy()

    if energy_profile == "Residential Type B" or "Timestamp" in df.columns:
        df["datetime"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df = df.dropna(subset=["datetime"])
        
        df["Electricity_Consumed"] = pd.to_numeric(df["Electricity_Consumed"], errors="coerce")
        df = df.dropna(subset=["Electricity_Consumed"])
        
        df["reading_date"] = df["datetime"].dt.date.astype(str)
        
        daily = (
            df.groupby("reading_date")["Electricity_Consumed"]
            .sum()
            .reset_index()
        )
        
        daily["consumption_kwh"] = daily["Electricity_Consumed"]
        daily = daily.drop(columns=["Electricity_Consumed"])
        
        return daily

    else:
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