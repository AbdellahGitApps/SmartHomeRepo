from datetime import datetime
import json
from pathlib import Path
import sqlite3
from typing import Any, Optional
import math

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# MQTT
from mqtt import start_mqtt, stop_mqtt, mqtt_client


app = FastAPI(
    title="Smart Home Edge API",
    description="Local Smart Home Backend (No Internet)",
    version="1.0.0",
)

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# DATABASE
# =========================
BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATABASE_DIR / "smart_home_edge.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def row_to_dict(row: sqlite3.Row | None):
    if row is None:
        return None

    data = dict(row)

    if "face_embedding" in data and data["face_embedding"]:
        try:
            data["face_embedding"] = json.loads(data["face_embedding"])
        except json.JSONDecodeError:
            data["face_embedding"] = None

    if "has_face_embedding" in data:
        data["has_face_embedding"] = bool(data["has_face_embedding"])

    if "mqtt_published" in data:
        data["mqtt_published"] = bool(data["mqtt_published"])

    return data


def init_database():
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS door_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                source TEXT,
                reason TEXT,
                mqtt_topic TEXT,
                mqtt_published INTEGER DEFAULT 0,
                mqtt_error TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS family_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'family_member',
                has_face_embedding INTEGER DEFAULT 0,
                face_embedding TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        connection.commit()


init_database()

# =========================
# TEMP ENERGY MOCK DATA
# =========================
latest_energy_reading = {
    "voltage": 220.0,
    "current": 1.25,
    "power": 275.0,
    "energy_kwh": 0.35,
    "created_at": datetime.now().isoformat(),
}

latest_energy_forecast = {
    "predicted_kwh": 12.5,
    "predicted_bill": 0.0,
    "model_used": "temporary_mock",
    "created_at": datetime.now().isoformat(),
}


# =========================
# REQUEST MODELS
# =========================
class DoorOpenRequest(BaseModel):
    source: str = "flutter_admin"
    reason: str = "manual_open_from_app"


class FamilyMemberCreate(BaseModel):
    name: str
    role: str = "family_member"
    face_embedding: Optional[list[float]] = None


class FaceEmbeddingUpdate(BaseModel):
    face_embedding: list[float]


class AddUnknownToFamilyRequest(BaseModel):
    name: str


class FaceVerifyRequest(BaseModel):
    face_embedding: list[float]
    source: str = "flutter_face_engine"
    threshold: float = 0.75


# =========================
# MQTT INIT
# =========================
@app.on_event("startup")
def startup_event():
    print("🚀 Starting Smart Home Backend...")
    init_database()
    start_mqtt()
    print("📡 MQTT Connected & Subscribed")


@app.on_event("shutdown")
def shutdown_event():
    print("🛑 Shutting down system...")
    stop_mqtt()


# =========================
# HEALTH CHECK
# =========================
@app.get("/")
def home():
    return {
        "status": "running",
        "system": "Smart Home Edge Backend",
        "mode": "LOCAL",
        "database": str(DATABASE_PATH),
    }


@app.get("/health")
def health():
    return {
        "mqtt": mqtt_client.is_connected(),
        "server": "ok",
        "database": DATABASE_PATH.exists(),
    }


# =========================
# HELPERS
# =========================
def insert_door_event(
    event_type: str,
    status: str,
    source: str | None = None,
    reason: str | None = None,
    mqtt_topic: str | None = None,
    mqtt_published: bool = False,
    mqtt_error: str | None = None,
):
    now = datetime.now().isoformat()

    with get_db_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO door_events (
                type,
                status,
                source,
                reason,
                mqtt_topic,
                mqtt_published,
                mqtt_error,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_type,
                status,
                source,
                reason,
                mqtt_topic,
                1 if mqtt_published else 0,
                mqtt_error,
                now,
            ),
        )

        connection.commit()
        event_id = cursor.lastrowid

        event = connection.execute(
            "SELECT * FROM door_events WHERE id = ?",
            (event_id,),
        ).fetchone()

    return row_to_dict(event)


def get_door_event_by_id(event_id: int):
    with get_db_connection() as connection:
        event = connection.execute(
            "SELECT * FROM door_events WHERE id = ?",
            (event_id,),
        ).fetchone()

    return row_to_dict(event)


def update_door_event_status(event_id: int, status: str, reason: str | None = None):
    with get_db_connection() as connection:
        existing_event = connection.execute(
            "SELECT * FROM door_events WHERE id = ?",
            (event_id,),
        ).fetchone()

        if existing_event is None:
            return None

        final_reason = reason if reason is not None else existing_event["reason"]

        connection.execute(
            """
            UPDATE door_events
            SET status = ?, reason = ?
            WHERE id = ?
            """,
            (
                status,
                final_reason,
                event_id,
            ),
        )

        connection.commit()

        updated_event = connection.execute(
            "SELECT * FROM door_events WHERE id = ?",
            (event_id,),
        ).fetchone()

    return row_to_dict(updated_event)


def create_family_member(name: str, face_embedding: Optional[list[float]] = None):
    now = datetime.now().isoformat()

    face_embedding_json = (
        json.dumps(face_embedding)
        if face_embedding is not None
        else None
    )

    has_face_embedding = face_embedding is not None

    with get_db_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO family_members (
                name,
                role,
                has_face_embedding,
                face_embedding,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                "family_member",
                1 if has_face_embedding else 0,
                face_embedding_json,
                now,
                now,
            ),
        )

        connection.commit()
        member_id = cursor.lastrowid

        new_member = connection.execute(
            "SELECT * FROM family_members WHERE id = ?",
            (member_id,),
        ).fetchone()

    return row_to_dict(new_member)


def publish_open_command(source: str, reason: str):
    now = datetime.now().isoformat()

    command_payload = {
        "action": "open",
        "source": source,
        "reason": reason,
        "created_at": now,
    }

    try:
        mqtt_client.publish("door/cmd", json.dumps(command_payload))
        return True, None
    except Exception as error:
        return False, str(error)


def cosine_similarity(vector_a: list[float], vector_b: list[float]):
    if len(vector_a) != len(vector_b):
        return None

    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))

    if norm_a == 0 or norm_b == 0:
        return None

    return dot_product / (norm_a * norm_b)


def find_best_family_match(face_embedding: list[float]):
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM family_members
            WHERE has_face_embedding = 1
            AND face_embedding IS NOT NULL
            """
        ).fetchall()

    best_member = None
    best_similarity = None

    for row in rows:
        member = row_to_dict(row)
        stored_embedding = member.get("face_embedding")

        if not isinstance(stored_embedding, list):
            continue

        similarity = cosine_similarity(face_embedding, stored_embedding)

        if similarity is None:
            continue

        if best_similarity is None or similarity > best_similarity:
            best_similarity = similarity
            best_member = member

    return best_member, best_similarity


# =========================
# FACE VERIFY ENDPOINT
# =========================
@app.post("/face/verify")
def verify_face(payload: FaceVerifyRequest):
    best_member, best_similarity = find_best_family_match(payload.face_embedding)

    is_known = (
        best_member is not None
        and best_similarity is not None
        and best_similarity >= payload.threshold
    )

    if is_known:
        mqtt_published, mqtt_error = publish_open_command(
            source=payload.source,
            reason=f"known_family_member_{best_member['id']}_{best_member['name']}",
        )

        event = insert_door_event(
            event_type="known_person",
            status="opened_automatically" if mqtt_published else "auto_open_failed",
            source=payload.source,
            reason=f"recognized_family_member_id_{best_member['id']}_similarity_{best_similarity:.4f}",
            mqtt_topic="door/cmd",
            mqtt_published=mqtt_published,
            mqtt_error=mqtt_error,
        )

        return {
            "success": True,
            "known": True,
            "message": "Known family member verified",
            "matched_member": best_member,
            "similarity": best_similarity,
            "threshold": payload.threshold,
            "door_opened": mqtt_published,
            "mqtt_error": mqtt_error,
            "event": event,
        }

    event = insert_door_event(
        event_type="unknown_person",
        status="pending_decision",
        source=payload.source,
        reason="unknown_face_embedding_not_matched_waiting_for_admin_decision",
        mqtt_topic=None,
        mqtt_published=False,
        mqtt_error=None,
    )

    return {
        "success": True,
        "known": False,
        "message": "Unknown face. Waiting for admin decision.",
        "matched_member": None,
        "similarity": best_similarity,
        "threshold": payload.threshold,
        "door_opened": False,
        "event": event,
    }


# =========================
# DOOR ENDPOINTS
# =========================
@app.get("/door/latest")
def get_latest_door_event():
    with get_db_connection() as connection:
        event = connection.execute(
            "SELECT * FROM door_events ORDER BY id DESC LIMIT 1"
        ).fetchone()

    if event is None:
        return {
            "message": "No door events yet",
            "latest": None,
        }

    return row_to_dict(event)


@app.get("/door/logs")
def get_door_logs():
    with get_db_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM door_events ORDER BY id DESC LIMIT 50"
        ).fetchall()

    items = [row_to_dict(row) for row in rows]

    return {
        "count": len(items),
        "items": items,
    }


@app.post("/door/open")
def open_door(request: DoorOpenRequest):
    mqtt_published, mqtt_error = publish_open_command(
        source=request.source,
        reason=request.reason,
    )

    event = insert_door_event(
        event_type="manual_open",
        status="open_command_sent" if mqtt_published else "open_command_failed",
        source=request.source,
        reason=request.reason,
        mqtt_topic="door/cmd",
        mqtt_published=mqtt_published,
        mqtt_error=mqtt_error,
    )

    return {
        "success": mqtt_published,
        "message": "Door open command sent" if mqtt_published else "Failed to send door command",
        "event": event,
    }


@app.post("/door/log/direct-open")
def log_direct_door_open():
    event = insert_door_event(
        event_type="direct_manual_open",
        status="direct_open_logged",
        source="flutter_direct",
        reason="door_opened_directly_from_app_to_esp32",
        mqtt_topic=None,
        mqtt_published=False,
        mqtt_error=None,
    )

    return {
        "success": True,
        "message": "Direct door open event logged",
        "event": event,
    }


@app.post("/door/events/unknown/test")
def create_test_unknown_door_event():
    event = insert_door_event(
        event_type="unknown_person",
        status="pending_decision",
        source="flutter_face_mock",
        reason="test_unknown_face_waiting_for_admin_decision",
        mqtt_topic=None,
        mqtt_published=False,
        mqtt_error=None,
    )

    return {
        "success": True,
        "message": "Test unknown door event created",
        "event": event,
    }


@app.get("/door/pending")
def get_pending_door_event():
    with get_db_connection() as connection:
        event = connection.execute(
            """
            SELECT * FROM door_events
            WHERE type = 'unknown_person'
            AND status = 'pending_decision'
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    if event is None:
        return {
            "message": "No pending unknown door event",
            "event": None,
        }

    return {
        "message": "Pending unknown door event found",
        "event": row_to_dict(event),
    }


@app.post("/door/events/{event_id}/open")
def open_pending_door_event(event_id: int):
    event = get_door_event_by_id(event_id)

    if event is None:
        return {
            "success": False,
            "message": "Door event not found",
            "event_id": event_id,
        }

    mqtt_published, mqtt_error = publish_open_command(
        source="flutter_admin",
        reason=f"admin_opened_pending_event_{event_id}",
    )

    new_status = "opened_by_admin" if mqtt_published else "open_failed"

    updated_event = update_door_event_status(
        event_id=event_id,
        status=new_status,
        reason=f"admin_decision_open_event_{event_id}",
    )

    return {
        "success": mqtt_published,
        "message": "Door opened by admin" if mqtt_published else "Failed to open door",
        "mqtt_error": mqtt_error,
        "event": updated_event,
    }


@app.post("/door/events/{event_id}/deny")
def deny_pending_door_event(event_id: int):
    event = get_door_event_by_id(event_id)

    if event is None:
        return {
            "success": False,
            "message": "Door event not found",
            "event_id": event_id,
        }

    updated_event = update_door_event_status(
        event_id=event_id,
        status="denied_by_admin",
        reason=f"admin_denied_event_{event_id}",
    )

    return {
        "success": True,
        "message": "Door event denied by admin",
        "event": updated_event,
    }


@app.post("/door/events/{event_id}/add-to-family")
def add_unknown_event_to_family(event_id: int, request: AddUnknownToFamilyRequest):
    event = get_door_event_by_id(event_id)

    if event is None:
        return {
            "success": False,
            "message": "Door event not found",
            "event_id": event_id,
        }

    new_member = create_family_member(name=request.name)

    updated_event = update_door_event_status(
        event_id=event_id,
        status="added_to_family",
        reason=f"unknown_event_{event_id}_added_to_family_member_{new_member['id']}",
    )

    return {
        "success": True,
        "message": "Unknown person added to family members",
        "member": new_member,
        "event": updated_event,
    }


# =========================
# FAMILY MEMBERS ENDPOINTS
# =========================
@app.get("/family/members")
def get_family_members():
    with get_db_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM family_members ORDER BY id DESC"
        ).fetchall()

    items = [row_to_dict(row) for row in rows]

    return {
        "count": len(items),
        "items": items,
    }


@app.post("/family/members")
def add_family_member(member: FamilyMemberCreate):
    new_member = create_family_member(
        name=member.name,
        face_embedding=member.face_embedding,
    )

    return {
        "success": True,
        "message": "Family member added",
        "member": new_member,
    }


@app.post("/family/members/test")
def add_test_family_member():
    new_member = create_family_member(name="Test Family Member")

    return {
        "success": True,
        "message": "Test family member added",
        "member": new_member,
    }


@app.post("/family/members/{member_id}/face-embedding")
def attach_face_embedding(member_id: int, payload: FaceEmbeddingUpdate):
    now = datetime.now().isoformat()
    face_embedding_json = json.dumps(payload.face_embedding)

    with get_db_connection() as connection:
        existing_member = connection.execute(
            "SELECT * FROM family_members WHERE id = ?",
            (member_id,),
        ).fetchone()

        if existing_member is None:
            return {
                "success": False,
                "message": "Family member not found",
                "member_id": member_id,
            }

        connection.execute(
            """
            UPDATE family_members
            SET
                face_embedding = ?,
                has_face_embedding = 1,
                updated_at = ?
            WHERE id = ?
            """,
            (
                face_embedding_json,
                now,
                member_id,
            ),
        )

        connection.commit()

        updated_member = connection.execute(
            "SELECT * FROM family_members WHERE id = ?",
            (member_id,),
        ).fetchone()

    return {
        "success": True,
        "message": "Face embedding attached to family member",
        "member": row_to_dict(updated_member),
    }


# =========================
# ENERGY ENDPOINTS
# =========================
@app.get("/energy/latest")
def get_latest_energy_reading():
    return latest_energy_reading


@app.get("/energy/forecast/latest")
def get_latest_energy_forecast():
    return latest_energy_forecast