from app.core.db import SessionLocal
from app.energy_model.energy_data import load_daily_readings_from_db
from app.energy_model.energy_predict import forecast_next_month_total
from app.energy_model.energy_analyze import analyze_energy_usage
from app.energy_model.energy_recommend import generate_energy_recommendations

def main():
    db = SessionLocal()
    daily_df = load_daily_readings_from_db(db)
    db.close()

    result = forecast_next_month_total(daily_df, weeks=4)
    analysis = analyze_energy_usage(daily_df, result["predicted_month_total_kwh"])
    recs = generate_energy_recommendations(analysis)

    print("=== NEXT MONTH FORECAST (WEEKLY-BASED) ===")
    print(f"Predicted total kWh: {result['predicted_month_total_kwh']:.2f}")

    print("\n=== FORECASTED WEEKS ===")
    print(result["forecast_weeks"].to_string(index=False))

    print("\n=== ANALYSIS ===")
    for k, v in analysis.items():
        print(f"{k}: {v}")

    print("\n=== RECOMMENDATIONS ===")
    for r in recs:
        print(f"[{r['type'].upper()}] {r['title']}")
        print(r["message"])
        print()

if __name__ == "__main__":
    main()