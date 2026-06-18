from fastapi import APIRouter, Request, Depends, HTTPException
import sqlite3
import json
import asyncio
from datetime import datetime

from fastapi import Body as _D7RealBody
from fastapi import Body as _D7FinalBody
router = APIRouter()
@router.get("/api/app/door-access-logs")
def d7m16_app_door_access_logs(home_id=None, home_code=None, admin_login=None, limit: int = 50):
    from main import devices, status
    """
    Flutter Doors / Access Log.
    Returns door-only logs for the current home:
    - manual app door open
    - smart_door enable/disable/restart commands
    - known/unknown face door events
    - approve/deny/open-once door events
    It does NOT include general app settings, OTP, family, energy, or account logs.
    """
    import sqlite3 as _sqlite3
    from pathlib import Path as _Path
    from datetime import datetime as _datetime

    db_path = _Path(__file__).resolve().parent / "database" / "smart_home_edge.db"

    def as_dict(row):
        return dict(row) if row else None

    def cols(conn, table):
        try:
            return {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        except Exception:
            return set()

    def text(value):
        return str(value or "").strip()

    def lower(value):
        return text(value).lower()

    def pick(row, *names, default=""):
        if not row:
            return default
        for name in names:
            if name in row.keys():
                value = row[name]
                if value is not None and str(value).strip() != "":
                    return value
        return default

    def normalize_time(value):
        raw = text(value)
        if not raw:
            return ""

        try:
            from datetime import timedelta as _timedelta
            if "+" in raw or raw.endswith("Z"):
                dt = _datetime.fromisoformat(raw.replace("Z", "+00:00"))
                local_dt = dt + _timedelta(hours=3)
                return local_dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass

        raw = raw.replace("T", " ").replace("Z", "").strip()

        if "+" in raw:
            raw = raw.split("+", 1)[0].strip()

        if "." in raw:
            raw = raw.split(".", 1)[0].strip()

        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d, %I:%M:%S %p",
            "%Y-%m-%d %I:%M:%S %p",
            "%Y-%m-%d, %I:%M %p",
            "%Y-%m-%d %I:%M %p",
        ):
            try:
                return _datetime.strptime(raw, fmt).strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass

        return raw[:16]

    def is_door_related(event_type, action_taken, details, device_id="", device_name=""):
        joined = lower(f"{event_type} {action_taken} {details} {device_id} {device_name}")

        if "family access granted" in joined:
            return True

        if any(bad in joined for bad in [
            "energy",
            "app account",
            "app settings",
            "password recovery",
            "otp",
            "family",
            "user management",
            "system owner account",
        ]):
            return False

        return any(key in joined for key in [
            "door",
            "smart_door",
            "face",
            "unknown",
            "known",
            "approve",
            "deny",
            "open_once",
            "open-once",
            "mqtt enable",
            "mqtt disable",
            "mqtt restart",
            "door_open",
        ])

    def result_from(event_type, action_taken, details, status=""):
        joined = lower(f"{event_type} {action_taken} {details} {status}")

        if any(key in joined for key in ["denied", "deny", "rejected", "reject", "failed"]):
            return "accessDenied"

        if "mqtt disable" in joined or "device disabled" in joined or " disable " in f" {joined} ":
            return "accessDenied"

        return "accessGranted"

    def label_from(event_type, action_taken, details, result, status=""):
        joined = lower(f"{event_type} {action_taken} {details} {status}")

        if "mqtt enable" in joined or "device enabled" in joined:
            return "Device Enabled"

        if "mqtt disable" in joined or "device disabled" in joined or " disable " in f" {joined} ":
            return "Device Disabled"

        if "mqtt restart" in joined or "device restarted" in joined or " restart " in f" {joined} ":
            return "Device Restarted"

        if "app door lock" in joined or "manual_lock" in joined or "door locked" in joined:
            return "Door Locked"

        if (
            "app door open" in joined
            or "mqtt door open" in joined
            or "manual_open" in joined
            or "door opened" in joined
            or "open command" in joined
        ):
            return "Door Opened"

        if any(key in joined for key in ["denied", "deny", "rejected", "reject", "failed"]):
            return "Access Denied"

        return "Access Granted"

    def method_from(event_type, action_taken, details):
        joined = lower(f"{event_type} {action_taken} {details}")

        if "mqtt enable" in joined or "mqtt disable" in joined or "mqtt restart" in joined:
            return "Device Command"

        if "face" in joined or "recognition" in joined or "known" in joined or "unknown" in joined:
            return "AI Recognition"

        if "door" in joined or "open" in joined or "lock" in joined or "manual" in joined:
            return "Door Event"

        return "Door Event"

    def user_from(actor, source, details, result):
        raw = text(actor)
        src = text(source)

        if raw:
            return raw

        if src:
            if src == "flutter_app":
                return "Admin App"
            return src

        if result == "accessDenied":
            return "Unknown Person"

        return "Admin App"

    conn = _sqlite3.connect(db_path)
    conn.row_factory = _sqlite3.Row

    try:
        tables = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

        if "homes" not in tables:
            return {"success": False, "items": [], "count": 0, "message": "homes table not found"}

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

        if home is None:
            return {"success": False, "items": [], "count": 0, "message": "home not found"}

        home_dict = as_dict(home)
        resolved_home_id = str(home_dict.get("id"))
        apartment_number = text(home_dict.get("apartment_number"))

        door_device_ids = set()
        door_device_names = set()

        if "devices" in tables:
            dcols = cols(conn, "devices")
            where_parts = []
            params = []

            if "home_id" in dcols:
                where_parts.append("CAST(home_id AS TEXT) = CAST(? AS TEXT)")
                params.append(resolved_home_id)

            if "apartment_number" in dcols and apartment_number:
                where_parts.append("CAST(apartment_number AS TEXT) = CAST(? AS TEXT)")
                params.append(apartment_number)

            if where_parts:
                devices = conn.execute(
                    f"SELECT * FROM devices WHERE {' OR '.join(where_parts)}",
                    params,
                ).fetchall()

                for d in devices:
                    dtype = lower(pick(d, "device_type", "type"))
                    dname = text(pick(d, "device_name", "name"))
                    did = text(pick(d, "device_id", "id"))

                    if "door" in dtype or "door" in lower(dname) or "door" in lower(did):
                        if did:
                            door_device_ids.add(did)
                        if dname:
                            door_device_names.add(dname)

        items = []

        def add_item(timestamp, event_type, details, action_taken="", actor="", source="", device_id="", device_name="", status=""):
            if not is_door_related(event_type, action_taken, details, device_id, device_name):
                return

            result = result_from(event_type, action_taken, details, status)
            method_label = method_from(event_type, action_taken, details)
            user = user_from(actor, source, details, result)

            door_label = text(device_name)
            if not door_label and door_device_names:
                door_label = sorted(door_device_names)[0]
            if not door_label:
                door_label = "Main Door"

            result_label = label_from(event_type, action_taken, details, result, status)

            items.append({
                "doorKey": door_label,
                "door": door_label,
                "userKey": None if user == "Unknown Person" else "user",
                "user": user,
                "method": "aiRecognition" if method_label == "AI Recognition" else "manualApp",
                "methodLabel": method_label,
                "result": result,
                "resultLabel": result_label,
                "time": normalize_time(timestamp),
                "timestamp": text(timestamp),
                "details": text(details),
                "action_taken": text(action_taken),
            })

        # door_events table
        if "door_events" in tables:
            c = cols(conn, "door_events")
            where = []
            params = []

            if "home_id" in c:
                where.append("CAST(home_id AS TEXT) = CAST(? AS TEXT)")
                params.append(resolved_home_id)

            if "apartment_number" in c and apartment_number:
                where.append("CAST(apartment_number AS TEXT) = CAST(? AS TEXT)")
                params.append(apartment_number)

            if where:
                rows = conn.execute(
                    f"SELECT * FROM door_events WHERE {' OR '.join(where)} ORDER BY id DESC LIMIT ?",
                    [*params, max(limit * 3, 100)],
                ).fetchall()

                for r in rows:
                    add_item(
                        timestamp=pick(r, "timestamp", "created_at"),
                        event_type=pick(r, "event_type", default="Door Event"),
                        details=pick(r, "details", "message", default="Door event"),
                        action_taken=pick(r, "action_taken", default=""),
                        actor=pick(r, "actor", "opened_by", default=""),
                        source=pick(r, "source", default=""),
                        device_id=pick(r, "device_id", default=""),
                        device_name=pick(r, "device_name", default=""),
                        status=pick(r, "status", default=""),
                    )

        # system_logs table
        if "system_logs" in tables:
            c = cols(conn, "system_logs")
            rows = conn.execute(
                "SELECT * FROM system_logs ORDER BY id DESC LIMIT ?",
                (max(limit * 5, 200),),
            ).fetchall()

            for r in rows:
                row_home = text(pick(r, "home", "home_id", default=""))
                row_apt = text(pick(r, "apartment_number", default=""))
                details = text(pick(r, "details", "message", default=""))
                action_taken = text(pick(r, "action_taken", default=""))
                event_type = text(pick(r, "event_type", default=""))
                device_id = text(pick(r, "device_id", default=""))
                device_name = text(pick(r, "device_name", default=""))

                home_match = False

                if row_apt and apartment_number and row_apt == apartment_number:
                    home_match = True

                if row_home and row_home in {resolved_home_id, apartment_number, home_dict.get("home_code"), f"Apartment {apartment_number}"}:
                    home_match = True

                if device_id and device_id in door_device_ids:
                    home_match = True

                if any(did and did in details for did in door_device_ids):
                    home_match = True

                if apartment_number and f"Apartment {apartment_number}" in details:
                    home_match = True

                if not home_match:
                    continue

                add_item(
                    timestamp=pick(r, "timestamp", "created_at"),
                    event_type=event_type,
                    details=details,
                    action_taken=action_taken,
                    actor=pick(r, "actor", default=""),
                    source=pick(r, "source", default=""),
                    device_id=device_id,
                    device_name=device_name,
                    status=pick(r, "status", default=""),
                )

        seen = set()
        unique_items = []

        for item in items:
            key = (
                item.get("time"),
                item.get("door"),
                item.get("methodLabel"),
                item.get("result"),
                item.get("details"),
                item.get("action_taken"),
            )

            if key in seen:
                continue

            seen.add(key)
            unique_items.append(item)

        unique_items = unique_items[:limit]

        return {
            "success": True,
            "home_id": resolved_home_id,
            "apartment_number": apartment_number,
            "count": len(unique_items),
            "items": unique_items,
        }

    finally:
        conn.close()

@router.post("/api/app/door-manual-action")
async def d7m16_app_door_manual_action(request: Request):
    import sqlite3 as _sqlite3
    from pathlib import Path as _Path
    from datetime import datetime as _datetime

    data = await request.json()

    try:
        from core_database import get_database_path
        db_path = get_database_path()
    except Exception:
        db_path = _Path(__file__).resolve().parent / "database" / "smart_home_edge.db"
    now = _datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    home_id = str(data.get("home_id") or "").strip()
    home_code = str(data.get("home_code") or "").strip()
    action = str(data.get("action") or "open").strip().lower()
    device_id = str(data.get("device_id") or "").strip()
    device_name = str(data.get("device_name") or "Main Door").strip()
    actor = str(data.get("actor") or "Admin App").strip()
    source = str(data.get("source") or "flutter_app").strip()
    reason = str(data.get("reason") or f"manual_{action}_from_flutter").strip()

    if action not in {"open", "lock"}:
        action = "open"

    conn = _sqlite3.connect(db_path)
    conn.row_factory = _sqlite3.Row

    try:
        cur = conn.cursor()

        home = None

        if home_id:
            home = cur.execute(
                "SELECT * FROM homes WHERE CAST(id AS TEXT) = CAST(? AS TEXT) LIMIT 1",
                (home_id,),
            ).fetchone()

        if home is None and home_code:
            home = cur.execute(
                "SELECT * FROM homes WHERE upper(home_code) = upper(?) LIMIT 1",
                (home_code,),
            ).fetchone()

        if home is None:
            return {"success": False, "message": "Home not found."}

        resolved_home_id = str(home["id"])
        apartment_number = str(home["apartment_number"] or resolved_home_id)

        door_status = "unlocked" if action == "open" else "locked"
        event_type = "manual_open" if action == "open" else "manual_lock"
        action_taken = "APP DOOR OPEN" if action == "open" else "APP DOOR LOCK"
        details = (
            f"Manual door open from Flutter App for Apartment {apartment_number}."
            if action == "open"
            else f"Manual door lock from Flutter App for Apartment {apartment_number}."
        )

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

        door_cols = {
            row["name"]
            for row in cur.execute("PRAGMA table_info(door_events)").fetchall()
        }

        for col, col_type in {
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
            "timestamp": "TEXT",
            "created_at": "TEXT",
        }.items():
            if col not in door_cols:
                cur.execute(f"ALTER TABLE door_events ADD COLUMN {col} {col_type}")

        cur.execute("""
            INSERT INTO door_events (
                home_id,
                apartment_number,
                device_id,
                device_name,
                status,
                event_type,
                details,
                source,
                reason,
                actor,
                action_taken,
                timestamp,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            resolved_home_id,
            apartment_number,
            device_id,
            device_name,
            door_status,
            event_type,
            details,
            source,
            reason,
            actor,
            action_taken,
            now,
            now,
        ))

        tables = {
            row["name"]
            for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }

        if "app_home_demo_state" in tables:
            state_cols = {
                row["name"]
                for row in cur.execute("PRAGMA table_info(app_home_demo_state)").fetchall()
            }

            updates = []
            values = []

            if "door_status" in state_cols:
                updates.append("door_status = ?")
                values.append(door_status)

            if "door_label" in state_cols:
                updates.append("door_label = ?")
                values.append(device_name or "Main Door")

            if "door_last_event" in state_cols:
                updates.append("door_last_event = ?")
                values.append(now)

            if "updated_at" in state_cols:
                updates.append("updated_at = ?")
                values.append(now)

            if updates:
                values.append(resolved_home_id)
                cur.execute(
                    f"UPDATE app_home_demo_state SET {', '.join(updates)} WHERE CAST(home_id AS TEXT) = CAST(? AS TEXT)",
                    values,
                )

        cur.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                event_type TEXT,
                severity TEXT,
                actor TEXT,
                source TEXT,
                apartment_number TEXT,
                home TEXT,
                action_taken TEXT,
                details TEXT,
                status TEXT,
                device_id TEXT,
                device_name TEXT,
                created_at TEXT
            )
        """)

        log_cols = {
            row["name"]
            for row in cur.execute("PRAGMA table_info(system_logs)").fetchall()
        }

        log_data = {
            "timestamp": now,
            "created_at": now,
            "event_type": "Smart Door Command",
            "severity": "info",
            "actor": actor or "Admin App",
            "source": source,
            "apartment_number": apartment_number,
            "home": resolved_home_id,
            "action_taken": action_taken,
            "details": details,
            "status": "sent",
            "device_id": device_id,
            "device_name": device_name,
        }

        insert_cols = [col for col in log_data if col in log_cols]

        if insert_cols:
            cur.execute(
                f"INSERT INTO system_logs ({', '.join(insert_cols)}) VALUES ({', '.join(['?'] * len(insert_cols))})",
                [log_data[col] for col in insert_cols],
            )

        conn.commit()

        return {
            "success": True,
            "home_id": resolved_home_id,
            "apartment_number": apartment_number,
            "device_id": device_id,
            "device_name": device_name,
            "action": action,
            "door_status": door_status,
            "action_taken": action_taken,
            "timestamp": now,
        }

    finally:
        conn.close()

def _d7real_result_label(action, event_type="", details="", severity=""):
    from main import _d7real_s
    text = " ".join([_d7real_s(action), _d7real_s(event_type), _d7real_s(details)]).lower()

    if "door lock" in text or "app door lock" in text or "manual door lock" in text:
        return "Door Locked"
    if "door open" in text or "app door open" in text or "mqtt door open" in text or "open command" in text:
        return "Door Opened"
    if "mqtt enable" in text or " enable" in text:
        return "Device Enabled"
    if "mqtt disable" in text or " disable" in text:
        return "Device Disabled"
    if "mqtt restart" in text or " restart" in text:
        return "Device Restarted"
    if "denied" in text or _d7real_s(severity).lower() in {"warning", "error", "critical"}:
        return "Access Denied"
    return "Access Granted"

def _d7real_log_to_app_item(row):
    from main import _d7real_time, _d7real_val
    timestamp = _d7real_val(row, "timestamp", "created_at", "created", "time", default="")
    action = _d7real_val(row, "action_taken", "action", default="")
    event_type = _d7real_val(row, "event_type", "type", default="Door Event")
    details = _d7real_val(row, "details", "message", default="")
    actor = _d7real_val(row, "actor", default="Admin App")
    severity = _d7real_val(row, "severity", default="info")
    label = _d7real_result_label(action, event_type, details, severity)

    device_name = _d7real_val(row, "device_name", "door", "device_id", default="")
    if not device_name:
        device_name = "Door"

    return {
        "source_table": "system_logs",
        "source_id": _d7real_val(row, "id", default=""),
        "id": _d7real_val(row, "id", default=""),
        "timestamp": timestamp,
        "time": _d7real_time(timestamp),
        "time_label": _d7real_time(timestamp),
        "doorKey": device_name,
        "door": device_name,
        "userKey": actor,
        "user": actor,
        "actor": actor,
        "method": "Door Event",
        "methodLabel": "Door Event",
        "result": label,
        "resultLabel": label,
        "event_type": event_type,
        "action_taken": action,
        "details": details,
        "severity": severity,
    }

def _d7real_door_where():
    return """(
        LOWER(COALESCE(event_type,'')) LIKE '%door%'
        OR LOWER(COALESCE(event_type,'')) LIKE '%smart door%'
        OR LOWER(COALESCE(action_taken,'')) LIKE '%door%'
        OR LOWER(COALESCE(details,'')) LIKE '%door%'
        OR LOWER(COALESCE(action_taken,'')) LIKE '%mqtt enable%'
        OR LOWER(COALESCE(action_taken,'')) LIKE '%mqtt disable%'
        OR LOWER(COALESCE(action_taken,'')) LIKE '%mqtt restart%'
    )"""

@router.get("/api/app/door-access-logs-real")
def d7real_app_door_access_logs_real(
    home_id: str = "",
    home_code: str = "",
    admin_login: str = "",
    limit: int = 80,
):
    from main import _d7real_conn, _d7real_home_match_sql, _d7real_resolve_home
    conn = _d7real_conn()
    try:
        home = _d7real_resolve_home(conn, home_id, home_code, admin_login)
        home_sql, home_params = _d7real_home_match_sql(conn, home)

        sql = f"""
            SELECT *
            FROM system_logs
            WHERE {_d7real_door_where()}
            {home_sql}
            ORDER BY COALESCE(timestamp, '') DESC, id DESC
            LIMIT ?
        """
        rows = conn.execute(sql, [*home_params, limit]).fetchall()
        items = [_d7real_log_to_app_item(r) for r in rows]
        return {"success": True, "count": len(items), "items": items}
    finally:
        conn.close()

@router.delete("/api/app/door-access-logs/{source_table}/{source_id}")
def d7real_delete_app_door_access_log(source_table: str, source_id: int):
    from main import _D7RealHTTPException, _d7real_conn
    if source_table not in {"system_logs"}:
        raise _D7RealHTTPException(status_code=400, detail="Unsupported log source.")

    conn = _d7real_conn()
    try:
        cur = conn.execute("DELETE FROM system_logs WHERE id = ? AND " + _d7real_door_where(), (source_id,))
        conn.commit()
        return {"success": True, "deleted": cur.rowcount}
    finally:
        conn.close()

@router.delete("/api/app/door-access-logs/bulk")
def d7real_delete_app_door_access_logs_bulk(payload: dict = _D7RealBody(default_factory=dict)):
    from main import _D7RealBody, _d7real_conn, _d7real_home_match_sql, _d7real_resolve_home, _d7real_s
    date_filter = _d7real_s(payload.get("date", "all")).lower()
    actor_filter = _d7real_s(payload.get("actor", "all"))
    home_id = _d7real_s(payload.get("home_id", ""))
    home_code = _d7real_s(payload.get("home_code", ""))
    admin_login = _d7real_s(payload.get("admin_login", ""))

    conn = _d7real_conn()
    try:
        home = _d7real_resolve_home(conn, home_id, home_code, admin_login)
        home_sql, home_params = _d7real_home_match_sql(conn, home)

        where = [_d7real_door_where()]
        params = list(home_params)

        if home_sql:
            where.append(home_sql.replace(" AND ", "", 1))

        if date_filter and date_filter != "all":
            where.append("substr(COALESCE(timestamp,''), 1, 10) = ?")
            params.append(date_filter)

        if actor_filter and actor_filter.lower() != "all":
            where.append("COALESCE(actor,'') = ?")
            params.append(actor_filter)

        sql = "DELETE FROM system_logs WHERE " + " AND ".join(f"({w})" for w in where)
        cur = conn.execute(sql, params)
        conn.commit()
        return {"success": True, "deleted": cur.rowcount}
    finally:
        conn.close()

def _d7final_home_filter(conn, home):
    from main import _d7final_cols, _d7final_home_values
    values = _d7final_home_values(home)
    cols = _d7final_cols(conn, "system_logs")
    clauses = []
    params = []

    if values["home_id"] and "home_id" in cols:
        clauses.append("CAST(home_id AS TEXT) = ?")
        params.append(values["home_id"])

    if values["apartment"]:
        for col in ["apartment_number", "home", "scope", "actor_scope"]:
            if col in cols:
                clauses.append(f"CAST({col} AS TEXT) = ?")
                params.append(values["apartment"])

    if not clauses:
        return "", []

    return " AND (" + " OR ".join(clauses) + ")", params

def _d7final_text(row):
    from main import _d7final_s, _d7final_val
    return " ".join([
        _d7final_s(_d7final_val(row, "event_type")),
        _d7final_s(_d7final_val(row, "action_taken")),
        _d7final_s(_d7final_val(row, "details")),
        _d7final_s(_d7final_val(row, "device_id")),
        _d7final_s(_d7final_val(row, "device_name")),
    ]).lower()

def _d7final_is_energy(row):
    text = _d7final_text(row)
    return "energy" in text or "meter" in text or "power" in text

def _d7final_is_door(row):
    from main import _d7final_s, _d7final_val
    # D7M16_DOORLOG_SKIP_PENDING_UNKNOWN_START
    pending_action = _d7final_s(_d7final_val(row, "action_taken")).upper()
    if pending_action == "UNKNOWN FACE DETECTED":
        return False
    # D7M16_DOORLOG_SKIP_PENDING_UNKNOWN_END
    text = _d7final_text(row)
    action = _d7final_s(_d7final_val(row, "action_taken")).upper()
    event = _d7final_s(_d7final_val(row, "event_type")).lower()
    details = _d7final_s(_d7final_val(row, "details")).lower()

    if _d7final_is_energy(row):
        return False

    if action == "FAMILY MEMBER ADDED":
        return False

    if "family management" in event and action != "DOOR OPENED AFTER FAMILY ADD":
        return False

    if action in {
        "UNKNOWN FACE DETECTED",
        "UNKNOWN OPEN ONCE",
        "UNKNOWN DENIED",
        "DOOR OPENED AFTER FAMILY ADD",
        "FAMILY ACCESS GRANTED",
        "APP DOOR OPEN",
        "APP DOOR LOCK",
        "MQTT ENABLE",
        "MQTT DISABLE",
        "MQTT RESTART",
    }:
        return True

    return any(key in text for key in [
        "door", "smart door", "camera", "unknown face", "access denied",
        "access granted", "manual_open", "manual_lock", "app door"
    ])

def _d7final_actor(row):
    from main import _d7final_s, _d7final_val
    raw = _d7final_s(_d7final_val(row, "actor", "source")).strip()
    text = f"{raw} {_d7final_text(row)}".lower()
    action = _d7final_s(_d7final_val(row, "action_taken")).upper()

    if raw in {"Admin App", "System Owner", "Server"}:
        return raw

    if action == "FAMILY ACCESS GRANTED":
        return "Server"

    if "system owner" in text or "mqtt " in text:
        return "System Owner"

    if "admin app" in text or "flutter" in text or "app door" in text:
        return "Admin App"

    if "server" in text or "auto" in text:
        return "Server"

    if "unknown" in text:
        return "Admin App"

    return "Admin App" if raw else "Server"

def _d7final_result_label(row):
    from main import _d7final_s, _d7final_val
    text = _d7final_text(row)
    severity = _d7final_s(_d7final_val(row, "severity")).lower()
    action = _d7final_s(_d7final_val(row, "action_taken")).upper()
    event = _d7final_s(_d7final_val(row, "event_type")).lower()
    details = _d7final_s(_d7final_val(row, "details")).lower()

    if action == "UNKNOWN FACE DETECTED":
        return "Unknown Face Detected"

    if action == "UNKNOWN OPEN ONCE":
        return "Unknown Face Opened Once"

    if action == "UNKNOWN DENIED":
        return "Unknown Face Denied"

    if action == "DOOR OPENED AFTER FAMILY ADD":
        return "Door Opened After Family Add"

    if action == "FAMILY ACCESS GRANTED":
        return "Family Member Access Granted"

    if action == "APP DOOR OPEN" or "manual door open" in details or "manual_open" in text:
        return "Manual Door Opened"

    if action == "APP DOOR LOCK" or "manual door lock" in details or "manual_lock" in text:
        return "Manual Door Locked"

    if "restart" in text:
        return "Device Restarted"

    if "enable" in text:
        return "Device Enabled"

    if "disable" in text or "offline" in text or "fault" in text:
        return "Device Disabled"

    if "unknown face" in text and not any(x in text for x in ["denied", "opened once", "after family add", "granted"]):
        return "Unknown Face Detected"

    if "lock" in text and "unlock" not in text:
        return "Door Locked"

    if "deny" in text or "denied" in text or severity in {"warning", "error", "critical"}:
        return "Access Denied"

    if "open" in text or "granted" in text:
        return "Door Opened"

    return "Access Granted"

def _d7final_result_key(label):
    clean = str(label or "").strip().lower()

    if clean in {
        "door opened",
        "manual door opened",
        "unknown face opened once",
        "unknown face opened one",
        "door opened after family add",
        "family member access granted",
        "device enabled",
        "access granted",
    }:
        return "accessGranted"

    if clean in {
        "unknown face denied",
        "access denied",
        "manual door locked",
        "door locked",
        "device disabled",
    }:
        return "accessDenied"

    if clean in {
        "device restarted",
        "unknown face detected",
    }:
        return "pendingDecision"

    if "opened once" in clean or "after family add" in clean or "family member access" in clean:
        return "accessGranted"

    if "denied" in clean or "locked" in clean or "disabled" in clean:
        return "accessDenied"

    return "pendingDecision"

def _d7final_log_item(row):
    from main import _d7final_s, _d7final_time_label, _d7final_val
    label = _d7final_result_label(row)
    ts = _d7final_val(row, "timestamp", "created_at")
    actor = _d7final_actor(row)
    device_name = _d7final_s(_d7final_val(row, "device_name", "device_id")) or "Main Door"
    method_label = "Device Command" if "mqtt" in _d7final_text(row) else ("Pending Decision" if label == "Unknown Face Detected" else "Door Event")

    return {
        "id": _d7final_s(_d7final_val(row, "id")),
        "source_table": "system_logs",
        "source_id": _d7final_s(_d7final_val(row, "id")),
        "timestamp": ts,
        "time": _d7final_time_label(ts),
        "time_label": _d7final_time_label(ts),
        "door": device_name,
        "doorKey": device_name,
        "user": actor,
        "userKey": actor,
        "actor": actor,
        "method": method_label,
        "methodLabel": method_label,
        "result": _d7final_result_key(label),
        "resultLabel": label,
        "event_type": _d7final_val(row, "event_type"),
        "action_taken": _d7final_val(row, "action_taken"),
        "details": _d7final_val(row, "details"),
        "severity": _d7final_val(row, "severity", default="INFO"),
    }

def _d7m16_door_log_hidden(conn, source_table, source_id, viewer_scope):
    from main import _d7m16_door_state_key, _d7m16_ensure_door_log_states
    _d7m16_ensure_door_log_states(conn)
    state_key = _d7m16_door_state_key(source_table, source_id, viewer_scope)
    row = conn.execute(
        "SELECT hidden FROM app_door_log_states WHERE state_key = ? LIMIT 1",
        (state_key,),
    ).fetchone()
    return bool(row and int(row["hidden"] or 0) == 1)

@router.get("/api/app/door-access-logs-final")
def d7final_get_door_logs(home_id: str = "", home_code: str = "", admin_login: str = "", viewer_role: str = "admin", limit: int = 80):
    from main import _d7final_conn, _d7final_ensure_system_logs, _d7final_find_home, _d7final_s, _d7final_val, _d7m16_viewer_scope
    conn = _d7final_conn()
    try:
        _d7final_ensure_system_logs(conn)
        home = _d7final_find_home(conn, home_id, home_code, admin_login)
        home_sql, params = _d7final_home_filter(conn, home)
        viewer_scope = _d7m16_viewer_scope(home, viewer_role, admin_login)

        rows = conn.execute(
            f"SELECT * FROM system_logs WHERE 1=1 {home_sql} ORDER BY COALESCE(timestamp, created_at, '') DESC, id DESC LIMIT ?",
            [*params, int(limit) * 3],
        ).fetchall()

        items = []
        for row in rows:
            if not _d7final_is_door(row):
                continue

            action = _d7final_s(_d7final_val(row, "action_taken")).upper()
            row_id = _d7final_s(_d7final_val(row, "id"))

            if _d7m16_door_log_hidden(conn, "system_logs", row_id, viewer_scope):
                continue

            items.append(_d7final_log_item(row))

            if len(items) >= int(limit):
                break

        return {"success": True, "count": len(items), "items": items}
    finally:
        conn.close()

@router.delete("/api/app/door-access-logs-final/{source_table}/{source_id}")
def d7final_delete_door_log(
    source_table: str,
    source_id: int,
    home_id: str = "",
    home_code: str = "",
    admin_login: str = "",
    viewer_role: str = "admin",
):
    from main import _D7FinalHTTPException, _d7final_conn, _d7final_find_home, _d7final_home_values, _d7m16_hide_door_log_for_viewer, _d7m16_viewer_scope
    if source_table != "system_logs":
        raise _D7FinalHTTPException(status_code=400, detail="Unsupported log source.")

    conn = _d7final_conn()
    try:
        home = _d7final_find_home(conn, home_id, home_code, admin_login)
        values = _d7final_home_values(home)
        viewer_scope = _d7m16_viewer_scope(home, viewer_role, admin_login)

        row = conn.execute("SELECT * FROM system_logs WHERE id = ?", (source_id,)).fetchone()
        if not row or not _d7final_is_door(row):
            return {"success": True, "hidden": 0}

        _d7m16_hide_door_log_for_viewer(
            conn,
            "system_logs",
            str(source_id),
            values["home_id"],
            viewer_scope,
        )

        conn.commit()
        return {"success": True, "hidden": 1}
    finally:
        conn.close()

@router.delete("/api/app/door-access-logs-final/bulk")
def d7final_delete_door_logs_bulk(payload: dict = _D7FinalBody(default_factory=dict)):
    from main import _D7FinalBody, _d7final_conn, _d7final_find_home, _d7final_home_values, _d7final_s, _d7final_val, _d7m16_hide_door_log_for_viewer, _d7m16_viewer_scope
    conn = _d7final_conn()
    try:
        home = _d7final_find_home(conn, _d7final_s(payload.get("home_id")), _d7final_s(payload.get("home_code")), _d7final_s(payload.get("admin_login")))
        values = _d7final_home_values(home)
        viewer_scope = _d7m16_viewer_scope(
            home,
            _d7final_s(payload.get("viewer_role", "admin")),
            _d7final_s(payload.get("admin_login")),
        )

        home_sql, params = _d7final_home_filter(conn, home)
        rows = conn.execute(f"SELECT * FROM system_logs WHERE 1=1 {home_sql}", params).fetchall()

        date_filter = _d7final_s(payload.get("date", "all"))
        actor_filter = _d7final_s(payload.get("actor", "all"))
        hidden_count = 0

        for row in rows:
            if not _d7final_is_door(row):
                continue

            ts = _d7final_s(_d7final_val(row, "timestamp", "created_at"))
            row_date = ts[:10] if len(ts) >= 10 else ""
            actor = _d7final_actor(row)

            if date_filter and date_filter != "all" and row_date != date_filter:
                continue
            if actor_filter and actor_filter != "all" and actor != actor_filter:
                continue

            row_id = _d7final_s(_d7final_val(row, "id"))
            _d7m16_hide_door_log_for_viewer(
                conn,
                "system_logs",
                row_id,
                values["home_id"],
                viewer_scope,
            )
            hidden_count += 1

        conn.commit()
        return {"success": True, "hidden": hidden_count}
    finally:
        conn.close()

def _d7_final_find_db():
    from main import _D7FinalPath, _d7_final_sqlite3
    old = globals().get("_d7_find_db")
    if callable(old):
        try:
            found = old()
            if found:
                return found
        except Exception:
            pass

    base = _D7FinalPath(__file__).resolve().parent
    candidates = [
        base / "database" / "smart_home_edge.db",
        base / "data" / "smart_home.db",
        base.parent / "data" / "smart_home.db",
        base / "ai" / "smart_home_models.db",
        base / "smart_home.db",
    ]

    for p in base.rglob("*.db"):
        if "__pycache__" not in str(p):
            candidates.append(p)

    seen = []
    for p in candidates:
        if p in seen or not p.exists():
            continue
        seen.append(p)
        try:
            con = _d7_final_sqlite3.connect(str(p))
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            con.close()
            if "system_logs" in tables or "devices" in tables:
                return p
        except Exception:
            pass

    return seen[0] if seen else None

def _d7_final_delete_by_id(con, table, log_id):
    from main import _D7FinalHTTPException, _d7_final_cols, _d7_final_tables
    if table not in {"system_logs", "security_logs", "door_events", "face_events"}:
        raise _D7FinalHTTPException(status_code=400, detail="Invalid log table")

    if table not in _d7_final_tables(con):
        return 0

    cols = _d7_final_cols(con, table)
    id_col = "id" if "id" in cols else "rowid"
    cur = con.execute(f"DELETE FROM {table} WHERE {id_col} = ?", (str(log_id),))
    return cur.rowcount

@router.delete("/api/app/door-access-logs/{source_table}/{source_id}")
def d7m16_final_delete_app_door_access_log(source_table: str, source_id: str):
    from main import _d7_final_conn
    con = _d7_final_conn()
    try:
        table = source_table.strip()
        deleted = _d7_final_delete_by_id(con, table, source_id)
        con.commit()
        return {"success": True, "deleted": deleted}
    finally:
        con.close()

@router.delete("/api/app/door-access-logs/bulk")
def d7m16_final_bulk_delete_app_door_access_logs(payload: dict = _D7FinalBody(default_factory=dict)):
    from main import _D7FinalBody, _d7_final_cols, _d7_final_conn, _d7_final_tables
    con = _d7_final_conn()
    try:
        if "system_logs" not in _d7_final_tables(con):
            return {"success": True, "deleted": 0}

        cols = _d7_final_cols(con, "system_logs")
        where = []
        params = []

        date_value = str(payload.get("date") or "").strip()
        actor = str(payload.get("actor") or "").strip().lower()
        home_id = str(payload.get("home_id") or "").strip()
        home_code = str(payload.get("home_code") or "").strip()

        door_terms = []
        for c in ["event_type", "details", "action_taken", "device_name", "device_type"]:
            if c in cols:
                door_terms.append(f"lower({c}) LIKE ?")
                params.append("%door%")
        if door_terms:
            where.append("(" + " OR ".join(door_terms) + ")")

        if date_value and date_value.lower() != "all":
            time_col = "timestamp" if "timestamp" in cols else "created_at" if "created_at" in cols else None
            if time_col:
                where.append(f"substr({time_col}, 1, 10) = ?")
                params.append(date_value)

        if actor and actor != "all" and "actor" in cols:
            where.append("lower(actor) = ?")
            params.append(actor)

        home_terms = []
        for value in [home_id, home_code]:
            if not value:
                continue
            for c in ["home", "home_id", "home_code", "apartment_number"]:
                if c in cols:
                    home_terms.append(f"{c} = ?")
                    params.append(value)
        if home_terms:
            where.append("(" + " OR ".join(home_terms) + ")")

        sql = "DELETE FROM system_logs"
        if where:
            sql += " WHERE " + " AND ".join(where)

        cur = con.execute(sql, params)
        con.commit()
        return {"success": True, "deleted": cur.rowcount}
    finally:
        con.close()

@router.post("/api/app/door-access-logs-final/bulk")
def d7m16_post_app_door_access_logs_final_bulk(payload: dict = _D7FinalBody(default_factory=dict)):
    from main import _D7FinalBody
    return d7final_delete_door_logs_bulk(payload)
