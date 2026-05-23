from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 🗄️ Database Connection URL (SQLite)
# Since the server runs from the 'edge' directory, the database file is located at ./database/smart_home_edge.db
DATABASE_URL = "sqlite:///./database/smart_home_edge.db"

# ⚙️ Create Database Engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Required for SQLite multi-threading in FastAPI
)

# 🔁 Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 🧱 Base class for all database models
Base = declarative_base()

# 🧪 Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
