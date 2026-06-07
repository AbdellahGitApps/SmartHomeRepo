from pathlib import Path
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Ensure base dir is in sys.path so we can import core_database safely
base_dir = Path(__file__).resolve().parents[2]
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from core_database import get_database_path

db_path = get_database_path()
DATABASE_URL = f"sqlite:///{db_path.as_posix()}"

print(f"[DB] Using database: {db_path.resolve()}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()