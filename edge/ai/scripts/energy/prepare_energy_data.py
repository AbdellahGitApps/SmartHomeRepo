from app.core.db import Base, engine, SessionLocal
from app.energy_model.energy_data import load_raw_energy_dataset, save_daily_energy_dataset, save_daily_readings_to_db
from app.energy_model.energy_preprocess import preprocess_raw_to_daily

def main():
    Base.metadata.create_all(bind=engine)

    raw_df = load_raw_energy_dataset()
    daily_df = preprocess_raw_to_daily(raw_df)
    save_daily_energy_dataset(daily_df)

    db = SessionLocal()
    save_daily_readings_to_db(db, daily_df)
    db.close()

    print("Daily energy dataset prepared and saved.")
    print(f"Rows: {len(daily_df)}")

if __name__ == "__main__":
    main()