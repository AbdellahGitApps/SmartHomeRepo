from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import sqlite3


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def model_db_path() -> Path:
    edge_dir = Path(__file__).resolve().parents[1]
    candidates = [
        edge_dir / "ai" / "smart_home_models.db",
        edge_dir / "smart_home_models.db",
        edge_dir.parent / "smart_home_models.db",
    ]

    for path in candidates:
        if path.exists():
            return path

    return edge_dir / "ai" / "smart_home_models.db"


def connect_energy_db():
    path = model_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_energy_tables(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS energy_monitoring_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            reading_date TEXT,
            device_id TEXT,
            source TEXT,
            topic TEXT,
            voltage REAL,
            current REAL,
            watts REAL,
            kwh_today REAL,
            consumption_kwh REAL,
            raw_json TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS energy_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reading_date TEXT NOT NULL UNIQUE,
            consumption_kwh REAL NOT NULL,
            created_at TEXT
        )
        """
    )

    conn.commit()


def normalize_energy_payload(payload: dict, source: str = "api", topic: Optional[str] = None) -> dict:
    timestamp = payload.get("timestamp") or now_iso()
    reading_date = payload.get("reading_date") or timestamp[:10]

    watts = payload.get("watts")
    if watts is None:
        watts = payload.get("power")
    if watts is None:
        watts = payload.get("power_w")

    voltage = payload.get("voltage")
    current = payload.get("current")
    kwh_today = payload.get("kwh_today")
    consumption_kwh = payload.get("consumption_kwh")

    if consumption_kwh is None and kwh_today is not None:
        consumption_kwh = kwh_today

    return {
        "timestamp": str(timestamp),
        "reading_date": str(reading_date),
        "device_id": payload.get("device_id"),
        "source": source,
        "topic": topic,
        "voltage": float(voltage) if voltage is not None else None,
        "current": float(current) if current is not None else None,
        "watts": float(watts) if watts is not None else None,
        "kwh_today": float(kwh_today) if kwh_today is not None else None,
        "consumption_kwh": float(consumption_kwh) if consumption_kwh is not None else None,
    }


def record_energy_payload(payload: dict, source: str = "api", topic: Optional[str] = None) -> dict:
    import json

    data = normalize_energy_payload(payload, source=source, topic=topic)

    conn = connect_energy_db()

    try:
        ensure_energy_tables(conn)

        conn.execute(
            """
            INSERT INTO energy_monitoring_readings (
                timestamp, reading_date, device_id, source, topic,
                voltage, current, watts, kwh_today, consumption_kwh, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["timestamp"],
                data["reading_date"],
                data["device_id"],
                data["source"],
                data["topic"],
                data["voltage"],
                data["current"],
                data["watts"],
                data["kwh_today"],
                data["consumption_kwh"],
                json.dumps(payload),
            ),
        )

        if data["consumption_kwh"] is not None:
            conn.execute(
                """
                INSERT INTO energy_readings (
                    reading_date, consumption_kwh, created_at
                )
                VALUES (?, ?, ?)
                ON CONFLICT(reading_date)
                DO UPDATE SET
                    consumption_kwh = excluded.consumption_kwh,
                    created_at = excluded.created_at
                """,
                (
                    data["reading_date"],
                    data["consumption_kwh"],
                    data["timestamp"],
                ),
            )

        conn.commit()

        latest_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

        return {
            "success": True,
            "id": latest_id,
            "reading": data,
            "model_db": str(model_db_path()),
        }
    finally:
        conn.close()


def get_latest_energy_reading():
    conn = connect_energy_db()

    try:
        ensure_energy_tables(conn)

        row = conn.execute(
            """
            SELECT *
            FROM energy_monitoring_readings
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        return dict(row) if row else None
    finally:
        conn.close()


def get_energy_logs(limit: int = 50):
    conn = connect_energy_db()

    try:
        ensure_energy_tables(conn)

        rows = conn.execute(
            """
            SELECT *
            FROM energy_monitoring_readings
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_energy_status():
    conn = connect_energy_db()

    try:
        ensure_energy_tables(conn)

        monitoring_count = conn.execute(
            "SELECT COUNT(*) AS c FROM energy_monitoring_readings"
        ).fetchone()["c"]

        daily_count = conn.execute(
            "SELECT COUNT(*) AS c FROM energy_readings"
        ).fetchone()["c"]

        latest = get_latest_energy_reading()

        return {
            "success": True,
            "model_db": str(model_db_path()),
            "monitoring_readings": monitoring_count,
            "daily_readings": daily_count,
            "latest": latest,
        }
    finally:
        conn.close()
