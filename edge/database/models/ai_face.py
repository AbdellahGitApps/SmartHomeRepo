from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from database.connection.database import Base


class Person(Base):

    __tablename__ = "persons"

    id = Column(Integer, primary_key=True)

    home_id = Column(
        Integer,
        ForeignKey("homes.id"),
        nullable=False
    )

    name = Column(String, nullable=False)

    role = Column(
        String,
        default="resident"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    embeddings = relationship(
        "FaceEmbedding",
        back_populates="person",
        cascade="all, delete-orphan"
    )


class FaceEmbedding(Base):

    __tablename__ = "face_embeddings"

    id = Column(Integer, primary_key=True)

    person_id = Column(
        Integer,
        ForeignKey("persons.id"),
        nullable=False
    )

    embedding_json = Column(
        String,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    person = relationship(
        "Person",
        back_populates="embeddings"
    )


class FaceEvent(Base):

    __tablename__ = "face_events"

    id = Column(Integer, primary_key=True)

    home_id = Column(
        Integer,
        ForeignKey("homes.id"),
        nullable=False
    )

    timestamp = Column(
        DateTime,
        default=datetime.utcnow
    )

    event_type = Column(
        String,
        nullable=False
    )

    person_id = Column(
        Integer,
        ForeignKey("persons.id"),
        nullable=True
    )

    score = Column(
        Float,
        nullable=True
    )

    snapshot_path = Column(
        String,
        nullable=True
    )