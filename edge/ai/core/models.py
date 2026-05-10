from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

# ===== Face tables =====
class Person(Base):
    __tablename__ = "persons"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    role = Column(String, default="resident")
    created_at = Column(DateTime, default=datetime.utcnow)

    embeddings = relationship("FaceEmbedding", back_populates="person", cascade="all, delete-orphan")


class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    embedding_json = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    person = relationship("Person", back_populates="embeddings")


class FaceEvent(Base):
    __tablename__ = "face_events"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String, nullable=False)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    score = Column(Float, nullable=True)
    snapshot_path = Column(String, nullable=True)

# ===== Energy tables =====
class EnergyReading(Base):
    __tablename__ = "energy_readings"
    id = Column(Integer, primary_key=True)
    reading_date = Column(String, nullable=False, unique=True)
    consumption_kwh = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class EnergyForecast(Base):
    __tablename__ = "energy_forecasts"
    id = Column(Integer, primary_key=True)
    forecast_date = Column(String, nullable=False)
    predicted_kwh = Column(Float, nullable=False)
    run_type = Column(String, default="next_month")
    created_at = Column(DateTime, default=datetime.utcnow)


class EnergyInsight(Base):
    __tablename__ = "energy_insights"
    id = Column(Integer, primary_key=True)
    insight_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    severity = Column(String, default="info")
    created_at = Column(DateTime, default=datetime.utcnow)