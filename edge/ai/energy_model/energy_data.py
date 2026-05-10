import pandas as pd
from sqlalchemy.orm import Session
from app.core.config import ENERGY_RAW_DATA_PATH, ENERGY_DAILY_DATA_PATH
from app.core.models import EnergyReading

def load_raw_energy_dataset() -> pd.DataFrame:
    df = pd.read_csv(
        ENERGY_RAW_DATA_PATH,
        sep=";",
        low_memory=False,
        na_values=["?"]
    )
    return df

def load_daily_energy_dataset() -> pd.DataFrame:
    return pd.read_csv(ENERGY_DAILY_DATA_PATH)

def save_daily_energy_dataset(df: pd.DataFrame) -> None:
    df.to_csv(ENERGY_DAILY_DATA_PATH, index=False)

def save_daily_readings_to_db(db: Session, df: pd.DataFrame) -> None:
    for _, row in df.iterrows():
        exists = db.query(EnergyReading).filter(
            EnergyReading.reading_date == row["reading_date"]
        ).first()

        if not exists:
            db.add(
                EnergyReading(
                    reading_date=row["reading_date"],
                    consumption_kwh=float(row["consumption_kwh"])
                )
            )
    db.commit()

def load_daily_readings_from_db(db: Session) -> pd.DataFrame:
    rows = db.query(EnergyReading).order_by(EnergyReading.reading_date.asc()).all()

    data = []
    for r in rows:
        data.append({
            "reading_date": r.reading_date,
            "consumption_kwh": r.consumption_kwh
        })

    return pd.DataFrame(data)