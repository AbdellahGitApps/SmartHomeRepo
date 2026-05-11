from datetime import datetime
import json
from typing import Any, Optional

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
    allow_origins=["*"],  # لاحقًا نخصصها
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# TEMP IN-MEMORY DATA
# لاحقًا سيتم استبدالها بقاعدة البيانات
# =========================
door_events: list[dict[str, Any]] = []
family_members: list[dict[str, Any]] = []

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


class DoorOpenRequest(BaseModel):
    source: str = "flutter_admin"
    reason: str = "manual_open_from_app"


class FamilyMemberCreate(BaseModel):
    name: str
    role: str = "family_member"
    face_embedding: Optional[list[float]] = None


class FaceEmbeddingUpdate(BaseModel):
    face_embedding: list[float]


# =========================
# MQTT INIT
# =========================
@app.on_event("startup")
def startup_event():
    print("🚀 Starting Smart Home Backend...")
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
    }


@app.get("/health")
def health():
    return {
        "mqtt": mqtt_client.is_connected(),
        "server": "ok",
    }


# =========================
# DOOR ENDPOINTS
# =========================
@app.get("/door/latest")
def get_latest_door_event():
    if not door_events:
        return {
            "message": "No door events yet",
            "latest": None,
        }

    return door_events[-1]


@app.get("/door/logs")
def get_door_logs():
    return {
        "count": len(door_events),
        "items": door_events,
    }


@app.post("/door/open")
def open_door(request: DoorOpenRequest):
    now = datetime.now().isoformat()

    command_payload = {
        "action": "open",
        "source": request.source,
        "reason": request.reason,
        "created_at": now,
    }

    mqtt_published = False
    mqtt_error = None

    try:
        mqtt_client.publish("door/cmd", json.dumps(command_payload))
        mqtt_published = True
    except Exception as error:
        mqtt_error = str(error)

    event = {
        "id": len(door_events) + 1,
        "type": "manual_open",
        "status": "open_command_sent" if mqtt_published else "open_command_failed",
        "source": request.source,
        "reason": request.reason,
        "mqtt_topic": "door/cmd",
        "mqtt_published": mqtt_published,
        "mqtt_error": mqtt_error,
        "created_at": now,
    }

    door_events.append(event)

    return {
        "success": mqtt_published,
        "message": "Door open command sent" if mqtt_published else "Failed to send door command",
        "event": event,
    }


@app.post("/door/log/direct-open")
def log_direct_door_open():
    now = datetime.now().isoformat()

    event = {
        "id": len(door_events) + 1,
        "type": "direct_manual_open",
        "status": "direct_open_logged",
        "source": "flutter_direct",
        "reason": "door_opened_directly_from_app_to_esp32",
        "mqtt_topic": None,
        "mqtt_published": False,
        "mqtt_error": None,
        "created_at": now,
    }

    door_events.append(event)

    return {
        "success": True,
        "message": "Direct door open event logged",
        "event": event,
    }


# =========================
# FAMILY MEMBERS ENDPOINTS
# =========================
@app.get("/family/members")
def get_family_members():
    return {
        "count": len(family_members),
        "items": family_members,
    }


@app.post("/family/members")
def add_family_member(member: FamilyMemberCreate):
    now = datetime.now().isoformat()

    new_member = {
        "id": len(family_members) + 1,
        "name": member.name,
        "role": member.role,
        "has_face_embedding": member.face_embedding is not None,
        "face_embedding": member.face_embedding,
        "created_at": now,
        "updated_at": now,
    }

    family_members.append(new_member)

    return {
        "success": True,
        "message": "Family member added",
        "member": new_member,
    }


@app.post("/family/members/test")
def add_test_family_member():
    now = datetime.now().isoformat()

    new_member = {
        "id": len(family_members) + 1,
        "name": f"Test Family Member {len(family_members) + 1}",
        "role": "family_member",
        "has_face_embedding": False,
        "face_embedding": None,
        "created_at": now,
        "updated_at": now,
    }

    family_members.append(new_member)

    return {
        "success": True,
        "message": "Test family member added",
        "member": new_member,
    }


@app.post("/family/members/{member_id}/face-embedding")
def attach_face_embedding(member_id: int, payload: FaceEmbeddingUpdate):
    for member in family_members:
        if member.get("id") == member_id:
            now = datetime.now().isoformat()

            member["face_embedding"] = payload.face_embedding
            member["has_face_embedding"] = True
            member["updated_at"] = now

            return {
                "success": True,
                "message": "Face embedding attached to family member",
                "member": member,
            }

    return {
        "success": False,
        "message": "Family member not found",
        "member_id": member_id,
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