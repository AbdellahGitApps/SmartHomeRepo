from datetime import datetime
import json
import math

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database.connection.database import get_db
import services.home_service as home_service
import services.device_service as device_service

from pathlib import Path
import sys

# =========================
# PATH SETUP
# =========================
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from mqtt import start_mqtt, stop_mqtt, mqtt_client

# =========================
# Create Tables
# =========================

from database.connection.database import Base, engine
from database.models.home import Home
from database.models.device import Device

Base.metadata.create_all(bind=engine)

# =========================
# APP INIT
# =========================
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
# STATIC FILES (FRONTEND)
# =========================
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "dashboard" / "static")),
    name="static"
)

templates = Jinja2Templates(directory=str(BASE_DIR / "dashboard" / "templates"))

# =========================
# REQUEST MODELS
# =========================
class DeviceCreateRequest(BaseModel):
    device_name: str
    device_type: str


class HomeCreateRequest(BaseModel):
    name: str
    owner_name: str
    owner_email: str
    apartment_number: str
    devices: list[DeviceCreateRequest] = []


class DoorOpenRequest(BaseModel):
    source: str = "flutter_admin"
    reason: str = "manual_open_from_app"

class FamilyMemberCreate(BaseModel):
    name: str
    role: str = "family_member"

class FaceVerifyRequest(BaseModel):
    face_embedding: list[float]
    source: str = "flutter_face_engine"
    threshold: float = 0.75

# =========================
# FRONTEND ROUTES (DO NOT TOUCH)
# =========================
@app.get("/")
def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/create-home")
def create_home_page(request: Request):
    return templates.TemplateResponse(request=request, name="create_home.html")


@app.post("/create-home")
def create_home_endpoint(payload: HomeCreateRequest, db: Session = Depends(get_db)):
    
    try:
        # Create Home using the service
        db_home = home_service.create_home(
            db=db,
            name=payload.name,
            owner_name=payload.owner_name,
            owner_email=payload.owner_email,
            apartment_number=payload.apartment_number,
        )

        # Create each associated Device using the service
        created_devices = []
        for dev in payload.devices:
            db_device = device_service.create_device(
                db=db,
                home_id=db_home.id,
                device_name=dev.device_name,
                device_type=dev.device_type,
            )
            created_devices.append(
                {
                    "device_id": db_device.device_id,
                    "device_name": db_device.device_name,
                    "device_type": db_device.device_type,
                    "claim_code": db_device.claim_code,
                    "device_token": db_device.device_token,
                }
            )

        return {
            "success": True,
            "home_id": db_home.id,
            "home_code": db_home.home_code,
            "devices": created_devices,
        }
    except Exception as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=str(e))

@app.get("/home-details")
def home_details(request: Request):
    return templates.TemplateResponse(request=request, name="home_details.html")

@app.get("/devices")
def devices(request: Request):
    return templates.TemplateResponse(request=request, name="devices.html")

@app.get("/cameras")
def cameras(request: Request):
    return templates.TemplateResponse(request=request, name="cameras.html")

@app.get("/energy")
def energy(request: Request):
    return templates.TemplateResponse(request=request, name="energy.html")

@app.get("/status")
def status(request: Request):
    return templates.TemplateResponse(request=request, name="status.html")

@app.get("/users")
def users(request: Request):
    return templates.TemplateResponse(request=request, name="users.html")

@app.get("/logs")
def logs(request: Request):
    return templates.TemplateResponse(request=request, name="logs.html")

# =========================
# MQTT INIT
# =========================
@app.on_event("startup")
def startup_event():
    print("Starting Smart Home Backend...")
    start_mqtt()
    print("MQTT Connected & Subscribed")

@app.on_event("shutdown")
def shutdown_event():
    print("Shutting down system...")
    stop_mqtt()

# =========================
# HEALTH CHECK
# =========================
@app.get("/api")
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
        "database": "migrated_to_sqlalchemy_pending"
    }

# =========================
# PLACEHOLDER HELPERS (DB WILL BE MOVED TO SERVICES LATER)
# =========================
def insert_door_event(*args, **kwargs):
    return {"status": "mock", "message": "DB removed - pending SQLAlchemy migration"}

def get_door_event_by_id(event_id: int):
    return None

def update_door_event_status(*args, **kwargs):
    return {"status": "mock"}

def create_family_member(*args, **kwargs):
    return {"id": 1, "name": kwargs.get("name", "mock_user")}

def publish_open_command(source: str, reason: str):
    try:
        mqtt_client.publish("door/cmd", json.dumps({
            "action": "open",
            "source": source,
            "reason": reason,
            "created_at": datetime.now().isoformat()
        }))
        return True, None
    except Exception as e:
        return False, str(e)

def cosine_similarity(a, b):
    if len(a) != len(b):
        return None
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(x*x for x in b))
    if na == 0 or nb == 0:
        return None
    return dot / (na * nb)

def find_best_family_match(face_embedding):
    return None, None

# =========================
# FACE VERIFY (STUBBED LOGIC)
# =========================
@app.post("/face/verify")
def verify_face(payload: FaceVerifyRequest):

    mqtt_published, mqtt_error = publish_open_command(
        source=payload.source,
        reason="mock_face_verification"
    )

    return {
        "success": True,
        "known": False,
        "message": "DB migrated - face system pending refactor",
        "door_opened": mqtt_published,
        "mqtt_error": mqtt_error
    }

# =========================
# DOOR ENDPOINTS (TEMP STUB)
# =========================
@app.post("/door/open")
def open_door(request: DoorOpenRequest):

    mqtt_published, mqtt_error = publish_open_command(
        source=request.source,
        reason=request.reason,
    )

    return {
        "success": mqtt_published,
        "message": "Door command sent (DB removed temporarily)",
        "mqtt_error": mqtt_error
    }