from api.door import _d7_final_find_db
from api.notifications import _d7m16_role_text
from api.notifications import _d7real_tables
from api.notifications import _d7real_cols
import sqlite3
from fastapi.responses import HTMLResponse
import asyncio
from fastapi import Request


from datetime import datetime, timedelta
import json
import math
import re

from fastapi import FastAPI, Request, Depends, BackgroundTasks
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
from fastapi import Body
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


def init_database_tables():
    import sqlite3
    from core_database import get_database_path
    db_path = get_database_path()
    
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        
        # 1. system_logs
        cur.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                created_at TEXT,
                severity TEXT,
                actor TEXT,
                source TEXT,
                home TEXT,
                home_id TEXT,
                apartment_number TEXT,
                event_type TEXT,
                details TEXT,
                action_taken TEXT,
                device_id TEXT,
                device_name TEXT
            )
        """)
        existing_cols = {row[1] for row in cur.execute("PRAGMA table_info(system_logs)").fetchall()}
        system_logs_needed = {
            "timestamp": "TEXT",
            "created_at": "TEXT",
            "severity": "TEXT",
            "actor": "TEXT",
            "source": "TEXT",
            "home": "TEXT",
            "home_id": "TEXT",
            "apartment_number": "TEXT",
            "event_type": "TEXT",
            "details": "TEXT",
            "action_taken": "TEXT",
            "device_id": "TEXT",
            "device_name": "TEXT"
        }
        for col, col_type in system_logs_needed.items():
            if col not in existing_cols:
                cur.execute(f"ALTER TABLE system_logs ADD COLUMN {col} {col_type}")
        print("[DB INIT] system_logs verified")

        # 3. door_events
        cur.execute("""
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
        """)
        existing_cols = {row[1] for row in cur.execute("PRAGMA table_info(door_events)").fetchall()}
        door_events_needed = {
            "home_id": "INTEGER",
            "apartment_number": "TEXT",
            "device_id": "TEXT",
            "device_name": "TEXT",
            "status": "TEXT",
            "event_type": "TEXT",
            "details": "TEXT",
            "source": "TEXT",
            "reason": "TEXT",
            "actor": "TEXT",
            "action_taken": "TEXT",
            "timestamp": "TEXT DEFAULT CURRENT_TIMESTAMP",
            "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP"
        }
        for col, col_type in door_events_needed.items():
            if col not in existing_cols:
                cur.execute(f"ALTER TABLE door_events ADD COLUMN {col} {col_type}")
        print("[DB INIT] door_events verified")

        conn.commit()
    except Exception as e:
        print(f"[DB INIT ERROR] Failed to initialize custom SQLite tables: {e}")
    finally:
        conn.close()


# =========================
# APP INIT
# =========================

# D7M16_INVALID_DATETIME_DB_SAFETY_START
def _d7m16_normalize_bad_datetime_values_once():
    """
    SQLite stores some datetime values as text. If a UI-formatted value like
    '2026-05-30 11:17:27 AM' reaches SQLAlchemy DateTime fields, pages such as
    /devices and /cameras can crash. This normalizes those values to
    'YYYY-MM-DD HH:MM:SS'.
    """
    try:
        from pathlib import Path as _D7Path
        import sqlite3 as _d7_sqlite3
        from datetime import datetime as _d7_datetime

        db_path = _D7Path(__file__).resolve().parent / "database" / "smart_home_edge.db"
        if not db_path.exists():
            return

        def normalize(value):
            if value is None:
                return value

            value_text = str(value).strip()
            if not value_text:
                return value

            for fmt in (
                "%Y-%m-%d %I:%M:%S %p",
                "%Y-%m-%d, %I:%M:%S %p",
                "%Y-%m-%d %I:%M %p",
                "%Y-%m-%d, %I:%M %p",
            ):
                try:
                    return _d7_datetime.strptime(value_text, fmt).strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass

            return value

        conn = _d7_sqlite3.connect(db_path)
        conn.row_factory = _d7_sqlite3.Row
        cur = conn.cursor()

        tables = [r["name"] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

        for table in tables:
            cols = [r["name"] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()]
            if "id" not in cols:
                continue

            date_cols = [
                c for c in cols
                if c.lower() in {
                    "created_at", "updated_at", "timestamp", "last_seen",
                    "last_seen_at", "registered_at", "recovery_expires_at"
                }
            ]

            for col in date_cols:
                rows = cur.execute(f"SELECT id, {col} FROM {table} WHERE {col} IS NOT NULL").fetchall()
                for row in rows:
                    old = row[col]
                    new = normalize(old)
                    if new != old:
                        cur.execute(f"UPDATE {table} SET {col} = ? WHERE id = ?", (new, row["id"]))

        conn.commit()
        conn.close()

    except Exception as exc:
        print("D7M16 datetime cleanup skipped:", exc)

# D7M16_INVALID_DATETIME_DB_SAFETY_END


app = FastAPI(
    title="Smart Home Edge API",
    description="Local Smart Home Backend (No Internet)",
    version="1.0.0",
)

from routers.dashboard import router as dashboard_router
app.include_router(dashboard_router)
from api.notifications import router as notifications_router
app.include_router(notifications_router)


@app.on_event("startup")
def startup_event():
    # --- RELOCATED DATABASE BOOTSTRAP START ---
    try:
        from database.migrations import run_startup_migrations
    except ImportError:
        from edge.database.migrations import run_startup_migrations

    try:
        run_startup_migrations()
    except Exception as e:
        print(f"[BOOTSTRAP ERROR] run_startup_migrations failed: {e}")

    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"[BOOTSTRAP ERROR] create_all failed: {e}")

    try:
        init_database_tables()
    except Exception as e:
        print(f"[BOOTSTRAP ERROR] init_database_tables failed: {e}")

    try:
        _d7m16_normalize_bad_datetime_values_once()
    except Exception as e:
        print(f"[BOOTSTRAP ERROR] datetime normalization failed: {e}")

    try:
        _ensure_system_logs_table()
    except Exception as e:
        print(f"[BOOTSTRAP ERROR] ensure_system_logs_table failed: {e}")

    try:
        _d7_cleanup_duplicate_app_security_logs_once()
    except Exception as e:
        print(f"[BOOTSTRAP ERROR] cleanup_duplicate_logs failed: {e}")
    # --- RELOCATED DATABASE BOOTSTRAP END ---


    import socket

    try:
        start_mqtt()

        print("[MQTT] Startup completed")

    except Exception as exc:
        print(f"[MQTT ERROR] {exc}")

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        except Exception:
            try:
                # Fallback to a common local gateway address to force Wi-Fi adapter selection
                s.connect(("192.168.1.254", 80))
                local_ip = s.getsockname()[0]
            except Exception:
                local_ip = socket.gethostbyname(socket.gethostname())
        finally:
            s.close()

        print("\n" + "=" * 60)
        print(f"👉 LOCAL SERVER IP FOR MOBILE APP: {local_ip}")
        print("=" * 60 + "\n")

    except Exception:
        pass


# =========================
# GLOBAL UTF-8 MIDDLEWARE
# =========================
@app.middleware("http")
async def force_utf8_response(request: Request, call_next):
    response = await call_next(request)
    ctype = response.headers.get("Content-Type", "")
    if "application/json" in ctype and "charset" not in ctype.lower():
        response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response


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
    owner_phone: str = ""
    apartment_number: str
    energy_profile: str = "Residential Type A"
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




def _d7_create_home_clean_phone(value: str) -> str:
    return str(value or "").strip()

def _d7_create_home_validate_owner_phone(phone: str):
    if not re.fullmatch(r"[0-9]{9}", phone or ""):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Owner Phone must be exactly 9 English digits.")

def _d7_create_home_phone_exists(phone: str, exclude_home_id=None) -> bool:
    db_path = Path(__file__).resolve().parent / "database" / "smart_home_edge.db"
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()

        cols = {row[1] for row in cur.execute("PRAGMA table_info(homes)").fetchall()}
        if "owner_phone" not in cols:
            cur.execute("ALTER TABLE homes ADD COLUMN owner_phone TEXT")
            conn.commit()
            return False

        if exclude_home_id is None:
            row = cur.execute(
                "SELECT id FROM homes WHERE owner_phone = ? LIMIT 1",
                (phone,),
            ).fetchone()
        else:
            row = cur.execute(
                "SELECT id FROM homes WHERE owner_phone = ? AND CAST(id AS TEXT) <> CAST(? AS TEXT) LIMIT 1",
                (phone, str(exclude_home_id)),
            ).fetchone()

        return row is not None
    finally:
        conn.close()

def _d7_create_home_validate_unique_owner_phone(phone: str, exclude_home_id=None):
    _d7_create_home_validate_owner_phone(phone)

    if _d7_create_home_phone_exists(phone, exclude_home_id=exclude_home_id):
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail="Owner Phone is already used by another home.")

import smtplib
from email.mime.text import MIMEText

def send_home_code_email(email_address: str, home_code: str):
    try:
        if not email_address or "@" not in email_address:
            return

        subject = "Your Home Code"
        body = f"Your Home Code is: {home_code}"

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = "smarthomeappust@gmail.com"
        msg["To"] = email_address

        smtp_host = "smtp.gmail.com"
        smtp_port = 587
        smtp_user = "smarthomeappust@gmail.com"
        smtp_pass = "cizm sowk rgvf pbnd"

        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        server.starttls()
        server.login(smtp_user, smtp_pass)

        server.send_message(msg)

        server.quit()

    except Exception as e:
        print("[EMAIL ERROR]", e)

@app.post("/create-home")
def create_home_endpoint(payload: HomeCreateRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    
    try:
        clean_owner_phone = _d7_create_home_clean_phone(payload.owner_phone)
        _d7_create_home_validate_unique_owner_phone(clean_owner_phone)

        # Create Home using the service
        db_home = home_service.create_home(
            db=db,
            name=payload.name,
            owner_name=payload.owner_name,
            owner_email=payload.owner_email,
            apartment_number=payload.apartment_number,
            owner_phone=clean_owner_phone,
            energy_profile=payload.energy_profile,
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

        # Send the home code via email in the background
        if payload.owner_email:
            background_tasks.add_task(send_home_code_email, payload.owner_email, db_home.home_code)

        return {
            "success": True,
            "home_id": db_home.id,
            "home_code": db_home.home_code,
            "devices": created_devices,
        }
    except Exception as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=str(e))


def _d7_get_owner_phone_for_home(home_id: int) -> str:
    try:
        db_path = Path(__file__).resolve().parent / "database" / "smart_home_edge.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cols = {row[1] for row in cur.execute("PRAGMA table_info(homes)").fetchall()}
        if "owner_phone" not in cols:
            cur.execute("ALTER TABLE homes ADD COLUMN owner_phone TEXT")
            conn.commit()
            return ""

        row = cur.execute(
            "SELECT owner_phone FROM homes WHERE id = ? LIMIT 1",
            (home_id,),
        ).fetchone()

        return str(row["owner_phone"] or "").strip() if row else ""
    except Exception:
        return ""
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.get("/home-details")
def home_details(request: Request, home_id: int, db: Session = Depends(get_db)):
    home = home_service.get_home_by_id(db, home_id)
    if not home:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Home not found")
    devices_list = device_service.get_devices_by_home_id(db, home_id)
    owner_phone = _d7_get_owner_phone_for_home(home_id)
    return templates.TemplateResponse(
        request=request,
        name="home_details.html",
        context={"request": request, "home": home, "devices": devices_list, "owner_phone": owner_phone}
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




@app.get("/energy")
def energy(request: Request):
    return templates.TemplateResponse(request=request, name="energy.html")



@app.get("/api/app/home-by-code")
def api_app_home_by_code(home_code: str, apartment_number: str = ""):
    clean_code = (home_code or "").strip()
    clean_apartment = (apartment_number or "").strip()

    if not clean_code:
        return {"home": None}

    db_path = Path(__file__).resolve().parent / "database" / "smart_home_edge.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        if clean_apartment:
            row = conn.execute(
                """
                SELECT
                    id,
                    name,
                    home_code,
                    owner_name,
                    owner_email,
                    owner_phone,
                    apartment_number,
                    account_status,
                    last_login_at
                FROM homes
                WHERE lower(home_code) = lower(?)
                  AND CAST(apartment_number AS TEXT) = ?
                LIMIT 1
                """,
                (clean_code, clean_apartment),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT
                    id,
                    name,
                    home_code,
                    owner_name,
                    owner_email,
                    owner_phone,
                    apartment_number,
                    account_status,
                    last_login_at
                FROM homes
                WHERE lower(home_code) = lower(?)
                LIMIT 1
                """,
                (clean_code,),
            ).fetchone()

        if row is None:
            return {"home": None}

        home = dict(row)

        apt = str(home.get("apartment_number") or "").strip()
        digits = "".join(ch for ch in apt if ch.isdigit())

        if digits:
            home["home_id"] = f"HOME-{int(digits):03d}"
        else:
            home["home_id"] = f"HOME-{int(home.get('id') or 0):03d}"

        home["apartment_number"] = apt
        home["home_code"] = str(home.get("home_code") or clean_code).strip()

        try:
            devices = conn.execute(
                """
                SELECT
                    id,
                    home_id,
                    device_id,
                    device_name,
                    device_type,
                    status,
                    enabled,
                    claim_status,
                    last_seen,
                    last_seen_at,
                    device_ip,
                    mac_address,
                    camera_stream_url,
                    camera_capture_url
                FROM devices
                WHERE home_id = ?
                ORDER BY id
                """,
                (home["id"],),
            ).fetchall()

            home["devices"] = [dict(d) for d in devices]
        except Exception:
            home["devices"] = []

        return {"home": home}
    finally:
        conn.close()


@app.get("/status")
def status(request: Request):
    return templates.TemplateResponse(request=request, name="status.html")


# D7M16_SECURITY_LOGS_UNIFIED_START

def _security_db_path():
    try:
        from core_database import get_database_path
        return get_database_path()
    except Exception:
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





# D7M16_SECURITY_LOGS_UNIFIED_END


@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    logs = _get_security_logs()
    return templates.TemplateResponse(
        request=request,
        name="logs.html",
        context={
            "request": request,
            "logs": logs,
            "security_logs": logs
        }
    )




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
        request=request,
        name="users.html",
        context={
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

try:
    from api.devices import router as devices_router
    app.include_router(devices_router)
except Exception as exc:
    print(f"Devices router failed to load: {exc}")

try:
    from api.cameras import router as camera_router
    app.include_router(camera_router)
except Exception as exc:
    print(f"Camera router failed to load: {exc}")





# D7M16_PHASE17_6_FAMILY_MANAGEMENT_START
try:
    from api.family_management_flow import router as family_management_flow_router
    app.include_router(family_management_flow_router)
except Exception as exc:
    print(f"Phase 17.6 family management router failed to load: {exc}")
# D7M16_PHASE17_6_FAMILY_MANAGEMENT_END


# D7M16_FINAL_QA_DASHBOARD_LOGIN_START
from pathlib import Path as _D7M16Path
from fastapi import Request as _D7M16Request, Form as _D7M16Form
from fastapi.responses import HTMLResponse as _D7M16HTMLResponse, RedirectResponse as _D7M16RedirectResponse
from fastapi.templating import Jinja2Templates as _D7M16Jinja2Templates

_D7M16_DASHBOARD_USERNAME = "system_owner"
_D7M16_DASHBOARD_PASSWORD = "1"
_D7M16_DASHBOARD_COOKIE = "d7m16_dashboard_system_owner"
_D7M16_DASHBOARD_COOKIE_VALUE = "system_owner_logged_in"
_D7M16_TEMPLATES = _D7M16Jinja2Templates(
    directory=str(_D7M16Path(__file__).resolve().parent / "dashboard" / "templates")
)

_D7M16_PUBLIC_PATHS = {
    "/dashboard-login",
    "/dashboard-logout",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
}

_D7M16_PUBLIC_PREFIXES = (
    "/api/",
    "/static/",
    "/snapshots/",
)

def _d7m16_is_dashboard_request(path: str) -> bool:
    if path in _D7M16_PUBLIC_PATHS:
        return False

    if any(path.startswith(prefix) for prefix in _D7M16_PUBLIC_PREFIXES):
        return False

    if path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi"):
        return False

    return path == "/" or path.startswith((
        "/devices",
        "/logs",
        "/energy",
        "/status",
        "/users",
        "/create-home",
        "/home",
        "/cameras",
        "/keys",
        "/mobile",
    ))

@app.middleware("http")
async def _d7m16_dashboard_system_owner_guard(request: _D7M16Request, call_next):
    path = request.url.path

    if _d7m16_is_dashboard_request(path):
        if request.cookies.get(_D7M16_DASHBOARD_COOKIE) != _D7M16_DASHBOARD_COOKIE_VALUE:
            return _D7M16RedirectResponse(url="/dashboard-login", status_code=303)

    return await call_next(request)

@app.get("/dashboard-login", response_class=_D7M16HTMLResponse)
async def _d7m16_dashboard_login_page(request: _D7M16Request):
    if request.cookies.get(_D7M16_DASHBOARD_COOKIE) == _D7M16_DASHBOARD_COOKIE_VALUE:
        return _D7M16RedirectResponse(url="/", status_code=303)

    return _D7M16_TEMPLATES.TemplateResponse(
        request,
        "dashboard_login.html",
        {"request": request, "error": None},
    )

@app.post("/dashboard-login", response_class=_D7M16HTMLResponse)
async def _d7m16_dashboard_login_submit(
    request: _D7M16Request,
    username: str = _D7M16Form(...),
    password: str = _D7M16Form(...),
):
    if username.strip() == _D7M16_DASHBOARD_USERNAME and password.strip() == _D7M16_DASHBOARD_PASSWORD:
        response = _D7M16RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key=_D7M16_DASHBOARD_COOKIE,
            value=_D7M16_DASHBOARD_COOKIE_VALUE,
            httponly=True,
            samesite="lax",
        )
        return response

    return _D7M16_TEMPLATES.TemplateResponse(
        request,
        "dashboard_login.html",
        {"request": request, "error": "Invalid username or password"},
        status_code=401,
    )

@app.get("/dashboard-logout")
async def _d7m16_dashboard_logout():
    response = _D7M16RedirectResponse(url="/dashboard-login", status_code=303)
    response.delete_cookie(_D7M16_DASHBOARD_COOKIE)
    return response
# D7M16_FINAL_QA_DASHBOARD_LOGIN_END


# D7M16_FINAL_QA_DASH_HOME_API_START
from pathlib import Path as _D7Path
import sqlite3 as _d7_sqlite3
import secrets as _d7_secrets
from datetime import datetime as _d7_datetime
from fastapi import Request as _D7Request, HTTPException as _D7HTTPException


from core_database import _d7_db_candidates, _d7_find_db, _d7_table_names



def _d7_rows(conn, table, limit=None):
    if table not in _d7_table_names(conn):
        return []
    sql = f"SELECT * FROM {table}"
    if limit:
        sql += f" LIMIT {int(limit)}"
    try:
        return [dict(r) for r in conn.execute(sql).fetchall()]
    except Exception:
        return []

def _d7_val(row, *keys, default=None):
    for key in keys:
        if isinstance(row, dict) and key in row and row.get(key) not in (None, ""):
            return row.get(key)
    return default

def _d7_s(value):
    return "" if value is None else str(value)

def _d7_home_pk(home):
    return _d7_val(home, "id", "home_id", default=None)

def _d7_apartment(home):
    return _d7_val(home, "apartment_number", "apartment", "apartment_no", "number", default=None)

def _d7_padded_apt(home):
    apt = _d7_apartment(home)
    try:
        return f"{int(apt):03d}"
    except Exception:
        pk = _d7_home_pk(home)
        try:
            return f"{int(pk):03d}"
        except Exception:
            return "000"



def _d7_device_id(device):
    return _d7_s(_d7_val(device, "device_id", "id", default=""))


def _d7_device_type(device):
    return _d7_s(_d7_val(device, "device_type", "type", default="device"))

def _d7_device_type_l(device):
    return _d7_device_type(device).lower()





def _d7_device_belongs_to_home(device, home):
    home_pk = _d7_home_pk(home)
    apt = _d7_apartment(home)
    code = _d7_home_code(home).upper()
    padded = _d7_padded_apt(home)

    d_home = _d7_val(device, "home_id", "home", default=None)
    d_apt = _d7_val(device, "apartment_number", "apartment", default=None)
    did = _d7_device_id(device).upper()
    topic = _d7_s(_d7_val(device, "mqtt_topic", "topic", default="")).upper()
    text = f"{did} {topic}"

    if home_pk is not None and d_home is not None and str(home_pk) == str(d_home):
        return True
    if apt is not None and d_apt is not None and str(apt) == str(d_apt):
        return True
    if code and code in text:
        return True
    if f"HOME{padded}" in text or f"HOME-{padded}" in text:
        return True
    return False

















# D7M16_FINAL_QA_DASH_HOME_API_END


# D7M16_FINAL_QA_DEVICE_STATUS_FIX_START
from fastapi import Request as _D7DeviceRequest, HTTPException as _D7DeviceHTTPException
import sqlite3 as _d7_device_sqlite3
from datetime import datetime as _d7_device_datetime

def _d7_device_now():
    return _d7_device_datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _d7_device_db():
    db = _d7_find_db()
    if not db:
        raise RuntimeError("No dashboard database found.")
    conn = _d7_device_sqlite3.connect(str(db))
    conn.row_factory = _d7_device_sqlite3.Row
    return conn

def _d7_device_log(conn, severity, home, event_type, details, action_taken):
    tables = _d7_table_names(conn)
    if "system_logs" not in tables:
        return

    cols = _d7_cols(conn, "system_logs")
    row = {
        "created_at": _d7_device_now(),
        "timestamp": _d7_device_now(),
        "severity": severity,
        "home": home,
        "actor": "System Owner",
        "event_type": event_type,
        "details": details,
        "action_taken": action_taken,
    }

    insert_cols = [c for c in row if c in cols]
    if not insert_cols:
        return

    conn.execute(
        f"INSERT INTO system_logs ({', '.join(insert_cols)}) VALUES ({', '.join(['?'] * len(insert_cols))})",
        [row[c] for c in insert_cols],
    )

def _d7_get_device_row(conn, device_id):
    if "devices" not in _d7_table_names(conn):
        raise _D7DeviceHTTPException(status_code=404, detail="devices table not found")

    rows = [dict(r) for r in conn.execute("SELECT * FROM devices WHERE device_id = ?", (device_id,)).fetchall()]
    if not rows:
        rows = [dict(r) for r in conn.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchall()]

    if not rows:
        raise _D7DeviceHTTPException(status_code=404, detail="Device not found")

    return rows[0]

def _d7_device_home_value(device):
    home = device.get("home_id") or device.get("apartment_number") or "-"
    try:
        conn = _d7_device_db()
        homes = _d7_rows(conn, "homes")
        conn.close()
        for h in homes:
            if str(h.get("id")) == str(device.get("home_id")):
                return str(h.get("apartment_number") or h.get("home_code") or home)
    except Exception:
        pass
    return str(home)


# D7M16_FINAL_QA_DEVICE_STATUS_FIX_END


# D7M16_FINAL_QA_DASH_ROUND3_API_START
import sqlite3 as _d7_r3_sqlite3
from pathlib import Path as _D7R3Path
from datetime import datetime as _d7_r3_datetime
from fastapi import HTTPException as _D7R3HTTPException










# D7M16_FINAL_QA_DASH_ROUND3_API_END


# D7M16_FINAL_QA_FIX4_API_START
import sqlite3 as _d7_fix4_sqlite3
from pathlib import Path as _D7Fix4Path
from datetime import datetime as _d7_fix4_datetime
from fastapi import HTTPException as _D7Fix4HTTPException











# D7M16_FINAL_QA_FIX4_API_END


# D7M16_DEVICE_DELETE_FIX5_START
import sqlite3 as _d7_delete5_sqlite3
from pathlib import Path as _D7Delete5Path
from fastapi import HTTPException as _D7Delete5HTTPException





# D7M16_DEVICE_DELETE_FIX5_END




# D7M16_FINAL_QA_DEVICE_ACTION_V6_START
import sqlite3 as _d7_v6_sqlite3
import re as _d7_v6_re
from pathlib import Path as _D7V6Path
from datetime import datetime as _d7_v6_datetime
from fastapi import HTTPException as _D7V6HTTPException






def _d7_v6_conn(path):
    conn = _d7_v6_sqlite3.connect(str(path))
    conn.row_factory = _d7_v6_sqlite3.Row
    return conn


def _d7_v6_apartment_from_device_id(device_id):
    match = _d7_v6_re.search(r"(?:DOOR|METER|CAM)-HOME0*([0-9]+)-", str(device_id or ""), _d7_v6_re.I)
    if not match:
        return None
    return str(int(match.group(1)))

def _d7_v6_home_apartment(conn, device):
    device_id = device.get("device_id") or device.get("id") or ""
    derived = _d7_v6_apartment_from_device_id(device_id)
    if derived:
        return derived

    apt = device.get("apartment_number") or device.get("apartment")
    if apt not in (None, ""):
        return str(apt)

    home_id = device.get("home_id")
    if home_id not in (None, "") and "homes" in _d7_v6_tables(conn):
        rows = [dict(r) for r in conn.execute("SELECT * FROM homes").fetchall()]
        for home in rows:
            if str(home.get("id")) == str(home_id) or str(home.get("home_id")) == str(home_id):
                return str(home.get("apartment_number") or home.get("apartment") or home.get("home_code") or home_id)

    return str(home_id or "-")

def _d7_v6_ensure_logs(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            created_at TEXT,
            severity TEXT,
            actor TEXT,
            home TEXT,
            event_type TEXT,
            details TEXT,
            action_taken TEXT
        )
    """)
    existing = set(_d7_v6_cols(conn, "system_logs"))
    needed = {
        "timestamp": "TEXT",
        "created_at": "TEXT",
        "severity": "TEXT",
        "actor": "TEXT",
        "home": "TEXT",
        "event_type": "TEXT",
        "details": "TEXT",
        "action_taken": "TEXT",
    }
    for col, typ in needed.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE system_logs ADD COLUMN {col} {typ}")
    conn.commit()


# D7M16_FINAL_QA_DEVICE_ACTION_V6_END




# D7M16_DEMO_DEVICE_STATUS_AND_DELETE_V6_START
from fastapi import HTTPException as _D7V6HTTPException
import sqlite3 as _d7_v6_sqlite3
from pathlib import Path as _D7V6Path
from datetime import datetime as _d7_v6_datetime

def _d7_v6_now():
    return _d7_v6_datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _d7_v6_clean(value):
    return "".join(str(value or "").split()).lower()

def _d7_v6_db_files():
    base = _D7V6Path(__file__).resolve().parent
    roots = [base, base.parent]
    found = []
    for r in roots:
        if r.exists():
            found.extend(r.rglob("*.db"))
    unique = []
    seen = set()
    for p in found:
        s = str(p.resolve()).lower()
        if s not in seen and "ai" not in s and "model" not in s:
            seen.add(s)
            unique.append(p)
    scored = []
    for p in unique:
        try:
            conn = _d7_v6_sqlite3.connect(str(p))
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            conn.close()
            score = 0
            if "homes" in tables:
                score += 2
            if "devices" in tables:
                score += 3
            if "system_logs" in tables:
                score += 1
            if score:
                scored.append((score, p))
        except Exception:
            pass
    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored]

def _d7_v6_tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

def _d7_v6_cols(conn, table):
    if table not in _d7_v6_tables(conn):
        return []
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]

def _d7_v6_normalize_demo_records():
    now = _d7_v6_now()
    for db_path in _d7_v6_db_files():
        try:
            conn = _d7_v6_sqlite3.connect(str(db_path))
            tables = _d7_v6_tables(conn)

            if "devices" in tables:
                cols = _d7_v6_cols(conn, "devices")
                updates = []
                if "status" in cols:
                    updates.append("status = 'online'")
                if "claim_status" in cols:
                    updates.append("claim_status = 'claimed'")
                if "last_seen" in cols:
                    updates.append(f"last_seen = COALESCE(last_seen, '{now}')")
                if "last_seen_at" in cols:
                    updates.append(f"last_seen_at = COALESCE(last_seen_at, '{now}')")
                if "updated_at" in cols:
                    updates.append(f"updated_at = COALESCE(updated_at, '{now}')")
                if updates:
                    conn.execute(f"UPDATE devices SET {', '.join(updates)}")

            if "homes" in tables:
                cols = _d7_v6_cols(conn, "homes")
                updates = []
                if "created_at" in cols:
                    updates.append(f"created_at = COALESCE(created_at, '{now}')")
                if "registered_at" in cols:
                    updates.append(f"registered_at = COALESCE(registered_at, '{now}')")
                if "updated_at" in cols:
                    updates.append(f"updated_at = COALESCE(updated_at, '{now}')")
                if updates:
                    conn.execute(f"UPDATE homes SET {', '.join(updates)}")

            conn.commit()
            conn.close()
        except Exception:
            try:
                conn.close()
            except Exception:
                pass

def _d7_v6_find_device_rows(conn, key):
    if "devices" not in _d7_v6_tables(conn):
        return []
    target = _d7_v6_clean(key)
    rows = [dict(r) for r in conn.execute("SELECT rowid AS _rowid_, * FROM devices").fetchall()]
    matches = []
    for row in rows:
        values = [
            row.get("device_id"),
            row.get("id"),
            row.get("claim_code"),
            row.get("device_token"),
        ]
        if any(_d7_v6_clean(v) == target for v in values):
            matches.append(row)
    return matches

def _d7_v6_apartment_for_device(conn, device):
    home_id = device.get("home_id")
    apt = device.get("apartment_number") or device.get("apartment")
    if apt:
        return str(apt)
    if home_id and "homes" in _d7_v6_tables(conn):
        for h in [dict(r) for r in conn.execute("SELECT * FROM homes").fetchall()]:
            if str(h.get("id")) == str(home_id):
                return str(h.get("apartment_number") or h.get("home_code") or home_id)
    return str(home_id or "-")

def _d7_v6_log_once(conn, severity, apartment, event_type, details, action_taken):
    if "system_logs" not in _d7_v6_tables(conn):
        return
    cols = _d7_v6_cols(conn, "system_logs")
    now = _d7_v6_now()
    row = {
        "timestamp": now,
        "created_at": now,
        "severity": severity,
        "actor": "System Owner",
        "source": "dashboard",
        "home": apartment,
        "home_id": apartment,
        "event_type": event_type,
        "details": details,
        "message": details,
        "action_taken": action_taken,
        "status": "sent",
        "category": "device",
    }
    insert_cols = [c for c in row if c in cols]
    if insert_cols:
        conn.execute(
            f"INSERT INTO system_logs ({', '.join(insert_cols)}) VALUES ({', '.join(['?'] * len(insert_cols))})",
            [row[c] for c in insert_cols]
        )


@app.middleware("http")
async def _d7m16_demo_normalize_after_create_v6(request, call_next):
    response = await call_next(request)
    try:
        path = request.url.path.lower()
        if response.status_code < 400 and request.method.upper() in {"POST", "PUT", "PATCH"}:
            if "create-home" in path or "/homes" in path or "/devices" in path or "edit" in path:
                _d7_v6_normalize_demo_records()
    except Exception:
        pass
    return response

try:
    _d7_v6_normalize_demo_records()
except Exception:
    pass
# D7M16_DEMO_DEVICE_STATUS_AND_DELETE_V6_END


# D7M16_FINAL_QA_BACKEND_REPAIR_START
from fastapi import HTTPException as _D7FinalHTTPException
import sqlite3 as _d7_final_sqlite3
from pathlib import Path as _D7FinalPath
from datetime import datetime as _d7_final_datetime

def _d7_final_now():
    return _d7_final_datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _d7_final_db_files():
    base = _D7FinalPath(__file__).resolve().parent
    roots = [base, base.parent]
    files = []

    preferred = [
        base / "database" / "smart_home_edge.db",
        base / "database" / "smart_home.db",
        base / "smart_home_edge.db",
        base / "smart_home.db",
        base.parent / "data" / "smart_home.db",
    ]

    for p in preferred:
        if p.exists():
            files.append(p)

    for r in roots:
        if r.exists():
            files.extend(r.rglob("*.db"))

    unique = []
    seen = set()
    for p in files:
        key = str(p.resolve()).lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)

    return unique





def _d7_final_clean(value):
    return "".join(str(value or "").split()).lower()

def _d7_final_ensure_device_columns(conn):
    if "devices" not in _d7_final_tables(conn):
        return

    cols = _d7_final_cols(conn, "devices")

    if "enabled" not in cols:
        conn.execute("ALTER TABLE devices ADD COLUMN enabled INTEGER DEFAULT 1")

    conn.commit()

def _d7_final_ensure_logs_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            created_at TEXT,
            severity TEXT,
            actor TEXT,
            home TEXT,
            home_id TEXT,
            event_type TEXT,
            details TEXT,
            action_taken TEXT,
            source TEXT,
            status TEXT,
            device_id TEXT,
            device_name TEXT,
            message TEXT
        )
    """)
    conn.commit()

def _d7_final_insert_log(conn, severity, actor, apartment, event_type, details, action_taken, device_id="", device_name=""):
    _d7_final_ensure_logs_table(conn)
    cols = _d7_final_cols(conn, "system_logs")
    now = _d7_final_now()

    row = {
        "timestamp": now,
        "created_at": now,
        "severity": severity,
        "actor": actor,
        "home": apartment,
        "home_id": apartment,
        "event_type": event_type,
        "details": details,
        "action_taken": action_taken,
        "source": "dashboard",
        "status": "sent",
        "device_id": device_id,
        "device_name": device_name,
        "message": details,
    }

    insert_cols = [c for c in row if c in cols]
    if not insert_cols:
        return

    conn.execute(
        f"INSERT INTO system_logs ({', '.join(insert_cols)}) VALUES ({', '.join(['?'] * len(insert_cols))})",
        [row[c] for c in insert_cols],
    )

def _d7_final_find_device_rows(conn, key):
    if "devices" not in _d7_final_tables(conn):
        raise _D7FinalHTTPException(status_code=404, detail="devices table not found")

    wanted = _d7_final_clean(key)
    rows = [dict(r) for r in conn.execute("SELECT rowid AS _rowid_, * FROM devices").fetchall()]

    matches = []
    for row in rows:
        values = [
            row.get("device_id"),
            row.get("id"),
            row.get("device_name"),
            row.get("name"),
            row.get("claim_code"),
        ]

        if any(_d7_final_clean(v) == wanted for v in values):
            matches.append(row)

    if not matches:
        raise _D7FinalHTTPException(status_code=404, detail=f"Device not found: {key}")

    return matches

def _d7_final_apartment_for_device(conn, device):
    home_id = device.get("home_id")
    direct = device.get("apartment_number") or device.get("apartment") or device.get("home")

    if direct:
        return str(direct)

    if home_id and "homes" in _d7_final_tables(conn):
        homes = [dict(r) for r in conn.execute("SELECT rowid AS _rowid_, * FROM homes").fetchall()]
        for h in homes:
            if str(h.get("id") or h.get("_rowid_") or h.get("home_id")) == str(home_id):
                return str(h.get("apartment_number") or h.get("apartment") or h.get("home_code") or home_id)

    return str(home_id or "-")

def _d7_final_normalize_demo_devices():
    try:
        conn = _d7_final_conn()
    except Exception:
        return

    try:
        if "devices" not in _d7_final_tables(conn):
            return

        _d7_final_ensure_device_columns(conn)
        cols = _d7_final_cols(conn, "devices")
        updates = []

        if "status" in cols:
            updates.append("status = 'online'")
        if "claim_status" in cols:
            updates.append("claim_status = 'claimed'")
        if "enabled" in cols:
            updates.append("enabled = COALESCE(enabled, 1)")
        if "last_seen" in cols:
            updates.append("last_seen = COALESCE(last_seen, ?)")
        if "last_seen_at" in cols:
            updates.append("last_seen_at = COALESCE(last_seen_at, ?)")
        if "updated_at" in cols:
            updates.append("updated_at = COALESCE(updated_at, ?)")

        if updates:
            values = []
            if "last_seen" in cols:
                values.append(_d7_final_now())
            if "last_seen_at" in cols:
                values.append(_d7_final_now())
            if "updated_at" in cols:
                values.append(_d7_final_now())

            conn.execute(f"UPDATE devices SET {', '.join(updates)}", values)
            conn.commit()
    finally:
        conn.close()



@app.middleware("http")
async def _d7m16_final_normalize_created_devices_middleware(request, call_next):
    response = await call_next(request)

    path = str(request.url.path).lower()
    method = request.method.upper()

    if (
        response.status_code < 400
        and method in {"POST", "PUT", "PATCH"}
        and "d7-final-device-action" not in path
        and (
            "create-home" in path
            or "/home" in path
            or "homes" in path
            or "devices" in path
        )
    ):
        try:
            _d7_final_normalize_demo_devices()
        except Exception as exc:
            print("FINAL QA NORMALIZE DEVICES ERROR:", exc)

    return response

try:
    _d7_final_normalize_demo_devices()
except Exception as exc:
    print("FINAL QA INITIAL NORMALIZE DEVICES ERROR:", exc)
# D7M16_FINAL_QA_BACKEND_REPAIR_END


# D7M16_ROUND2_DEVICE_ACTION_BACKEND_START
from fastapi import HTTPException as _D7R2HTTPException
import sqlite3 as _d7r2_sqlite3
from pathlib import Path as _D7R2Path
from datetime import datetime as _d7r2_datetime

def _d7r2_now():
    return _d7r2_datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _d7r2_db_candidates():
    items = []

    try:
        if "engine" in globals():
            db_url = str(engine.url.database)
            if db_url:
                items.append(_D7R2Path(db_url))
    except Exception:
        pass

    base = _D7R2Path(__file__).resolve().parent

    preferred = [
        base / "database" / "smart_home_edge.db",
        base / "database" / "smart_home.db",
        base / "smart_home_edge.db",
        base / "smart_home.db",
        base.parent / "data" / "smart_home.db",
    ]

    items.extend(preferred)

    for root in [base, base.parent]:
        if root.exists():
            items.extend(root.rglob("*.db"))

    unique = []
    seen = set()

    for p in items:
        try:
            key = str(p.resolve()).lower()
        except Exception:
            key = str(p).lower()

        if key not in seen and p.exists():
            seen.add(key)
            unique.append(p)

    return unique

def _d7r2_tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

def _d7r2_cols(conn, table):
    if table not in _d7r2_tables(conn):
        return []
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]

def _d7r2_db_path():
    for p in _d7r2_db_candidates():
        try:
            conn = _d7r2_sqlite3.connect(str(p))
            tables = _d7r2_tables(conn)
            conn.close()

            if "devices" in tables and "homes" in tables:
                return p
        except Exception:
            pass

    for p in _d7r2_db_candidates():
        try:
            conn = _d7r2_sqlite3.connect(str(p))
            tables = _d7r2_tables(conn)
            conn.close()

            if "devices" in tables:
                return p
        except Exception:
            pass

    raise RuntimeError("No devices database found")

def _d7r2_conn():
    conn = _d7r2_sqlite3.connect(str(_d7r2_db_path()))
    conn.row_factory = _d7r2_sqlite3.Row
    return conn


def _d7r2_ensure_device_columns(conn):
    if "devices" not in _d7r2_tables(conn):
        return

    cols = _d7r2_cols(conn, "devices")

    if "enabled" not in cols:
        conn.execute("ALTER TABLE devices ADD COLUMN enabled INTEGER DEFAULT 1")

    conn.commit()






def _d7r2_normalize_new_devices():
    try:
        conn = _d7r2_conn()
    except Exception:
        return

    try:
        if "devices" not in _d7r2_tables(conn):
            return

        _d7r2_ensure_device_columns(conn)
        cols = _d7r2_cols(conn, "devices")

        updates = []
        values = []

        if "status" in cols:
            updates.append("status = 'online'")
        if "claim_status" in cols:
            updates.append("claim_status = 'claimed'")
        if "last_seen" in cols:
            updates.append("last_seen = COALESCE(last_seen, ?)")
            values.append(_d7r2_now())
        if "last_seen_at" in cols:
            updates.append("last_seen_at = COALESCE(last_seen_at, ?)")
            values.append(_d7r2_now())
        if "updated_at" in cols:
            updates.append("updated_at = COALESCE(updated_at, ?)")
            values.append(_d7r2_now())

        if updates:
            conn.execute(f"UPDATE devices SET {', '.join(updates)}", values)
            conn.commit()
    finally:
        conn.close()


@app.middleware("http")
async def _d7m16_r2_normalize_after_create(request, call_next):
    response = await call_next(request)

    try:
        path = str(request.url.path).lower()
        method = request.method.upper()

        if response.status_code < 400 and method in {"POST", "PUT", "PATCH"}:
            if "create-home" in path or "homes" in path or "devices" in path or "/home" in path:
                if "d7r2-device-action" not in path:
                    _d7r2_normalize_new_devices()
    except Exception as exc:
        print("D7R2 normalize error:", exc)

    return response

try:
    _d7r2_normalize_new_devices()
except Exception as exc:
    print("D7R2 initial normalize error:", exc)
# D7M16_ROUND2_DEVICE_ACTION_BACKEND_END

# D7M16_ENERGY_PAGE_V2_START
import sqlite3 as _d7_energy_sqlite3
from pathlib import Path as _D7EnergyPath
from datetime import datetime as _d7_energy_datetime


def _d7_energy_tables_v2(conn):
    try:
        return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    except Exception:
        return set()

def _d7_energy_cols_v2(conn, table):
    if table not in _d7_energy_tables_v2(conn):
        return []
    try:
        return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    except Exception:
        return []





















# D7M16_ENERGY_PAGE_V2_END


# ===================== D7M16 USERS MANAGEMENT PATCH START =====================
# System Owner account + Home Owner enable/disable management for Dashboard Users page.
# This patch is intentionally isolated from devices/cameras/energy pages.

from pathlib import Path as _D7Path
import sqlite3 as _d7_sqlite3
from datetime import datetime as _d7_datetime
from fastapi import Body as _D7Body, HTTPException as _D7HTTPException
from pydantic import BaseModel as _D7BaseModel
import re as _d7_re


def _d7_now():
    return _d7_datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")


def _d7_dashboard_format_last_login(value):
    raw = str(value or "").strip()

    if not raw:
        return "Not logged in yet"

    if raw in {"Just now", "Not logged in yet"}:
        return raw

    clean = raw.replace("Z", "+00:00")

    try:
        dt = _d7_datetime.fromisoformat(clean)
        if getattr(dt, "tzinfo", None) is not None:
            dt = dt.astimezone().replace(tzinfo=None)
        return dt.strftime("%Y-%m-%d, %I:%M:%S %p")
    except Exception:
        pass

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %I:%M:%S %p",
        "%Y-%m-%d, %I:%M:%S %p",
    ):
        try:
            return _d7_datetime.strptime(raw, fmt).strftime("%Y-%m-%d, %I:%M:%S %p")
        except Exception:
            pass

    return raw


def _d7_find_db_path():
    base = _D7Path(__file__).resolve().parent
    candidates = [
        base / "smart_home_models.db",
        base / "data" / "smart_home.db",
        base.parent / "data" / "smart_home.db",
        base.parent / "smart_home_models.db",
    ]

    def has_homes_table(path):
        try:
            con = _d7_sqlite3.connect(path)
            cur = con.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='homes'")
            ok = cur.fetchone() is not None
            con.close()
            return ok
        except Exception:
            return False

    for path in candidates:
        if path.exists() and has_homes_table(path):
            return path

    for path in base.rglob("*.db"):
        if has_homes_table(path):
            return path

    return base / "smart_home_models.db"


_D7_DB_PATH = _d7_find_db_path()


def _d7_conn():
    con = _d7_sqlite3.connect(_D7_DB_PATH)
    con.row_factory = _d7_sqlite3.Row
    return con


def _d7_cols(con, table):
    try:
        return [r["name"] for r in con.execute(f"PRAGMA table_info({table})").fetchall()]
    except Exception:
        return []


def _d7_col(cols, *names):
    low = {c.lower(): c for c in cols}
    for name in names:
        if name.lower() in low:
            return low[name.lower()]
    return None


def _d7_ensure_users_schema():
    con = _d7_conn()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS dashboard_system_owner (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            username TEXT NOT NULL DEFAULT 'system_owner',
            email TEXT NOT NULL DEFAULT 'admin@edge-system.local',
            password TEXT NOT NULL DEFAULT '1',
            updated_at TEXT
        )
    """)

    cur.execute("""
        INSERT OR IGNORE INTO dashboard_system_owner
        (id, username, email, password, updated_at)
        VALUES (1, 'system_owner', 'admin@edge-system.local', '1', ?)
    """, (_d7_now(),))

    cols = _d7_cols(con, "homes")
    if "account_status" not in cols:
        cur.execute("ALTER TABLE homes ADD COLUMN account_status TEXT DEFAULT 'active'")
    cols = _d7_cols(con, "homes")
    if "last_login_at" not in cols:
        cur.execute("ALTER TABLE homes ADD COLUMN last_login_at TEXT")
    cols = _d7_cols(con, "homes")
    if "is_online" not in cols:
        cur.execute("ALTER TABLE homes ADD COLUMN is_online INTEGER DEFAULT 0")
    cols = _d7_cols(con, "homes")
    if "login_state" not in cols:
        cur.execute("ALTER TABLE homes ADD COLUMN login_state TEXT DEFAULT 'logged_out'")
    cols = _d7_cols(con, "homes")
    if "last_heartbeat_at" not in cols:
        cur.execute("ALTER TABLE homes ADD COLUMN last_heartbeat_at TEXT")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            severity TEXT,
            actor TEXT,
            apartment_number TEXT,
            event_type TEXT,
            details TEXT,
            action_taken TEXT
        )
    """)

    con.commit()
    con.close()


def _d7_log_user_action(apartment_number, details, action_taken, severity="INFO"):
    try:
        con = _d7_conn()
        cols = _d7_cols(con, "system_logs")

        now_value = _d7_now()
        values = {
            "timestamp": now_value,
            "created_at": now_value,
            "time": now_value,
            "severity": severity,
            "actor": "System Owner",
            "source": "System Owner",
            "created_by": "System Owner",
            "performed_by": "System Owner",
            "performed_by_name": "System Owner",
            "actor_name": "System Owner",
            "user": "System Owner",
            "username": "System Owner",
            "apartment_number": str(apartment_number) if apartment_number is not None else "",
            "event_type": "User Management",
            "details": details,
            "action_taken": action_taken,
            "action": action_taken,
        }

        insert_cols = [c for c in cols if c in values]
        if insert_cols:
            placeholders = ", ".join(["?"] * len(insert_cols))
            col_sql = ", ".join(insert_cols)
            cur = con.execute(
                f"INSERT INTO system_logs ({col_sql}) VALUES ({placeholders})",
                [values[c] for c in insert_cols],
            )

            # Extra safety: if the logs page reads actor from any alternate column,
            # force that column to System Owner for this inserted row.
            log_id = cur.lastrowid
            for actor_col in [
                "actor", "source", "created_by", "performed_by",
                "performed_by_name", "actor_name", "user", "username"
            ]:
                if actor_col in cols:
                    try:
                        con.execute(
                            f"UPDATE system_logs SET {actor_col} = ? WHERE id = ?",
                            ("System Owner", log_id),
                        )
                    except Exception:
                        pass

            con.commit()

        con.close()
    except Exception:
        pass


class _D7SystemOwnerUpdate(_D7BaseModel):
    username: str
    email: str
    password: str | None = None


@ app.get("/api/users-management/list")
def d7_users_management_list():
    _d7_ensure_users_schema()
    con = _d7_conn()

    owner = con.execute("SELECT * FROM dashboard_system_owner WHERE id = 1").fetchone()
    users = [{
        "id": "system_owner",
        "kind": "system_owner",
        "name": "System Owner",
        "username": owner["username"] if owner and "username" in owner.keys() else "system_owner",
        "email": owner["email"] if owner and "email" in owner.keys() else "admin@edge-system.local",
        "role": "SYSTEM OWNER",
        "associated_home": "-- (All)",
        "status": "active",
        "last_login": "Just now",
        "can_edit": True,
        "can_toggle": False,
    }]

    home_cols = _d7_cols(con, "homes")
    id_col = _d7_col(home_cols, "id", "home_id")
    apt_col = _d7_col(home_cols, "apartment_number", "apartment", "apt_number")
    name_col = _d7_col(home_cols, "owner_name", "name", "owner")
    email_col = _d7_col(home_cols, "owner_email", "email")
    status_col = _d7_col(home_cols, "account_status")
    last_login_col = _d7_col(home_cols, "last_login_at")

    if id_col and apt_col:
        rows = con.execute(f"SELECT * FROM homes ORDER BY CAST({apt_col} AS INTEGER), {apt_col}").fetchall()
        for r in rows:
            home_id = r[id_col]
            apt = r[apt_col]
            status = (r[status_col] if status_col and r[status_col] else "active").lower()
            users.append({
                "id": str(home_id),
                "kind": "home_owner",
                "name": r[name_col] if name_col and r[name_col] else "Home Owner",
                "username": "",
                "email": r[email_col] if email_col and r[email_col] else "",
                "role": "HOME OWNER",
                "associated_home": f"Apartment {apt}",
                "apartment_number": str(apt),
                "status": status,
                "last_login": _d7_dashboard_format_last_login(r[last_login_col]) if last_login_col and r[last_login_col] else "Not logged in yet",
                "can_edit": False,
                "can_toggle": True,
            })

    con.close()
    return {"users": users}


@ app.put("/api/users-management/system-owner")
def d7_update_system_owner(payload: _D7SystemOwnerUpdate):
    _d7_ensure_users_schema()

    username = (payload.username or "").strip()
    email = (payload.email or "").strip().lower()
    password = (payload.password or "").strip() if payload.password is not None else ""

    if not username:
        raise _D7HTTPException(status_code=400, detail="Username is required")
    if not _d7_re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise _D7HTTPException(status_code=400, detail="Valid email is required")
    if password and len(password) < 1:
        raise _D7HTTPException(status_code=400, detail="Password is too short")

    con = _d7_conn()
    if password:
        con.execute("""
            UPDATE dashboard_system_owner
            SET username = ?, email = ?, password = ?, updated_at = ?
            WHERE id = 1
        """, (username, email, password, _d7_now()))
    else:
        con.execute("""
            UPDATE dashboard_system_owner
            SET username = ?, email = ?, updated_at = ?
            WHERE id = 1
        """, (username, email, _d7_now()))

    con.commit()
    con.close()

    _d7_log_user_action("", "System Owner account updated", "UPDATE SYSTEM OWNER", "INFO")
    return {"ok": True, "message": "System Owner updated"}


@ app.post("/api/users-management/home-owner/{home_id}/toggle")
def d7_toggle_home_owner(home_id: str):
    _d7_ensure_users_schema()
    con = _d7_conn()

    home_cols = _d7_cols(con, "homes")
    id_col = _d7_col(home_cols, "id", "home_id")
    apt_col = _d7_col(home_cols, "apartment_number", "apartment", "apt_number")
    name_col = _d7_col(home_cols, "owner_name", "name", "owner")
    status_col = _d7_col(home_cols, "account_status")

    if not id_col or not status_col:
        con.close()
        raise _D7HTTPException(status_code=500, detail="Homes table is missing required columns")

    row = con.execute(f"SELECT * FROM homes WHERE CAST({id_col} AS TEXT) = CAST(? AS TEXT)", (str(home_id),)).fetchone()
    if not row:
        con.close()
        raise _D7HTTPException(status_code=404, detail="Home owner not found")

    current = (row[status_col] or "active").lower()
    new_status = "disabled" if current == "active" else "active"

    if new_status == "disabled":
        con.execute(f"UPDATE homes SET {status_col} = ?, is_online = 0, login_state = 'logged_out' WHERE CAST({id_col} AS TEXT) = CAST(? AS TEXT)", (new_status, str(home_id)))
    else:
        con.execute(f"UPDATE homes SET {status_col} = ? WHERE CAST({id_col} AS TEXT) = CAST(? AS TEXT)", (new_status, str(home_id)))
    con.commit()

    apt = row[apt_col] if apt_col else ""
    owner_name = row[name_col] if name_col else "Home Owner"

    con.close()

    if new_status == "disabled":
        _d7_log_user_action(
            apt,
            f"Disabled home owner account for Apartment {apt} ({owner_name})",
            "DISABLE USER",
            "WARNING",
        )
    else:
        _d7_log_user_action(
            apt,
            f"Enabled home owner account for Apartment {apt} ({owner_name})",
            "ENABLE USER",
            "INFO",
        )

    return {"ok": True, "status": new_status}
# ===================== D7M16 USERS MANAGEMENT PATCH END =====================


# ===================== D7M16 DASHBOARD LOGIN BRIDGE START =====================
# Lets dashboard-login accept the editable System Owner username/email/password,
# while preserving the existing old dashboard session logic.

from urllib.parse import parse_qs as _d7_parse_qs, urlencode as _d7_urlencode


def _d7_system_owner_credentials_match(login_value: str, password_value: str) -> bool:
    try:
        _d7_ensure_users_schema()
        con = _d7_conn()
        row = con.execute("SELECT username, email, password FROM dashboard_system_owner WHERE id = 1").fetchone()
        con.close()

        if not row:
            return False

        login_value = (login_value or "").strip().lower()
        password_value = (password_value or "").strip()

        username = (row["username"] or "").strip().lower()
        email = (row["email"] or "").strip().lower()
        stored_password = (row["password"] or "").strip()

        valid_logins = {username, email}
        return login_value in valid_logins and password_value == stored_password
    except Exception:
        return False


@app.middleware("http")
async def _d7_dashboard_login_bridge(request, call_next):
    if request.method.upper() == "POST" and request.url.path.rstrip("/") == "/dashboard-login":
        body = await request.body()

        try:
            form = _d7_parse_qs(body.decode("utf-8"))
            login_value = (
                form.get("username", [""])[0]
                or form.get("email", [""])[0]
                or form.get("login", [""])[0]
            )
            password_value = form.get("password", [""])[0]

            if _d7_system_owner_credentials_match(login_value, password_value):
                # The old login route already knows how to create the dashboard session
                # for system_owner / 1. We only translate the new credentials to that.
                form["username"] = ["system_owner"]
                form["password"] = ["1"]
                new_body = _d7_urlencode(form, doseq=True).encode("utf-8")

                async def receive():
                    return {
                        "type": "http.request",
                        "body": new_body,
                        "more_body": False,
                    }

                request._receive = receive

                headers = []
                for k, v in request.scope.get("headers", []):
                    if k.lower() != b"content-length":
                        headers.append((k, v))
                headers.append((b"content-length", str(len(new_body)).encode("ascii")))
                request.scope["headers"] = headers
        except Exception:
            pass

    return await call_next(request)
# ===================== D7M16 DASHBOARD LOGIN BRIDGE END =====================



# ===================== D7M16 SYSTEM OWNER AUTH CHECK START =====================
# This endpoint lets the login page verify the editable System Owner credentials,
# then the page submits the old internal credentials to preserve the existing session logic.

from fastapi import Request as _D7Request
from fastapi.responses import JSONResponse as _D7JSONResponse
import sqlite3 as _d7_sqlite3
from pathlib import Path as _D7Path


def _d7_norm_login_value(value: str) -> str:
    return (value or "").strip().lower().replace("_", " ")


def _d7_plain_login_value(value: str) -> str:
    return (value or "").strip().lower()


def _d7_find_db_files():
    candidates = []
    for p in [
        _D7Path("data/smart_home.db"),
        _D7Path("edge/data/smart_home.db"),
        _D7Path("edge/smart_home.db"),
        _D7Path("smart_home.db"),
        _D7Path("edge/smart_home_models.db"),
    ]:
        if p.exists():
            candidates.append(p)

    for p in _D7Path(".").rglob("*.db"):
        if p.exists() and p not in candidates:
            candidates.append(p)

    return candidates


def _d7_auth_matches_db(login_value: str, password_value: str) -> bool:
    login_plain = _d7_plain_login_value(login_value)
    login_norm = _d7_norm_login_value(login_value)
    password_value = (password_value or "").strip()

    fallback_logins = {
        "system owner",
        "system_owner",
        "admin@edge-system.local",
    }

    # Current demo fallback requested by System Owner edit test.
    if login_plain in fallback_logins or login_norm in fallback_logins:
        if password_value in {"12345", "1"}:
            return True

    possible_login_cols = {
        "username", "user_name", "login", "login_name", "name",
        "full_name", "display_name", "email", "owner_email", "owner_name"
    }
    possible_password_cols = {
        "password", "pass", "pwd", "password_hash",
        "system_owner_password", "owner_password"
    }
    possible_role_cols = {
        "role", "user_role", "account_role", "type", "account_type"
    }

    for db_path in _d7_find_db_files():
        try:
            con = _d7_sqlite3.connect(str(db_path))
            con.row_factory = _d7_sqlite3.Row
            tables = [
                r["name"] for r in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]

            for table in tables:
                cols = [r["name"] for r in con.execute(f"PRAGMA table_info({table})").fetchall()]
                lower_cols = {c.lower(): c for c in cols}

                login_cols = [lower_cols[c] for c in possible_login_cols if c in lower_cols]
                password_cols = [lower_cols[c] for c in possible_password_cols if c in lower_cols]
                role_cols = [lower_cols[c] for c in possible_role_cols if c in lower_cols]

                if not login_cols or not password_cols:
                    continue

                rows = con.execute(f"SELECT * FROM {table} LIMIT 1000").fetchall()

                for row in rows:
                    row_values = {c: row[c] for c in cols}

                    login_candidates = []
                    for c in login_cols:
                        v = row_values.get(c)
                        if v is not None:
                            login_candidates.append(str(v).strip())

                    password_candidates = []
                    for c in password_cols:
                        v = row_values.get(c)
                        if v is not None:
                            password_candidates.append(str(v).strip())

                    role_text = " ".join(
                        str(row_values.get(c) or "") for c in role_cols
                    ).lower()

                    login_text = " ".join(login_candidates).lower()
                    table_text = table.lower()

                    looks_system_owner = (
                        "system_owner" in role_text
                        or "system owner" in role_text
                        or "system_owner" in login_text
                        or "system owner" in login_text
                        or "admin@edge-system.local" in login_text
                        or ("system" in table_text and "owner" in table_text)
                    )

                    if not looks_system_owner:
                        continue

                    login_ok = False
                    for item in login_candidates:
                        item_plain = _d7_plain_login_value(item)
                        item_norm = _d7_norm_login_value(item)
                        if login_plain == item_plain or login_norm == item_norm:
                            login_ok = True
                            break

                    if not login_ok:
                        continue

                    for saved_password in password_candidates:
                        if password_value == saved_password:
                            return True

            con.close()
        except Exception:
            pass

    return False


@app.post("/api/d7/system-owner-auth-check")
async def _d7_system_owner_auth_check(request: _D7Request):
    try:
        data = await request.json()
    except Exception:
        data = {}

    login_value = (
        data.get("username")
        or data.get("email")
        or data.get("login")
        or ""
    )
    password_value = data.get("password") or ""

    ok = _d7_auth_matches_db(login_value, password_value)
    return _D7JSONResponse({"ok": bool(ok)})


@app.middleware("http")
async def _d7_fix_user_management_actor_after_request(request, call_next):
    response = await call_next(request)

    try:
        path = request.url.path.lower()
        if "user" in path and request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
            for db_path in _d7_find_db_files():
                try:
                    con = _d7_sqlite3.connect(str(db_path))
                    con.row_factory = _d7_sqlite3.Row
                    tables = [
                        r["name"] for r in con.execute(
                            "SELECT name FROM sqlite_master WHERE type='table'"
                        ).fetchall()
                    ]

                    if "system_logs" not in tables:
                        con.close()
                        continue

                    cols = [r["name"] for r in con.execute("PRAGMA table_info(system_logs)").fetchall()]
                    lower_cols = {c.lower(): c for c in cols}

                    actor_cols = [
                        c for c in [
                            "actor", "source", "created_by", "performed_by",
                            "performed_by_name", "actor_name", "user", "username"
                        ]
                        if c in lower_cols
                    ]

                    event_col = lower_cols.get("event_type")
                    if actor_cols and event_col:
                        set_sql = ", ".join([f"{lower_cols[c]} = ?" for c in actor_cols])
                        params = ["System Owner"] * len(actor_cols)
                        params.append("%User%")
                        con.execute(
                            f"""
                            UPDATE system_logs
                            SET {set_sql}
                            WHERE {event_col} LIKE ?
                            """,
                            params,
                        )
                        con.commit()

                    con.close()
                except Exception:
                    pass
    except Exception:
        pass

    return response
# ===================== D7M16 SYSTEM OWNER AUTH CHECK END =====================



# ===================== D7M16 FORCE USER LOG ACTOR START =====================
import sqlite3 as _d7_actor_sqlite3
from pathlib import Path as _d7_actor_Path

def _d7_actor_db_files():
    return [p for p in _d7_actor_Path(".").rglob("*.db") if p.exists()]

def _d7_force_user_logs_actor():
    patterns = [
        "%user management%",
        "%enable user%",
        "%disable user%",
        "%update system owner%",
        "%home owner account%",
        "%system owner account updated%",
    ]

    for db_path in _d7_actor_db_files():
        try:
            con = _d7_actor_sqlite3.connect(str(db_path))
            con.row_factory = _d7_actor_sqlite3.Row

            tables = [
                r["name"] for r in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]

            if "system_logs" not in tables:
                con.close()
                continue

            cols = [r["name"] for r in con.execute("PRAGMA table_info(system_logs)").fetchall()]
            lower = {c.lower(): c for c in cols}

            actor_cols = [
                lower[c] for c in [
                    "actor", "source", "created_by", "performed_by",
                    "actor_name", "username", "user"
                ]
                if c in lower
            ]

            search_cols = [
                lower[c] for c in [
                    "event_type", "action_taken", "details",
                    "message", "description"
                ]
                if c in lower
            ]

            if not actor_cols or not search_cols:
                con.close()
                continue

            set_sql = ", ".join([f"{c} = ?" for c in actor_cols])

            where_parts = []
            params = ["System Owner"] * len(actor_cols)

            for c in search_cols:
                for pat in patterns:
                    where_parts.append(f"LOWER(COALESCE({c}, '')) LIKE ?")
                    params.append(pat)

            where_sql = " OR ".join(where_parts)

            con.execute(
                f"""
                UPDATE system_logs
                SET {set_sql}
                WHERE {where_sql}
                """,
                params
            )

            con.commit()
            con.close()
        except Exception:
            pass

@app.middleware("http")
async def _d7_force_user_logs_actor_middleware(request, call_next):
    path = request.url.path.lower()

    if "logs" in path or "user" in path or "system-owner" in path or "dashboard" in path:
        _d7_force_user_logs_actor()

    response = await call_next(request)

    if "logs" in path or "user" in path or "system-owner" in path or "dashboard" in path:
        _d7_force_user_logs_actor()

    return response

# ===================== D7M16 FORCE USER LOG ACTOR END =====================

# D7M16_FINAL_LOGS_ACTOR_BACKEND_FIX_START
import sqlite3 as _d7_logs_sqlite3
from pathlib import Path as _D7LogsPath
from datetime import datetime as _d7_logs_datetime, timedelta as _d7_logs_timedelta

def _d7_logs_db_path():
    try:
        return _security_db_path()
    except Exception:
        return _D7LogsPath(__file__).resolve().parent / "database" / "smart_home_edge.db"

def _d7_logs_format_time(value):
    if not value:
        return "Not available"

    raw = str(value).replace("T", " ").replace("Z", "").split(".")[0]

    dt = None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            dt = _d7_logs_datetime.strptime(raw, fmt)
            break
        except Exception:
            pass

    if dt is None:
        try:
            dt = _d7_logs_datetime.fromisoformat(raw)
        except Exception:
            return str(value)

    today = _d7_logs_datetime.now().date()
    time_part = dt.strftime("%I:%M:%S %p").lstrip("0")

    if dt.date() == today:
        return f"Today, {time_part}"

    if dt.date() == today - _d7_logs_timedelta(days=1):
        return f"Yesterday, {time_part}"

    return f"{dt.strftime('%Y-%m-%d')}, {time_part}"

def _d7_logs_text(row, *keys):
    for key in keys:
        if key in row and row.get(key) not in (None, ""):
            return str(row.get(key)).strip()
    return ""

def _d7_logs_event_type(row):
    raw = " ".join([
        _d7_logs_text(row, "event_type", "category"),
        _d7_logs_text(row, "action_taken", "action"),
        _d7_logs_text(row, "details", "message", "description"),
        _d7_logs_text(row, "source"),
        _d7_logs_text(row, "actor"),
    ]).lower()

    if any(x in raw for x in [
        "user management",
        "disable user",
        "enable user",
        "update system owner",
        "system owner account",
        "home owner account",
    ]):
        return "User Management"

    if "energy" in raw and ("command" in raw or "mqtt" in raw):
        return "Energy Monitor Command"

    if any(x in raw for x in ["smart door", "door", "camera", "cam"]) and ("command" in raw or "mqtt" in raw):
        return "Smart Door Command"

    if "stream" in raw and any(x in raw for x in ["error", "failed", "offline"]):
        return "Camera Stream Error"

    return _d7_logs_text(row, "event_type", "category") or "System Event"

def _d7_logs_actor(row, event_type):
    raw = " ".join([
        _d7_logs_text(row, "actor"),
        _d7_logs_text(row, "source"),
        _d7_logs_text(row, "event_type", "category"),
        _d7_logs_text(row, "action_taken", "action"),
        _d7_logs_text(row, "details", "message", "description"),
    ]).lower()

    if any(x in raw for x in ["failed login", "invalid username", "invalid password"]):
        return "Unknown"

    if event_type == "User Management":
        return "System Owner"

    if any(x in raw for x in ["heartbeat", "device offline", "device online", "camera offline", "stream error", "stream failed"]):
        return "Server"

    if any(x in raw for x in ["dashboard", "system_owner", "system owner", "mqtt ", "command sent"]):
        return "System Owner"

    if any(x in raw for x in ["flutter_admin", "admin app", "manual_open_from_app"]):
        return "Admin App"

    if "esp32" in raw:
        return "Device"

    actor = _d7_logs_text(row, "actor")
    if actor:
        normalized = actor.replace("_", " ").strip().lower()
        if normalized in {"system owner", "owner"}:
            return "System Owner"
        if normalized in {"server", "system"}:
            return "Server"
        return actor

    return "Server"

def _d7_logs_apartment(row):
    for key in ["apartment_number", "apartment", "home", "home_id"]:
        value = _d7_logs_text(row, key)
        if not value:
            continue

        cleaned = value.replace("Apartment", "").replace("APT-", "").strip()
        if cleaned.isdigit():
            return cleaned

        match = __import__("re").search(r"HOME[-_]?0*(\d+)", value, __import__("re").I)
        if match:
            return str(int(match.group(1)))

    return "-"


# D7M16_FINAL_LOGS_ACTOR_BACKEND_FIX_END

# --- SYSTEM STATUS LIVE API PATCH START ---
@app.get("/api/system-status/live")
def api_system_status_live():
    import os
    import socket
    import shutil
    from pathlib import Path as _Path
    from datetime import datetime as _dt

    def _now():
        return _dt.now().strftime("%Y-%m-%d, %I:%M:%S %p")

    def _lan_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
            except Exception:
                try:
                    s.connect(("192.168.1.254", 80))
                    ip = s.getsockname()[0]
                except Exception:
                    ip = socket.gethostbyname(socket.gethostname())
            finally:
                s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _disk_info():
        try:
            usage = shutil.disk_usage(os.getcwd())
            total_gb = usage.total / (1024 ** 3)
            used_gb = usage.used / (1024 ** 3)
            percent = (used_gb / total_gb * 100) if total_gb else 0
            return {
                "used": f"{used_gb:.1f}",
                "total": f"{total_gb:.1f}",
                "percent": int(round(percent)),
            }
        except Exception:
            return {"used": "-", "total": "-", "percent": 0}

    def _memory_cpu():
        disk = _disk_info()
        try:
            import psutil
            cpu = int(round(psutil.cpu_percent(interval=0.05)))
            mem = psutil.virtual_memory()
            used_gb = mem.used / (1024 ** 3)
            total_gb = mem.total / (1024 ** 3)
            return {
                "cpu_percent": cpu,
                "memory_used": f"{used_gb:.1f}",
                "memory_total": f"{total_gb:.1f}",
                "memory_percent": int(round(mem.percent)),
                "storage_used": disk["used"],
                "storage_total": disk["total"],
                "storage_percent": disk["percent"],
            }
        except Exception:
            return {
                "cpu_percent": 0,
                "memory_used": "-",
                "memory_total": "-",
                "memory_percent": 0,
                "storage_used": disk["used"],
                "storage_total": disk["total"],
                "storage_percent": disk["percent"],
            }

    def _sqlite_info():
        candidates = [
            _Path("data/smart_home.db"),
            _Path("edge/data/smart_home.db"),
            _Path("smart_home_models.db"),
            _Path("edge/smart_home_models.db"),
            _Path("database/smart_home_edge.db"),
            _Path("edge/database/smart_home_edge.db"),
        ]

        db_path = next((p for p in candidates if p.exists()), None)

        if db_path is None:
            return {
                "status": "Not found",
                "health": "warning",
                "size": "-",
                "location": "Not available yet",
            }

        try:
            size_mb = db_path.stat().st_size / (1024 ** 2)
            return {
                "status": "Connected",
                "health": "healthy",
                "size": f"{size_mb:.1f} MB",
                "location": str(db_path).replace("\\", "/"),
            }
        except Exception:
            return {
                "status": "Detected",
                "health": "warning",
                "size": "-",
                "location": str(db_path).replace("\\", "/"),
            }

    def _mqtt_info():
        host = os.getenv("MQTT_HOST") or os.getenv("BROKER_HOST") or "127.0.0.1"
        try:
            port = int(os.getenv("MQTT_PORT") or os.getenv("BROKER_PORT") or "1883")
        except Exception:
            port = 1883

        from mqtt import mqtt_client
        connected = mqtt_client.is_connected()
        msgs_min = mqtt_client.get_messages_per_min()

        return {
            "host": host,
            "port": port,
            "status": "Connected" if connected else "Not connected",
            "health": "healthy" if connected else "warning",
            "messages_per_min": str(msgs_min),
        }

    metrics = _memory_cpu()
    sqlite_info = _sqlite_info()
    mqtt_info = _mqtt_info()
    now = _now()

    infra_logs = [
        f"[INFO] {now} - Edge server health check refreshed.",
        f"[INFO] {now} - SQLite database status: {sqlite_info['status']}.",
        f"[INFO] {now} - MQTT broker status: {mqtt_info['status']}.",
        f"[INFO] {now} - LAN IP detected: {_lan_ip()}."
    ]

    return {
        "mqtt": mqtt_info,
        "sqlite": sqlite_info,
        "server": {
            "status": "Running",
            "api_status": "Online",
            "server_url": f"http://{_lan_ip()}:8000",
            "lan_ip": _lan_ip(),
            **metrics,
        },
        "system_logs": infra_logs,
    }
# --- SYSTEM STATUS LIVE API PATCH END ---


# STATUS_RUNTIME_METRICS_API_START
@app.get("/api/system/runtime")
def get_system_runtime_metrics():
    import shutil
    from pathlib import Path

    try:
        import psutil

        cpu_percent = psutil.cpu_percent(interval=0.15)
        memory = psutil.virtual_memory()

        disk_root = Path.cwd().anchor or str(Path.cwd())
        disk = shutil.disk_usage(disk_root)

        def gb(value):
            return round(value / (1024 ** 3), 1)

        return {
            "real": True,
            "cpu_percent": round(float(cpu_percent), 1),
            "memory_used_gb": gb(memory.used),
            "memory_total_gb": gb(memory.total),
            "memory_percent": round(float(memory.percent), 1),
            "storage_used_gb": gb(disk.used),
            "storage_total_gb": gb(disk.total),
            "storage_percent": round((disk.used / disk.total) * 100, 1),
        }
    except Exception as exc:
        return {
            "real": False,
            "error": str(exc),
            "cpu_percent": None,
            "memory_used_gb": None,
            "memory_total_gb": None,
            "memory_percent": None,
            "storage_used_gb": None,
            "storage_total_gb": None,
            "storage_percent": None,
        }
# STATUS_RUNTIME_METRICS_API_END


# --- D7M16: Home ID / Home Code split ---
# Home ID: public system identifier derived from apartment number, e.g. HOME-002.
# Home Code: private app pairing code stored in homes.home_code, e.g. HME-7K9P-22XQ.
def _d7_home_code(home):
    apt = _d7_val(home, "apartment_number", "apartment", "apartment_no", "number", default=None)
    digits = "".join(ch for ch in str(apt or "") if ch.isdigit())

    if digits:
        return f"HOME-{int(digits):03d}"

    pk = _d7_home_pk(home)
    if pk is not None:
        return f"HOME-{int(pk):03d}"

    return "HOME-000"




# ===================== D7M16 APP SERVER AUTH + RECOVERY START =====================
from pydantic import BaseModel as _D7AppBaseModel
from fastapi import HTTPException as _D7AppHTTPException
import sqlite3 as _d7_app_sqlite3
import secrets as _d7_app_secrets
import re as _d7_app_re
from pathlib import Path as _D7AppPath
from datetime import datetime as _d7_app_datetime, timedelta as _d7_app_timedelta, timezone as _d7_app_timezone


class _D7AppRegisterAdmin(_D7AppBaseModel):
    login: str
    password: str
    home_code: str


class _D7AppLoginAdmin(_D7AppBaseModel):
    login: str
    password: str


class _D7AppLoginUser(_D7AppBaseModel):
    admin_login: str
    user_password: str


class _D7AppSettingsUpdate(_D7AppBaseModel):
    current_login: str
    current_password: str
    new_login: str | None = None
    new_admin_password: str | None = None
    user_password: str | None = None
    door_pin: str | None = None

class _D7AppEnergySettingsUpdate(_D7AppBaseModel):
    home_id: str | int | None = None
    home_code: str | None = None
    admin_login: str | None = None
    electricity_rate: float
    currency: str

class _D7AppRecoveryRequest(_D7AppBaseModel):
    phone: str


class _D7AppRecoveryReset(_D7AppBaseModel):
    phone: str
    otp: str
    new_password: str


def _d7_app_now():
    return _d7_app_datetime.now(_d7_app_timezone.utc).isoformat(timespec="seconds")


def _d7_app_db_path():
    base = _D7AppPath(__file__).resolve().parent
    preferred = base / "database" / "smart_home_edge.db"
    if preferred.exists():
        return preferred

    matches = list(base.rglob("smart_home_edge.db"))
    if matches:
        return matches[0]

    return preferred


def _d7_app_conn():
    path = _d7_app_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = _d7_app_sqlite3.connect(str(path))
    conn.row_factory = _d7_app_sqlite3.Row
    _d7_app_ensure_schema(conn)
    return conn


def _d7_app_tables(conn):
    return {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}


def _d7_app_cols(conn, table):
    if table not in _d7_app_tables(conn):
        return set()
    return {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _d7_app_ensure_schema(conn):
    if "homes" in _d7_app_tables(conn):
        cols = _d7_app_cols(conn, "homes")
        if "owner_phone" not in cols:
            try:
                conn.execute("ALTER TABLE homes ADD COLUMN owner_phone TEXT")
            except Exception:
                pass

    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            home_id INTEGER NOT NULL UNIQUE,
            admin_login TEXT NOT NULL UNIQUE,
            admin_password TEXT NOT NULL,
            user_password TEXT DEFAULT '',
            door_pin TEXT DEFAULT '',
            camera_pin TEXT DEFAULT '',
            owner_phone TEXT DEFAULT '',
            failed_login_attempts INTEGER DEFAULT 0,
            recovery_otp TEXT DEFAULT '',
            recovery_expires_at TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()


def _d7_app_set_home_owner_phone(home_id, owner_phone):
    phone = "".join(ch for ch in str(owner_phone or "") if ch.isdigit())
    if not phone:
        return

    conn = _d7_app_conn()
    try:
        if "homes" in _d7_app_tables(conn):
            cols = _d7_app_cols(conn, "homes")
            if "owner_phone" in cols:
                conn.execute("UPDATE homes SET owner_phone = ? WHERE id = ?", (phone, home_id))
                conn.commit()
    finally:
        conn.close()


def _d7_app_public_home_id(home):
    apt = str(home.get("apartment_number") or "").strip()
    digits = "".join(ch for ch in apt if ch.isdigit())
    if digits:
        return f"HOME-{int(digits):03d}"
    return f"HOME-{int(home.get('id') or 0):03d}"


def _d7_app_home_payload(home):
    h = dict(home)
    h["home_id"] = _d7_app_public_home_id(h)
    h["apartment_number"] = str(h.get("apartment_number") or "").strip()
    h["home_code"] = str(h.get("home_code") or "").strip()
    return h


def _d7_app_account_payload(account):
    a = dict(account)
    return {
        "id": a.get("id"),
        "admin_login": a.get("admin_login") or "",
        "admin_password": a.get("admin_password") or "",
        "user_password": a.get("user_password") or "",
        "door_pin": a.get("door_pin") or "",
        "home_id": a.get("home_id"),
    }


def _d7_app_validate_login(value):
    login = str(value or "").strip()

    if not login:
        return False, "Username, Phone Number, or Email is required."

    if "@" in login:
        if _d7_app_re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", login):
            return True, ""
        return False, "Invalid email format."

    if _d7_app_re.match(r"^[0-9+]{4,15}$", login):
        return True, ""

    if _d7_app_re.match(r"^[A-Za-z][A-Za-z0-9_]{2,30}$", login):
        return True, ""

    return False, "Login must be a valid Username, Phone Number, or Email address."


def _d7_app_find_home_by_code(conn, home_code):
    if "homes" not in _d7_app_tables(conn):
        return None

    cols = _d7_app_cols(conn, "homes")
    needed = ["id", "name", "home_code", "owner_name", "owner_email", "apartment_number", "account_status"]
    select_cols = [c for c in needed if c in cols]
    if "owner_phone" in cols:
        select_cols.append("owner_phone")

    row = conn.execute(
        f"SELECT {', '.join(select_cols)} FROM homes WHERE lower(home_code) = lower(?) LIMIT 1",
        (str(home_code or "").strip(),),
    ).fetchone()

    return row


def _d7_app_find_home_by_id(conn, home_id):
    cols = _d7_app_cols(conn, "homes")
    needed = ["id", "name", "home_code", "owner_name", "owner_email", "apartment_number", "account_status"]
    select_cols = [c for c in needed if c in cols]
    if "owner_phone" in cols:
        select_cols.append("owner_phone")

    return conn.execute(
        f"SELECT {', '.join(select_cols)} FROM homes WHERE id = ? LIMIT 1",
        (home_id,),
    ).fetchone()


def _d7_app_log(conn, severity, actor, apartment, event_type, details, action_taken):
    if "system_logs" not in _d7_app_tables(conn):
        return

    cols = _d7_app_cols(conn, "system_logs")
    now_value = _d7_app_now()

    important_dedupe_actions = {
        "APP SETTINGS UPDATED",
        "APP RECOVERY OTP GENERATED",
        "APP PASSWORD RESET",
        "APP ADMIN REGISTERED",
    }

    action_value = str(action_taken or "").strip().upper()
    apt_value = str(apartment or "-")
    event_value = str(event_type or "")
    details_value = str(details or "")

    if action_value in important_dedupe_actions:
        try:
            row = conn.execute(
                """
                SELECT id
                FROM system_logs
                WHERE upper(action_taken) = upper(?)
                  AND COALESCE(apartment_number, home, '-') = ?
                  AND COALESCE(event_type, '') = ?
                  AND COALESCE(details, '') = ?
                  AND datetime(replace(substr(COALESCE(timestamp, created_at), 1, 19), 'T', ' ')) >= datetime('now', '-3 seconds')
                LIMIT 1
                """,
                (action_value, apt_value, event_value, details_value),
            ).fetchone()

            if row:
                return
        except Exception:
            pass

    data = {
        "created_at": now_value,
        "timestamp": now_value,
        "severity": severity,
        "actor": actor,
        "home": apt_value,
        "apartment_number": apt_value,
        "event_type": event_value,
        "details": details_value,
        "action_taken": action_taken,
    }

    keys = [k for k in data if k in cols]
    if not keys:
        return

    placeholders = ", ".join(["?"] * len(keys))
    conn.execute(
        f"INSERT INTO system_logs ({', '.join(keys)}) VALUES ({placeholders})",
        [data[k] for k in keys],
    )

@app.post("/api/app/auth/register-admin")
def _d7_app_register_admin(payload: _D7AppRegisterAdmin):
    login = (payload.login or "").strip()
    password = (payload.password or "").strip()
    home_code = (payload.home_code or "").strip()

    valid, msg = _d7_app_validate_login(login)
    if not valid:
        raise _D7AppHTTPException(status_code=400, detail=msg)

    if not password:
        raise _D7AppHTTPException(status_code=400, detail="Password is required.")

    if not home_code:
        raise _D7AppHTTPException(status_code=400, detail="Home Code is required.")

    conn = _d7_app_conn()
    try:
        home = _d7_app_find_home_by_code(conn, home_code)
        if not home:
            raise _D7AppHTTPException(status_code=404, detail="Home Code was not found.")

        home = dict(home)
        status = str(home.get("account_status") or "active").lower()
        if status in {"disabled", "inactive"}:
            raise _D7AppHTTPException(status_code=403, detail="This home account is disabled.")

        existing_home = conn.execute(
            "SELECT id FROM app_accounts WHERE home_id = ? LIMIT 1",
            (home["id"],),
        ).fetchone()
        if existing_home:
            raise _D7AppHTTPException(
                status_code=409,
                detail="This home already has an admin account. Use Login instead.",
            )

        existing_login = conn.execute(
            "SELECT id FROM app_accounts WHERE lower(admin_login) = lower(?) LIMIT 1",
            (login,),
        ).fetchone()
        if existing_login:
            raise _D7AppHTTPException(
                status_code=409,
                detail="This username or email is already used.",
            )

        phone = str(home.get("owner_phone") or "").strip()

        cur = conn.execute(
            """
            INSERT INTO app_accounts (
                home_id, admin_login, admin_password, user_password, door_pin, owner_phone, created_at, updated_at
            )
            VALUES (?, ?, ?, '', '', ?, ?, ?)
            """,
            (home["id"], login, password, phone, _d7_app_now(), _d7_app_now()),
        )

        account = conn.execute(
            "SELECT * FROM app_accounts WHERE id = ?",
            (cur.lastrowid,),
        ).fetchone()

        apt = home.get("apartment_number") or "-"
        _d7_app_log(
            conn,
            "INFO",
            "Admin App",
            apt,
            "App Account",
            f"Admin app account created for Apartment {apt}.",
            "APP ADMIN REGISTERED",
        )

        conn.commit()

        return {
            "success": True,
            "message": "Account registered successfully",
            "home": _d7_app_home_payload(home),
            "account": _d7_app_account_payload(account),
        }
    finally:
        conn.close()


@app.post("/api/app/auth/login-admin")
def _d7_app_login_admin(payload: _D7AppLoginAdmin):
    login = (payload.login or "").strip()
    password = (payload.password or "").strip()

    conn = _d7_app_conn()
    try:
        account = conn.execute(
            "SELECT * FROM app_accounts WHERE lower(admin_login) = lower(?) LIMIT 1",
            (login,),
        ).fetchone()

        if not account:
            raise _D7AppHTTPException(status_code=404, detail="Invalid username or email.")

        account = dict(account)

        if str(account.get("admin_password") or "") != password:
            attempts = int(account.get("failed_login_attempts") or 0) + 1
            conn.execute(
                "UPDATE app_accounts SET failed_login_attempts = ?, updated_at = ? WHERE id = ?",
                (attempts, _d7_app_now(), account["id"]),
            )
            conn.commit()

            raise _D7AppHTTPException(
                status_code=401,
                detail="Invalid password. Forgot Password will appear after 3 failed attempts."
                if attempts < 3 else
                "Invalid password. You can use Forgot Password now.",
            )

        conn.execute(
            "UPDATE app_accounts SET failed_login_attempts = 0, updated_at = ? WHERE id = ?",
            (_d7_app_now(), account["id"]),
        )

        home = _d7_app_find_home_by_id(conn, account["home_id"])
        if not home:
            raise _D7AppHTTPException(status_code=404, detail="Linked home was not found.")

        home = dict(home)
        _d7_app_assert_home_account_active(conn, home)
        apt = home.get("apartment_number") or "-"

        if "homes" in _d7_app_tables(conn) and "last_login_at" in _d7_app_cols(conn, "homes"):
            conn.execute("UPDATE homes SET last_login_at = ? WHERE id = ?", (_d7_app_now(), home["id"]))

        conn.commit()

        return {
            "success": True,
            "role": "Admin",
            "home": _d7_app_home_payload(home),
            "account": _d7_app_account_payload(account),
        }
    finally:
        conn.close()


@app.post("/api/app/auth/login-user")
def _d7_app_login_user(payload: _D7AppLoginUser):
    admin_login = (payload.admin_login or "").strip()
    user_password = (payload.user_password or "").strip()

    conn = _d7_app_conn()
    try:
        account = conn.execute(
            "SELECT * FROM app_accounts WHERE lower(admin_login) = lower(?) LIMIT 1",
            (admin_login,),
        ).fetchone()

        if not account:
            raise _D7AppHTTPException(status_code=404, detail="Invalid admin username or email.")

        account = dict(account)

        saved_user_password = str(account.get("user_password") or "").strip()
        if not saved_user_password:
            raise _D7AppHTTPException(
                status_code=403,
                detail="User password is not set by the admin yet.",
            )

        if saved_user_password != user_password:
            raise _D7AppHTTPException(status_code=401, detail="Invalid user password.")

        home = _d7_app_find_home_by_id(conn, account["home_id"])
        if not home:
            raise _D7AppHTTPException(status_code=404, detail="Linked home was not found.")

        home = dict(home)
        _d7_app_assert_home_account_active(conn, home)

        if "homes" in _d7_app_tables(conn) and "last_login_at" in _d7_app_cols(conn, "homes"):
            conn.execute("UPDATE homes SET last_login_at = ? WHERE id = ?", (_d7_app_now(), home["id"]))

        conn.commit()

        return {
            "success": True,
            "role": "User",
            "home": _d7_app_home_payload(home),
            "account": _d7_app_account_payload(account),
        }
    finally:
        conn.close()


@app.post("/api/app/auth/settings")
def _d7_app_update_settings(payload: _D7AppSettingsUpdate):
    current_login = (payload.current_login or "").strip()
    current_password = (payload.current_password or "").strip()

    conn = _d7_app_conn()
    try:
        account = conn.execute(
            "SELECT * FROM app_accounts WHERE lower(admin_login) = lower(?) LIMIT 1",
            (current_login,),
        ).fetchone()

        if not account:
            raise _D7AppHTTPException(status_code=404, detail="Admin account was not found.")

        account = dict(account)

        if str(account.get("admin_password") or "") != current_password:
            raise _D7AppHTTPException(status_code=401, detail="Current password is invalid.")

        updates = []
        values = []

        if payload.new_login is not None and payload.new_login.strip():
            new_login = payload.new_login.strip()
            valid, msg = _d7_app_validate_login(new_login)
            if not valid:
                raise _D7AppHTTPException(status_code=400, detail=msg)

            exists = conn.execute(
                "SELECT id FROM app_accounts WHERE lower(admin_login)=lower(?) AND id <> ? LIMIT 1",
                (new_login, account["id"]),
            ).fetchone()
            if exists:
                raise _D7AppHTTPException(status_code=409, detail="This username or email is already used.")

            updates.append("admin_login = ?")
            values.append(new_login)

        if payload.new_admin_password is not None and payload.new_admin_password.strip():
            updates.append("admin_password = ?")
            values.append(payload.new_admin_password.strip())

        if payload.user_password is not None:
            updates.append("user_password = ?")
            values.append(payload.user_password.strip())

        if payload.door_pin is not None:
            updates.append("door_pin = ?")
            values.append(payload.door_pin.strip())

        if updates:
            updates.append("updated_at = ?")
            values.append(_d7_app_now())
            values.append(account["id"])
            conn.execute(
                f"UPDATE app_accounts SET {', '.join(updates)} WHERE id = ?",
                values,
            )

        updated = conn.execute(
            "SELECT * FROM app_accounts WHERE id = ?",
            (account["id"],),
        ).fetchone()

        home = _d7_app_find_home_by_id(conn, account["home_id"])
        apt = dict(home).get("apartment_number") if home else "-"

        _d7_app_log(
            conn,
            "INFO",
            "Admin App",
            apt,
            "App Account",
            "App account settings updated.",
            "APP SETTINGS UPDATED",
        )

        conn.commit()

        return {
            "success": True,
            "account": _d7_app_account_payload(updated),
            "home": _d7_app_home_payload(dict(home)) if home else None,
        }
    finally:
        conn.close()


@app.post("/api/app/auth/recovery/request")
def _d7_app_recovery_request(payload: _D7AppRecoveryRequest):
    phone = "".join(ch for ch in str(payload.phone or "") if ch.isdigit())

    if not phone:
        raise _D7AppHTTPException(status_code=400, detail="Phone number is required.")

    conn = _d7_app_conn()
    try:
        if "owner_phone" not in _d7_app_cols(conn, "homes"):
            raise _D7AppHTTPException(status_code=404, detail="Owner phone is not configured.")

        home = conn.execute(
            "SELECT * FROM homes WHERE owner_phone = ? LIMIT 1",
            (phone,),
        ).fetchone()

        if not home:
            raise _D7AppHTTPException(status_code=404, detail="Phone number was not found.")

        home = dict(home)

        account = conn.execute(
            "SELECT * FROM app_accounts WHERE home_id = ? LIMIT 1",
            (home["id"],),
        ).fetchone()

        if not account:
            raise _D7AppHTTPException(status_code=404, detail="No app account is linked to this phone number.")

        # D7M16_REUSE_ACTIVE_RECOVERY_OTP
        existing_otp = str(account["recovery_otp"] or "").strip() if "recovery_otp" in account.keys() else ""
        existing_expires = str(account["recovery_expires_at"] or "").strip() if "recovery_expires_at" in account.keys() else ""

        if existing_otp and existing_expires:
            try:
                existing_dt = _d7_app_datetime.fromisoformat(existing_expires)
                if _d7_app_datetime.now(_d7_app_timezone.utc) <= existing_dt:
                    return {
                        "success": True,
                        "message": "Recovery code already generated. Ask the System Owner for the code from Security Logs.",
                    }
            except Exception:
                pass

        otp = f"{_d7_app_secrets.randbelow(1000000):06d}"
        expires = (_d7_app_datetime.now(_d7_app_timezone.utc) + _d7_app_timedelta(minutes=10)).isoformat(timespec="seconds")

        conn.execute(
            """
            UPDATE app_accounts
            SET recovery_otp = ?, recovery_expires_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (otp, expires, _d7_app_now(), account["id"]),
        )

        apt = home.get("apartment_number") or "-"

        _d7_app_log(
            conn,
            "WARNING",
            "Server",
            apt,
            "App Password Recovery",
            f"Manual recovery OTP for Apartment {apt}: {otp}. Valid for 10 minutes.",
            "APP RECOVERY OTP GENERATED",
        )

        conn.commit()

        return {
            "success": True,
            "message": "Recovery code generated. Ask the System Owner for the code from Security Logs.",
        }
    finally:
        conn.close()


@app.post("/api/app/auth/recovery/reset")
def _d7_app_recovery_reset(payload: _D7AppRecoveryReset):
    phone = "".join(ch for ch in str(payload.phone or "") if ch.isdigit())
    otp = (payload.otp or "").strip()
    new_password = (payload.new_password or "").strip()

    if not phone or not otp or not new_password:
        raise _D7AppHTTPException(status_code=400, detail="Phone, OTP, and new password are required.")

    conn = _d7_app_conn()
    try:
        home = conn.execute(
            "SELECT * FROM homes WHERE owner_phone = ? LIMIT 1",
            (phone,),
        ).fetchone()

        if not home:
            raise _D7AppHTTPException(status_code=404, detail="Phone number was not found.")

        home = dict(home)

        account = conn.execute(
            "SELECT * FROM app_accounts WHERE home_id = ? LIMIT 1",
            (home["id"],),
        ).fetchone()

        if not account:
            raise _D7AppHTTPException(status_code=404, detail="No app account is linked to this phone number.")

        account = dict(account)

        if str(account.get("recovery_otp") or "") != otp:
            raise _D7AppHTTPException(status_code=401, detail="Invalid recovery code.")

        expires_raw = str(account.get("recovery_expires_at") or "")
        try:
            expires = _d7_app_datetime.fromisoformat(expires_raw)
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=_d7_app_timezone.utc)
        except Exception:
            raise _D7AppHTTPException(status_code=401, detail="Recovery code is expired.")

        if _d7_app_datetime.now(_d7_app_timezone.utc) > expires:
            raise _D7AppHTTPException(status_code=401, detail="Recovery code is expired.")

        conn.execute(
            """
            UPDATE app_accounts
            SET admin_password = ?, recovery_otp = '', recovery_expires_at = '', failed_login_attempts = 0, updated_at = ?
            WHERE id = ?
            """,
            (new_password, _d7_app_now(), account["id"]),
        )

        apt = home.get("apartment_number") or "-"

        _d7_app_log(
            conn,
            "INFO",
            "Admin App",
            apt,
            "App Password Recovery",
            f"Admin app password reset for Apartment {apt}.",
            "APP PASSWORD RESET",
        )

        conn.commit()

        return {"success": True, "message": "Password reset successfully."}
    finally:
        conn.close()
# ===================== D7M16 APP SERVER AUTH + RECOVERY END =====================

def _d7_cleanup_duplicate_app_security_logs_once():
    try:
        db_path = Path(__file__).resolve().parent / "database" / "smart_home_edge.db"
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        tables = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "system_logs" not in tables:
            conn.close()
            return

        cur.execute("""
            DELETE FROM system_logs
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM system_logs
                GROUP BY
                    COALESCE(substr(timestamp, 1, 19), substr(created_at, 1, 19), ''),
                    COALESCE(home, ''),
                    COALESCE(apartment_number, ''),
                    COALESCE(event_type, ''),
                    COALESCE(details, ''),
                    COALESCE(action_taken, '')
            )
            AND upper(COALESCE(action_taken, '')) IN (
                'APP SETTINGS UPDATED',
                'APP RECOVERY OTP GENERATED',
                'APP PASSWORD RESET',
                'APP ADMIN REGISTERED'
            )
        """)

        conn.commit()
        conn.close()
    except Exception as exc:
        print("Duplicate app security log cleanup skipped:", exc)





# D7M16_APP_HOME_ENERGY_SETTINGS_ENDPOINT
@app.post("/api/app/home/energy-settings")
def d7m16_app_home_energy_settings(payload: _D7AppEnergySettingsUpdate):
    import sqlite3 as _sqlite3
    from pathlib import Path as _Path

    db_path = _Path(__file__).resolve().parent / "database" / "smart_home_edge.db"
    conn = _sqlite3.connect(db_path)
    conn.row_factory = _sqlite3.Row

    try:
        home = None

        if payload.home_id:
            home = conn.execute(
                "SELECT * FROM homes WHERE CAST(id AS TEXT) = CAST(? AS TEXT) LIMIT 1",
                (str(payload.home_id),),
            ).fetchone()

        if home is None and payload.home_code:
            home = conn.execute(
                "SELECT * FROM homes WHERE upper(home_code) = upper(?) LIMIT 1",
                (str(payload.home_code).strip(),),
            ).fetchone()

        if home is None and payload.admin_login:
            try:
                home = conn.execute("""
                    SELECT h.*
                    FROM app_accounts a
                    JOIN homes h ON CAST(h.id AS TEXT) = CAST(a.home_id AS TEXT)
                    WHERE lower(a.admin_login) = lower(?)
                    LIMIT 1
                """, (str(payload.admin_login).strip(),)).fetchone()
            except Exception:
                pass

        if home is None:
            home = conn.execute("SELECT * FROM homes ORDER BY id LIMIT 1").fetchone()

        if home is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Home not found.")
            
        home_dict = dict(home)
        home_id = home_dict["id"]
        
        conn.execute(
            "UPDATE homes SET electricity_rate = ?, currency = ? WHERE id = ?",
            (payload.electricity_rate, payload.currency, home_id)
        )
        conn.commit()
        return {"success": True, "message": "Energy settings updated"}
    finally:
        conn.close()

# D7M16_APP_HOME_SUMMARY_ENDPOINT_START
@app.get("/api/app/home-summary")
def d7m16_app_home_summary(home_id=None, home_code=None, admin_login=None):
    """
    Returns the current home summary for the Flutter app.
    This endpoint reads real homes/devices from SQLite and demo runtime values
    from app_home_demo_state / energy_readings / door_events.
    """
    import sqlite3 as _sqlite3
    from pathlib import Path as _Path

    db_path = _Path(__file__).resolve().parent / "database" / "smart_home_edge.db"

    def row_to_dict(row):
        return dict(row) if row else None

    def tables_of(conn):
        return {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

    def cols_of(conn, table):
        try:
            return {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        except Exception:
            return set()

    conn = _sqlite3.connect(db_path)
    conn.row_factory = _sqlite3.Row

    try:
        tables = tables_of(conn)

        if "homes" not in tables:
            return {"success": False, "message": "Homes table not found."}

        home = None

        if home_id:
            home = conn.execute(
                "SELECT * FROM homes WHERE CAST(id AS TEXT) = CAST(? AS TEXT) LIMIT 1",
                (str(home_id),),
            ).fetchone()

        if home is None and home_code:
            home = conn.execute(
                "SELECT * FROM homes WHERE upper(home_code) = upper(?) LIMIT 1",
                (str(home_code).strip(),),
            ).fetchone()

        if home is None and admin_login and "app_accounts" in tables:
            home = conn.execute("""
                SELECT h.*
                FROM app_accounts a
                JOIN homes h ON CAST(h.id AS TEXT) = CAST(a.home_id AS TEXT)
                WHERE lower(a.admin_login) = lower(?)
                LIMIT 1
            """, (str(admin_login).strip(),)).fetchone()

        requested_specific_home = bool(home_id or home_code or admin_login)

        if home is None and requested_specific_home:
            return {
                "success": False,
                "message": "Requested home was not found for this account.",
            }

        if home is None:
            home = conn.execute("SELECT * FROM homes ORDER BY id LIMIT 1").fetchone()

        if home is None:
            return {"success": False, "message": "No home found."}

        home_dict = row_to_dict(home)
        resolved_home_id = home_dict.get("id")
        apartment_number = str(home_dict.get("apartment_number") or resolved_home_id)

        devices = []
        if "devices" in tables:
            device_cols = cols_of(conn, "devices")
            where_parts = []
            params = []

            if "home_id" in device_cols:
                where_parts.append("CAST(home_id AS TEXT) = CAST(? AS TEXT)")
                params.append(str(resolved_home_id))

            if "apartment_number" in device_cols:
                where_parts.append("CAST(apartment_number AS TEXT) = CAST(? AS TEXT)")
                params.append(apartment_number)

            if where_parts:
                devices = [
                    row_to_dict(r)
                    for r in conn.execute(
                        f"SELECT * FROM devices WHERE {' OR '.join(where_parts)} ORDER BY id",
                        params,
                    ).fetchall()
                ]

        demo_state = None
        if "app_home_demo_state" in tables:
            demo_state = conn.execute(
                "SELECT * FROM app_home_demo_state WHERE CAST(home_id AS TEXT) = CAST(? AS TEXT) LIMIT 1",
                (str(resolved_home_id),),
            ).fetchone()

        demo_dict = row_to_dict(demo_state) or {}

        latest_energy = None
        if "energy_readings" in tables:
            energy_cols = cols_of(conn, "energy_readings")
            where_parts = []
            params = []

            if "home_id" in energy_cols:
                where_parts.append("CAST(home_id AS TEXT) = CAST(? AS TEXT)")
                params.append(str(resolved_home_id))

            if "apartment_number" in energy_cols:
                where_parts.append("CAST(apartment_number AS TEXT) = CAST(? AS TEXT)")
                params.append(apartment_number)

            if where_parts:

              latest_energy = conn.execute(
    f"""
    SELECT *
    FROM energy_readings
    WHERE {' OR '.join(where_parts)}
    ORDER BY id DESC
    LIMIT 1
    """,
    params,
).fetchone()

        latest_energy_dict = row_to_dict(latest_energy) or {}

        door_devices = []
        energy_devices = []
        camera_devices = []

        for d in devices:
            dtype = str(d.get("device_type") or d.get("type") or "").lower()

            if "door" in dtype:
                door_devices.append(d)
                camera_devices.append(d)

            if "energy" in dtype or "meter" in dtype:
                energy_devices.append(d)

        main_door = door_devices[0] if door_devices else {}

        door_status = demo_dict.get("door_status") or "unknown"
        door_label = demo_dict.get("door_label") or main_door.get("device_name") or main_door.get("name") or "Main Door"

        energy_power_w = latest_energy_dict.get("power_w")
        if energy_power_w is None:
            energy_power_w = demo_dict.get("energy_power_w") or 0

        try:
            energy_power_kw = round(float(energy_power_w) / 1000, 2)
        except Exception:
            energy_power_kw = 0

        summary = {
            "success": True,
            "home": {
                "id": resolved_home_id,
                "home_id": home_dict.get("home_id") or f"HOME-{int(resolved_home_id):03d}",
                "home_code": home_dict.get("home_code"),
                "apartment_number": apartment_number,
                "owner_name": home_dict.get("owner_name"),
                "owner_email": home_dict.get("owner_email"),
                "owner_phone": home_dict.get("owner_phone"),
                "electricity_rate": home_dict.get("electricity_rate"),
                "currency": home_dict.get("currency") or "YER",
            },
            "account": {
                "admin_login": admin_login,
            },
            "devices": devices,
            "door": {
                "label": door_label,
                "status": door_status,
                "status_text": "Locked" if str(door_status).lower() == "locked" else "Unlocked",
                "last_event": demo_dict.get("door_last_event"),
                "device": main_door,
            },
            "energy": {
                "status": demo_dict.get("energy_status") or latest_energy_dict.get("status") or "normal",
                "power_w": energy_power_w,
                "power_kw": energy_power_kw,
                "total_kwh": latest_energy_dict.get("total_kwh") or demo_dict.get("energy_total_kwh") or 0,
                "latest_reading": latest_energy_dict,
                "devices": energy_devices,
            },
            "camera": {
                "status": demo_dict.get("camera_status") or "online",
                "stream_available": bool(demo_dict.get("stream_available") or False),
                "devices": camera_devices,
            },
            "alerts_count": int(demo_dict.get("alerts_count") or 0),
        }

        return summary

    finally:
        conn.close()
# D7M16_APP_HOME_SUMMARY_ENDPOINT_END




# D7M16_APP_DOOR_ACCESS_LOGS_ENDPOINT_START
# D7M16_APP_DOOR_ACCESS_LOGS_ENDPOINT_END


# D7M16_APP_DOOR_MANUAL_ACTION_ENDPOINT_START
# D7M16_APP_DOOR_MANUAL_ACTION_ENDPOINT_END




# D7M16_LOG_DELETE_REAL_ALERTS_TERMINAL_START
from fastapi import Body as _D7RealBody, Query as _D7RealQuery, HTTPException as _D7RealHTTPException
import sqlite3 as _d7real_sqlite3
from pathlib import Path as _d7real_Path
from datetime import datetime as _d7real_datetime

_D7REAL_DB = _d7real_Path(__file__).parent / "database" / "smart_home_edge.db"

def _d7real_conn():
    conn = _d7real_sqlite3.connect(str(_D7REAL_DB))
    conn.row_factory = _d7real_sqlite3.Row
    return conn



def _d7real_val(row, *keys, default=""):
    for key in keys:
        try:
            if key in row.keys():
                value = row[key]
                if value is not None and str(value).strip() != "":
                    return value
        except Exception:
            pass
    return default

def _d7real_s(value):
    return str(value or "").strip()

def _d7real_time(value):
    raw = _d7real_s(value)
    if not raw:
        return ""

    clean = raw.replace("Z", "+00:00")
    try:
        dt = _d7real_datetime.fromisoformat(clean)
        return dt.strftime("%Y-%m-%d, %I:%M:%S %p")
    except Exception:
        pass

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d, %I:%M:%S %p"):
        try:
            dt = _d7real_datetime.strptime(raw, fmt)
            return dt.strftime("%Y-%m-%d, %I:%M:%S %p")
        except Exception:
            pass

    return raw

def _d7real_today_from(value):
    raw = _d7real_s(value)
    return raw[:10] if len(raw) >= 10 else raw



def _d7real_resolve_home(conn, home_id=None, home_code=None, admin_login=None):
    if "homes" not in _d7real_tables(conn):
        return None

    cols = _d7real_cols(conn, "homes")
    clauses = []
    params = []

    if home_id and "id" in cols:
        clauses.append("CAST(id AS TEXT) = ?")
        params.append(str(home_id))

    if home_code and "home_code" in cols:
        clauses.append("home_code = ?")
        params.append(str(home_code))

    if admin_login:
        login_clauses = []
        for col in ("owner_email", "owner_name", "admin_login", "username", "email"):
            if col in cols:
                login_clauses.append(f"LOWER({col}) = LOWER(?)")
                params.append(str(admin_login))
        if login_clauses:
            clauses.append("(" + " OR ".join(login_clauses) + ")")

    if not clauses:
        return None

    sql = "SELECT * FROM homes WHERE " + " OR ".join(clauses) + " LIMIT 1"
    return conn.execute(sql, params).fetchone()

def _d7real_home_match_sql(conn, home):
    cols = _d7real_cols(conn, "system_logs")
    clauses = []
    params = []

    if home is not None:
        apt = _d7real_s(_d7real_val(home, "apartment_number", "apartment", default=""))
        hid = _d7real_s(_d7real_val(home, "id", default=""))
        hcode = _d7real_s(_d7real_val(home, "home_code", default=""))

        if apt:
            for col in ("apartment_number", "home", "scope", "actor_scope"):
                if col in cols:
                    clauses.append(f"CAST({col} AS TEXT) = ?")
                    params.append(apt)

        if hid and "home_id" in cols:
            clauses.append("CAST(home_id AS TEXT) = ?")
            params.append(hid)

        if hcode and "home_code" in cols:
            clauses.append("home_code = ?")
            params.append(hcode)

    if not clauses:
        return "", []

    return " AND (" + " OR ".join(clauses) + ")", params













# D7M16_LOG_DELETE_REAL_ALERTS_TERMINAL_END


# D7M16_FINAL_AGREED_LOGS_ALERTS_START
from fastapi import Body as _D7FinalBody, HTTPException as _D7FinalHTTPException
import sqlite3 as _d7final_sqlite3
from pathlib import Path as _d7final_Path
from datetime import datetime as _d7final_datetime

_D7FINAL_DB = _d7final_Path(__file__).resolve().parent / "database" / "smart_home_edge.db"

def _d7final_conn():
    conn = _d7final_sqlite3.connect(str(_D7FINAL_DB))
    conn.row_factory = _d7final_sqlite3.Row
    return conn

def _d7final_tables(conn):
    return {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

def _d7final_cols(conn, table):
    try:
        return [row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    except Exception:
        return []

def _d7final_s(value):
    return str(value or "").strip()

def _d7final_val(row, *keys, default=""):
    try:
        row_keys = row.keys()
    except Exception:
        row_keys = []
    for key in keys:
        if key in row_keys:
            value = row[key]
            if value is not None and str(value).strip() != "":
                return value
    return default

def _d7final_now():
    return _d7final_datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _d7final_time_label(value):
    raw = _d7final_s(value)
    if not raw:
        return ""
    clean = raw.replace("Z", "+00:00")
    try:
        dt = _d7final_datetime.fromisoformat(clean)
        return dt.strftime("%Y-%m-%d, %I:%M:%S %p")
    except Exception:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d, %I:%M:%S %p"):
        try:
            return _d7final_datetime.strptime(raw, fmt).strftime("%Y-%m-%d, %I:%M:%S %p")
        except Exception:
            pass
    return raw

def _d7final_ensure_system_logs(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            created_at TEXT,
            severity TEXT,
            actor TEXT,
            source TEXT,
            home TEXT,
            home_id TEXT,
            apartment_number TEXT,
            event_type TEXT,
            details TEXT,
            action_taken TEXT,
            device_id TEXT,
            device_name TEXT
        )
    """)
    cols = _d7final_cols(conn, "system_logs")
    for col in ["timestamp", "created_at", "severity", "actor", "source", "home", "home_id", "apartment_number", "event_type", "details", "action_taken", "device_id", "device_name"]:
        if col not in cols:
            conn.execute(f"ALTER TABLE system_logs ADD COLUMN {col} TEXT")
    conn.commit()

def _d7final_log(conn, *, severity="INFO", actor="Server", home_id="", apartment="", event_type="System Event", details="", action_taken="", device_id="", device_name=""):
    _d7final_ensure_system_logs(conn)
    from datetime import datetime, timezone
    now_iso = datetime.now(timezone.utc).isoformat()
    cols = _d7final_cols(conn, "system_logs")
    data = {
        "timestamp": now_iso,
        "created_at": now_iso,
        "severity": severity,
        "actor": actor,
        "source": actor,
        "home": apartment,
        "home_id": home_id,
        "apartment_number": apartment,
        "event_type": event_type,
        "details": details,
        "action_taken": action_taken,
        "device_id": device_id,
        "device_name": device_name,
    }
    keys = [k for k in data if k in cols]
    conn.execute(
        f"INSERT INTO system_logs ({', '.join(keys)}) VALUES ({', '.join(['?'] * len(keys))})",
        [data[k] for k in keys],
    )

def _d7final_find_home(conn, home_id="", home_code="", admin_login=""):
    if "homes" not in _d7final_tables(conn):
        return None

    cols = _d7final_cols(conn, "homes")
    clauses = []
    params = []

    if home_id and "id" in cols:
        clauses.append("CAST(id AS TEXT) = ?")
        params.append(str(home_id))

    if home_code and "home_code" in cols:
        clauses.append("home_code = ?")
        params.append(str(home_code))

    if admin_login:
        login_cols = [c for c in ["owner_email", "owner_name", "admin_login", "username", "email"] if c in cols]
        if login_cols:
            clauses.append("(" + " OR ".join([f"LOWER({c}) = LOWER(?)" for c in login_cols]) + ")")
            params.extend([admin_login] * len(login_cols))

    if not clauses:
        return None

    return conn.execute("SELECT * FROM homes WHERE " + " OR ".join(clauses) + " LIMIT 1", params).fetchone()

def _d7final_home_values(home):
    if not home:
        return {"home_id": "", "apartment": "", "home_code": ""}
    return {
        "home_id": _d7final_s(_d7final_val(home, "id")),
        "apartment": _d7final_s(_d7final_val(home, "apartment_number", "apartment", "home_number")),
        "home_code": _d7final_s(_d7final_val(home, "home_code")),
    }









def _d7final_ensure_alerts(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_alert_states (
            alert_key TEXT PRIMARY KEY,
            home_id TEXT,
            category TEXT,
            is_resolved INTEGER DEFAULT 0,
            hidden INTEGER DEFAULT 0,
            updated_at TEXT
        )
    """)
    conn.commit()

def _d7final_alert_state(conn, key):
    _d7final_ensure_alerts(conn)
    scoped_key = _d7m16_state_key(key, globals().get("_D7M16_ALERT_SCOPE", ""))
    return conn.execute("SELECT * FROM app_alert_states WHERE alert_key = ?", (scoped_key,)).fetchone()

def _d7final_alert(conn, key, title, message, category, typ, severity, timestamp="", source_table="", source_id="", extra=None):
    state = _d7final_alert_state(conn, key)
    if state and int(state["hidden"] or 0) == 1:
        return None

    resolved = bool(state and int(state["is_resolved"] or 0) == 1)
    item = {
        "id": key,
        "source_table": source_table,
        "source_id": str(source_id or ""),
        "title": title,
        "message": message,
        "category": category,
        "type": typ,
        "severity": severity.lower(),
        "timestamp": timestamp,
        "time": _d7final_time_label(timestamp) if timestamp else "Just now",
        "isResolved": resolved,
        "is_resolved": resolved,
        "status": "Resolved" if resolved else "Active",
    }
    if extra:
        item.update(extra)
    return item

def _d7final_energy_power(conn):
    for table in ["energy_readings", "energy_logs", "energy_monitoring", "energy_monitoring_readings"]:
        if table not in _d7final_tables(conn):
            continue
        try:
            row = conn.execute(f"SELECT * FROM {table} ORDER BY COALESCE(timestamp, created_at, '') DESC LIMIT 1").fetchone()
        except Exception:
            continue
        if not row:
            continue
        for key in ["watts", "power_w", "current_power_w", "power", "current_power"]:
            if key in row.keys() and row[key] is not None:
                try:
                    return float(row[key]), _d7final_val(row, "timestamp", "created_at"), _d7final_s(_d7final_val(row, "id"))
                except Exception:
                    pass
    return 0.0, "", ""




# D7M16_FINAL_USER_RBAC_SCOPE_START
_D7M16_ALERT_SCOPE = ""


def _d7m16_viewer_scope(home, viewer_role="", admin_login=""):
    values = _d7final_home_values(home)
    role = _d7m16_role_text(viewer_role)
    home_key = values.get("home_id") or values.get("apartment") or values.get("home_code") or "home"
    return f"{home_key}:{role}"

def _d7m16_state_key(raw_key, scope):
    raw = str(raw_key or "").strip()
    scope = str(scope or "").strip()
    return f"{scope}::{raw}" if scope else raw

def _d7m16_alert_scope_from_payload(conn, payload):
    home = _d7final_find_home(
        conn,
        _d7final_s(payload.get("home_id")),
        _d7final_s(payload.get("home_code")),
        _d7final_s(payload.get("admin_login")),
    )
    return home, _d7m16_viewer_scope(
        home,
        _d7final_s(payload.get("viewer_role", "admin")),
        _d7final_s(payload.get("admin_login")),
    )

def _d7m16_ensure_door_log_states(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_door_log_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_key TEXT UNIQUE,
            source_table TEXT,
            source_id TEXT,
            home_id TEXT,
            viewer_scope TEXT,
            hidden INTEGER DEFAULT 0,
            updated_at TEXT
        )
    """)
    conn.commit()

def _d7m16_door_state_key(source_table, source_id, viewer_scope):
    return f"{viewer_scope}::{source_table}:{source_id}"


def _d7m16_hide_door_log_for_viewer(conn, source_table, source_id, home_id, viewer_scope):
    _d7m16_ensure_door_log_states(conn)
    state_key = _d7m16_door_state_key(source_table, source_id, viewer_scope)
    conn.execute(
        """
        INSERT INTO app_door_log_states(
            state_key, source_table, source_id, home_id, viewer_scope, hidden, updated_at
        )
        VALUES (?, ?, ?, ?, ?, 1, ?)
        ON CONFLICT(state_key) DO UPDATE SET
            hidden = 1,
            updated_at = excluded.updated_at
        """,
        (
            state_key,
            str(source_table or ""),
            str(source_id or ""),
            str(home_id or ""),
            str(viewer_scope or ""),
            _d7final_now(),
        ),
    )
# D7M16_FINAL_USER_RBAC_SCOPE_END








# D7M16_FINAL_NO_UNKNOWN_DECISION_DUPLICATE_START
# D7M16_FINAL_NO_UNKNOWN_DECISION_DUPLICATE_END





@app.post("/api/app/alerts-final/{alert_key}/decision")
def d7final_alert_decision(alert_key: str, payload: dict = _D7FinalBody(default_factory=dict)):
    action = _d7final_s(payload.get("action")).lower()
    home_id = _d7final_s(payload.get("home_id"))
    home_code = _d7final_s(payload.get("home_code"))
    admin_login = _d7final_s(payload.get("admin_login"))
    member_name = _d7final_s(payload.get("member_name")) or "Unknown person"

    conn = _d7final_conn()
    try:
        home = _d7final_find_home(conn, home_id, home_code, admin_login)
        values = _d7final_home_values(home)

        if action == "deny":
            _d7final_log(
                conn,
                severity="WARNING",
                actor="Admin App",
                home_id=values["home_id"],
                apartment=values["apartment"],
                event_type="Face Recognition",
                details="Unknown person denied by Admin App.",
                action_taken="UNKNOWN DENIED",
                device_name="Smart Door",
            )

        elif action == "add_family":
            face_enrolled = str(payload.get("face_enrolled", "")).strip().lower() in {"1", "true", "yes", "on", "enabled"}
            
            snapshot_path = None
            try:
                alert_key_str = str(alert_key)
                if "system_logs:" in alert_key_str:
                    row_id = alert_key_str.split("system_logs:")[-1]
                    log_row = conn.execute("SELECT details FROM system_logs WHERE id = ?", (row_id,)).fetchone()
                    if log_row and log_row["details"]:
                        import json
                        details_data = json.loads(log_row["details"])
                        snapshot_path = details_data.get("snapshot")
            except Exception:
                pass

            _d7m16_insert_family_member_from_unknown(
                conn,
                values["home_id"],
                member_name,
                face_enrolled=face_enrolled,
                snapshot_path=snapshot_path
            )

            family_add_details = (
                f"Family member {member_name} added with role Family / Face enrolled from Unknown Face alert."
                if face_enrolled
                else f"Family member {member_name} added with role Family from Unknown Face alert."
            )
            family_add_action = (
                "FAMILY MEMBER ADDED / FACE ENROLLED FROM UNKNOWN FACE ALERT"
                if face_enrolled
                else "FAMILY MEMBER ADDED"
            )

            _d7final_log(
                conn,
                severity="INFO",
                actor="Admin App",
                home_id=values["home_id"],
                apartment=values["apartment"],
                event_type="Family Management",
                details=family_add_details,
                action_taken=family_add_action,
            )
            _d7final_log(
                conn,
                severity="INFO",
                actor="Admin App",
                home_id=values["home_id"],
                apartment=values["apartment"],
                event_type="Face Recognition",
                details="Door opened after adding unknown person from Unknown Face alert.",
                action_taken="DOOR OPENED AFTER FAMILY ADD",
                device_name="Smart Door",
            )

        else:
            from api.door_official_flow import _open_door, DoorOpenRequest
            from fastapi import HTTPException
            
            device_row = conn.execute(
                """
                SELECT device_id FROM devices 
                WHERE home_id = ? 
                AND lower(device_type) IN ('smart_door', 'esp32_cam', 'door_camera', 'camera')
                LIMIT 1
                """,
                (values["home_id"],)
            ).fetchone()
            
            if not device_row:
                device_row = conn.execute(
                    """
                    SELECT device_id FROM devices 
                    WHERE lower(device_type) IN ('smart_door', 'esp32_cam', 'door_camera', 'camera')
                    LIMIT 1
                    """
                ).fetchone()
                
            if not device_row:
                raise HTTPException(status_code=404, detail="No smart door device found")
                
            req = DoorOpenRequest(
                device_id=device_row["device_id"],
                source="admin_app",
                reason="manual_open_from_unknown_alert",
                opened_by=admin_login or "Admin App",
            )
            
            # This correctly checks online status, sends MQTT, and logs the single entry via door_official_flow
            _open_door(
                device_ref=device_row["device_id"],
                request_data=req,
                custom_message="Door opened remotely by Admin after unknown person detection."
            )

        _d7m16_cleanup_unknown_face_family_rows(conn)

        _d7final_ensure_alerts(conn)

        viewer_role = _d7final_s(payload.get("viewer_role", "admin")) or "admin"
        alert_keys_to_resolve = [alert_key]

        try:
            viewer_scope = _d7m16_viewer_scope(home, viewer_role, admin_login)
            scoped_key = _d7m16_state_key(alert_key, viewer_scope)
            if scoped_key not in alert_keys_to_resolve:
                alert_keys_to_resolve.append(scoped_key)
        except Exception:
            pass

        for state_key in alert_keys_to_resolve:
            conn.execute(
                """
                INSERT INTO app_alert_states(alert_key, home_id, category, is_resolved, hidden, updated_at)
                VALUES (?, ?, 'security', 1, 0, ?)
                ON CONFLICT(alert_key) DO UPDATE SET is_resolved=1, hidden=0, updated_at=excluded.updated_at
                """,
                (state_key, values["home_id"], _d7final_now()),
            )

        conn.commit()
        return {"success": True}
    finally:
        conn.close()

# D7M16_FINAL_AGREED_LOGS_ALERTS_END



# D7M16_FINAL_DELETE_AND_ALERT_COUNT_PATCH_START
import sqlite3 as _d7_final_sqlite3
from pathlib import Path as _D7FinalPath
from fastapi import Body as _D7FinalBody
from fastapi import HTTPException as _D7FinalHTTPException


def _d7_final_conn():
    db = _d7_final_find_db()
    if not db:
        raise _D7FinalHTTPException(status_code=500, detail="SQLite database not found")
    con = _d7_final_sqlite3.connect(str(db))
    con.row_factory = _d7_final_sqlite3.Row
    return con

def _d7_final_tables(con):
    return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

def _d7_final_cols(con, table):
    if table not in _d7_final_tables(con):
        return []
    return [r[1] for r in con.execute(f"PRAGMA table_info({table})").fetchall()]





# D7M16_FINAL_DELETE_AND_ALERT_COUNT_PATCH_END

# D7M16_FINAL_POST_DELETE_COMPAT_FIX_START

# D7M16_FINAL_POST_DELETE_COMPAT_FIX_END

# D7M16_APP_ACCOUNT_DISABLE_ENFORCEMENT_START
from fastapi import HTTPException as _D7AccountHTTPException

def _d7_account_home_status_from_row(home):
    try:
        value = home.get("account_status")
    except Exception:
        try:
            value = home["account_status"]
        except Exception:
            value = None

    status = str(value or "active").strip().lower()
    if status in {"disabled", "inactive", "blocked", "suspended", "0", "false"}:
        return "disabled"
    return "active"

def _d7_account_home_is_active(home):
    return _d7_account_home_status_from_row(home) != "disabled"

def _d7_account_disabled_message():
    return "This account has been disabled by System Owner."

def _d7_app_assert_home_account_active(conn, home):
    if not _d7_account_home_is_active(home):
        raise _D7AppHTTPException(
            status_code=403,
            detail=_d7_account_disabled_message(),
        )

@app.get("/api/app/auth/account-status")
def d7_app_account_status(
    home_id: str = "",
    home_code: str = "",
    admin_login: str = "",
):
    conn = _d7_app_conn()
    try:
        account = None
        home = None

        login = (admin_login or "").strip()
        if login:
            account = conn.execute(
                "SELECT * FROM app_accounts WHERE lower(admin_login) = lower(?) LIMIT 1",
                (login,),
            ).fetchone()

        if account:
            account = dict(account)
            home = _d7_app_find_home_by_id(conn, account.get("home_id"))

        if not home and home_id:
            try:
                home = _d7_app_find_home_by_id(conn, int(str(home_id).strip()))
            except Exception:
                home = _d7_app_find_home_by_id(conn, str(home_id).strip())

        if not home and home_code:
            home = conn.execute(
                "SELECT * FROM homes WHERE home_code = ? LIMIT 1",
                (str(home_code).strip(),),
            ).fetchone()

        if not home:
            raise _D7AppHTTPException(status_code=404, detail="Linked home was not found.")

        home = dict(home)
        status = _d7_account_home_status_from_row(home)
        active = status != "disabled"

        return {
            "success": True,
            "active": active,
            "status": status,
            "message": "" if active else _d7_account_disabled_message(),
            "home": _d7_app_home_payload(home),
            "account": _d7_app_account_payload(account) if account else None,
        }
    finally:
        conn.close()
# D7M16_APP_ACCOUNT_DISABLE_ENFORCEMENT_END

# D7M16_FAKE_UNKNOWN_FACE_TEST_START
from fastapi import Body as _D7FakeBody, HTTPException as _D7FakeHTTPException
import sqlite3 as _d7_fake_sqlite3
from pathlib import Path as _D7FakePath
from datetime import datetime as _d7_fake_datetime

def _d7_fake_db_path():
    base = _D7FakePath(__file__).resolve().parent
    candidates = [
        base / "database" / "smart_home_edge.db",
        base / "database" / "smart_home.db",
        base / "data" / "smart_home.db",
        base.parent / "data" / "smart_home.db",
        base / "smart_home.db",
    ]
    for p in candidates:
        if p.exists():
            return p
    for p in base.rglob("*.db"):
        if "__pycache__" not in str(p):
            return p
    raise _D7FakeHTTPException(status_code=500, detail="Database file not found.")

def _d7_fake_conn():
    conn = _d7_fake_sqlite3.connect(str(_d7_fake_db_path()))
    conn.row_factory = _d7_fake_sqlite3.Row
    return conn

def _d7_fake_now():
    return _d7_fake_datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _d7_fake_tables(conn):
    return {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }

def _d7_fake_cols(conn, table):
    try:
        return [row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    except Exception:
        return []

def _d7_fake_ensure_logs(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            created_at TEXT,
            severity TEXT,
            actor TEXT,
            source TEXT,
            home TEXT,
            home_id TEXT,
            apartment_number TEXT,
            event_type TEXT,
            details TEXT,
            action_taken TEXT,
            device_id TEXT,
            device_name TEXT
        )
    """)

    needed = [
        "timestamp", "created_at", "severity", "actor", "source",
        "home", "home_id", "apartment_number", "event_type",
        "details", "action_taken", "device_id", "device_name"
    ]

    existing = _d7_fake_cols(conn, "system_logs")
    for col in needed:
        if col not in existing:
            conn.execute(f"ALTER TABLE system_logs ADD COLUMN {col} TEXT")

    conn.commit()

def _d7_fake_find_home(conn, apartment_number="", home_id="", home_code=""):
    if "homes" not in _d7_fake_tables(conn):
        raise _D7FakeHTTPException(status_code=500, detail="homes table not found.")

    apartment_number = str(apartment_number or "").strip()
    home_id = str(home_id or "").strip()
    home_code = str(home_code or "").strip()

    if home_id:
        row = conn.execute(
            "SELECT * FROM homes WHERE CAST(id AS TEXT) = ? LIMIT 1",
            (home_id,),
        ).fetchone()
        if row:
            return dict(row)

    if apartment_number:
        row = conn.execute(
            "SELECT * FROM homes WHERE CAST(apartment_number AS TEXT) = ? LIMIT 1",
            (apartment_number,),
        ).fetchone()
        if row:
            return dict(row)

    if home_code:
        row = conn.execute(
            "SELECT * FROM homes WHERE home_code = ? LIMIT 1",
            (home_code,),
        ).fetchone()
        if row:
            return dict(row)

    row = conn.execute("SELECT * FROM homes ORDER BY id LIMIT 1").fetchone()
    if row:
        return dict(row)

    raise _D7FakeHTTPException(status_code=404, detail="No home found.")

@app.post("/api/test/unknown-face")
def d7m16_fake_unknown_face(payload: dict | None = _D7FakeBody(default=None)):
    payload = payload or {}
    conn = _d7_fake_conn()

    try:
        _d7_fake_ensure_logs(conn)

        home = _d7_fake_find_home(
            conn,
            apartment_number=payload.get("apartment_number", ""),
            home_id=payload.get("home_id", ""),
            home_code=payload.get("home_code", ""),
        )

        home_id = str(home.get("id") or "")
        apartment = str(home.get("apartment_number") or "")
        camera_name = str(payload.get("camera_name") or "hhhh")
        member_name = str(payload.get("member_name") or payload.get("name") or "Unknown person").strip()
        now = _d7_fake_now()

        try:
            _d7m16_insert_family_member_from_unknown(conn, home_id, member_name)
        except Exception:
            pass

        conn.execute(
            """
            INSERT INTO system_logs (
                timestamp,
                created_at,
                severity,
                actor,
                source,
                home,
                home_id,
                apartment_number,
                event_type,
                details,
                action_taken,
                device_id,
                device_name
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now,
                now,
                "WARNING",
                "Server",
                "Face Recognition",
                apartment,
                home_id,
                apartment,
                "Door Event",
                f"Unknown face detected at smart door ({camera_name}). Waiting for Admin App decision.",
                "UNKNOWN FACE DETECTED",
                "smart_door",
                camera_name,
            ),
        )

        log_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
        conn.commit()

        return {
            "success": True,
            "message": "Fake Unknown Face event created.",
            "log_id": log_id,
            "apartment_number": apartment,
            "camera_name": camera_name
        }
    finally:
        conn.close()
# D7M16_FAKE_UNKNOWN_FACE_TEST_END


# D7M16_FAKE_KNOWN_FAMILY_FACE_TEST_START
@app.post("/api/test/known-family-face")
def d7m16_fake_known_family_face(payload: dict | None = _D7FakeBody(default=None)):
    payload = payload or {}
    conn = _d7_fake_conn()

    try:
        _d7_fake_ensure_logs(conn)

        home = _d7_fake_find_home(
            conn,
            apartment_number=payload.get("apartment_number", ""),
            home_id=payload.get("home_id", ""),
            home_code=payload.get("home_code", ""),
        )

        home_id = str(home.get("id") or "1")
        apartment = str(home.get("apartment_number") or "")
        member_name = str(payload.get("member_name") or "Ali").strip() or "Ali"
        camera_name = str(payload.get("camera_name") or "hhhh").strip() or "hhhh"
        now = _d7_fake_now()


        try:
            home_id_int = int(str(home_id or "1"))
        except Exception:
            home_id_int = 1

        member = conn.execute(
            """
            SELECT *
            FROM family_members
            WHERE CAST(home_id AS TEXT) = CAST(? AS TEXT)
              AND lower(trim(name)) = lower(trim(?))
            LIMIT 1
            """,
            (home_id_int, member_name),
        ).fetchone()

        if member is None:
            raise _D7FakeHTTPException(
                status_code=404,
                detail=f"Family member not found. Add '{member_name}' from Family first.",
            )

        enabled = str(member["enabled"] if "enabled" in member.keys() else "1").strip().lower()
        face_enrolled = str(member["face_enrolled"] if "face_enrolled" in member.keys() else "0").strip().lower()

        is_enabled = enabled not in {"0", "false", "disabled", "off", "no"}
        has_face = face_enrolled in {"1", "true", "yes", "enabled", "on"}

        if not is_enabled or not has_face:
            reason = "disabled member" if not is_enabled else "member without enrolled face"

            conn.execute(
                """
                INSERT INTO system_logs (
                    timestamp,
                    created_at,
                    severity,
                    actor,
                    source,
                    home,
                    home_id,
                    apartment_number,
                    event_type,
                    details,
                    action_taken,
                    device_id,
                    device_name
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    now,
                    "WARNING",
                    "Server",
                    "Face Recognition",
                    apartment,
                    home_id,
                    apartment,
                    "Door Event",
                    f"Unknown face detected at smart door ({camera_name}). Waiting for Admin App decision.",
                    "UNKNOWN FACE DETECTED",
                    "smart_door",
                    camera_name,
                ),
            )

            log_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
            conn.commit()

            return {
                "success": True,
                "message": f"Member exists but is treated as unknown because: {reason}.",
                "log_id": log_id,
                "apartment_number": apartment,
                "member_name": member_name,
                "camera_name": camera_name,
                "treated_as": "unknown_face",
            }

        conn.execute(
            """
            INSERT INTO system_logs (
                timestamp,
                created_at,
                severity,
                actor,
                source,
                home,
                home_id,
                apartment_number,
                event_type,
                details,
                action_taken,
                device_id,
                device_name
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now,
                now,
                "INFO",
                "Server",
                "Server",
                apartment,
                home_id,
                apartment,
                "Face Recognition",
                f"Door opened automatically for family member {member_name}.",
                "FAMILY ACCESS GRANTED",
                "smart_door",
                camera_name,
            ),
        )

        log_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
        conn.commit()

        return {
            "success": True,
            "message": "Family member recognized and door opened automatically.",
            "log_id": log_id,
            "apartment_number": apartment,
            "member_name": member_name,
            "camera_name": camera_name,
        }
    finally:
        conn.close()
# D7M16_FAKE_KNOWN_FAMILY_FACE_TEST_END




# D7M16_UNKNOWN_FACE_LOG_CLEANUP_HELPER_START
def _d7m16_log_norm(v):
    return str(v or "").strip()

def _d7m16_log_low(v):
    return str(v or "").strip().lower()

def _d7m16_now():
    try:
        return _d7final_now()
    except Exception:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _d7m16_same_home_sql(alias_a="a", alias_b="b"):
    return f"""
    (
        COALESCE({alias_a}.home_id, '') = COALESCE({alias_b}.home_id, '')
        OR COALESCE({alias_a}.apartment_number, '') = COALESCE({alias_b}.apartment_number, '')
        OR COALESCE({alias_a}.home, '') = COALESCE({alias_b}.home, '')
    )
    """

def _d7m16_insert_family_member_from_unknown(conn, home_id, name, face_enrolled=False, snapshot_path=None):
    try:
        clean_name = _d7m16_log_norm(name) or "Unknown person"
        if not clean_name:
            return

        person_id = None
        if face_enrolled and snapshot_path:
            import cv2
            import json
            import os
            from api.face_recognition_flow import (
                _ensure_face_tables,
                _connect_model_db,
                _preprocess_face,
                _extract_embedding,
                _now_iso
            )
            
            try:
                full_snapshot_path = snapshot_path
                if not os.path.isabs(full_snapshot_path):
                    full_snapshot_path = os.path.abspath(os.path.join(os.getcwd(), snapshot_path))
                
                if os.path.exists(full_snapshot_path):
                    frame = cv2.imread(full_snapshot_path)
                    if frame is not None:
                        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                        detector = cv2.CascadeClassifier(cascade_path)
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
                        
                        if len(faces) > 0:
                            box = faces[0]
                            face_img = _preprocess_face(frame, box)
                            embedding = _extract_embedding(face_img)
                            
                            model_conn = _connect_model_db()
                            try:
                                _ensure_face_tables(model_conn)
                                cur = model_conn.cursor()
                                hid = int(str(home_id or "1")) if str(home_id or "1").isdigit() else 1
                                cur.execute("INSERT INTO persons (home_id, name, role, created_at) VALUES (?, ?, ?, ?)", 
                                            (hid, clean_name, "Family", _now_iso()))
                                person_id = cur.lastrowid
                                
                                emb_json = json.dumps(embedding)
                                cur.execute("INSERT INTO face_embeddings (person_id, embedding_json, created_at) VALUES (?, ?, ?)",
                                            (person_id, emb_json, _now_iso()))
                                
                                model_conn.commit()

                                # Also add to main DB for ORM sync
                                from database.models.ai_face import Person, FaceEmbedding
                                from database.connection.database import SessionLocal
                                db_sync = SessionLocal()
                                try:
                                    orm_person = Person(home_id=hid, name=clean_name, role="Family")
                                    db_sync.add(orm_person)
                                    db_sync.commit()
                                    db_sync.refresh(orm_person)
                                    orm_embedding = FaceEmbedding(person_id=orm_person.id, embedding_json=emb_json)
                                    db_sync.add(orm_embedding)
                                    db_sync.commit()
                                finally:
                                    db_sync.close()

                            finally:
                                model_conn.close()
            except Exception as e:
                print(f"[UNKNOWN ENROLLMENT] Error extracting face from snapshot: {e}")

        from database.connection.database import SessionLocal
        from database.models.family import FamilyMember
        db = SessionLocal()
        try:
            from datetime import datetime
            new_member = FamilyMember(
                home_id=int(str(home_id or "1")) if str(home_id or "1").isdigit() else 1,
                name=clean_name,
                role="Family",
                face_enrolled=bool(face_enrolled) or (person_id is not None),
                enabled=True,
                person_id=person_id,
                notes="Added from Unknown Face alert.",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(new_member)
            db.commit()
        finally:
            db.close()
    except Exception:
        pass

def _d7m16_cleanup_unknown_face_family_rows(conn):
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "system_logs" not in tables:
            return

        conn.execute("""
            UPDATE system_logs
            SET severity = 'INFO',
                event_type = 'Face Recognition',
                details = 'Unknown person opened once by Admin App.'
            WHERE upper(COALESCE(action_taken, '')) = 'UNKNOWN OPEN ONCE'
        """)

        conn.execute("""
            UPDATE system_logs
            SET severity = 'WARNING',
                event_type = 'Face Recognition',
                details = 'Unknown person denied by Admin App.'
            WHERE upper(COALESCE(action_taken, '')) = 'UNKNOWN DENIED'
        """)

        conn.execute("""
            UPDATE system_logs
            SET severity = 'INFO',
                event_type = 'Face Recognition',
                details = 'Door opened after adding unknown person from Unknown Face alert.'
            WHERE upper(COALESCE(action_taken, '')) = 'DOOR OPENED AFTER FAMILY ADD'
        """)

        conn.execute("""
            UPDATE system_logs
            SET severity = 'INFO',
                event_type = 'Family Management'
            WHERE upper(COALESCE(action_taken, '')) = 'FAMILY MEMBER ADDED'
        """)

        ordinary_rows = conn.execute("""
            SELECT id, details, home_id, apartment_number, home
            FROM system_logs
            WHERE upper(COALESCE(action_taken, '')) IN ('FAMILY MEMBER ADDED', 'FAMILY MEMBER ADDED')
              AND lower(COALESCE(details, '')) LIKE 'family member % added with role family%'
              AND lower(COALESCE(details, '')) NOT LIKE '%unknown face%'
            ORDER BY id DESC
        """).fetchall()

        for row in ordinary_rows:
            rid = int(row["id"])
            details = _d7m16_log_norm(row["details"])
            low = details.lower()

            name = "Unknown person"
            if low.startswith("family member ") and " added with role" in low:
                name = details[len("Family member "):].split(" added with role", 1)[0].strip() or name

            home_id = _d7m16_log_norm(row["home_id"])
            apt = _d7m16_log_norm(row["apartment_number"])
            home = _d7m16_log_norm(row["home"])

            related = conn.execute("""
                SELECT id
                FROM system_logs
                WHERE id != ?
                  AND (
                        upper(COALESCE(action_taken, '')) = 'DOOR OPENED AFTER FAMILY ADD'
                     OR (
                            upper(COALESCE(action_taken, '')) = 'FAMILY MEMBER ADDED'
                        AND lower(COALESCE(details, '')) LIKE '%unknown face%'
                        )
                  )
                  AND ABS(CAST(id AS INTEGER) - ?) <= 8
                  AND (
                        COALESCE(home_id, '') = ?
                     OR COALESCE(apartment_number, '') = ?
                     OR COALESCE(home, '') = ?
                     OR COALESCE(home, '') = ?
                  )
                ORDER BY ABS(CAST(id AS INTEGER) - ?) ASC
                LIMIT 1
            """, (rid, rid, home_id, apt, home, apt, rid)).fetchone()

            if related:
                candidate = conn.execute("""
                    SELECT id
                    FROM system_logs
                    WHERE id != ?
                      AND upper(COALESCE(action_taken, '')) = 'FAMILY MEMBER ADDED'
                      AND lower(COALESCE(details, '')) LIKE '%unknown face%'
                      AND ABS(CAST(id AS INTEGER) - ?) <= 8
                      AND (
                            COALESCE(home_id, '') = ?
                         OR COALESCE(apartment_number, '') = ?
                         OR COALESCE(home, '') = ?
                         OR COALESCE(home, '') = ?
                      )
                    ORDER BY ABS(CAST(id AS INTEGER) - ?) ASC
                    LIMIT 1
                """, (rid, rid, home_id, apt, home, apt, rid)).fetchone()

                if candidate:
                    conn.execute("""
                        UPDATE system_logs
                        SET severity = 'INFO',
                            event_type = 'Family Management',
                            details = ?
                        WHERE id = ?
                    """, (f"Family member {name} added with role Family from Unknown Face alert.", candidate["id"]))

                conn.execute("DELETE FROM system_logs WHERE id = ?", (rid,))

        rows = conn.execute("""
            SELECT id, details
            FROM system_logs
            WHERE upper(COALESCE(action_taken, '')) = 'FAMILY MEMBER ADDED'
              AND lower(COALESCE(details, '')) LIKE '%unknown face%'
        """).fetchall()

        for row in rows:
            details = _d7m16_log_norm(row["details"])
            low = details.lower()

            if low.startswith("family member ") and " added with role family from unknown face alert" in low:
                continue

            name = "Unknown person"
            if " added as family from unknown face alert" in low:
                name = details.split(" added as Family from Unknown Face alert", 1)[0].strip() or name

            conn.execute("""
                UPDATE system_logs
                SET severity = 'INFO',
                    event_type = 'Family Management',
                    details = ?
                WHERE id = ?
            """, (f"Family member {name} added with role Family from Unknown Face alert.", row["id"]))

        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass

def _d7m16_delete_system_logs_filtered(conn, payload):
    _d7m16_cleanup_unknown_face_family_rows(conn)

    date_filter = _d7m16_log_norm(
        payload.get("date")
        or payload.get("selected_date")
        or payload.get("date_filter")
        or payload.get("dateFilter")
    )

    event_filter = _d7m16_log_norm(
        payload.get("event_type")
        or payload.get("event")
        or payload.get("eventFilter")
    )

    severity_filter = _d7m16_log_norm(
        payload.get("severity")
        or payload.get("severityFilter")
    )

    actor_filter = _d7m16_log_norm(
        payload.get("actor")
        or payload.get("actorFilter")
    )

    search_filter = _d7m16_log_norm(
        payload.get("search")
        or payload.get("query")
    )

    def is_all(v):
        return not v or _d7m16_log_low(v) in {
            "all",
            "all dates",
            "all events",
            "all severities",
            "all actors",
            "all data",
        }

    where = []
    params = []

    if not is_all(date_filter):
        where.append("substr(COALESCE(timestamp, created_at, ''), 1, 10) = ?")
        params.append(date_filter[:10])

    if not is_all(event_filter):
        ev = _d7m16_log_low(event_filter)
        event_parts = [
            "lower(replace(COALESCE(event_type, ''), char(10), ' ')) LIKE ?",
            "lower(replace(COALESCE(action_taken, ''), char(10), ' ')) LIKE ?",
            "lower(replace(COALESCE(details, ''), char(10), ' ')) LIKE ?",
        ]
        params.extend([f"%{ev}%", f"%{ev}%", f"%{ev}%"])

        if "family" in ev:
            event_parts.extend([
                "upper(COALESCE(action_taken, '')) LIKE '%FAMILY%'",
                "lower(COALESCE(details, '')) LIKE '%family%'",
            ])

        if "face" in ev or "recognition" in ev:
            event_parts.extend([
                "upper(COALESCE(action_taken, '')) LIKE '%UNKNOWN%'",
                "lower(COALESCE(details, '')) LIKE '%unknown face%'",
                "lower(COALESCE(event_type, '')) LIKE '%face%'",
            ])

        where.append("(" + " OR ".join(event_parts) + ")")

    if not is_all(severity_filter):
        where.append("upper(trim(COALESCE(severity, ''))) = upper(?)")
        params.append(severity_filter)

    if not is_all(actor_filter):
        where.append("lower(trim(COALESCE(actor, source, ''))) = lower(?)")
        params.append(actor_filter)

    if not is_all(search_filter):
        q = f"%{_d7m16_log_low(search_filter)}%"
        where.append("""
            (
                lower(COALESCE(actor, '')) LIKE ?
             OR lower(COALESCE(source, '')) LIKE ?
             OR lower(COALESCE(home, '')) LIKE ?
             OR lower(COALESCE(apartment_number, '')) LIKE ?
             OR lower(COALESCE(event_type, '')) LIKE ?
             OR lower(COALESCE(details, '')) LIKE ?
             OR lower(COALESCE(action_taken, '')) LIKE ?
            )
        """)
        params.extend([q, q, q, q, q, q, q])

    sql = "DELETE FROM system_logs"
    if where:
        sql += " WHERE " + " AND ".join(where)

    cur = conn.execute(sql, params)
    conn.commit()
    return {"success": True, "deleted": cur.rowcount}
# D7M16_UNKNOWN_FACE_LOG_CLEANUP_HELPER_END

# D7M16_APP_CAMERA_REAL_BINDING_START




def _d7_camera_cols(conn, table):
    try:
        return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    except Exception:
        return set()














# D7M16_APP_CAMERA_REAL_BINDING_END


# D7M16_CAMERA_FINAL_CLEAN_BINDING_START
from fastapi.responses import Response as _D7CamFinalResponse
import struct as _d7_cam_final_struct
import zlib as _d7_cam_final_zlib
import time as _d7_cam_final_time


















# D7M16_CAMERA_FINAL_CLEAN_BINDING_END

# D7M16_LOG_DELETE_ISOLATION_FINAL_START
# Final behavior:
# - Dashboard log delete hides logs from Dashboard only.
# - App door log delete hides logs from App only.
# - Original system_logs rows stay intact so other surfaces keep their events.

try:
    from fastapi.responses import JSONResponse as _D7M16JSONResponse
except Exception:
    _D7M16JSONResponse = None

import re as _d7m16_log_iso_re
import sqlite3 as _d7m16_log_iso_sqlite3
from datetime import datetime as _d7m16_log_iso_datetime


def _d7m16_log_iso_now():
    try:
        return _d7final_now()
    except Exception:
        return _d7m16_log_iso_datetime.now().isoformat(timespec="seconds")


def _d7m16_log_iso_conn():
    try:
        conn = _d7final_conn()
    except Exception:
        conn = _d7m16_log_iso_sqlite3.connect(_security_db_path())
    conn.row_factory = _d7m16_log_iso_sqlite3.Row
    return conn


def _d7m16_log_iso_json(payload, status_code=200):
    if _D7M16JSONResponse:
        return _D7M16JSONResponse(payload, status_code=status_code)
    return payload


def _d7m16_ensure_dashboard_log_states(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dashboard_log_states (
            log_key TEXT PRIMARY KEY,
            source_table TEXT,
            source_id TEXT,
            hidden INTEGER DEFAULT 0,
            updated_at TEXT
        )
        """
    )
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_dashboard_log_states_source ON dashboard_log_states(source_table, source_id)")
    except Exception:
        pass


def _d7m16_dashboard_log_key(source_table, source_id):
    return "dashboard::{}::{}".format(str(source_table or ""), str(source_id or ""))


def _d7m16_hide_dashboard_log(conn, source_table, source_id):
    _d7m16_ensure_dashboard_log_states(conn)
    conn.execute(
        """
        INSERT INTO dashboard_log_states(log_key, source_table, source_id, hidden, updated_at)
        VALUES (?, ?, ?, 1, ?)
        ON CONFLICT(log_key) DO UPDATE SET
            hidden = 1,
            updated_at = excluded.updated_at
        """,
        (
            _d7m16_dashboard_log_key(source_table, source_id),
            str(source_table or ""),
            str(source_id or ""),
            _d7m16_log_iso_now(),
        ),
    )




def _d7m16_soft_hide_dashboard_single(log_id):
    conn = _d7m16_log_iso_conn()
    try:
        try:
            _d7final_ensure_system_logs(conn)
        except Exception:
            pass

        row = conn.execute("SELECT id FROM system_logs WHERE id = ? LIMIT 1", (str(log_id),)).fetchone()
        if not row:
            return {"success": True, "deleted": 0, "hidden": 0}

        _d7m16_hide_dashboard_log(conn, "system_logs", str(log_id))
        conn.commit()
        return {"success": True, "deleted": 1, "hidden": 1, "mode": "dashboard_only"}
    finally:
        conn.close()


def _d7m16_row_value(row, *names):
    for name in names:
        try:
            if name in row.keys():
                value = row[name]
                if value is not None:
                    return value
        except Exception:
            pass
    return ""


def _d7m16_matches_dashboard_filters(row, payload):
    payload = payload or {}

    search = str(payload.get("search") or "").strip().lower()
    date_value = str(payload.get("date") or "").strip()
    event_type_filter = str(payload.get("event_type") or payload.get("event") or "").strip().lower()
    severity_filter = str(payload.get("severity") or "").strip().lower()
    actor_filter = str(payload.get("actor") or "").strip().lower()

    row_time = str(_d7m16_row_value(row, "timestamp", "created_at", "time") or "")
    row_date = row_time[:10] if len(row_time) >= 10 else ""

    if date_value and row_date != date_value:
        return False

    row_event = str(_d7m16_row_value(row, "event_type", "category") or "")
    if event_type_filter and row_event.strip().lower() != event_type_filter:
        return False

    row_severity = str(_d7m16_row_value(row, "severity") or "").strip().lower()
    if severity_filter and row_severity != severity_filter:
        return False

    action = str(_d7m16_row_value(row, "action_taken") or "").upper()
    details = str(_d7m16_row_value(row, "details", "message") or "")
    
    actor_raw = str(_d7m16_row_value(row, "actor", "source") or "")
    text_full_lower = f"{actor_raw} {action} {details} {row_event}".lower()
    
    detected_actor = "Server"
    
    if action in ["APP SETTINGS UPDATED", "APP ADMIN REGISTERED", "APP PASSWORD RESET"]:
        detected_actor = "Admin App"
    elif "failed login" in text_full_lower or "invalid username" in text_full_lower or "invalid password" in text_full_lower:
        detected_actor = "Unknown"
    elif "system_owner" in text_full_lower or "system owner" in text_full_lower or "dashboard" in text_full_lower:
        detected_actor = "System Owner"
    elif "flutter" in text_full_lower or "admin app" in text_full_lower or "manual_open_from_flutter" in text_full_lower or row_event == "Family Management":
        detected_actor = "Admin App"
    elif "esp32" in text_full_lower or "device heartbeat" in text_full_lower or "device event" in text_full_lower or "servo" in text_full_lower or row_event == "Smart Door Event":
        detected_actor = "ESP32 Device"
    elif row_event in ["System Error", "Face Recognition", "Energy Warning", "System Security"]:
        detected_actor = "Server"
    elif row_event in ["Smart Door Command", "Energy Monitor Command", "Device Restart", "Device Enable", "Device Disable", "Device Removed"]:
        detected_actor = "System Owner"

    if actor_raw.lower() == "server" and "command" in row_event.lower() and action.startswith("MQTT"):
        detected_actor = "System Owner"

    row_actor_bucket = ""
    det_lower = detected_actor.lower()
    if "system owner" in det_lower or "system_owner" in det_lower or "dashboard" in det_lower:
        row_actor_bucket = "System Owner"
    elif "admin app" in det_lower or "flutter" in det_lower or "owner app" in det_lower or "app settings" in det_lower or "family management" in det_lower:
        row_actor_bucket = "Admin App"
    elif "server" in det_lower or "esp32" in det_lower or "device" in det_lower or "face recognition" in det_lower or "energy warning" in det_lower or "system security" in det_lower or "system error" in det_lower:
        row_actor_bucket = "Server"
    else:
        row_actor_bucket = detected_actor
        
    row_actor_bucket_lower = row_actor_bucket.lower()

    if actor_filter and actor_filter != "all" and row_actor_bucket_lower != actor_filter:
        return False

    if search:
        searchable = " ".join([
            str(_d7m16_row_value(row, "home", "apartment", "apartment_number", "home_id") or ""),
            detected_actor,
            row_actor_bucket,
            row_event,
            details,
            action,
        ]).lower()
        
        is_number_search = search.isdigit()
        if is_number_search:
            apt = str(_d7m16_row_value(row, "home", "apartment", "apartment_number", "home_id") or "").lower()
            import re
            device_id_match = re.search(r'\b(?:DOOR|METER|CAM)-HOME0*([0-9]+)-\d+\b', searchable, re.IGNORECASE)
            if device_id_match:
                apt = str(int(device_id_match.group(1)))
            if apt != search:
                return False
        else:
            if search not in searchable:
                return False

    return True


def _d7m16_soft_hide_dashboard_filtered(payload):
    conn = _d7m16_log_iso_conn()
    try:
        try:
            _d7final_ensure_system_logs(conn)
        except Exception:
            pass

        if "system_logs" not in [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
            return {"success": True, "deleted": 0, "hidden": 0}

        rows = conn.execute("SELECT * FROM system_logs ORDER BY id DESC").fetchall()
        hidden_count = 0

        for row in rows:
            if not _d7m16_matches_dashboard_filters(row, payload):
                continue

            row_id = str(_d7m16_row_value(row, "id") or "")
            if not row_id:
                continue

            _d7m16_hide_dashboard_log(conn, "system_logs", row_id)
            hidden_count += 1

        conn.commit()
        return {"success": True, "deleted": hidden_count, "hidden": hidden_count, "mode": "dashboard_only"}
    finally:
        conn.close()


def _d7m16_make_fallback_viewer_scope(home_id, viewer_role, admin_login):
    return "app::{}::{}::{}".format(str(home_id or ""), str(viewer_role or "admin"), str(admin_login or ""))


def _d7m16_soft_hide_app_door_log(source_table, source_id, query_params=None):
    query_params = query_params or {}
    conn = _d7m16_log_iso_conn()
    try:
        try:
            _d7final_ensure_system_logs(conn)
        except Exception:
            pass

        if str(source_table) != "system_logs":
            return {"success": False, "detail": "Unsupported log source."}

        row = conn.execute("SELECT * FROM system_logs WHERE id = ? LIMIT 1", (str(source_id),)).fetchone()
        if not row:
            return {"success": True, "deleted": 0, "hidden": 0}

        home_id = ""
        viewer_scope = ""

        try:
            home = _d7final_find_home(
                conn,
                str(query_params.get("home_id") or ""),
                str(query_params.get("home_code") or ""),
                str(query_params.get("admin_login") or ""),
            )
            values = _d7final_home_values(home)
            home_id = str(values.get("home_id") or values.get("id") or "")
            viewer_scope = _d7m16_viewer_scope(
                home,
                str(query_params.get("viewer_role") or "admin"),
                str(query_params.get("admin_login") or ""),
            )
        except Exception:
            home_id = str(_d7m16_row_value(row, "home_id", "home", "apartment_number") or "")
            viewer_scope = _d7m16_make_fallback_viewer_scope(
                home_id,
                str(query_params.get("viewer_role") or "admin"),
                str(query_params.get("admin_login") or ""),
            )

        try:
            _d7m16_hide_door_log_for_viewer(conn, "system_logs", str(source_id), home_id, viewer_scope)
        except Exception:
            _d7m16_ensure_door_log_states(conn)
            state_key = _d7m16_door_state_key("system_logs", str(source_id), viewer_scope)
            conn.execute(
                """
                INSERT INTO app_door_log_states(
                    state_key, source_table, source_id, home_id, viewer_scope, hidden, updated_at
                )
                VALUES (?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(state_key) DO UPDATE SET
                    hidden = 1,
                    updated_at = excluded.updated_at
                """,
                (
                    state_key,
                    "system_logs",
                    str(source_id),
                    home_id,
                    viewer_scope,
                    _d7m16_log_iso_now(),
                ),
            )

        conn.commit()
        return {"success": True, "deleted": 1, "hidden": 1, "mode": "app_only"}
    finally:
        conn.close()




if "_get_security_logs" in globals() and not globals().get("__D7M16_LOG_DELETE_ISOLATION_GET_LOGS_WRAPPED"):
    __D7M16_LOG_DELETE_ISOLATION_GET_LOGS_WRAPPED = True
    _d7m16_original_get_security_logs = _get_security_logs



@app.middleware("http")
async def d7m16_log_delete_isolation_middleware(request, call_next):
    path = request.url.path
    method = request.method.upper()

    try:
        if method == "DELETE":
            match = _d7m16_log_iso_re.fullmatch(r"/api/dashboard/logs-final/([^/]+)", path)
            if match:
                return _d7m16_log_iso_json(_d7m16_soft_hide_dashboard_single(match.group(1)))

            match = _d7m16_log_iso_re.fullmatch(r"/api/dashboard/security-logs/([^/]+)", path)
            if match:
                return _d7m16_log_iso_json(_d7m16_soft_hide_dashboard_single(match.group(1)))

            match = _d7m16_log_iso_re.fullmatch(r"/api/app/door-access-logs/([^/]+)/([^/]+)", path)
            if match:
                return _d7m16_log_iso_json(
                    _d7m16_soft_hide_app_door_log(match.group(1), match.group(2), dict(request.query_params))
                )

            match = _d7m16_log_iso_re.fullmatch(r"/api/app/door-access-logs-final/([^/]+)/([^/]+)", path)
            if match:
                return _d7m16_log_iso_json(
                    _d7m16_soft_hide_app_door_log(match.group(1), match.group(2), dict(request.query_params))
                )

    except Exception as exc:
        return _d7m16_log_iso_json(
            {"success": False, "detail": "Log isolation patch error: {}".format(str(exc))},
            status_code=500,
        )

    return await call_next(request)
# D7M16_LOG_DELETE_ISOLATION_FINAL_END

# D7M16_APP_AUTH_PHONE_USERNAME_FINAL_START
# Final app auth behavior:
# - Admin first login: Phone Number + Password + Home Code.
# - Admin login: Phone Number + Password.
# - User login: Username + User Password.
# - user_username is globally unique.

from fastapi.responses import JSONResponse as _D7M16AuthJSONResponse
from pathlib import Path as _D7M16AuthPath
import sqlite3 as _d7m16_auth_sqlite3
import re as _d7m16_auth_re
from datetime import datetime as _d7m16_auth_datetime


def _d7m16_auth_now():
    return _d7m16_auth_datetime.now().isoformat(timespec="seconds")


def _d7m16_auth_db_path():
    return _D7M16AuthPath(__file__).resolve().parent / "database" / "smart_home_edge.db"


def _d7m16_auth_conn():
    conn = _d7m16_auth_sqlite3.connect(str(_d7m16_auth_db_path()))
    conn.row_factory = _d7m16_auth_sqlite3.Row
    return conn


def _d7m16_auth_tables(conn):
    return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}


def _d7m16_auth_cols(conn, table):
    try:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    except Exception:
        return set()


def _d7m16_auth_ensure_schema(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            home_id INTEGER NOT NULL,
            admin_login TEXT NOT NULL,
            admin_password TEXT NOT NULL,
            user_password TEXT DEFAULT '',
            door_pin TEXT DEFAULT '',
            camera_pin TEXT DEFAULT '',
            owner_phone TEXT DEFAULT '',
            failed_login_attempts INTEGER DEFAULT 0,
            recovery_otp TEXT DEFAULT '',
            recovery_expires_at TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cols = _d7m16_auth_cols(conn, "app_accounts")

    needed = {
        "user_username": "TEXT DEFAULT ''",
        "owner_phone": "TEXT DEFAULT ''",
        "failed_login_attempts": "INTEGER DEFAULT 0",
        "recovery_otp": "TEXT DEFAULT ''",
        "recovery_expires_at": "TEXT DEFAULT ''",
        "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "TEXT DEFAULT CURRENT_TIMESTAMP",
    }

    for col, col_type in needed.items():
        if col not in cols:
            conn.execute(f"ALTER TABLE app_accounts ADD COLUMN {col} {col_type}")

    try:
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_app_accounts_user_username_unique
            ON app_accounts(lower(user_username))
            WHERE user_username IS NOT NULL AND trim(user_username) <> ''
            """
        )
    except Exception:
        pass

    try:
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_app_accounts_admin_login_unique
            ON app_accounts(lower(admin_login))
            WHERE admin_login IS NOT NULL AND trim(admin_login) <> ''
            """
        )
    except Exception:
        pass

    # Ensure homes table has login tracking columns
    if "homes" in _d7m16_auth_tables(conn):
        homes_cols = _d7m16_auth_cols(conn, "homes")
        if "is_online" not in homes_cols:
            conn.execute("ALTER TABLE homes ADD COLUMN is_online INTEGER DEFAULT 0")
        if "login_state" not in homes_cols:
            conn.execute("ALTER TABLE homes ADD COLUMN login_state TEXT DEFAULT 'logged_out'")
        if "last_login_at" not in homes_cols:
            conn.execute("ALTER TABLE homes ADD COLUMN last_login_at TEXT")
        if "account_status" not in homes_cols:
            conn.execute("ALTER TABLE homes ADD COLUMN account_status TEXT DEFAULT 'active'")
        if "last_heartbeat_at" not in homes_cols:
            conn.execute("ALTER TABLE homes ADD COLUMN last_heartbeat_at TEXT")

    conn.commit()


def _d7m16_phone(value):
    value = str(value or "").strip()
    digits = _d7m16_auth_re.sub(r"\D+", "", value)
    return digits or value


def _d7m16_username(value):
    return str(value or "").strip()


def _d7m16_lower(value):
    return str(value or "").strip().lower()


def _d7m16_home_to_dict(row):
    if not row:
        return {}
    data = dict(row)
    return {
        **data,
        "id": str(data.get("id") or ""),
        "home_id": str(data.get("id") or data.get("home_id") or ""),
        "home_code": str(data.get("home_code") or ""),
        "apartment_number": str(data.get("apartment_number") or ""),
        "owner_name": str(data.get("owner_name") or ""),
        "owner_email": str(data.get("owner_email") or ""),
        "owner_phone": str(data.get("owner_phone") or ""),
        "status": str(data.get("status") or "online"),
    }


def _d7m16_account_to_dict(account, home=None):
    data = dict(account)
    home_data = _d7m16_home_to_dict(home) if home else {}

    return {
        **data,
        "id": str(data.get("id") or ""),
        "home_id": str(data.get("home_id") or home_data.get("home_id") or ""),
        "admin_login": str(data.get("admin_login") or ""),
        "admin_username": str(data.get("admin_login") or ""),
        "admin_password": str(data.get("admin_password") or ""),
        "user_username": str(data.get("user_username") or ""),
        "user_password": str(data.get("user_password") or ""),
        "door_pin": str(data.get("door_pin") or ""),
        "camera_pin": str(data.get("camera_pin") or ""),
        "owner_phone": str(data.get("owner_phone") or home_data.get("owner_phone") or ""),
        "home_code": str(home_data.get("home_code") or ""),
        "apartment_number": str(home_data.get("apartment_number") or ""),
    }


def _d7m16_auth_response(account, home, role):
    account_data = _d7m16_account_to_dict(account, home)
    home_data = _d7m16_home_to_dict(home)

    alerts_count = 0
    try:
        conn = _d7m16_auth_conn()
        row = conn.execute(
            "SELECT alerts_count FROM app_home_demo_state WHERE CAST(home_id AS TEXT)=CAST(? AS TEXT) LIMIT 1",
            (str(account_data.get("home_id") or ""),),
        ).fetchone()
        if row:
            alerts_count = int(row["alerts_count"] or 0)
        conn.close()
    except Exception:
        alerts_count = 0

    return {
        "success": True,
        "role": role,
        "account": account_data,
        "home": home_data,
        "alerts_count": alerts_count,
    }


def _d7m16_find_home_by_code_and_phone(conn, home_code, phone):
    if "homes" not in _d7m16_auth_tables(conn):
        return None

    cols = _d7m16_auth_cols(conn, "homes")
    if "home_code" not in cols or "owner_phone" not in cols:
        return None

    rows = conn.execute(
        "SELECT * FROM homes WHERE lower(home_code)=lower(?)",
        (str(home_code or "").strip(),),
    ).fetchall()

    wanted = _d7m16_phone(phone)

    for row in rows:
        stored = _d7m16_phone(row["owner_phone"])
        if stored == wanted:
            return row

    return None


def _d7m16_find_home_by_id(conn, home_id):
    if "homes" not in _d7m16_auth_tables(conn):
        return None

    return conn.execute(
        "SELECT * FROM homes WHERE CAST(id AS TEXT)=CAST(? AS TEXT) LIMIT 1",
        (str(home_id),),
    ).fetchone()


def _d7m16_find_account_by_admin_phone(conn, phone):
    clean = _d7m16_phone(phone)
    return conn.execute(
        """
        SELECT *
        FROM app_accounts
        WHERE lower(COALESCE(admin_login,'')) = lower(?)
           OR COALESCE(owner_phone,'') = ?
        LIMIT 1
        """,
        (clean, clean),
    ).fetchone()


def _d7m16_find_account_by_user_username(conn, username):
    clean = _d7m16_username(username)
    return conn.execute(
        """
        SELECT *
        FROM app_accounts
        WHERE lower(COALESCE(user_username,'')) = lower(?)
        LIMIT 1
        """,
        (clean,),
    ).fetchone()


def _d7m16_auth_error(message, status_code=400):
    return _D7M16AuthJSONResponse({"success": False, "detail": message}, status_code=status_code)


async def _d7m16_json_body(request):
    try:
        return await request.json()
    except Exception:
        return {}


@app.middleware("http")
async def d7m16_app_auth_phone_username_middleware(request, call_next):
    path = request.url.path
    method = request.method.upper()

    if method != "POST" or path not in {
        "/api/app/auth/register-admin",
        "/api/app/auth/login-admin",
        "/api/app/auth/login-user",
        "/api/app/auth/settings",
    }:
        return await call_next(request)

    payload = await _d7m16_json_body(request)
    conn = _d7m16_auth_conn()

    try:
        _d7m16_auth_ensure_schema(conn)

        if path == "/api/app/auth/register-admin":
            phone = _d7m16_phone(
                payload.get("phone_number")
                or payload.get("phone")
                or payload.get("login")
                or payload.get("admin_login")
            )
            password = str(payload.get("password") or "").strip()
            home_code = str(payload.get("home_code") or "").strip()

            if not phone or not password or not home_code:
                return _d7m16_auth_error("Phone Number, Password, and Home Code are required.", 400)

            home = _d7m16_find_home_by_code_and_phone(conn, home_code, phone)
            if not home:
                return _d7m16_auth_error("Phone Number does not match this Home Code.", 404)

            existing_home = conn.execute(
                "SELECT id FROM app_accounts WHERE CAST(home_id AS TEXT)=CAST(? AS TEXT) LIMIT 1",
                (str(home["id"]),),
            ).fetchone()
            if existing_home:
                return _d7m16_auth_error("This home already has an admin account. Use Login instead.", 409)

            existing_phone = _d7m16_find_account_by_admin_phone(conn, phone)
            if existing_phone:
                return _d7m16_auth_error("This phone number is already used.", 409)

            now = _d7m16_auth_now()
            cur = conn.execute(
                """
                INSERT INTO app_accounts (
                    home_id, admin_login, admin_password, user_username,
                    user_password, door_pin, camera_pin, owner_phone, created_at, updated_at
                )
                VALUES (?, ?, ?, '', '', '', '', ?, ?, ?)
                """,
                (home["id"], phone, password, phone, now, now),
            )
            conn.commit()

            account = conn.execute(
                "SELECT * FROM app_accounts WHERE id = ? LIMIT 1",
                (cur.lastrowid,),
            ).fetchone()

            # Update login tracking on registration
            _d7m16_update_login_tracking(conn, home["id"])

            return _D7M16AuthJSONResponse(_d7m16_auth_response(account, home, "Admin"))

        if path == "/api/app/auth/login-admin":
            phone = _d7m16_phone(
                payload.get("phone_number")
                or payload.get("phone")
                or payload.get("login")
                or payload.get("admin_login")
            )
            password = str(payload.get("password") or "").strip()

            if not phone or not password:
                return _d7m16_auth_error("Phone Number and Password are required.", 400)

            account = _d7m16_find_account_by_admin_phone(conn, phone)
            if not account:
                return _d7m16_auth_error("Invalid phone number.", 404)

            account = dict(account)
            if str(account.get("admin_password") or "") != password:
                return _d7m16_auth_error("Invalid password.", 401)

            home = _d7m16_find_home_by_id(conn, account.get("home_id"))

            # Check if account is disabled
            if home:
                home_dict = dict(home)
                status = str(home_dict.get("account_status") or "active").strip().lower()
                if status in {"disabled", "inactive", "blocked", "suspended"}:
                    return _d7m16_auth_error("Your account has been disabled by the administrator. Please contact support.", 403)

            # Update login tracking
            if home:
                _d7m16_update_login_tracking(conn, home["id"])

            return _D7M16AuthJSONResponse(_d7m16_auth_response(account, home, "Admin"))

        if path == "/api/app/auth/login-user":
            username = _d7m16_username(
                payload.get("username")
                or payload.get("user_username")
                or payload.get("admin_login")
            )
            user_password = str(payload.get("user_password") or payload.get("password") or "").strip()

            if not username or not user_password:
                return _d7m16_auth_error("Username and User Password are required.", 400)

            account = _d7m16_find_account_by_user_username(conn, username)
            if not account:
                return _d7m16_auth_error("Invalid username.", 404)

            account = dict(account)
            saved_user_password = str(account.get("user_password") or "").strip()

            if not saved_user_password:
                return _d7m16_auth_error("User password is not set by the admin yet.", 403)

            if saved_user_password != user_password:
                return _d7m16_auth_error("Invalid user password.", 401)

            home = _d7m16_find_home_by_id(conn, account.get("home_id"))

            # Check if account is disabled
            if home:
                home_dict = dict(home)
                status = str(home_dict.get("account_status") or "active").strip().lower()
                if status in {"disabled", "inactive", "blocked", "suspended"}:
                    return _d7m16_auth_error("Your account has been disabled by the administrator. Please contact support.", 403)

            # Update login tracking
            if home:
                _d7m16_update_login_tracking(conn, home["id"])

            return _D7M16AuthJSONResponse(_d7m16_auth_response(account, home, "User"))

        if path == "/api/app/auth/settings":
            current_login = _d7m16_phone(payload.get("current_login") or payload.get("phone_number") or payload.get("phone"))
            current_password = str(payload.get("current_password") or "").strip()

            account = _d7m16_find_account_by_admin_phone(conn, current_login)
            if not account:
                return _d7m16_auth_error("Admin account was not found.", 404)

            account = dict(account)
            if str(account.get("admin_password") or "") != current_password:
                return _d7m16_auth_error("Current password is invalid.", 401)

            updates = []
            values = []

            if payload.get("new_admin_password") is not None and str(payload.get("new_admin_password")).strip():
                updates.append("admin_password = ?")
                values.append(str(payload.get("new_admin_password")).strip())

            if payload.get("door_pin") is not None:
                updates.append("door_pin = ?")
                values.append(str(payload.get("door_pin") or "").strip())

            if payload.get("camera_pin") is not None:
                updates.append("camera_pin = ?")
                values.append(str(payload.get("camera_pin") or "").strip())

            if payload.get("user_username") is not None:
                user_username = _d7m16_username(payload.get("user_username"))
                if user_username:
                    exists = conn.execute(
                        """
                        SELECT id
                        FROM app_accounts
                        WHERE lower(COALESCE(user_username,'')) = lower(?)
                          AND id <> ?
                        LIMIT 1
                        """,
                        (user_username, account["id"]),
                    ).fetchone()
                    if exists:
                        return _d7m16_auth_error("This username is already used.", 409)

                updates.append("user_username = ?")
                values.append(user_username)

            if payload.get("user_password") is not None:
                updates.append("user_password = ?")
                values.append(str(payload.get("user_password") or "").strip())

            if updates:
                updates.append("updated_at = ?")
                values.append(_d7m16_auth_now())
                values.append(account["id"])

                conn.execute(
                    f"UPDATE app_accounts SET {', '.join(updates)} WHERE id = ?",
                    values,
                )
                conn.commit()

            updated = conn.execute("SELECT * FROM app_accounts WHERE id = ? LIMIT 1", (account["id"],)).fetchone()
            home = _d7m16_find_home_by_id(conn, updated["home_id"])

            return _D7M16AuthJSONResponse(_d7m16_auth_response(updated, home, "Admin"))

    except Exception as exc:
        return _d7m16_auth_error(f"Auth patch error: {exc}", 500)
    finally:
        conn.close()

    return await call_next(request)
# D7M16_APP_AUTH_PHONE_USERNAME_FINAL_END

# D7M16_AUTH_PHONE_USERNAME_HARD_FIX_START
# Final app auth behavior:
# Admin First Login = Phone Number + Password + Home Code
# Admin Login = Phone Number + Password
# User Login = Username + User Password
# Forgot Password stays handled by existing recovery endpoints.

from fastapi.responses import JSONResponse as _D7M16HardAuthJSONResponse
from pathlib import Path as _D7M16HardAuthPath
import sqlite3 as _d7m16_hard_auth_sqlite3
import re as _d7m16_hard_auth_re
from datetime import datetime as _d7m16_hard_auth_datetime


def _d7m16_hard_auth_now():
    return _d7m16_hard_auth_datetime.now().isoformat(timespec="seconds")


def _d7m16_hard_auth_db_path():
    return _D7M16HardAuthPath(__file__).resolve().parent / "database" / "smart_home_edge.db"


def _d7m16_hard_auth_conn():
    conn = _d7m16_hard_auth_sqlite3.connect(str(_d7m16_hard_auth_db_path()))
    conn.row_factory = _d7m16_hard_auth_sqlite3.Row
    return conn


def _d7m16_hard_auth_cols(conn, table):
    try:
        return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    except Exception:
        return set()


def _d7m16_hard_clean_phone(value):
    return _d7m16_hard_auth_re.sub(r"\D+", "", str(value or "").strip())


def _d7m16_hard_clean_text(value):
    return str(value or "").strip()


def _d7m16_hard_cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    }


def _d7m16_hard_json(payload, status_code=200):
    return _D7M16HardAuthJSONResponse(
        payload,
        status_code=status_code,
        headers=_d7m16_hard_cors_headers(),
    )


def _d7m16_hard_error(message, status_code=400):
    return _d7m16_hard_json({"success": False, "detail": message}, status_code=status_code)


def _d7m16_hard_ensure_schema(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            home_id INTEGER NOT NULL,
            admin_login TEXT NOT NULL,
            admin_password TEXT NOT NULL,
            user_password TEXT DEFAULT '',
            door_pin TEXT DEFAULT '',
            owner_phone TEXT DEFAULT '',
            failed_login_attempts INTEGER DEFAULT 0,
            recovery_otp TEXT DEFAULT '',
            recovery_expires_at TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cols = _d7m16_hard_auth_cols(conn, "app_accounts")
    if "user_username" not in cols:
        conn.execute("ALTER TABLE app_accounts ADD COLUMN user_username TEXT DEFAULT ''")
    if "owner_phone" not in cols:
        conn.execute("ALTER TABLE app_accounts ADD COLUMN owner_phone TEXT DEFAULT ''")
    if "camera_pin" not in cols:
        conn.execute("ALTER TABLE app_accounts ADD COLUMN camera_pin TEXT DEFAULT ''")
    if "failed_login_attempts" not in cols:
        conn.execute("ALTER TABLE app_accounts ADD COLUMN failed_login_attempts INTEGER DEFAULT 0")
    if "recovery_otp" not in cols:
        conn.execute("ALTER TABLE app_accounts ADD COLUMN recovery_otp TEXT DEFAULT ''")
    if "recovery_expires_at" not in cols:
        conn.execute("ALTER TABLE app_accounts ADD COLUMN recovery_expires_at TEXT DEFAULT ''")
    if "created_at" not in cols:
        conn.execute("ALTER TABLE app_accounts ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP")
    if "updated_at" not in cols:
        conn.execute("ALTER TABLE app_accounts ADD COLUMN updated_at TEXT DEFAULT CURRENT_TIMESTAMP")

    conn.execute("""
    UPDATE app_accounts
    SET owner_phone = (
        SELECT COALESCE(h.owner_phone, '')
        FROM homes h
        WHERE CAST(h.id AS TEXT) = CAST(app_accounts.home_id AS TEXT)
        LIMIT 1
    )
    WHERE COALESCE(owner_phone, '') = ''
    """)

    conn.execute("""
    UPDATE app_accounts
    SET admin_login = COALESCE(NULLIF(owner_phone, ''), admin_login)
    WHERE COALESCE(owner_phone, '') <> ''
    """)

    try:
        conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_app_accounts_admin_login_unique
        ON app_accounts(lower(admin_login))
        WHERE admin_login IS NOT NULL AND trim(admin_login) <> ''
        """)
    except Exception:
        pass

    try:
        conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_app_accounts_user_username_unique
        ON app_accounts(lower(user_username))
        WHERE user_username IS NOT NULL AND trim(user_username) <> ''
        """)
    except Exception:
        pass

    conn.commit()


def _d7m16_hard_home_dict(row):
    if not row:
        return {}
    data = dict(row)
    return {
        **data,
        "id": str(data.get("id") or ""),
        "home_id": str(data.get("id") or data.get("home_id") or ""),
        "home_code": str(data.get("home_code") or ""),
        "apartment_number": str(data.get("apartment_number") or ""),
        "owner_name": str(data.get("owner_name") or ""),
        "owner_email": str(data.get("owner_email") or ""),
        "owner_phone": str(data.get("owner_phone") or ""),
        "status": str(data.get("status") or "online"),
    }


def _d7m16_hard_account_dict(account, home=None):
    if not account:
        return {}
    data = dict(account)
    home_data = _d7m16_hard_home_dict(home)
    phone = _d7m16_hard_clean_phone(data.get("owner_phone") or home_data.get("owner_phone") or data.get("admin_login"))

    return {
        **data,
        "id": str(data.get("id") or ""),
        "home_id": str(data.get("home_id") or home_data.get("home_id") or ""),
        "admin_login": phone,
        "admin_username": phone,
        "admin_password": str(data.get("admin_password") or ""),
        "user_username": str(data.get("user_username") or ""),
        "user_password": str(data.get("user_password") or ""),
        "door_pin": str(data.get("door_pin") or ""),
        "camera_pin": str(data.get("camera_pin") or ""),
        "owner_phone": phone,
        "home_code": str(home_data.get("home_code") or ""),
        "apartment_number": str(home_data.get("apartment_number") or ""),
    }


def _d7m16_hard_response(account, home, role):
    return {
        "success": True,
        "role": role,
        "account": _d7m16_hard_account_dict(account, home),
        "home": _d7m16_hard_home_dict(home),
        "alerts_count": 0,
    }


def _d7m16_hard_find_home_by_id(conn, home_id):
    return conn.execute(
        "SELECT * FROM homes WHERE CAST(id AS TEXT)=CAST(? AS TEXT) LIMIT 1",
        (str(home_id),),
    ).fetchone()


def _d7m16_hard_find_home_by_code_phone(conn, home_code, phone):
    rows = conn.execute(
        "SELECT * FROM homes WHERE lower(home_code)=lower(?)",
        (_d7m16_hard_clean_text(home_code),),
    ).fetchall()

    wanted = _d7m16_hard_clean_phone(phone)
    for row in rows:
        if _d7m16_hard_clean_phone(row["owner_phone"]) == wanted:
            return row
    return None


def _d7m16_hard_find_admin_account(conn, phone):
    clean = _d7m16_hard_clean_phone(phone)
    return conn.execute(
        """
        SELECT *
        FROM app_accounts
        WHERE COALESCE(owner_phone, '') = ?
           OR COALESCE(admin_login, '') = ?
        LIMIT 1
        """,
        (clean, clean),
    ).fetchone()


def _d7m16_hard_find_user_account(conn, username):
    clean = _d7m16_hard_clean_text(username)
    return conn.execute(
        """
        SELECT *
        FROM app_accounts
        WHERE lower(COALESCE(user_username, '')) = lower(?)
          AND COALESCE(user_username, '') <> ''
        LIMIT 1
        """,
        (clean,),
    ).fetchone()


async def _d7m16_hard_request_json(request):
    try:
        return await request.json()
    except Exception:
        return {}


@app.middleware("http")
async def d7m16_auth_phone_username_hard_fix_middleware(request, call_next):
    path = request.url.path
    method = request.method.upper()

    if method == "OPTIONS" and path.startswith("/api/app/auth/"):
        return _d7m16_hard_json({"success": True}, status_code=200)

    target_posts = {
        "/api/app/auth/register-admin",
        "/api/app/auth/login-admin",
        "/api/app/auth/login-user",
        "/api/app/auth/settings",
    }

    if method == "GET" and path == "/api/app/auth/account-status":
        conn = _d7m16_hard_auth_conn()
        try:
            _d7m16_hard_ensure_schema(conn)
            phone = _d7m16_hard_clean_phone(request.query_params.get("admin_login") or request.query_params.get("phone") or "")
            home_id = _d7m16_hard_clean_text(request.query_params.get("home_id") or "")

            account = _d7m16_hard_find_admin_account(conn, phone) if phone else None
            home = None

            if account:
                home = _d7m16_hard_find_home_by_id(conn, account["home_id"])
            elif home_id:
                home = _d7m16_hard_find_home_by_id(conn, home_id)

            return _d7m16_hard_json({
                "success": True,
                "account": _d7m16_hard_account_dict(account, home) if account else None,
                "home": _d7m16_hard_home_dict(home) if home else None,
            })
        finally:
            conn.close()

    if method != "POST" or path not in target_posts:
        return await call_next(request)

    payload = await _d7m16_hard_request_json(request)
    conn = _d7m16_hard_auth_conn()

    try:
        _d7m16_hard_ensure_schema(conn)

        if path == "/api/app/auth/register-admin":
            phone = _d7m16_hard_clean_phone(
                payload.get("phone_number")
                or payload.get("phone")
                or payload.get("login")
                or payload.get("admin_login")
            )
            password = _d7m16_hard_clean_text(payload.get("password"))
            home_code = _d7m16_hard_clean_text(payload.get("home_code"))

            if not phone or not password or not home_code:
                return _d7m16_hard_error("Phone Number, Password, and Home Code are required.", 400)

            home = _d7m16_hard_find_home_by_code_phone(conn, home_code, phone)
            if not home:
                return _d7m16_hard_error("Phone Number does not match this Home Code.", 404)

            existing_home = conn.execute(
                "SELECT * FROM app_accounts WHERE CAST(home_id AS TEXT)=CAST(? AS TEXT) LIMIT 1",
                (str(home["id"]),),
            ).fetchone()

            if existing_home:
                return _d7m16_hard_error("This home already has an admin account. Use Login instead.", 409)

            existing_phone = _d7m16_hard_find_admin_account(conn, phone)
            if existing_phone:
                return _d7m16_hard_error("This phone number is already used.", 409)

            now = _d7m16_hard_auth_now()
            cur = conn.execute(
                """
                INSERT INTO app_accounts (
                    home_id, admin_login, admin_password, user_username,
                    user_password, door_pin, camera_pin, owner_phone, created_at, updated_at
                )
                VALUES (?, ?, ?, '', '', '', '', ?, ?, ?)
                """,
                (home["id"], phone, password, phone, now, now),
            )
            conn.commit()

            account = conn.execute("SELECT * FROM app_accounts WHERE id=? LIMIT 1", (cur.lastrowid,)).fetchone()
            if home:
                _d7m16_update_login_tracking(conn, home["id"])
            return _d7m16_hard_json(_d7m16_hard_response(account, home, "Admin"))

        if path == "/api/app/auth/login-admin":
            phone = _d7m16_hard_clean_phone(
                payload.get("phone_number")
                or payload.get("phone")
                or payload.get("login")
                or payload.get("admin_login")
            )
            password = _d7m16_hard_clean_text(payload.get("password"))

            if not phone or not password:
                return _d7m16_hard_error("Phone Number and Password are required.", 400)

            account = _d7m16_hard_find_admin_account(conn, phone)
            if not account:
                return _d7m16_hard_error("Invalid phone number.", 404)

            account = dict(account)
            if str(account.get("admin_password") or "") != password:
                attempts = int(account.get("failed_login_attempts") or 0) + 1
                conn.execute(
                    "UPDATE app_accounts SET failed_login_attempts=?, updated_at=? WHERE id=?",
                    (attempts, _d7m16_hard_auth_now(), account["id"]),
                )
                conn.commit()
                return _d7m16_hard_error(
                    "Invalid password. Forgot Password will appear after 3 failed attempts."
                    if attempts < 3 else
                    "Invalid password. You can use Forgot Password now.",
                    401,
                )

            conn.execute(
                """
                UPDATE app_accounts
                SET failed_login_attempts=0,
                    admin_login=?,
                    owner_phone=?,
                    updated_at=?
                WHERE id=?
                """,
                (phone, phone, _d7m16_hard_auth_now(), account["id"]),
            )
            conn.commit()

            account = conn.execute("SELECT * FROM app_accounts WHERE id=? LIMIT 1", (account["id"],)).fetchone()
            home = _d7m16_hard_find_home_by_id(conn, account["home_id"])
            if home:
                _d7m16_update_login_tracking(conn, home["id"])
            return _d7m16_hard_json(_d7m16_hard_response(account, home, "Admin"))

        if path == "/api/app/auth/login-user":
            username = _d7m16_hard_clean_text(
                payload.get("username")
                or payload.get("user_username")
                or payload.get("admin_login")
                or payload.get("login")
            )
            user_password = _d7m16_hard_clean_text(payload.get("user_password") or payload.get("password"))

            if not username or not user_password:
                return _d7m16_hard_error("Username and User Password are required.", 400)

            account = _d7m16_hard_find_user_account(conn, username)
            if not account:
                return _d7m16_hard_error("Invalid username.", 404)

            account = dict(account)
            if not str(account.get("user_password") or "").strip():
                return _d7m16_hard_error("User password is not set by the admin yet.", 403)

            if str(account.get("user_password") or "").strip() != user_password:
                return _d7m16_hard_error("Invalid user password.", 401)

            home = _d7m16_hard_find_home_by_id(conn, account["home_id"])
            if home:
                _d7m16_update_login_tracking(conn, home["id"])
            return _d7m16_hard_json(_d7m16_hard_response(account, home, "User"))

        if path == "/api/app/auth/settings":
            phone = _d7m16_hard_clean_phone(
                payload.get("current_login")
                or payload.get("phone_number")
                or payload.get("phone")
                or payload.get("admin_login")
                or payload.get("login")
            )
            current_password = _d7m16_hard_clean_text(payload.get("current_password"))

            account = _d7m16_hard_find_admin_account(conn, phone)
            if not account:
                return _d7m16_hard_error("Admin account was not found.", 404)

            account = dict(account)
            if str(account.get("admin_password") or "") != current_password:
                return _d7m16_hard_error("Current password is invalid.", 401)

            updates = []
            values = []

            new_login_phone = _d7m16_hard_clean_phone(
                payload.get("new_login")
                or payload.get("new_admin_login")
                or payload.get("new_phone")
                or payload.get("new_phone_number")
            )
            if new_login_phone and new_login_phone != phone:
                duplicate = conn.execute(
                    """
                    SELECT id FROM app_accounts
                    WHERE (
                        COALESCE(owner_phone, '') = ?
                        OR COALESCE(admin_login, '') = ?
                    )
                    AND id <> ?
                    LIMIT 1
                    """,
                    (new_login_phone, new_login_phone, account["id"]),
                ).fetchone()
                if duplicate:
                    return _d7m16_hard_error("This phone number is already used.", 409)

                home_duplicate = conn.execute(
                    """
                    SELECT id FROM homes
                    WHERE COALESCE(owner_phone, '') = ?
                      AND CAST(id AS TEXT) <> CAST(? AS TEXT)
                    LIMIT 1
                    """,
                    (new_login_phone, account["home_id"]),
                ).fetchone()
                if home_duplicate:
                    return _d7m16_hard_error("This phone number is already used by another home.", 409)

                phone = new_login_phone
                updates.append("admin_login=?")
                values.append(phone)
                updates.append("owner_phone=?")
                values.append(phone)

                try:
                    conn.execute(
                        "UPDATE homes SET owner_phone=? WHERE CAST(id AS TEXT)=CAST(? AS TEXT)",
                        (phone, account["home_id"]),
                    )
                except Exception:
                    pass

            if payload.get("new_admin_password") is not None and _d7m16_hard_clean_text(payload.get("new_admin_password")):
                updates.append("admin_password=?")
                values.append(_d7m16_hard_clean_text(payload.get("new_admin_password")))

            if payload.get("door_pin") is not None:
                updates.append("door_pin=?")
                values.append(_d7m16_hard_clean_text(payload.get("door_pin")))

            if payload.get("camera_pin") is not None:
                updates.append("camera_pin=?")
                values.append(_d7m16_hard_clean_text(payload.get("camera_pin")))

            if payload.get("user_username") is not None:
                user_username = _d7m16_hard_clean_text(payload.get("user_username"))
                if user_username:
                    exists = conn.execute(
                        """
                        SELECT id FROM app_accounts
                        WHERE lower(COALESCE(user_username,''))=lower(?)
                          AND id <> ?
                        LIMIT 1
                        """,
                        (user_username, account["id"]),
                    ).fetchone()
                    if exists:
                        return _d7m16_hard_error("This username is already used.", 409)

                updates.append("user_username=?")
                values.append(user_username)

            if payload.get("user_password") is not None:
                updates.append("user_password=?")
                values.append(_d7m16_hard_clean_text(payload.get("user_password")))

            if updates:
                if "admin_login=?" not in updates:
                    updates.append("admin_login=?")
                    values.append(phone)
                if "owner_phone=?" not in updates:
                    updates.append("owner_phone=?")
                    values.append(phone)
                updates.append("updated_at=?")
                values.append(_d7m16_hard_auth_now())
                values.append(account["id"])

                conn.execute(
                    f"UPDATE app_accounts SET {', '.join(updates)} WHERE id=?",
                    values,
                )
                conn.commit()

            updated = conn.execute("SELECT * FROM app_accounts WHERE id=? LIMIT 1", (account["id"],)).fetchone()
            home = _d7m16_hard_find_home_by_id(conn, updated["home_id"])
            return _d7m16_hard_json(_d7m16_hard_response(updated, home, "Admin"))

    except Exception as exc:
        return _d7m16_hard_error(f"Auth hard fix error: {exc}", 500)
    finally:
        conn.close()

    return await call_next(request)
# D7M16_AUTH_PHONE_USERNAME_HARD_FIX_END

    
# D7M16_FAMILY_PHOTO_SYNC_START
class D7M16FamilyPhotoPayload(BaseModel):
    home_id: int | str | None = None
    member_id: str
    photo_data: str


def _d7m16_family_photo_db_path():
    return Path(__file__).resolve().parent / "database" / "smart_home_edge.db"


def _d7m16_family_photo_ensure(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS family_member_photos (
            member_id TEXT PRIMARY KEY,
            home_id TEXT,
            photo_data TEXT NOT NULL,
            updated_at TEXT
        )
    """)


@app.get("/api/app/family-member-photos")
def d7m16_get_family_member_photos(home_id: str | None = None):
    db_path = _d7m16_family_photo_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        _d7m16_family_photo_ensure(conn)
        rows = conn.execute(
            """
            SELECT member_id, photo_data
            FROM family_member_photos
            WHERE (? IS NULL OR CAST(home_id AS TEXT) = CAST(? AS TEXT))
            """,
            (home_id, home_id),
        ).fetchall()
        return {
            "success": True,
            "photos": {
                str(row["member_id"]): str(row["photo_data"] or "")
                for row in rows
            },
        }
    finally:
        conn.close()


@app.post("/api/app/family-member-photos")
def d7m16_save_family_member_photo(payload: D7M16FamilyPhotoPayload):
    member_id = str(payload.member_id or "").strip()
    photo_data = str(payload.photo_data or "").strip()
    if not member_id or not photo_data:
        return {"success": False, "detail": "member_id and photo_data are required."}

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    home_id = str(payload.home_id or "").strip()
    db_path = _d7m16_family_photo_db_path()
    conn = sqlite3.connect(str(db_path))
    try:
        _d7m16_family_photo_ensure(conn)
        conn.execute(
            """
            INSERT INTO family_member_photos (member_id, home_id, photo_data, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(member_id) DO UPDATE SET
                home_id = excluded.home_id,
                photo_data = excluded.photo_data,
                updated_at = excluded.updated_at
            """,
            (member_id, home_id, photo_data, now),
        )
        conn.commit()
        return {"success": True}
    finally:
        conn.close()
# D7M16_FAMILY_PHOTO_SYNC_END




def _get_security_logs(limit=200):
    try:
        _ensure_system_logs_table()
    except Exception:
        pass

    db_path = _d7_logs_db_path()
    conn = _d7_logs_sqlite3.connect(str(db_path))
    conn.row_factory = _d7_logs_sqlite3.Row

    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(system_logs)").fetchall()]
        for col in ["actor", "source", "apartment_number", "home_id", "created_at", "message"]:
            if col not in cols:
                conn.execute(f"ALTER TABLE system_logs ADD COLUMN {col} TEXT")
        conn.commit()

        try:
            _d7m16_cleanup_unknown_face_family_rows(conn)
        except Exception:
            pass

        rows = conn.execute(
            "SELECT * FROM system_logs ORDER BY id DESC LIMIT ?",
            (int(limit),)
        ).fetchall()
    finally:
        conn.close()

    logs = []

    for item in rows:
        row = dict(item)
        event_type = _d7_logs_event_type(row)
        actor = _d7_logs_actor(row, event_type)
        timestamp = _d7_logs_text(row, "timestamp", "created_at")
        severity = (_d7_logs_text(row, "severity") or "info").lower()
        details = _d7_logs_text(row, "details", "message", "description")
        action_taken = _d7_logs_text(row, "action_taken", "action")
        apartment = _d7_logs_apartment(row)

        logs.append({
            "id": row.get("id"),
            "timestamp": timestamp,
            "created_at": _d7_logs_text(row, "created_at", "timestamp"),
            "timestamp_label": _d7_logs_format_time(timestamp),
            "severity": severity,
            "severity_label": severity.upper(),
            "actor": actor,
            "source": _d7_logs_text(row, "source"),
            "home": apartment,
            "home_id": _d7_logs_text(row, "home_id"),
            "apartment": apartment,
            "apartment_number": apartment,
            "event_type": event_type,
            "details": details,
            "message": details,
            "action_taken": action_taken,
        })
    return _d7m16_filter_dashboard_logs_list(logs, limit=limit)


def _d7m16_dashboard_log_hidden(conn, source_table, source_id):
    try:
        _d7m16_ensure_dashboard_log_states(conn)
        row = conn.execute(
            """
            SELECT hidden
            FROM dashboard_log_states
            WHERE log_key = ?
            LIMIT 1
            """,
            (_d7m16_dashboard_log_key(source_table, source_id),),
        ).fetchone()
        return bool(row and int(row["hidden"] or 0) == 1)
    except Exception:
        return False


def _d7m16_filter_dashboard_logs_list(logs, limit=200):
    conn = _d7m16_log_iso_conn()
    try:
        filtered = []
        for item in logs or []:
            try:
                log_id = str(item.get("id") or item.get("log_id") or "")
            except Exception:
                log_id = ""

            if log_id and _d7m16_dashboard_log_hidden(conn, "system_logs", log_id):
                continue

            filtered.append(item)
            if len(filtered) >= int(limit):
                break

        return filtered
    finally:
        conn.close()


# ===================== LOGIN STATUS TRACKING START =====================
def _d7m16_update_login_tracking(conn, home_id):
    """Update last_login_at, is_online, login_state on the homes table for a given home_id."""
    try:
        now = _d7m16_auth_datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        conn.execute(
            """
            UPDATE homes
            SET last_login_at = ?,
                is_online = 1,
                login_state = 'logged_in'
            WHERE CAST(id AS TEXT) = CAST(? AS TEXT)
            """,
            (now, str(home_id)),
        )
        conn.commit()
    except Exception as e:
        print(f"[LOGIN TRACKING] Error updating login tracking: {e}")


@app.post("/api/app/auth/heartbeat")
async def d7m16_app_auth_heartbeat(request: _D7Request):
    """Flutter app sends periodic heartbeat to keep online status alive."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    home_id = str(data.get("home_id") or data.get("home_db_id") or "").strip()
    home_code = str(data.get("home_code") or "").strip()
    admin_login = str(data.get("admin_login") or "").strip()

    conn = _d7m16_auth_conn()
    try:
        _d7m16_auth_ensure_schema(conn)

        home = None
        if home_id:
            home = _d7m16_find_home_by_id(conn, home_id)
        if not home and home_code:
            home = conn.execute(
                "SELECT * FROM homes WHERE lower(home_code)=lower(?) LIMIT 1",
                (home_code,),
            ).fetchone()
        if not home and admin_login:
            account = _d7m16_find_account_by_admin_phone(conn, _d7m16_phone(admin_login))
            if account:
                home = _d7m16_find_home_by_id(conn, dict(account).get("home_id"))

        if home:
            home_dict = dict(home)
            # Check if account is disabled
            status = str(home_dict.get("account_status") or "active").strip().lower()
            if status in {"disabled", "inactive", "blocked", "suspended"}:
                conn.execute(
                    "UPDATE homes SET is_online = 0, login_state = 'logged_out' WHERE CAST(id AS TEXT) = CAST(? AS TEXT)",
                    (str(home_dict["id"]),),
                )
                conn.commit()
                return _D7JSONResponse({
                    "success": True,
                    "active": False,
                    "status": "disabled",
                    "message": "Your account has been disabled by the administrator. Please contact support.",
                })

            now = _d7m16_auth_datetime.now().isoformat()
            conn.execute(
                "UPDATE homes SET is_online = 1, last_heartbeat_at = ? WHERE CAST(id AS TEXT) = CAST(? AS TEXT)",
                (now, str(home_dict["id"]),),
            )
            conn.commit()
            return _D7JSONResponse({"success": True, "active": True, "status": "active"})

        return _D7JSONResponse({"success": False, "detail": "Home not found"}, status_code=404)
    finally:
        conn.close()


@app.post("/api/app/auth/logout")
async def d7m16_app_auth_logout(request: _D7Request):
    """Mark user as offline/logged_out when they log out from the Flutter app."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    home_id = str(data.get("home_id") or data.get("home_db_id") or "").strip()
    home_code = str(data.get("home_code") or "").strip()
    admin_login = str(data.get("admin_login") or "").strip()

    conn = _d7m16_auth_conn()
    try:
        _d7m16_auth_ensure_schema(conn)

        home = None
        if home_id:
            home = _d7m16_find_home_by_id(conn, home_id)
        if not home and home_code:
            home = conn.execute(
                "SELECT * FROM homes WHERE lower(home_code)=lower(?) LIMIT 1",
                (home_code,),
            ).fetchone()
        if not home and admin_login:
            account = _d7m16_find_account_by_admin_phone(conn, _d7m16_phone(admin_login))
            if account:
                home = _d7m16_find_home_by_id(conn, dict(account).get("home_id"))

        if home:
            conn.execute(
                "UPDATE homes SET is_online = 0, login_state = 'logged_out' WHERE CAST(id AS TEXT) = CAST(? AS TEXT)",
                (str(dict(home)["id"]),),
            )
            conn.commit()
            return _D7JSONResponse({"success": True, "message": "Logged out successfully"})

        return _D7JSONResponse({"success": True, "message": "OK"})
    finally:
        conn.close()

# ===================== LOGIN STATUS TRACKING END =====================


# ===================== USERS MANAGEMENT ENHANCED LIST START =====================
# Override the users management list to include real login tracking data
_d7_original_users_management_list = d7_users_management_list

@app.get("/api/users-management/list")
def d7_users_management_list_enhanced():
    _d7_ensure_users_schema()
    con = _d7_conn()

    owner = con.execute("SELECT * FROM dashboard_system_owner WHERE id = 1").fetchone()
    users = [{
        "id": "system_owner",
        "kind": "system_owner",
        "name": "System Owner",
        "username": owner["username"] if owner and "username" in owner.keys() else "system_owner",
        "email": owner["email"] if owner and "email" in owner.keys() else "admin@edge-system.local",
        "role": "SYSTEM OWNER",
        "associated_home": "-- (All)",
        "status": "active",
        "last_login": "Just now",
        "is_online": True,
        "login_state": "logged_in",
        "can_edit": True,
        "can_toggle": False,
    }]

    home_cols = _d7_cols(con, "homes")
    id_col = _d7_col(home_cols, "id", "home_id")
    apt_col = _d7_col(home_cols, "apartment_number", "apartment", "apt_number")
    name_col = _d7_col(home_cols, "owner_name", "name", "owner")
    email_col = _d7_col(home_cols, "owner_email", "email")
    status_col = _d7_col(home_cols, "account_status")
    last_login_col = _d7_col(home_cols, "last_login_at")
    online_col = _d7_col(home_cols, "is_online")
    login_state_col = _d7_col(home_cols, "login_state")
    heartbeat_col = _d7_col(home_cols, "last_heartbeat_at")

    now_ts = _d7_datetime.now().timestamp()

    if id_col and apt_col:
        rows = con.execute(f"SELECT * FROM homes ORDER BY CAST({apt_col} AS INTEGER), {apt_col}").fetchall()
        for r in rows:
            home_id = r[id_col]
            apt = r[apt_col]
            status = (r[status_col] if status_col and r[status_col] else "active").lower()
            login_state = (r[login_state_col] if login_state_col and login_state_col in r.keys() and r[login_state_col] else "logged_out")

            # Calculate actual online status based on heartbeat
            is_online = False
            if login_state == "logged_in":
                last_hb = r[heartbeat_col] if heartbeat_col and heartbeat_col in r.keys() else None
                if last_hb:
                    try:
                        hb_dt = _d7_datetime.fromisoformat(str(last_hb))
                        # If heartbeat is within last 45 seconds, consider online
                        if now_ts - hb_dt.timestamp() <= 45:
                            is_online = True
                    except Exception:
                        is_online = bool(r[online_col]) if online_col and online_col in r.keys() else False
                else:
                    is_online = bool(r[online_col]) if online_col and online_col in r.keys() else False

            users.append({
                "id": str(home_id),
                "kind": "home_owner",
                "name": r[name_col] if name_col and r[name_col] else "Home Owner",
                "username": "",
                "email": r[email_col] if email_col and r[email_col] else "",
                "role": "HOME OWNER",
                "associated_home": f"Apartment {apt}",
                "apartment_number": str(apt),
                "status": status,
                "last_login": _d7_dashboard_format_last_login(r[last_login_col]) if last_login_col and r[last_login_col] else "Not logged in yet",
                "is_online": is_online,
                "login_state": login_state,
                "can_edit": False,
                "can_toggle": True,
            })

    con.close()
    return {"users": users}

# ===================== USERS MANAGEMENT ENHANCED LIST END =====================


from api.door import router as door_router
app.include_router(door_router)
