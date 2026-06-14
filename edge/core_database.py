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


# Relocated from main.py Phase 26A.2
def _d7_db_candidates():
    base = Path(__file__).resolve().parent
    candidates = [
        base / "database" / "smart_home_edge.db",
        base / "data" / "smart_home.db",
        base.parent / "data" / "smart_home.db",
        base / "ai" / "smart_home_models.db",
        base / "smart_home.db",
    ]
    for p in base.rglob("*.db"):
        if "__pycache__" not in str(p):
            candidates.append(p)

    clean = []
    for p in candidates:
        if p not in clean:
            clean.append(p)
    return clean

def _d7_table_names(conn):
    try:
        return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    except Exception:
        return set()

def _d7_find_db():
    fallback = None
    for p in _d7_db_candidates():
        if not p.exists():
            continue
        fallback = p
        try:
            conn = sqlite3.connect(str(p))
            tables = _d7_table_names(conn)
            conn.close()
            if "homes" in tables and "devices" in tables:
                return p
        except Exception:
            pass
    return fallback
