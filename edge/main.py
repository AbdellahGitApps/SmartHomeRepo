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

try:
    from api.energy_monitoring_flow import router as energy_monitoring_flow_router
    app.include_router(energy_monitoring_flow_router)
except Exception as exc:
    print(f"Phase 15 energy monitoring router failed to load: {exc}")

try:
    from api.energy_prediction_flow import router as energy_prediction_flow_router
    app.include_router(energy_prediction_flow_router)
except Exception as exc:
    print(f"Phase 16 energy prediction router failed to load: {exc}")


# D7M16_PHASE10_DEVICE_ACTIONS_START
from fastapi import Request as _D7Phase10Request, HTTPException as _D7Phase10HTTPException
from pathlib import Path as _D7Phase10Path
import sqlite3 as _d7_phase10_sqlite3
import json as _d7_phase10_json
import uuid as _d7_phase10_uuid
from datetime import datetime as _d7_phase10_datetime, timezone as _d7_phase10_timezone

try:
    from edge.mqtt.publishers.device_command_publisher import publish_device_command as _d7_phase10_publish_device_command
except Exception:
    try:
        from mqtt.publishers.device_command_publisher import publish_device_command as _d7_phase10_publish_device_command
    except Exception:
        _d7_phase10_publish_device_command = None


_D7_PHASE10_ALLOWED_ACTIONS = {"restart", "enable", "disable", "remove", "status_request"}


def _d7_phase10_now():
    return _d7_phase10_datetime.now(_d7_phase10_timezone.utc).isoformat()


def _d7_phase10_has_table(path: _D7Phase10Path, table_name: str) -> bool:
    if not path.exists():
        return False

    try:
        conn = _d7_phase10_sqlite3.connect(path)
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
        conn.close()
        return row is not None
    except _d7_phase10_sqlite3.Error:
        return False


def _d7_phase10_db_path() -> _D7Phase10Path:
    edge_dir = _D7Phase10Path(__file__).resolve().parent
    candidates = [
        edge_dir / "database" / "smart_home.db",
        edge_dir / "database" / "smart_home_edge.db",
        edge_dir / "data" / "smart_home.db",
        edge_dir / "smart_home.db",
        edge_dir.parent / "data" / "smart_home.db",
    ]

    for path in candidates:
        if _d7_phase10_has_table(path, "devices"):
            return path

    for path in edge_dir.rglob("*.db"):
        lower = str(path).lower()
        if "ai" in lower or "model" in lower:
            continue

        if _d7_phase10_has_table(path, "devices"):
            return path

    for path in edge_dir.rglob("*.db"):
        if _d7_phase10_has_table(path, "devices"):
            return path

    return edge_dir / "database" / "smart_home.db"


def _d7_phase10_connect():
    path = _d7_phase10_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = _d7_phase10_sqlite3.connect(path)
    conn.row_factory = _d7_phase10_sqlite3.Row
    return conn


def _d7_phase10_table_columns(conn, table_name: str):
    try:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}
    except _d7_phase10_sqlite3.Error:
        return set()


def _d7_phase10_ensure_system_logs_table(conn):
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
            home TEXT,
            home_id TEXT,
            device_id TEXT,
            device_name TEXT,
            details TEXT,
            message TEXT,
            status TEXT
        )
        """
    )
    conn.commit()


def _d7_phase10_device_to_dict(row):
    if row is None:
        return {}

    data = dict(row)

    if "device_name" not in data and "name" in data:
        data["device_name"] = data.get("name")

    if "name" not in data and "device_name" in data:
        data["name"] = data.get("device_name")

    return data


def _d7_phase10_get_device(conn, device_ref: str):
    device_ref = str(device_ref or "").strip()

    if not device_ref:
        raise _D7Phase10HTTPException(status_code=400, detail="Missing device id")

    try:
        row = conn.execute(
            """
            SELECT *
            FROM devices
            WHERE device_id = ? OR CAST(id AS TEXT) = ?
            LIMIT 1
            """,
            (device_ref, device_ref),
        ).fetchone()
    except _d7_phase10_sqlite3.Error as error:
        raise _D7Phase10HTTPException(status_code=500, detail=f"Device lookup failed: {error}")

    if not row:
        raise _D7Phase10HTTPException(status_code=404, detail=f"Device not found: {device_ref}")

    return _d7_phase10_device_to_dict(row)


def _d7_phase10_get_active_mqtt_client():
    for name in ["mqtt_client", "mqtt", "mqtt_manager", "mqtt_service", "client"]:
        obj = globals().get(name)
        if obj is not None and (
            hasattr(obj, "publish")
            or hasattr(obj, "client")
            or hasattr(obj, "mqtt_client")
        ):
            return obj

    try:
        import edge.mqtt as mqtt_module
        obj = getattr(mqtt_module, "mqtt_client", None)
        if obj is not None:
            return obj
    except Exception:
        pass

    try:
        import mqtt as mqtt_module
        obj = getattr(mqtt_module, "mqtt_client", None)
        if obj is not None:
            return obj
    except Exception:
        pass

    return None


def _d7_phase10_update_device_state(conn, device_ref: str, action: str):
    columns = _d7_phase10_table_columns(conn, "devices")
    updates = {}

    if action == "disable":
        if "enabled" in columns:
            updates["enabled"] = 0
        if "status" in columns:
            updates["status"] = "offline"

    elif action == "enable":
        if "enabled" in columns:
            updates["enabled"] = 1

    elif action == "restart":
        pass

    if not updates:
        return

    set_sql = ", ".join([f"{key} = ?" for key in updates])
    values = list(updates.values())
    values.extend([device_ref, device_ref])

    conn.execute(
        f"UPDATE devices SET {set_sql} WHERE device_id = ? OR CAST(id AS TEXT) = ?",
        values,
    )


def _d7_phase10_insert_system_log(conn, device, action, actor_role, mqtt_result):
    _d7_phase10_ensure_system_logs_table(conn)
    columns = _d7_phase10_table_columns(conn, "system_logs")

    device_id = str(device.get("device_id") or device.get("id") or "")
    device_name = str(device.get("device_name") or device.get("name") or device_id)
    home_id = str(device.get("home_id") or device.get("home") or "-")

    details_text = (
        f"{action.upper()} command sent to {device_name} ({device_id}) "
        f"through FastAPI → MQTT."
    )

    values = {
        "timestamp": _d7_phase10_now(),
        "created_at": _d7_phase10_now(),
        "category": "device",
        "event_type": "Device Command",
        "severity": "warning" if action == "disable" else "info",
        "source": "dashboard",
        "actor": actor_role,
        "action_taken": f"MQTT {action.upper()}",
        "home": home_id,
        "home_id": home_id,
        "device_id": device_id,
        "device_name": device_name,
        "details": details_text,
        "message": details_text,
        "status": "sent" if mqtt_result.get("published") else "prepared",
    }

    insert_columns = [key for key in values if key in columns]
    if not insert_columns:
        return

    placeholders = ", ".join(["?"] * len(insert_columns))
    names = ", ".join(insert_columns)

    conn.execute(
        f"INSERT INTO system_logs ({names}) VALUES ({placeholders})",
        [values[key] for key in insert_columns],
    )


def _d7_phase10_actor_role(request: _D7Phase10Request):
    return (
        request.headers.get("X-Actor-Role")
        or request.headers.get("x-actor-role")
        or "system_owner"
    )


@app.post("/api/dashboard/devices/{device_id}/actions/{action}")
def d7_phase10_dashboard_device_action(
    device_id: str,
    action: str,
    request: _D7Phase10Request,
):
    action = str(action or "").strip().lower()

    if action not in _D7_PHASE10_ALLOWED_ACTIONS:
        raise _D7Phase10HTTPException(status_code=400, detail=f"Unsupported device action: {action}")

    actor_role = _d7_phase10_actor_role(request)

    with _d7_phase10_connect() as conn:
        device = _d7_phase10_get_device(conn, device_id)

        if action in {"enable", "disable", "restart"}:
            _d7_phase10_update_device_state(conn, device_id, action)
            device = _d7_phase10_get_device(conn, device_id)

        mqtt_client_obj = _d7_phase10_get_active_mqtt_client()

        if _d7_phase10_publish_device_command is None:
            mqtt_result = {
                "published": False,
                "command": action,
                "topics": [],
                "results": [],
                "error": "device_command_publisher unavailable",
            }
        else:
            mqtt_result = _d7_phase10_publish_device_command(
                mqtt_client=mqtt_client_obj,
                device=device,
                command=action,
                source="dashboard",
                actor_role=actor_role,
                extra={
                    "dashboard_action": True,
                    "request_id": _d7_phase10_uuid.uuid4().hex[:12],
                },
            )

        conn.commit()

        return {
            "success": True,
            "message": f"{action.upper()} command sent through FastAPI → MQTT.",
            "device_id": device.get("device_id") or device_id,
            "action": action,
            "mqtt": mqtt_result,
        }


@app.post("/api/devices/{device_id}/restart")
def d7_phase10_restart_compat(device_id: str, request: _D7Phase10Request):
    return d7_phase10_dashboard_device_action(device_id, "restart", request)


@app.patch("/api/devices/{device_id}/disable")
def d7_phase10_disable_compat(device_id: str, request: _D7Phase10Request):
    return d7_phase10_dashboard_device_action(device_id, "disable", request)


@app.patch("/api/devices/{device_id}/enable")
def d7_phase10_enable_compat(device_id: str, request: _D7Phase10Request):
    return d7_phase10_dashboard_device_action(device_id, "enable", request)
# D7M16_PHASE10_DEVICE_ACTIONS_END


# D7M16_PHASE17_6_FAMILY_MANAGEMENT_START
try:
    from api.family_management_flow import router as family_management_flow_router
    app.include_router(family_management_flow_router)
except Exception as exc:
    print(f"Phase 17.6 family management router failed to load: {exc}")
# D7M16_PHASE17_6_FAMILY_MANAGEMENT_END

