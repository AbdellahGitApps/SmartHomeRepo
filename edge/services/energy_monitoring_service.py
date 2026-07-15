from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import sqlite3
from ai.energy_model.energy_aggregation import update_daily_consumption


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
            device_id TEXT NOT NULL,
            reading_date TEXT NOT NULL,
            consumption_kwh REAL NOT NULL,
            created_at TEXT,
            UNIQUE(device_id, reading_date)
)
        """
    )

    conn.commit()


def normalize_energy_payload(
    payload: dict, source: str = "api", topic: Optional[str] = None
) -> dict:
    timestamp = payload.get("timestamp") or now_iso()
    reading_date = payload.get("reading_date") or timestamp[:10]

    watts = payload.get("watts")
    if watts is None:
        watts = payload.get("power")
    if watts is None:
        watts = payload.get("power_w")

    voltage = payload.get("voltage")
    current = payload.get("current")

    return {
        "timestamp": str(timestamp),
        "reading_date": str(reading_date),
        "device_id": payload.get("device_id"),
        "source": source,
        "topic": topic,
        "voltage": float(voltage) if voltage is not None else None,
        "current": float(current) if current is not None else None,
        "watts": float(watts) if watts is not None else None,
        # سيتم حساب الاستهلاك داخل السيرفر لاحقاً
        "kwh_today": None,
        "consumption_kwh": None,
    }


def record_energy_payload(
    payload: dict, source: str = "api", topic: Optional[str] = None
) -> dict:
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

        conn.commit()
        update_daily_consumption(data["device_id"])

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
            """,
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

        latest = None

        return {
            "success": True,
            "model_db": str(model_db_path()),
            "monitoring_readings": monitoring_count,
            "daily_readings": daily_count,
            "latest": latest,
        }
    finally:
        conn.close()
