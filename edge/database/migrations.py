import sqlite3
from pathlib import Path


DEVICE_COLUMNS = {
    "mac_address": "TEXT",
    "device_ip": "TEXT",
    "camera_stream_url": "TEXT",
    "camera_capture_url": "TEXT",
    "firmware_version": "TEXT",
    "updated_at": "DATETIME",
    "last_seen_at": "DATETIME",
    "enabled": "INTEGER DEFAULT 1",
}


def get_default_db_path():
    return Path(__file__).resolve().parent / "smart_home_edge.db"


def table_exists(cursor, table_name):
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def get_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def add_column_if_missing(cursor, table_name, column_name, column_type):
    existing_columns = get_columns(cursor, table_name)
    if column_name not in existing_columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        return True
    return False


def migrate_devices_table(db_path=None):
    db_file = Path(db_path) if db_path else get_default_db_path()

    if not db_file.exists():
        print(f"[MIGRATION] SQLite DB not found: {db_file}")
        return {"db_exists": False, "changed": []}

    connection = sqlite3.connect(db_file)
    try:
        cursor = connection.cursor()

        if not table_exists(cursor, "devices"):
            print("[MIGRATION] devices table not found. Skipping devices migration.")
            return {"db_exists": True, "devices_table_exists": False, "changed": []}

        changed = []
        for column_name, column_type in DEVICE_COLUMNS.items():
            if add_column_if_missing(cursor, "devices", column_name, column_type):
                changed.append(column_name)

        connection.commit()

        if changed:
            print(f"[MIGRATION] Added devices columns: {', '.join(changed)}")
        else:
            print("[MIGRATION] devices table already up to date.")

        return {"db_exists": True, "devices_table_exists": True, "changed": changed}
    finally:
        connection.close()


def run_startup_migrations():
    return migrate_devices_table()
