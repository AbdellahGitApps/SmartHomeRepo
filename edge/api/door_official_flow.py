from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import json
import logging
import sqlite3
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from mqtt import mqtt_client

logger = logging.getLogger(__name__)

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

    actor_val = payload.get("opened_by") or payload["source"]
    if payload["source"] == "face_recognition":
        actor_val = "Server"

    values = {
        "timestamp": _now_iso(),
        "created_at": _now_iso(),
        "category": "door",
        "event_type": "Smart Door Command",
        "severity": "info",
        "source": payload["source"],
        "actor": actor_val,
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


def _is_device_online(device) -> bool:
    """
    Check whether the ESP32 door controller is reachable.
    Uses the device status column and last_seen timestamp.
    """
    # 1. Check MQTT broker connection
    if not mqtt_client.is_connected():
        logger.warning("MQTT broker is not connected — cannot reach ESP32")
        return False

    # 2. Check device status in database
    device_dict = dict(device)
    status = str(device_dict.get("status") or "").lower().strip()
    if status in ("offline", "disconnected", "disabled"):
        logger.warning(f"Device {device_dict.get('device_id')} status is '{status}'")
        return False

    # 3. Check last_seen freshness (within 120 seconds)
    last_seen_raw = (
        device_dict.get("last_seen")
        or device_dict.get("last_seen_at")
        or ""
    )
    if last_seen_raw:
        try:
            raw = str(last_seen_raw).replace("T", " ").replace("Z", "").strip()
            if "+" in raw:
                raw = raw.split("+", 1)[0].strip()
            if "." in raw:
                raw = raw.split(".", 1)[0].strip()
            last_seen_dt = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
            age_seconds = (datetime.now() - last_seen_dt).total_seconds()
            if age_seconds > 120:
                logger.warning(
                    f"Device {device_dict.get('device_id')} last seen {age_seconds:.0f}s ago — treating as offline"
                )
                return False
        except Exception as exc:
            logger.debug(f"Could not parse last_seen '{last_seen_raw}': {exc}")

    return True


def _ensure_door_events_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS door_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            home_id INTEGER,
            apartment_number TEXT,
            device_id TEXT,
            device_name TEXT,
            status TEXT,
            event_type TEXT,
            details TEXT,
            source TEXT,
            reason TEXT,
            actor TEXT,
            action_taken TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def _insert_door_event(conn, device, payload):
    _ensure_door_events_table(conn)

    device_dict = dict(device)
    now = _now_iso()
    home_id = device_dict.get("home_id", "")
    device_id = device_dict.get("device_id", "")
    device_name = (
        device_dict.get("device_name")
        or device_dict.get("name")
        or device_id
    )
    actor = payload.get("opened_by") or payload.get("source", "flutter_app")

    conn.execute(
        """
        INSERT INTO door_events (
            home_id, device_id, device_name, status,
            event_type, details, source, reason, actor,
            action_taken, timestamp, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            home_id,
            device_id,
            device_name,
            "unlocked",
            "mqtt_door_open",
            f"Door open command sent to {device_id} via MQTT",
            payload.get("source", "flutter_app"),
            payload.get("reason", "manual_open"),
            actor,
            "MQTT DOOR OPEN",
            now,
            now,
        ),
    )
    conn.commit()


def _mqtt_topics_for_device(device):
    topics = []

    device_token = device.get("device_token")
    if device_token:
        topics.append(f"device/{device_token}/cmd")
    else:
        topics.append(f"device/{device['device_id']}/cmd")

    clean = []
    for topic in topics:
        if topic not in clean:
            clean.append(topic)

    return clean

http_unlock_count = 0
mqtt_publish_count = 0

def _publish_open_command(device, request_data: DoorOpenRequest):
    global mqtt_publish_count
    device = dict(device)
    request_id = uuid.uuid4().hex[:12]

    payload = {
        "request_id": request_id,
        "command": "open",
        "action": "open",
        "device_token": device.get("device_token"),
        "source": request_data.source,
        "reason": request_data.reason,
        "opened_by": request_data.opened_by,
        "timestamp": _now_iso(),
    }

    topics = _mqtt_topics_for_device(device)

    payload_text = json.dumps(payload)
    for topic in topics:
        mqtt_publish_count += 1
        print(f"Publishing MQTT #{mqtt_publish_count} -> topic {topic}")
        mqtt_client.publish(topic, payload_text)

    return payload, topics


def _open_door(device_ref: Optional[str], request_data: DoorOpenRequest):
    global http_unlock_count
    http_unlock_count += 1
    print(f"HTTP unlock request #{http_unlock_count}")

    conn = _connect()

    try:
        device = _get_device(conn, device_ref or request_data.device_id)

        # Verify ESP32 is reachable before sending MQTT command
        if not _is_device_online(device):
            device_dict = dict(device)
            device_id = device_dict.get("device_id", "unknown")
            logger.warning(f"Door open rejected — device {device_id} is offline")
            raise HTTPException(
                status_code=503,
                detail=(
                    "Door controller is currently offline. "
                    "Please check the device connection."
                ),
            )

        payload, topics = _publish_open_command(device, request_data)
        _insert_system_log(conn, device, payload, topics)
        _insert_door_event(conn, device, payload)

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


@router.get("/api/door/device-status")
def api_door_device_status():
    """
    Returns the current online/offline status of the primary door device.
    Used by the Flutter app to show connection state.
    """
    conn = _connect()
    try:
        device = _get_device(conn)
        online = _is_device_online(device)
        device_dict = dict(device)
        return {
            "success": True,
            "device_id": device_dict.get("device_id"),
            "online": online,
            "status": device_dict.get("status", "unknown"),
            "last_seen": device_dict.get("last_seen") or device_dict.get("last_seen_at"),
            "mqtt_connected": mqtt_client.is_connected(),
        }
    except HTTPException:
        return {
            "success": False,
            "online": False,
            "status": "no_device",
            "message": "No door device registered",
        }
    finally:
        conn.close()
