from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)

from database.connection.database import Base


class EnergyReading(Base):

    __tablename__ = "energy_readings"

    id = Column(Integer, primary_key=True)

    home_id = Column(
        Integer,
        ForeignKey("homes.id"),
        nullable=False
    )

    reading_date = Column(
        String,
        nullable=False
    )

    consumption_kwh = Column(
        Float,
        nullable=False
    )

    source = Column(
        String,
        default="mqtt"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            "home_id",
            "reading_date"
        ),
    )


class EnergyForecast(Base):

    __tablename__ = "energy_forecasts"

    id = Column(Integer, primary_key=True)

    forecast_date = Column(String)

    predicted_kwh = Column(Float)

    run_type = Column(
        String,
        default="next_month"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class EnergyInsight(Base):

    __tablename__ = "energy_insights"

    id = Column(Integer, primary_key=True)

    insight_type = Column(String)

    title = Column(String)

    message = Column(String)

    severity = Column(
        String,
        default="info"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )