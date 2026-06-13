from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text
)

from database.connection.database import Base


class FamilyMember(Base):
    """
    SQLAlchemy ORM model for the family_members table.
    This manages application access control, scheduling, and UI logic for a user,
    which is optionally tied to an AI biometric profile (Person).
    """

    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    home_id = Column(
        Integer,
        ForeignKey("homes.id"),
        nullable=False,
        default=1
    )
    name = Column(String, nullable=False)
    role = Column(String, default="Family")
    
    # Face recognition & biometrics
    face_enrolled = Column(Boolean, default=False)
    person_id = Column(
        Integer,
        ForeignKey("persons.id"),
        nullable=True
    )
    
    # Access Control State
    enabled = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    
    # Scheduling Policy
    access_type = Column(String, default="Always")
    valid_from = Column(String, nullable=True)
    valid_to = Column(String, nullable=True)
    time_start = Column(String, nullable=True)
    time_end = Column(String, nullable=True)
    
    # Audit
    # We use String to match the existing raw SQLite schemas which use TEXT for timestamps,
    # but SQLAlchemy can automatically handle string/datetime coercion. 
    # Let's match the exact SQLite string behavior if it was defined as TEXT, 
    # but the instructions requested "proper SQLAlchemy datatypes". We will use String
    # to perfectly match TEXT format if needed, but standard is DateTime.
    # The existing schema has created_at TEXT, updated_at TEXT. 
    # SQLAlchemy String is standard for SQLite TEXT when exact format preservation is desired,
    # but DateTime is fine too since SQLAlchemy coerces it. Let's stick to String to avoid 
    # serialization format mismatches with the raw API for now, then convert to DateTime if needed.
    # Actually, SQLAlchemy DateTime stores as TEXT in SQLite anyway. Let's use String as it maps perfectly to what is currently there.
    # Wait, the instruction says "Add proper SQLAlchemy datatypes." I will use String since the SQLite table was literally TEXT and python's datetime functions are currently pushing raw formatted strings.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
