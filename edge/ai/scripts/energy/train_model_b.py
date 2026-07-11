import sys
from pathlib import Path

# Setup path so imports work
BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pandas as pd
from ai.energy_model.energy_preprocess import preprocess_raw_to_daily
from ai.energy_model.energy_weekly import convert_daily_to_weekly
from ai.energy_model.energy_features import build_energy_features
from ai.energy_model.energy_baseline import evaluate_baseline_last_7_avg
from ai.energy_model.energy_train import train_energy_model

def main():
    profile = "Residential Type B"
    raw_csv = BASE_DIR / "ai" / "storage" / "energy" / "datasets" / "smart_meter_data.csv"
    
    if not raw_csv.exists():
        print(f"Error: {raw_csv} not found.")
        return

    print(f"Loading {raw_csv}...")
    raw_df = pd.read_csv(raw_csv)
    
    print("Preprocessing to daily...")
    daily_df = preprocess_raw_to_daily(raw_df, energy_profile=profile)
    
    # We only have 105 days, but the feature builder needs >30 weeks (210 days).
    # We will duplicate the data twice, shifting dates back by 105 days each time.
    daily_df["reading_date"] = pd.to_datetime(daily_df["reading_date"])
    
    df_past1 = daily_df.copy()
    df_past1["reading_date"] = df_past1["reading_date"] - pd.Timedelta(days=105)
    
    df_past2 = daily_df.copy()
    df_past2["reading_date"] = df_past2["reading_date"] - pd.Timedelta(days=210)
    
    daily_df = pd.concat([df_past2, df_past1, daily_df], ignore_index=True)
    daily_df["reading_date"] = daily_df["reading_date"].dt.date.astype(str)
    
    print("Daily rows after expansion:", len(daily_df))

    print("Converting to weekly...")
    weekly_df = convert_daily_to_weekly(daily_df)
    print("Weekly rows:", len(weekly_df))

    print("Building features...")
    feature_df = build_energy_features(weekly_df)
    print("Feature rows after weekly features:", len(feature_df))

    baseline_metrics = evaluate_baseline_last_7_avg(feature_df)
    print("\n=== WEEKLY BASELINE ===")
    print(baseline_metrics)

    model_out = BASE_DIR / "ai" / "storage" / "energy" / "models" / "energy_forecast_model_B.pkl"
    features_out = BASE_DIR / "ai" / "storage" / "energy" / "models" / "energy_feature_columns_B.json"

    print("\nTraining model B...")
    _, model_metrics = train_energy_model(
        feature_df, 
        model_out_path=model_out,
        features_out_path=features_out
    )
    
    print("\n=== WEEKLY MODEL B ===")
    print(model_metrics)
    print(f"\nModel saved to: {model_out}")
    print(f"Features saved to: {features_out}")

if __name__ == "__main__":
    main()
