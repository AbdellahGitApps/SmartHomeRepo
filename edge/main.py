import sqlite3
from fastapi.responses import HTMLResponse
import asyncio
from fastapi import Request

try:
    try:
        from database.migrations import run_startup_migrations
    except ImportError:
        from edge.database.migrations import run_startup_migrations

    run_startup_migrations()
except Exception as migration_error:
    print(f"[MIGRATION WARNING] {migration_error}")

from datetime import datetime, timedelta
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


# D7M16_SECURITY_LOGS_UNIFIED_START

def _security_db_path():
    return Path(__file__).resolve().parent / "database" / "smart_home_edge.db"


def _ensure_system_logs_table():
    db_path = _security_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            severity TEXT,
            home TEXT,
            event_type TEXT,
            details TEXT,
            action_taken TEXT
        )
    """)

    existing = {row[1] for row in cur.execute("PRAGMA table_info(system_logs)").fetchall()}
    needed = {
        "timestamp": "TEXT",
        "severity": "TEXT",
        "home": "TEXT",
        "event_type": "TEXT",
        "details": "TEXT",
        "action_taken": "TEXT"
    }

    for col, col_type in needed.items():
        if col not in existing:
            cur.execute(f"ALTER TABLE system_logs ADD COLUMN {col} {col_type}")

    conn.commit()
    conn.close()


def _format_security_time(value):
    if not value:
        return "Not available"

    raw = str(value).replace("T", " ").split(".")[0]

    try:
        dt = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
    except Exception:
        try:
            dt = datetime.fromisoformat(raw)
        except Exception:
            return raw

    today = datetime.now().date()
    log_day = dt.date()
    time_part = dt.strftime("%I:%M %p").lstrip("0")

    if log_day == today:
        return f"Today, {time_part}"

    if log_day == today - timedelta(days=1):
        return f"Yesterday, {time_part}"

    return f"{dt.strftime('%Y-%m-%d')}, {time_part}"


def _get_device_log_context(device_ref):
    _ensure_system_logs_table()

    conn = sqlite3.connect(_security_db_path())
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    row = cur.execute("""
        SELECT
            d.id,
            d.device_id,
            d.device_name,
            d.device_type,
            d.home_id,
            h.apartment_number,
            h.home_code
        FROM devices d
        LEFT JOIN homes h ON h.id = d.home_id
        WHERE d.device_id = ? OR CAST(d.id AS TEXT) = ?
        LIMIT 1
    """, (str(device_ref), str(device_ref))).fetchone()

    conn.close()

    if not row:
        return {
            "device_name": str(device_ref),
            "home": "Unknown Home"
        }

    if row["apartment_number"]:
        home = f"Apartment {row['apartment_number']}"
    elif row["home_code"]:
        home = row["home_code"]
    else:
        home = f"Home {row['home_id']}"

    return {
        "device_name": row["device_name"] or row["device_id"] or str(device_ref),
        "home": home
    }


def _insert_security_log(severity, home, event_type, details, action_taken):
    _ensure_system_logs_table()

    conn = sqlite3.connect(_security_db_path())
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO system_logs (
            timestamp,
            severity,
            home,
            event_type,
            details,
            action_taken
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        str(severity or "info").lower(),
        home or "System",
        event_type or "System Event",
        details or "",
        action_taken or ""
    ))

    conn.commit()
    conn.close()


def _get_security_logs(limit=200):
    _ensure_system_logs_table()

    conn = sqlite3.connect(_security_db_path())
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT id, timestamp, severity, home, event_type, details, action_taken
        FROM system_logs
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()

    conn.close()

    logs = []

    for row in rows:
        severity = (row["severity"] or "info").lower()

        logs.append({
            "id": row["id"],
            "timestamp": row["timestamp"],
            "timestamp_label": _format_security_time(row["timestamp"]),
            "severity": severity,
            "severity_label": severity.upper(),
            "home": row["home"] or "System",
            "event_type": row["event_type"] or "System Event",
            "details": row["details"] or "",
            "action_taken": row["action_taken"] or ""
        })

    return logs


def _extract_device_action_from_path(path_value):
    parts = path_value.strip("/").split("/")
    lower_parts = [p.lower() for p in parts]
    valid_actions = {"restart", "enable", "disable", "remove", "delete"}

    action = None

    for item in reversed(lower_parts):
        item = item.replace("_", "-")
        if item in valid_actions:
            action = item
            break

    if not action:
        return None, None

    if "devices" in lower_parts:
        device_index = lower_parts.index("devices") + 1
        if device_index < len(parts):
            return parts[device_index], action

    if "device-command" in lower_parts:
        device_index = lower_parts.index("device-command") + 1
        if device_index < len(parts):
            return parts[device_index], action

    return None, None


@app.middleware("http")
async def _security_log_device_commands(request: Request, call_next):
    device_ref = None
    action = None

    if request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
        device_ref, action = _extract_device_action_from_path(request.url.path)

    response = await call_next(request)

    if device_ref and action and response.status_code < 400:
        try:
            ctx = _get_device_log_context(device_ref)

            severity = "warning" if action in {"disable", "remove", "delete"} else "info"
            action_title = action.replace("-", " ").title()

            _insert_security_log(
                severity=severity,
                home=ctx["home"],
                event_type="Device Command",
                details=f"{action_title} command sent to {ctx['device_name']}",
                action_taken=f"MQTT {action.upper()}"
            )
        except Exception as exc:
            print("SECURITY LOG WRITE ERROR:", exc)

    return response


@app.get("/api/dashboard/security-logs-data")
def api_dashboard_security_logs_data(limit: int = 100):
    return {
        "success": True,
        "logs": _get_security_logs(limit)
    }


_ensure_system_logs_table()

# D7M16_SECURITY_LOGS_UNIFIED_END


@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    logs = _get_security_logs()
    return templates.TemplateResponse("logs.html", {
        "request": request,
        "logs": logs,
        "security_logs": logs
    })


@app.get("/api/dashboard/logs")
async def api_dashboard_logs():
    logs = _get_security_logs()
    return {
        "success": True,
        "logs": logs
    }


@app.get("/users")
def users_page(request: Request):
    import sqlite3
    from pathlib import Path
    from fastapi.templating import Jinja2Templates

    template_engine = globals().get("templates")
    if template_engine is None:
        template_engine = Jinja2Templates(
            directory=str(Path(__file__).resolve().parent / "dashboard" / "templates")
        )

    db_path = globals().get("DB_PATH")
    if db_path is None:
        db_path = Path(__file__).resolve().parent / "database" / "smart_home_edge.db"

    users = [
        {
            "initials": "SO",
            "name": "System Owner",
            "email": "admin@edge-system.local",
            "role": "SYSTEM OWNER",
            "home": "-- (All)",
            "associated_home": "-- (All)",
            "status": "ACTIVE",
            "last_login": "Just now",
            "can_disable": False,
        }
    ]

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        homes = cursor.execute("""
            SELECT id, home_code, apartment_number, owner_name, owner_email
            FROM homes
            ORDER BY id DESC
        """).fetchall()

        conn.close()

        for home in homes:
            owner_name = home["owner_name"] or "Home Owner"
            owner_email = home["owner_email"] or "owner@example.com"
            apartment = home["apartment_number"] or home["home_code"] or "Home"

            parts = owner_name.split()
            initials = "".join([p[0] for p in parts[:2]]).upper() or "HO"

            users.append(
                {
                    "initials": initials,
                    "name": owner_name,
                    "email": owner_email,
                    "role": "HOME OWNER",
                    "home": f"Apartment {apartment}",
                    "associated_home": f"Apartment {apartment}",
                    "status": "ACTIVE",
                    "last_login": "Not logged in yet",
                    "can_disable": True,
                }
            )

    except Exception as e:
        print("USERS PAGE DB ERROR:", e)

    return template_engine.TemplateResponse(
        "users.html",
        {
            "request": request,
            "users": users,
            "active_page": "users",
        },
    )


try:
    from api.door_official_flow import router as door_official_flow_router
    app.include_router(door_official_flow_router)
except Exception as exc:
    print(f"Phase 13 door official flow router failed to load: {exc}")

try:
    from api.face_recognition_flow import router as face_recognition_flow_router
    app.include_router(face_recognition_flow_router)
except Exception as exc:
    print(f"Phase 14 face recognition flow router failed to load: {exc}")
