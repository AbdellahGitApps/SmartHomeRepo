from sqlalchemy.orm import Session

from ai.core.models import EnergyReading


class EnergyRepository:

    @staticmethod
    def create_or_update_reading(
        db: Session,
        home_id: int,
        reading_date: str,
        consumption_kwh: float,
    ):
        reading = (
            db.query(EnergyReading)
            .filter(
                EnergyReading.home_id == home_id,
                EnergyReading.reading_date == reading_date,
            )
            .first()
        )

        if reading:
            reading.consumption_kwh = consumption_kwh
        else:
            reading = EnergyReading(
                home_id=home_id,
                reading_date=reading_date,
                consumption_kwh=consumption_kwh,
            )
            db.add(reading)

        db.commit()
        db.refresh(reading)

        return reading

    @staticmethod
    def get_latest_reading(
        db: Session,
        home_id: int,
    ):
        return (
            db.query(EnergyReading)
            .filter(EnergyReading.home_id == home_id)
            .order_by(EnergyReading.reading_date.desc())
            .first()
        )

    @staticmethod
    def get_all_readings(
        db: Session,
        home_id: int,
    ):
        return (
            db.query(EnergyReading)
            .filter(EnergyReading.home_id == home_id)
            .order_by(EnergyReading.reading_date.asc())
            .all()
        )

    @staticmethod
    def get_reading_count(
        db: Session,
        home_id: int,
    ):
        return (
            db.query(EnergyReading)
            .filter(EnergyReading.home_id == home_id)
            .count()
        )