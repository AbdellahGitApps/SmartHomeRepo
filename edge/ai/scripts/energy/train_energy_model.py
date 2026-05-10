from app.energy_model.energy_data import load_daily_energy_dataset
from app.energy_model.energy_features import build_energy_features
from app.energy_model.energy_train import train_energy_model
from app.energy_model.energy_baseline import evaluate_baseline_last_7_avg
from app.energy_model.energy_weekly import convert_daily_to_weekly

def main():
    daily_df = load_daily_energy_dataset()
    print("Raw daily rows:", len(daily_df))

    weekly_df = convert_daily_to_weekly(daily_df)
    print("Weekly rows:", len(weekly_df))

    feature_df = build_energy_features(weekly_df)
    print("Feature rows after weekly features:", len(feature_df))

    baseline_metrics = evaluate_baseline_last_7_avg(feature_df)
    print("\n=== WEEKLY BASELINE ===")
    print(baseline_metrics)

    _, model_metrics = train_energy_model(feature_df)
    print("\n=== WEEKLY MODEL ===")
    print(model_metrics)

if __name__ == "__main__":
    main()