from datetime import datetime
import json
from typing import Any

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
# سيتم استبدالها لاحقًا بقاعدة البيانات
# =========================
door_events: list[dict[str, Any]] = []

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


# =========================
# ENERGY ENDPOINTS
# =========================
@app.get("/energy/latest")
def get_latest_energy_reading():
    return latest_energy_reading


@app.get("/energy/forecast/latest")
def get_latest_energy_forecast():
    return latest_energy_forecast