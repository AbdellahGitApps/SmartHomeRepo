from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import json
import sqlite3
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from mqtt import mqtt_client


router = APIRouter()


class DoorOpenRequest(BaseModel):
    device_id: Optional[str] = None
    source: str = "dashboard"
    reason: str = "manual_open"
    opened_by: Optional[str] = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _has_table(path: Path, table_name: str) -> bool:
    if not path.exists():
        return False

    try:
        conn = sqlite3.connect(path)
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
        conn.close()
        return row is not None
    except sqlite3.Error:
        return False


def _db_path() -> Path:
    edge_dir = Path(__file__).resolve().parents[1]
    candidates = [
        edge_dir / "data" / "smart_home.db",
        edge_dir / "database" / "smart_home.db",
        edge_dir / "smart_home.db",
        edge_dir.parent / "data" / "smart_home.db",
    ]

    for path in candidates:
        if _has_table(path, "devices"):
            return path

    for path in edge_dir.rglob("*.db"):
        path_text = str(path).lower()
        if "ai" in path_text or "model" in path_text:
            continue

        if _has_table(path, "devices"):
            return path

    for path in edge_dir.rglob("*.db"):
        if _has_table(path, "devices"):
            return path

    return edge_dir / "database" / "smart_home.db"


def _connect():
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_system_logs_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            created_at TEXT,
            category TEXT,
            event_type TEXT,
            severity TEXT,
            source TEXT,
            actor TEXT,
            action_taken TEXT,
            device_id TEXT,
            device_name TEXT,
            details TEXT,
            message TEXT,
            status TEXT
        )
        """
    )
    conn.commit()


def _table_columns(conn, table_name: str):
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row[1] for row in rows}


def _insert_system_log(conn, device, payload, topics):
    _ensure_system_logs_table(conn)

    columns = _table_columns(conn, "system_logs")
    details = {
        "request_id": payload["request_id"],
        "command": "open",
        "topics": topics,
        "reason": payload["reason"],
        "source": payload["source"],
    }

    values = {
        "timestamp": _now_iso(),
        "created_at": _now_iso(),
        "category": "door",
        "event_type": "door_open_command",
        "severity": "info",
        "source": payload["source"],
        "actor": payload.get("opened_by") or payload["source"],
        "action_taken": "MQTT DOOR OPEN",
        "device_id": device["device_id"],
        "device_name": device["name"] if "name" in device.keys() else device["device_id"],
        "details": json.dumps(details),
        "message": f"Door open command sent to {device['device_id']}",
        "status": "sent",
    }

    insert_columns = [key for key in values.keys() if key in columns]
    placeholders = ", ".join(["?"] * len(insert_columns))
    column_names = ", ".join(insert_columns)

    conn.execute(
        f"INSERT INTO system_logs ({column_names}) VALUES ({placeholders})",
        [values[key] for key in insert_columns],
    )
    conn.commit()


def _get_device(conn, device_ref: Optional[str] = None):
    if device_ref:
        row = conn.execute(
            """
            SELECT *
            FROM devices
            WHERE device_id = ? OR CAST(id AS TEXT) = ?
            LIMIT 1
            """,
            (device_ref, device_ref),
        ).fetchone()

        if row:
            return row

        raise HTTPException(status_code=404, detail="Door device not found")

    row = conn.execute(
        """
        SELECT *
        FROM devices
        WHERE lower(device_type) IN ('smart_door', 'esp32_cam', 'door_camera', 'camera')
        ORDER BY
            CASE
                WHEN lower(claim_status) IN ('claimed', 'active') THEN 0
                ELSE 1
            END,
            id ASC
        LIMIT 1
        """
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="No smart door device found")

    return row


def _mqtt_topics_for_device(device):
    topics = []

    if "mqtt_topic" in device.keys() and device["mqtt_topic"]:
        topics.append(f"{device['mqtt_topic']}/cmd")
        topics.append(f"{device['mqtt_topic']}/door/control")

    topics.append(f"device/{device['device_id']}/cmd")
    topics.append(f"device/{device['device_id']}/control")

    clean = []
    for topic in topics:
        if topic not in clean:
            clean.append(topic)

    return clean


def _publish_open_command(device, request_data: DoorOpenRequest):
    request_id = uuid.uuid4().hex[:12]

    payload = {
        "request_id": request_id,
        "command": "open",
        "action": "open",
        "device_id": device["device_id"],
        "device_token": device["device_token"] if "device_token" in device.keys() else None,
        "source": request_data.source,
        "reason": request_data.reason,
        "opened_by": request_data.opened_by,
        "timestamp": _now_iso(),
    }

    topics = _mqtt_topics_for_device(device)
    payload_text = json.dumps(payload)

    for topic in topics:
        mqtt_client.publish(topic, payload_text)

    return payload, topics


def _open_door(device_ref: Optional[str], request_data: DoorOpenRequest):
    conn = _connect()

    try:
        device = _get_device(conn, device_ref or request_data.device_id)
        payload, topics = _publish_open_command(device, request_data)
        _insert_system_log(conn, device, payload, topics)

        return {
            "success": True,
            "message": "Door open command sent through backend MQTT flow",
            "device_id": device["device_id"],
            "mqtt_topics": topics,
            "request_id": payload["request_id"],
            "source": request_data.source,
            "reason": request_data.reason,
        }
    finally:
        conn.close()


@router.post("/api/door/open")
def api_open_door(request_data: DoorOpenRequest):
    return _open_door(None, request_data)


@router.post("/door/open")
def legacy_open_door(request_data: DoorOpenRequest):
    return _open_door(None, request_data)


@router.post("/api/devices/{device_ref}/door/open")
def open_specific_door(device_ref: str, request_data: DoorOpenRequest):
    return _open_door(device_ref, request_data)
