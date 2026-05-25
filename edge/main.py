
try:
    try:
        from database.migrations import run_startup_migrations
    except ImportError:
        from edge.database.migrations import run_startup_migrations

    run_startup_migrations()
except Exception as migration_error:
    print(f"[MIGRATION WARNING] {migration_error}")

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
def dashboard(request: Request, db: Session = Depends(get_db)):
    total_homes = db.query(Home).count()
    total_devices = db.query(Device).count()
    online_devices = db.query(Device).filter(Device.status == 'online').count()
    pending_claims = db.query(Device).filter(Device.claim_status == 'pending').count()
    
    stats = {
        "total_homes": total_homes,
        "total_devices": total_devices,
        "online_devices": online_devices,
        "pending_claims": pending_claims
    }
    
    homes_list = home_service.get_all_homes(db)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request, "stats": stats, "homes": homes_list}
    )

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
def home_details(request: Request, home_id: int, db: Session = Depends(get_db)):
    home = home_service.get_home_by_id(db, home_id)
    if not home:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Home not found")
    devices_list = device_service.get_devices_by_home_id(db, home_id)
    return templates.TemplateResponse(
        request=request,
        name="home_details.html",
        context={"request": request, "home": home, "devices": devices_list}
    )

@app.delete("/home/{home_id}")
def delete_home_endpoint(home_id: int, db: Session = Depends(get_db)):
    try:
        home_service.delete_home(db, home_id)
        return {
            "success": True,
            "message": "Home and all related devices deleted successfully"
        }
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/devices")
def devices(request: Request, db: Session = Depends(get_db)):
    devices_list = device_service.get_all_devices(db)
    homes_list = home_service.get_all_homes(db)
    home_map = {home.id: home for home in homes_list}
    return templates.TemplateResponse(
        request=request,
        name="devices.html",
        context={"request": request, "devices": devices_list, "home_map": home_map}
    )

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
# MQTT & BACKGROUND TASKS INIT
# =========================
import asyncio

async def auto_offline_task():
    while True:
        try:
            await asyncio.sleep(30)
            from database.connection.database import SessionLocal
            db = SessionLocal()
            try:
                count = device_service.mark_inactive_devices_offline(db)
                if count > 0:
                    print(f"[Offline Task] Marked {count} devices as offline")
            finally:
                db.close()
        except Exception as e:
            print(f"[Offline Task] Error: {e}")

@app.on_event("startup")
async def startup_event():
    print("Starting Smart Home Backend...")
    start_mqtt()
    print("MQTT Connected & Subscribed")
    asyncio.create_task(auto_offline_task())

@app.on_event("shutdown")
def shutdown_event():
    print("Shutting down system...")
    stop_mqtt()

# =========================
# DEVICE STATUS API
# =========================
@app.get("/api/devices/status")
def get_devices_status(db: Session = Depends(get_db)):
    devices = device_service.get_all_devices(db)
    return [
        {
            "device_id": dev.device_id,
            "status": dev.status,
            "last_seen": dev.last_seen.isoformat() if dev.last_seen else None
        }
        for dev in devices
    ]

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

# System network configuration API
import socket

try:
    from config import SERVER_PUBLIC_URL, MQTT_BROKER_HOST, MQTT_BROKER_PORT
except ImportError:
    from edge.config import SERVER_PUBLIC_URL, MQTT_BROKER_HOST, MQTT_BROKER_PORT


def _get_current_lan_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.2)
        sock.connect(("8.8.8.8", 80))
        ip_address = sock.getsockname()[0]
        sock.close()
        return ip_address
    except Exception:
        return "127.0.0.1"


@app.get("/api/system/network")
def get_system_network_config():
    current_lan_ip = _get_current_lan_ip()

    return {
        "server_url": SERVER_PUBLIC_URL,
        "current_lan_ip": current_lan_ip,
        "api_status": "online",
        "mqtt_broker_host": MQTT_BROKER_HOST,
        "mqtt_broker_port": MQTT_BROKER_PORT,
        "mqtt_broker": f"{MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}",
    }

# App Home Code linking API
import sqlite3
from pathlib import Path
from fastapi import HTTPException
from pydantic import BaseModel


class AppLinkHomeRequest(BaseModel):
    home_code: str


def _link_home_db_path():
    return Path(__file__).resolve().parent / "database" / "smart_home_edge.db"


@app.post("/api/app/link-home")
def app_link_home(request: AppLinkHomeRequest):
    home_code = request.home_code.strip()

    if not home_code:
        raise HTTPException(status_code=400, detail="Home Code is required")

    db_file = _link_home_db_path()

    if not db_file.exists():
        raise HTTPException(status_code=500, detail="Database file not found")

    connection = sqlite3.connect(db_file)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        home = cursor.execute(
            """
            SELECT id, apartment_number, owner_name, owner_email, home_code
            FROM homes
            WHERE home_code = ?
            LIMIT 1
            """,
            (home_code,),
        ).fetchone()

        if home is None:
            raise HTTPException(status_code=404, detail="Invalid Home Code")

        devices = cursor.execute(
            """
            SELECT
                device_id,
                device_name,
                device_type,
                status,
                mqtt_topic,
                claim_code,
                claim_status
            FROM devices
            WHERE home_id = ?
            ORDER BY id ASC
            """,
            (home["id"],),
        ).fetchall()

        return {
            "success": True,
            "home": {
                "id": home["id"],
                "apartment_number": home["apartment_number"],
                "owner_name": home["owner_name"],
                "owner_email": home["owner_email"],
                "home_code": home["home_code"],
            },
            "devices": [dict(device) for device in devices],
        }
    finally:
        connection.close()

# Device Claim API
import sqlite3
from pathlib import Path
from datetime import datetime
from fastapi import HTTPException
from pydantic import BaseModel


class DeviceClaimRequest(BaseModel):
    claim_code: str
    mac_address: str
    device_ip: str
    device_type: str | None = None
    firmware_version: str | None = None


def _device_claim_db_path():
    return Path(__file__).resolve().parent / "database" / "smart_home_edge.db"


def _device_claim_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _device_claim_columns(cursor):
    rows = cursor.execute("PRAGMA table_info(devices)").fetchall()
    return {row[1] for row in rows}


def _is_camera_device(saved_type, reported_type):
    values = {
        (saved_type or "").lower(),
        (reported_type or "").lower(),
    }
    camera_types = {
        "smart_door",
        "door_camera",
        "camera",
        "esp32_cam",
        "front_door_camera",
    }
    return bool(values & camera_types)


def _build_camera_urls(device_ip):
    return {
        "camera_stream_url": f"http://{device_ip}/stream",
        "camera_capture_url": f"http://{device_ip}/capture",
    }


@app.post("/api/devices/claim")
def claim_device(request: DeviceClaimRequest):
    claim_code = request.claim_code.strip()
    mac_address = request.mac_address.strip()
    device_ip = request.device_ip.strip()
    reported_device_type = (request.device_type or "").strip()
    firmware_version = (request.firmware_version or "").strip()

    if not claim_code:
        raise HTTPException(status_code=400, detail="Claim Code is required")

    if not mac_address:
        raise HTTPException(status_code=400, detail="MAC Address is required")

    if not device_ip:
        raise HTTPException(status_code=400, detail="Device IP is required")

    db_file = _device_claim_db_path()

    if not db_file.exists():
        raise HTTPException(status_code=500, detail="Database file not found")

    connection = sqlite3.connect(db_file)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()
        columns = _device_claim_columns(cursor)

        device = cursor.execute(
            """
            SELECT *
            FROM devices
            WHERE claim_code = ?
            LIMIT 1
            """,
            (claim_code,),
        ).fetchone()

        if device is None:
            raise HTTPException(status_code=404, detail="Invalid Claim Code")

        saved_device_type = device["device_type"] if "device_type" in device.keys() else ""

        updates = {
            "mac_address": mac_address,
            "device_ip": device_ip,
            "claim_status": "claimed",
            "status": "online",
        }

        now = _device_claim_now()

        if "last_seen_at" in columns:
            updates["last_seen_at"] = now

        if "last_seen" in columns:
            updates["last_seen"] = now

        if "updated_at" in columns:
            updates["updated_at"] = now

        if firmware_version and "firmware_version" in columns:
            updates["firmware_version"] = firmware_version

        if "enabled" in columns:
            updates["enabled"] = 1

        if _is_camera_device(saved_device_type, reported_device_type):
            urls = _build_camera_urls(device_ip)

            if "camera_stream_url" in columns:
                updates["camera_stream_url"] = urls["camera_stream_url"]

            if "camera_capture_url" in columns:
                updates["camera_capture_url"] = urls["camera_capture_url"]

        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values())
        values.append(device["id"])

        cursor.execute(
            f"UPDATE devices SET {set_clause} WHERE id = ?",
            values,
        )

        connection.commit()

        updated_device = cursor.execute(
            """
            SELECT *
            FROM devices
            WHERE id = ?
            LIMIT 1
            """,
            (device["id"],),
        ).fetchone()

        return {
            "success": True,
            "message": "Device claimed successfully",
            "device": {
                "id": updated_device["id"],
                "home_id": updated_device["home_id"],
                "device_id": updated_device["device_id"],
                "device_name": updated_device["device_name"],
                "device_type": updated_device["device_type"],
                "device_token": updated_device["device_token"],
                "mqtt_topic": updated_device["mqtt_topic"],
                "claim_code": updated_device["claim_code"],
                "claim_status": updated_device["claim_status"],
                "status": updated_device["status"],
                "mac_address": updated_device["mac_address"] if "mac_address" in updated_device.keys() else None,
                "device_ip": updated_device["device_ip"] if "device_ip" in updated_device.keys() else None,
                "camera_stream_url": updated_device["camera_stream_url"] if "camera_stream_url" in updated_device.keys() else None,
                "camera_capture_url": updated_device["camera_capture_url"] if "camera_capture_url" in updated_device.keys() else None,
                "firmware_version": updated_device["firmware_version"] if "firmware_version" in updated_device.keys() else None,
                "last_seen_at": updated_device["last_seen_at"] if "last_seen_at" in updated_device.keys() else None,
            },
        }
    finally:
        connection.close()

# Device Heartbeat API
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import HTTPException
from pydantic import BaseModel


class DeviceHeartbeatRequest(BaseModel):
    device_id: str
    device_token: str
    device_ip: str | None = None
    mac_address: str | None = None
    status: str | None = "online"
    firmware_version: str | None = None


class DeviceRefreshStatusRequest(BaseModel):
    offline_after_seconds: int | None = 120


def _heartbeat_db_path():
    return Path(__file__).resolve().parent / "database" / "smart_home_edge.db"


def _heartbeat_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _heartbeat_columns(cursor):
    rows = cursor.execute("PRAGMA table_info(devices)").fetchall()
    return {row[1] for row in rows}


def _heartbeat_is_camera_device(device_type):
    return (device_type or "").lower() in {
        "smart_door",
        "door_camera",
        "camera",
        "esp32_cam",
        "front_door_camera",
    }


def _heartbeat_build_camera_urls(device_ip):
    return {
        "camera_stream_url": f"http://{device_ip}/stream",
        "camera_capture_url": f"http://{device_ip}/capture",
    }


@app.post("/api/devices/heartbeat")
def device_heartbeat(request: DeviceHeartbeatRequest):
    device_id = request.device_id.strip()
    device_token = request.device_token.strip()

    if not device_id:
        raise HTTPException(status_code=400, detail="Device ID is required")

    if not device_token:
        raise HTTPException(status_code=400, detail="Device token is required")

    db_file = _heartbeat_db_path()

    if not db_file.exists():
        raise HTTPException(status_code=500, detail="Database file not found")

    connection = sqlite3.connect(db_file)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()
        columns = _heartbeat_columns(cursor)

        device = cursor.execute(
            """
            SELECT *
            FROM devices
            WHERE device_id = ? AND device_token = ?
            LIMIT 1
            """,
            (device_id, device_token),
        ).fetchone()

        if device is None:
            raise HTTPException(status_code=401, detail="Invalid device credentials")

        now = _heartbeat_now()

        updates = {
            "status": request.status or "online",
        }

        if "last_seen_at" in columns:
            updates["last_seen_at"] = now

        if "last_seen" in columns:
            updates["last_seen"] = now

        if "updated_at" in columns:
            updates["updated_at"] = now

        if request.device_ip and "device_ip" in columns:
            updates["device_ip"] = request.device_ip

            if _heartbeat_is_camera_device(device["device_type"]):
                urls = _heartbeat_build_camera_urls(request.device_ip)

                if "camera_stream_url" in columns:
                    updates["camera_stream_url"] = urls["camera_stream_url"]

                if "camera_capture_url" in columns:
                    updates["camera_capture_url"] = urls["camera_capture_url"]

        if request.mac_address and "mac_address" in columns:
            updates["mac_address"] = request.mac_address

        if request.firmware_version and "firmware_version" in columns:
            updates["firmware_version"] = request.firmware_version

        if "enabled" in columns:
            updates["enabled"] = 1

        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values())
        values.append(device["id"])

        cursor.execute(
            f"UPDATE devices SET {set_clause} WHERE id = ?",
            values,
        )

        connection.commit()

        updated_device = cursor.execute(
            """
            SELECT *
            FROM devices
            WHERE id = ?
            LIMIT 1
            """,
            (device["id"],),
        ).fetchone()

        return {
            "success": True,
            "message": "Heartbeat received",
            "device": {
                "id": updated_device["id"],
                "home_id": updated_device["home_id"],
                "device_id": updated_device["device_id"],
                "device_name": updated_device["device_name"],
                "device_type": updated_device["device_type"],
                "status": updated_device["status"],
                "device_ip": updated_device["device_ip"] if "device_ip" in updated_device.keys() else None,
                "mac_address": updated_device["mac_address"] if "mac_address" in updated_device.keys() else None,
                "camera_stream_url": updated_device["camera_stream_url"] if "camera_stream_url" in updated_device.keys() else None,
                "camera_capture_url": updated_device["camera_capture_url"] if "camera_capture_url" in updated_device.keys() else None,
                "last_seen_at": updated_device["last_seen_at"] if "last_seen_at" in updated_device.keys() else None,
                "firmware_version": updated_device["firmware_version"] if "firmware_version" in updated_device.keys() else None,
            },
        }
    finally:
        connection.close()


@app.post("/api/devices/refresh-status")
def refresh_device_status(request: DeviceRefreshStatusRequest):
    offline_after_seconds = request.offline_after_seconds or 120

    if offline_after_seconds < 10:
        offline_after_seconds = 10

    cutoff = datetime.now() - timedelta(seconds=offline_after_seconds)

    db_file = _heartbeat_db_path()

    if not db_file.exists():
        raise HTTPException(status_code=500, detail="Database file not found")

    connection = sqlite3.connect(db_file)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()
        columns = _heartbeat_columns(cursor)

        if "last_seen_at" not in columns:
            return {
                "success": True,
                "message": "last_seen_at column not available",
                "offline_after_seconds": offline_after_seconds,
                "marked_offline": 0,
            }

        rows = cursor.execute(
            """
            SELECT id, last_seen_at
            FROM devices
            WHERE status = 'online' AND last_seen_at IS NOT NULL
            """
        ).fetchall()

        stale_ids = []

        for row in rows:
            try:
                last_seen = datetime.strptime(row["last_seen_at"], "%Y-%m-%d %H:%M:%S")
                if last_seen < cutoff:
                    stale_ids.append(row["id"])
            except Exception:
                continue

        for device_id in stale_ids:
            cursor.execute(
                """
                UPDATE devices
                SET status = ?
                WHERE id = ?
                """,
                ("offline", device_id),
            )

        connection.commit()

        return {
            "success": True,
            "offline_after_seconds": offline_after_seconds,
            "marked_offline": len(stale_ids),
        }
    finally:
        connection.close()
