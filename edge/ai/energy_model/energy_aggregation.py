from datetime import datetime
from pathlib import Path
import sqlite3


# ==========================================================
# Database
# ==========================================================


def model_db_path() -> Path:
    edge_dir = Path(__file__).resolve().parents[2]

    candidates = [
        edge_dir / "ai" / "smart_home_models.db",
        edge_dir / "smart_home_models.db",
        edge_dir.parent / "smart_home_models.db",
    ]

    for path in candidates:
        if path.exists():
            return path

    return edge_dir / "ai" / "smart_home_models.db"


def connect_db():
    conn = sqlite3.connect(model_db_path())
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================================
# Energy Calculation
# ==========================================================


def calculate_energy(power_watts: float, elapsed_seconds: float) -> float:
    """
    Convert Power (Watts) to Energy (kWh)
    """

    return (power_watts * elapsed_seconds) / 3600000.0


# ==========================================================
# Daily Aggregation
# ==========================================================


def update_daily_consumption(device_id: str):

    conn = connect_db()

    try:

        today = datetime.now().strftime("%Y-%m-%d")

        rows = conn.execute(
            """
            SELECT timestamp, watts
            FROM energy_monitoring_readings
            WHERE device_id = ?
            AND reading_date = ?
            ORDER BY timestamp ASC
            """,
            (
                device_id,
                today,
            ),
        ).fetchall()

        if len(rows) < 2:
            return 0.0

        total_kwh = 0.0

        previous = rows[0]

        for current in rows[1:]:

            t1 = datetime.fromisoformat(previous["timestamp"])
            t2 = datetime.fromisoformat(current["timestamp"])

            elapsed = (t2 - t1).total_seconds()

            average_power = (
                previous["watts"] + current["watts"]
            ) / 2.0

            total_kwh += calculate_energy(
                average_power,
                elapsed,
            )

            previous = current

        conn.execute(
            """
            INSERT INTO energy_readings
            (
                device_id,
                reading_date,
                consumption_kwh,
                created_at
            )
            VALUES
            (
                ?,
                ?,
                ?,
                ?
            )
            ON CONFLICT(device_id, reading_date)
            DO UPDATE SET
                consumption_kwh = excluded.consumption_kwh,
                created_at = excluded.created_at
            """,
            (
                device_id,
                today,
                total_kwh,
                datetime.now().isoformat(),
            ),
        )

        conn.commit()

        return total_kwh

    finally:
        conn.close()


# ==========================================================
# Queries
# ==========================================================


def get_today_consumption():

    conn = connect_db()

    try:

        today = datetime.now().strftime("%Y-%m-%d")

        row = conn.execute(
            """
           SELECT consumption_kwh
           FROM energy_readings
           WHERE reading_date = ?
            """,
            (today,),
        ).fetchone()

        if row is None:
            return 0.0

        return row["consumption_kwh"]

    finally:
        conn.close()


def get_daily_history(limit: int = 30):

    conn = connect_db()

    try:

        rows = conn.execute(
            """
            SELECT *
            FROM energy_readings
            ORDER BY reading_date DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [dict(r) for r in rows]

    finally:
        conn.close()
