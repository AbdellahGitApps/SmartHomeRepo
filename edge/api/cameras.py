from fastapi.templating import Jinja2Templates
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(
    directory=str(BASE_DIR / "dashboard" / "templates")
)
import time
import struct
import zlib
from fastapi import APIRouter, Request, Query, Depends, Response
from sqlalchemy.orm import Session
from database.connection.database import get_db
from fastapi.responses import HTMLResponse
import sqlite3
import re
from datetime import datetime
from pathlib import Path
from core_database import _d7_find_db
from database.models import Device, Home
router = APIRouter(tags=['cameras'])

@router.get("/cameras")
def cameras(request: Request, db: Session = Depends(get_db)):
    def _text(value):
        return str(value or "").strip()

    def _lower(value):
        return _text(value).lower()

    def _device_value(device, *names, default=""):
        for name in names:
            if hasattr(device, name):
                value = getattr(device, name)
                if value is not None and str(value).strip() != "":
                    return value
        return default

    def _is_camera_device(device):
        device_type = _lower(_device_value(device, "device_type", "type"))
        device_name = _lower(_device_value(device, "device_name", "name"))
        device_id = _lower(_device_value(device, "device_id", "id"))
        combined = f"{device_type} {device_name} {device_id}"

        if "energy" in device_type or "meter" in device_type:
            return False

        return any(key in combined for key in [
            "smart_door",
            "door_camera",
            "esp32_cam",
            "camera",
            "cam",
            "door"
        ])

    def _stream_url(device):
        for attr in ["camera_stream_url", "stream_url", "camera_stream", "camera_stream_url_url"]:
            value = _device_value(device, attr, default="")
            value = _text(value)
            if value and "not available" not in value.lower():
                return value
        return ""

    def _home_label(home, device):
        if home:
            apt = _device_value(home, "apartment_number", "apartment", default="")
            if _text(apt):
                return _text(apt)

        apt = _device_value(device, "apartment_number", "apartment", default="")
        if _text(apt):
            return _text(apt)

        home_id = _device_value(device, "home_id", "home", default="")
        return _text(home_id) if _text(home_id) else "--"

    devices_list = db.query(Device).all()
    homes_list = db.query(Home).all()
    home_map = {getattr(home, "id", None): home for home in homes_list}

    camera_items = []

    for device in devices_list:
        if not _is_camera_device(device):
            continue

        home = home_map.get(getattr(device, "home_id", None))
        status = _lower(_device_value(device, "status", "device_status", "connection_status", default="offline"))
        online = status == "online"
        stream = _stream_url(device)
        stream_available = bool(online and stream)

        camera_items.append({
            "name": _text(_device_value(device, "device_name", "name", default="Camera Device")),
            "device_type": _text(_device_value(device, "device_type", "type", default="smart_door")),
            "device_id": _text(_device_value(device, "device_id", "id", default="--")),
            "apartment_number": _home_label(home, device),
            "online": online,
            "status_label": "ONLINE" if online else "OFFLINE",
            "stream_url": stream,
            "stream_available": stream_available,
            "stream_label": "AVAILABLE" if stream_available else "NOT AVAILABLE",
            "last_seen": _text(_device_value(device, "last_seen", "last_seen_at", "updated_at", default="Not available yet")),
        })

    stats = {
        "total_cameras": len(camera_items),
        "online_cameras": sum(1 for item in camera_items if item["online"]),
        "streams_available": sum(1 for item in camera_items if item["stream_available"]),
    }

    return templates.TemplateResponse(
        request=request,
        name="cameras.html",
        context={
            "request": request,
            "cameras": camera_items,
            "stats": stats,
        },
    )

def _d7_camera_db_path():
    try:
        if "_d7_find_db" in globals():
            db = _d7_find_db()
            if db:
                return db
    except Exception:
        pass

    base = Path(__file__).resolve().parent
    candidates = [
        base / "database" / "smart_home_edge.db",
        base / "database" / "smart_home.db",
        base / "data" / "smart_home.db",
        base.parent / "data" / "smart_home.db",
    ]

    for p in candidates:
        if p.exists():
            return p

    for p in base.rglob("*.db"):
        if "model" not in str(p).lower() and "ai" not in str(p).lower():
            return p

    return base / "database" / "smart_home_edge.db"

def _d7_camera_conn():
    db = _d7_camera_db_path()
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    return conn

def _d7_camera_tables(conn):
    try:
        return {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    except Exception:
        return set()

def _d7_camera_text(value):
    return "" if value is None else str(value).strip()

def _d7_camera_lower(value):
    return _d7_camera_text(value).lower()

def _d7_camera_bool(value, default=True):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    if text in {"0", "false", "disabled", "off", "no"}:
        return False
    if text in {"1", "true", "enabled", "on", "yes"}:
        return True
    return default

def _d7_camera_home_code_from_apt(apt):
    digits = "".join(ch for ch in _d7_camera_text(apt) if ch.isdigit())
    if digits:
        return f"HOME-{int(digits):03d}"
    return ""

def _d7_camera_find_home(conn, home_id="", home_code="", apartment_number=""):
    if "homes" not in _d7_camera_tables(conn):
        return None

    rows = [dict(r) for r in conn.execute("SELECT * FROM homes ORDER BY id").fetchall()]

    home_id = _d7_camera_text(home_id)
    home_code = _d7_camera_text(home_code)
    apartment_number = _d7_camera_text(apartment_number)

    wanted = {x for x in [home_id, home_code, apartment_number] if x}
    extra = set()

    for item in list(wanted):
        digits = "".join(ch for ch in item if ch.isdigit())
        if digits:
            extra.add(str(int(digits)))
            extra.add(f"HOME-{int(digits):03d}")
            extra.add(f"HOME{int(digits):03d}")

    wanted |= extra
    wanted_lower = {x.lower() for x in wanted}

    for h in rows:
        values = {
            _d7_camera_text(h.get("id")),
            _d7_camera_text(h.get("home_id")),
            _d7_camera_text(h.get("home_code")),
            _d7_camera_text(h.get("apartment_number")),
            _d7_camera_home_code_from_apt(h.get("apartment_number")),
        }
        values_lower = {x.lower() for x in values if x}

        if wanted_lower and wanted_lower.intersection(values_lower):
            return h

    if rows:
        return rows[0]

    return None

def _d7_camera_is_camera_device(device):
    combined = " ".join([
        _d7_camera_text(device.get("device_type")),
        _d7_camera_text(device.get("type")),
        _d7_camera_text(device.get("device_name")),
        _d7_camera_text(device.get("name")),
        _d7_camera_text(device.get("device_id")),
    ]).lower()

    if any(x in combined for x in ["energy", "meter", "electric"]):
        return False

    return any(x in combined for x in ["smart_door", "door", "camera", "cam", "esp32"])

def _d7_camera_device_home_match(device, home):
    if not home:
        return True

    home_id = _d7_camera_text(home.get("id"))
    apt = _d7_camera_text(home.get("apartment_number"))
    home_code = _d7_camera_text(home.get("home_code"))
    device_home_id = _d7_camera_text(device.get("home_id"))
    device_apt = _d7_camera_text(device.get("apartment_number"))

    if home_id and device_home_id and home_id == device_home_id:
        return True
    if apt and device_apt and apt == device_apt:
        return True

    text = " ".join(str(v or "") for v in device.values()).upper()
    if home_code and home_code.upper() in text:
        return True

    generated = _d7_camera_home_code_from_apt(apt)
    if generated and generated.upper() in text:
        return True

    return False

def _d7_camera_stream_value(device, *keys):
    for key in keys:
        value = _d7_camera_text(device.get(key))
        if value and "not available" not in value.lower():
            return value
    return ""

def _d7_camera_format_time(value):
    value = _d7_camera_text(value)
    if not value:
        return ""
    return value.replace("T", " ").split(".")[0]

def _d7_camera_log_home_match(log, home):
    if not home:
        return True

    home_id = _d7_camera_text(home.get("id"))
    apt = _d7_camera_text(home.get("apartment_number"))
    home_code = _d7_camera_text(home.get("home_code"))

    log_home_id = _d7_camera_text(log.get("home_id"))
    log_apt = _d7_camera_text(log.get("apartment_number"))
    log_home = _d7_camera_text(log.get("home"))

    if home_id and log_home_id and home_id == log_home_id:
        return True
    if apt and log_apt and apt == log_apt:
        return True
    if apt and log_home:
        clean = log_home.replace("Apartment", "").strip()
        if clean == apt:
            return True

    text = " ".join(str(v or "") for v in log.values()).upper()
    if home_code and home_code.upper() in text:
        return True

    generated = _d7_camera_home_code_from_apt(apt)
    if generated and generated.upper() in text:
        return True

    return False

def _d7_camera_face_title(action, details, event_type):
    text = " ".join([action, details, event_type]).upper()

    if "UNKNOWN FACE DETECTED" in text:
        return "Unknown Face Detected", "Pending", "warning", False

    if "UNKNOWN OPEN ONCE" in text or "OPENED ONCE" in text:
        return "Unknown Face Opened Once", "Granted", "info", False

    if "UNKNOWN DENIED" in text or "ACCESS DENIED" in text:
        return "Unknown Face Denied", "Denied", "warning", False

    if "DOOR OPENED AFTER FAMILY ADD" in text or "AFTER FAMILY ADD" in text:
        return "Door Opened After Family Add", "Granted", "info", True

    if "FAMILY ACCESS GRANTED" in text:
        return "Family Member Access Granted", "Granted", "info", True

    return "", "", "info", False

def _d7_camera_extract_member(details):
    details = _d7_camera_text(details)

    patterns = [
        r"family member\s+(.+?)\s+added",
        r"family member\s+(.+?)\.",
        r"for family member\s+(.+?)\.",
    ]

    for pat in patterns:
        m = re.search(pat, details, flags=re.I)
        if m:
            return m.group(1).strip()

    return ""

@router.get("/api/app/cameras-real")
def d7m16_app_cameras_real(
    home_id: str = Query(default=""),
    home_code: str = Query(default=""),
    apartment_number: str = Query(default=""),
    admin_login: str = Query(default=""),
):
    conn = _d7_camera_conn()

    try:
        if "devices" not in _d7_camera_tables(conn):
            return {"success": True, "cameras": []}

        home = _d7_camera_find_home(conn, home_id, home_code, apartment_number)

        rows = [dict(r) for r in conn.execute("SELECT * FROM devices ORDER BY id").fetchall()]
        cameras = []

        for d in rows:
            if not _d7_camera_is_camera_device(d):
                continue

            if home and not _d7_camera_device_home_match(d, home):
                continue

            status_raw = _d7_camera_lower(d.get("status") or d.get("device_status") or d.get("connection_status"))
            online = status_raw == "online"
            enabled = _d7_camera_bool(d.get("enabled", d.get("is_enabled")), default=True)

            stream_url = _d7_camera_stream_value(d, "camera_stream_url", "camera_stream_url_url", "stream_url", "camera_stream")
            capture_url = _d7_camera_stream_value(d, "camera_capture_url", "camera_capture_url_url", "capture_url")

            live = bool(online and enabled)

            cameras.append({
                "id": _d7_camera_text(d.get("device_id") or d.get("id")),
                "raw_id": _d7_camera_text(d.get("id")),
                "name": _d7_camera_text(d.get("device_name") or d.get("name") or "Smart Door Camera"),
                "device_name": _d7_camera_text(d.get("device_name") or d.get("name") or "Smart Door Camera"),
                "device_type": _d7_camera_text(d.get("device_type") or d.get("type") or "smart_door"),
                "apartment_number": _d7_camera_text((home or {}).get("apartment_number") or d.get("apartment_number")),
                "home_id": _d7_camera_text(d.get("home_id") or (home or {}).get("id")),
                "online": online,
                "enabled": enabled,
                "live": live,
                "status": "Online" if online else "Offline",
                "status_label": "Live" if live else "Offline",
                "stream_url": stream_url,
                "capture_url": capture_url,
                "stream_available": bool(stream_url and live),
                "last_seen": _d7_camera_format_time(d.get("last_seen") or d.get("last_seen_at") or d.get("updated_at")),
            })

        return {"success": True, "cameras": cameras, "count": len(cameras)}
    finally:
        conn.close()

@router.get("/api/app/camera-face-events-real")
def d7m16_app_camera_face_events_real(
    home_id: str = Query(default=""),
    home_code: str = Query(default=""),
    apartment_number: str = Query(default=""),
    admin_login: str = Query(default=""),
    limit: int = Query(default=50),
):
    conn = _d7_camera_conn()

    try:
        if "system_logs" not in _d7_camera_tables(conn):
            return {"success": True, "events": []}

        home = _d7_camera_find_home(conn, home_id, home_code, apartment_number)
        rows = [dict(r) for r in conn.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT ?", (int(limit) * 4,)).fetchall()]
        events = []

        for r in rows:
            if home and not _d7_camera_log_home_match(r, home):
                continue

            action = _d7_camera_text(r.get("action_taken"))
            details = _d7_camera_text(r.get("details") or r.get("message"))
            event_type = _d7_camera_text(r.get("event_type"))
            title, status, severity, known = _d7_camera_face_title(action, details, event_type)

            if not title:
                continue

            # ?? ???? ??? ????? ??????? ???? ?? Face Events? ???? ????? ????????/????? ???.
            if action.upper() == "FAMILY MEMBER ADDED":
                continue

            events.append({
                "id": _d7_camera_text(r.get("id")),
                "title": title,
                "status": status,
                "severity": severity,
                "known": known,
                "camera": _d7_camera_text(r.get("device_name") or "Smart Door"),
                "member_name": _d7_camera_extract_member(details),
                "details": details,
                "action_taken": action,
                "timestamp": _d7_camera_format_time(r.get("created_at") or r.get("timestamp")),
                "source_table": "system_logs",
                "source_id": _d7_camera_text(r.get("id")),
            })

            if len(events) >= int(limit):
                break

        return {"success": True, "events": events, "count": len(events)}
    finally:
        conn.close()

def _d7_cam_final_db_path():
    try:
        if "_d7_find_db" in globals():
            found = _d7_find_db()
            if found:
                return found
    except Exception:
        pass

    base = Path(__file__).resolve().parent
    candidates = [
        base / "database" / "smart_home_edge.db",
        base / "database" / "smart_home.db",
        base.parent / "data" / "smart_home.db",
        base / "data" / "smart_home.db",
    ]

    for p in candidates:
        if p.exists():
            return p

    return base / "database" / "smart_home_edge.db"

def _d7_cam_final_conn():
    conn = sqlite3.connect(str(_d7_cam_final_db_path()))
    conn.row_factory = sqlite3.Row
    return conn

def _d7_cam_final_tables(conn):
    return {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

def _d7_cam_final_text(value):
    return "" if value is None else str(value).strip()

def _d7_cam_final_bool(value, default=True):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    if text in {"0", "false", "disabled", "off", "no"}:
        return False
    if text in {"1", "true", "enabled", "on", "yes"}:
        return True
    return default

def _d7_cam_final_home_code_from_apt(apt):
    digits = "".join(ch for ch in _d7_cam_final_text(apt) if ch.isdigit())
    if digits:
        return f"HOME-{int(digits):03d}"
    return ""

def _d7_cam_final_find_home(conn, home_id="", home_code="", apartment_number=""):
    if "homes" not in _d7_cam_final_tables(conn):
        return None

    rows = [dict(r) for r in conn.execute("SELECT * FROM homes ORDER BY id").fetchall()]

    wanted = {
        _d7_cam_final_text(home_id),
        _d7_cam_final_text(home_code),
        _d7_cam_final_text(apartment_number),
    }
    wanted = {x for x in wanted if x}

    extra = set()
    for item in wanted:
        digits = "".join(ch for ch in item if ch.isdigit())
        if digits:
            extra.add(str(int(digits)))
            extra.add(f"HOME-{int(digits):03d}")
            extra.add(f"HOME{int(digits):03d}")

    wanted_lower = {x.lower() for x in (wanted | extra)}

    for h in rows:
        values = {
            _d7_cam_final_text(h.get("id")),
            _d7_cam_final_text(h.get("home_id")),
            _d7_cam_final_text(h.get("home_code")),
            _d7_cam_final_text(h.get("apartment_number")),
            _d7_cam_final_home_code_from_apt(h.get("apartment_number")),
        }
        values_lower = {x.lower() for x in values if x}
        if wanted_lower and wanted_lower.intersection(values_lower):
            return h

    return rows[0] if rows else None

def _d7_cam_final_device_home_match(device, home):
    if not home:
        return True

    home_id = _d7_cam_final_text(home.get("id"))
    apt = _d7_cam_final_text(home.get("apartment_number"))
    home_code = _d7_cam_final_text(home.get("home_code"))

    if home_id and _d7_cam_final_text(device.get("home_id")) == home_id:
        return True

    if apt and _d7_cam_final_text(device.get("apartment_number")) == apt:
        return True

    text = " ".join(str(v or "") for v in device.values()).upper()
    generated = _d7_cam_final_home_code_from_apt(apt)

    if home_code and home_code.upper() in text:
        return True

    if generated and generated.upper() in text:
        return True

    return False

def _d7_cam_final_is_camera_device(device):
    combined = " ".join([
        _d7_cam_final_text(device.get("device_type")),
        _d7_cam_final_text(device.get("type")),
        _d7_cam_final_text(device.get("device_name")),
        _d7_cam_final_text(device.get("name")),
        _d7_cam_final_text(device.get("device_id")),
    ]).lower()

    if any(x in combined for x in ["energy", "meter", "electric"]):
        return False

    return any(x in combined for x in ["smart_door", "door", "camera", "cam", "esp32"])

def _d7_cam_final_stream_value(device):
    for key in ["camera_stream_url", "stream_url", "camera_stream", "camera_stream_url_url"]:
        value = _d7_cam_final_text(device.get(key))
        if value and "not available" not in value.lower():
            return value
    return ""

def _d7_cam_final_device_name_for_home(conn, home):
    if "devices" not in _d7_cam_final_tables(conn):
        return "Smart Door"

    rows = [dict(r) for r in conn.execute("SELECT * FROM devices ORDER BY id").fetchall()]

    for d in rows:
        if _d7_cam_final_is_camera_device(d) and _d7_cam_final_device_home_match(d, home):
            return _d7_cam_final_text(d.get("device_name") or d.get("name") or d.get("device_id")) or "Smart Door"

    return "Smart Door"

def _d7_cam_final_log_home_match(log, home):
    if not home:
        return True

    home_id = _d7_cam_final_text(home.get("id"))
    apt = _d7_cam_final_text(home.get("apartment_number"))
    home_code = _d7_cam_final_text(home.get("home_code"))

    if home_id and _d7_cam_final_text(log.get("home_id")) == home_id:
        return True

    log_apt = _d7_cam_final_text(log.get("apartment_number"))
    log_home = _d7_cam_final_text(log.get("home"))

    if apt and log_apt == apt:
        return True

    if apt and log_home:
        clean = log_home.replace("Apartment", "").strip()
        if clean == apt:
            return True

    text = " ".join(str(v or "") for v in log.values()).upper()
    generated = _d7_cam_final_home_code_from_apt(apt)

    if home_code and home_code.upper() in text:
        return True

    if generated and generated.upper() in text:
        return True

    return False

def _d7_cam_final_format_time(value):
    raw = _d7_cam_final_text(value)
    if not raw:
        return ""
        
    try:
        from datetime import datetime as _dt, timedelta as _td
        if "+" in raw or raw.endswith("Z"):
            dt = _dt.fromisoformat(raw.replace("Z", "+00:00"))
            local_dt = dt + _td(hours=3)
            return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
        
    return raw.replace("T", " ").split(".")[0]

def _d7_cam_final_extract_member(details):
    details = _d7_cam_final_text(details)

    patterns = [
        r"for family member\s+(.+?)\.",
        r"family member\s+(.+?)\.",
        r"family member\s+(.+?)\s+added",
    ]

    for pat in patterns:
        m = re.search(pat, details, flags=re.I)
        if m:
            return m.group(1).strip()

    return ""

def _d7_cam_final_png(width=960, height=420):
    tick = int(time.time())
    rows = []

    for y in range(height):
        row = bytearray()
        for x in range(width):
            base = (x * 255) // max(1, width - 1)
            wave = (tick * 12 + x // 12 + y // 10) % 80
            r = 24 + (base // 7)
            g = 34 + wave
            b = 54 + ((y * 120) // max(1, height - 1))
            if 40 < y < 88 and 42 < x < width - 42:
                r, g, b = 245, 190, 60
            if (x + tick * 18) % 180 < 12:
                r, g, b = 40, 160, 90
            row.extend([r % 256, g % 256, b % 256])
        rows.append(b"\x00" + bytes(row))

    raw = b"".join(rows)

    def chunk(kind, data):
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 6))
        + chunk(b"IEND", b"")
    )

@router.get("/api/app/fake-camera-frame/{camera_id}")
def d7m16_fake_camera_frame(camera_id: str):
    return Response(
        content=_d7_cam_final_png(),
        media_type="image/png",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )

@router.get("/api/app/cameras-real-v2")
def d7m16_app_cameras_real_v2(
    home_id: str = Query(default=""),
    home_code: str = Query(default=""),
    apartment_number: str = Query(default=""),
    admin_login: str = Query(default=""),
):
    conn = _d7_cam_final_conn()

    try:
        if "devices" not in _d7_cam_final_tables(conn):
            return {"success": True, "cameras": []}

        home = _d7_cam_final_find_home(conn, home_id, home_code, apartment_number)
        rows = [dict(r) for r in conn.execute("SELECT * FROM devices ORDER BY id").fetchall()]
        cameras = []

        for d in rows:
            if not _d7_cam_final_is_camera_device(d):
                continue

            if home and not _d7_cam_final_device_home_match(d, home):
                continue

            status_raw = _d7_cam_final_text(d.get("status") or d.get("device_status") or d.get("connection_status")).lower()
            online = status_raw == "online"
            enabled = _d7_cam_final_bool(d.get("enabled", d.get("is_enabled")), default=True)
            live = bool(online and enabled)

            device_key = _d7_cam_final_text(d.get("device_id") or d.get("id") or d.get("device_name") or "camera")
            real_stream = _d7_cam_final_stream_value(d)
            fake_stream = f"/api/app/fake-camera-frame/{device_key}"

            stream_url = real_stream or fake_stream
            is_fake = not bool(real_stream)

            cameras.append({
                "id": device_key,
                "raw_id": _d7_cam_final_text(d.get("id")),
                "name": _d7_cam_final_text(d.get("device_name") or d.get("name") or "Smart Door Camera"),
                "device_name": _d7_cam_final_text(d.get("device_name") or d.get("name") or "Smart Door Camera"),
                "device_type": _d7_cam_final_text(d.get("device_type") or d.get("type") or "smart_door"),
                "apartment_number": _d7_cam_final_text((home or {}).get("apartment_number") or d.get("apartment_number")),
                "home_id": _d7_cam_final_text(d.get("home_id") or (home or {}).get("id")),
                "online": online,
                "enabled": enabled,
                "live": live,
                "status": "Online" if online else "Offline",
                "status_label": "Live" if live else "Offline",
                "stream_url": stream_url,
                "capture_url": _d7_cam_final_text(d.get("camera_capture_url") or d.get("capture_url")),
                "stream_available": live and bool(stream_url),
                "is_fake_stream": is_fake,
                "last_seen": _d7_cam_final_format_time(d.get("last_seen") or d.get("last_seen_at") or d.get("updated_at")),
            })

        return {"success": True, "cameras": cameras, "count": len(cameras)}
    finally:
        conn.close()

@router.get("/api/app/camera-face-events-real-v2")
def d7m16_app_camera_face_events_real_v2(
    home_id: str = Query(default=""),
    home_code: str = Query(default=""),
    apartment_number: str = Query(default=""),
    admin_login: str = Query(default=""),
    limit: int = Query(default=50),
):
    conn = _d7_cam_final_conn()

    try:
        if "system_logs" not in _d7_cam_final_tables(conn):
            return {"success": True, "events": []}

        home = _d7_cam_final_find_home(conn, home_id, home_code, apartment_number)
        fallback_camera = _d7_cam_final_device_name_for_home(conn, home)
        rows = [dict(r) for r in conn.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT ?", (int(limit) * 5,)).fetchall()]
        events = []

        for r in rows:
            if home and not _d7_cam_final_log_home_match(r, home):
                continue

            action = _d7_cam_final_text(r.get("action_taken")).upper()
            details = _d7_cam_final_text(r.get("details") or r.get("message"))
            event_type = _d7_cam_final_text(r.get("event_type"))
            combined = f"{action} {details} {event_type}".upper()

            if "UNKNOWN FACE DETECTED" in combined:
                title = "Unknown Face Detected"
                status = "Pending"
                severity = "warning"
                known = False
            elif action == "FAMILY ACCESS GRANTED" or "FAMILY ACCESS GRANTED" in combined:
                title = "Family Face Recognized"
                status = "Granted"
                severity = "info"
                known = True
            else:
                continue

            camera_name = _d7_cam_final_text(r.get("device_name"))
            if not camera_name or camera_name.lower() in {"smart door", "main door"}:
                camera_name = fallback_camera

            events.append({
                "id": _d7_cam_final_text(r.get("id")),
                "title": title,
                "status": status,
                "severity": severity,
                "known": known,
                "camera": camera_name,
                "member_name": _d7_cam_final_extract_member(details),
                "details": details,
                "action_taken": action,
                "timestamp": _d7_cam_final_format_time(r.get("created_at") or r.get("timestamp")),
                "source_table": "system_logs",
                "source_id": _d7_cam_final_text(r.get("id")),
            })

            if len(events) >= int(limit):
                break

        return {"success": True, "events": events, "count": len(events)}
    finally:
        conn.close()
