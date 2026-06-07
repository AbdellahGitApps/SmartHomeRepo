import sqlite3
import threading
from pathlib import Path

# Unified thread-safe connection pool for SQLite
_db_lock = threading.Lock()

def get_database_path() -> Path:
    """Resolve the definitive path to the main database."""
    base = Path(__file__).resolve().parent
    candidates = [
        base / "database" / "smart_home_edge.db",
        base / "data" / "smart_home.db",
        base.parent / "data" / "smart_home.db",
        base / "smart_home.db",
    ]
    
    for p in candidates:
        if p.exists():
            return p

    # Fallback default
    default_path = base / "database" / "smart_home_edge.db"
    default_path.parent.mkdir(parents=True, exist_ok=True)
    return default_path

def get_db_connection():
    """Dependency generator for FastAPI routes to share a single DB connection logic safely."""
    path = get_database_path()
    
    with _db_lock:
        conn = sqlite3.connect(
            str(path), 
            check_same_thread=False, 
            timeout=10.0  # Prevent "database is locked"
        )
        conn.row_factory = sqlite3.Row
        conn.text_factory = str
        
        # Enforce foreign keys and WAL mode for better concurrency
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
