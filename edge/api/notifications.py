from fastapi import APIRouter, Request, BackgroundTasks, Depends, Body as _D7RealBody, Body as _D7FinalBody
import json
import sqlite3
from pathlib import Path
from datetime import datetime as _d7real_datetime

router = APIRouter()

def _d7real_tables(conn):
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {r[0] for r in rows}

def _d7real_cols(conn, table):
    try:
        return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    except Exception:
        return []

def _d7real_ensure_alert_table(conn):
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

def _d7real_state(conn, key):
    _d7real_ensure_alert_table(conn)
    row = conn.execute("SELECT * FROM app_alert_states WHERE alert_key = ?", (key,)).fetchone()
    return row

def _d7real_alert_item(conn, key, title, message, category, typ, severity, timestamp="", source_table="", source_id="", extra=None):
    from edge.main import _d7real_time
    state = _d7real_state(conn, key)
    if state and int(state["hidden"] or 0) == 1:
        return None

    resolved = bool(state and int(state["is_resolved"] or 0) == 1)
    item = {
        "id": key,
        "source_table": source_table,
        "source_id": source_id,
        "title": title,
        "message": message,
        "category": category,
        "type": typ,
        "severity": severity,
        "time": _d7real_time(timestamp) if timestamp else "Just now",
        "timestamp": timestamp,
        "isResolved": resolved,
        "is_resolved": resolved,
        "status": "Resolved" if resolved else "Active",
    }
    if extra:
        item.update(extra)
    return item

@router.get("/api/app/alerts")
def d7real_get_app_alerts(home_id: str = "", home_code: str = "", admin_login: str = ""):
    from edge.main import _d7real_val, _d7real_resolve_home, _d7real_s, _d7real_conn, _d7real_home_match_sql
    conn = _d7real_conn()
    try:
        _d7real_ensure_alert_table(conn)
        home = _d7real_resolve_home(conn, home_id, home_code, admin_login)
        home_sql, home_params = _d7real_home_match_sql(conn, home)
        alerts = []

        if "system_logs" in _d7real_tables(conn):
            rows = conn.execute(
                f"""
                SELECT *
                FROM system_logs
                WHERE LOWER(COALESCE(severity,'')) IN ('warning','error','critical')
                {home_sql}
                ORDER BY COALESCE(timestamp,'') DESC, id DESC
                LIMIT 40
                """,
                home_params,
            ).fetchall()

            for row in rows:
                action = _d7real_val(row, "action_taken", default="")
                event_type = _d7real_val(row, "event_type", default="System Event")
                details = _d7real_val(row, "details", "message", default="")
                ts = _d7real_val(row, "timestamp", default="")
                severity = _d7real_val(row, "severity", default="warning").lower()
                source_id = _d7real_s(_d7real_val(row, "id", default=""))
                text = " ".join([action, event_type, details]).lower()

                if "door" in text:
                    title = "Smart Door Warning"
                    category = "security"
                    typ = "doorEvent"
                elif "energy" in text:
                    title = "High Energy Usage"
                    category = "system"
                    typ = "highEnergy"
                elif "offline" in text or "disable" in text:
                    title = "Device Offline"
                    category = "system"
                    typ = "deviceOffline"
                else:
                    title = event_type or "System Alert"
                    category = "system"
                    typ = "system"

                item = _d7real_alert_item(
                    conn,
                    f"system_logs:{source_id}",
                    title,
                    details or action or event_type,
                    category,
                    typ,
                    severity,
                    ts,
                    "system_logs",
                    source_id,
                    {"action_taken": action, "camera": "Smart Door"},
                )
                if item:
                    alerts.append(item)

        if "devices" in _d7real_tables(conn):
            dcols = _d7real_cols(conn, "devices")
            conditions = []
            params = []

            if home is not None:
                hid = _d7real_s(_d7real_val(home, "id", default=""))
                apt = _d7real_s(_d7real_val(home, "apartment_number", default=""))

                if hid and "home_id" in dcols:
                    conditions.append("CAST(home_id AS TEXT) = ?")
                    params.append(hid)
                if apt and "apartment_number" in dcols:
                    conditions.append("CAST(apartment_number AS TEXT) = ?")
                    params.append(apt)

            device_sql = "SELECT * FROM devices"
            if conditions:
                device_sql += " WHERE " + " OR ".join(conditions)

            for row in conn.execute(device_sql, params).fetchall():
                status = _d7real_s(_d7real_val(row, "status", default="")).lower()
                enabled = _d7real_s(_d7real_val(row, "enabled", default="1")).lower()
                if status in {"offline", "disabled"} or enabled in {"0", "false", "no"}:
                    device_id = _d7real_s(_d7real_val(row, "device_id", "id", default=""))
                    name = _d7real_s(_d7real_val(row, "device_name", "name", default=device_id or "Device"))
                    item = _d7real_alert_item(
                        conn,
                        f"device:{device_id}",
                        "Device Offline",
                        f"{name} is not online or disabled.",
                        "system",
                        "deviceOffline",
                        "warning",
                        _d7real_val(row, "last_seen", "last_seen_at", "updated_at", default=""),
                        "devices",
                        device_id,
                    )
                    if item:
                        alerts.append(item)

        if "energy_readings" in _d7real_tables(conn):
            try:
                erow = conn.execute("SELECT * FROM energy_readings ORDER BY COALESCE(timestamp, created_at, '') DESC LIMIT 1").fetchone()
                if erow:
                    watts = 0.0
                    for key in ("watts", "power_w", "power", "current_power"):
                        try:
                            if key in erow.keys() and erow[key] is not None:
                                watts = float(erow[key])
                                break
                        except Exception:
                            pass
                    if watts >= 2500:
                        item = _d7real_alert_item(
                            conn,
                            "energy:high-current-power",
                            "High Energy Usage",
                            f"Current power is {watts:.0f} W, higher than normal.",
                            "system",
                            "highEnergy",
                            "warning",
                            _d7real_val(erow, "timestamp", "created_at", default=""),
                            "energy_readings",
                            _d7real_s(_d7real_val(erow, "id", default="")),
                            {"comparison": "Higher than normal usage"},
                        )
                        if item:
                            alerts.append(item)
            except Exception:
                pass

        alerts = sorted(alerts, key=lambda x: _d7real_s(x.get("timestamp")), reverse=True)
        active_count = sum(1 for a in alerts if not a.get("isResolved"))

        return {"success": True, "alerts": alerts, "active_count": active_count}
    finally:
        conn.close()

@router.post("/api/app/alerts/{alert_key:path}/resolve")
def d7real_resolve_alert(alert_key: str):
    from edge.main import _d7real_conn
    conn = _d7real_conn()
    try:
        _d7real_ensure_alert_table(conn)
        now = _d7real_datetime.now().isoformat(timespec="seconds")
        conn.execute(
            """
            INSERT INTO app_alert_states(alert_key, is_resolved, hidden, updated_at)
            VALUES (?, 1, 0, ?)
            ON CONFLICT(alert_key) DO UPDATE SET is_resolved=1, hidden=0, updated_at=excluded.updated_at
            """,
            (alert_key, now),
        )
        conn.commit()
        return {"success": True}
    finally:
        conn.close()

@router.delete("/api/app/alerts/{alert_key:path}")
def d7real_hide_alert(alert_key: str):
    from edge.main import _d7real_conn
    conn = _d7real_conn()
    try:
        _d7real_ensure_alert_table(conn)
        now = _d7real_datetime.now().isoformat(timespec="seconds")
        conn.execute(
            """
            INSERT INTO app_alert_states(alert_key, is_resolved, hidden, updated_at)
            VALUES (?, 0, 1, ?)
            ON CONFLICT(alert_key) DO UPDATE SET hidden=1, updated_at=excluded.updated_at
            """,
            (alert_key, now),
        )
        conn.commit()
        return {"success": True}
    finally:
        conn.close()

@router.post("/api/app/alerts/clear")
def d7real_clear_alerts(payload: dict = _D7RealBody(default_factory=dict)):
    from edge.main import _d7real_conn, _d7real_s
    conn = _d7real_conn()
    try:
        data = d7real_get_app_alerts(
            home_id=_d7real_s(payload.get("home_id", "")),
            home_code=_d7real_s(payload.get("home_code", "")),
            admin_login=_d7real_s(payload.get("admin_login", "")),
        )
        _d7real_ensure_alert_table(conn)
        now = _d7real_datetime.now().isoformat(timespec="seconds")
        count = 0

        for alert in data.get("alerts", []):
            key = alert.get("id")
            if not key:
                continue
            conn.execute(
                """
                INSERT INTO app_alert_states(alert_key, is_resolved, hidden, updated_at)
                VALUES (?, 1, 1, ?)
                ON CONFLICT(alert_key) DO UPDATE SET is_resolved=1, hidden=1, updated_at=excluded.updated_at
                """,
                (key, now),
            )
            count += 1

        conn.commit()
        return {"success": True, "cleared": count}
    finally:
        conn.close()

def _d7final_alerts_for_home(conn, home):
    from edge.main import _d7final_s, _d7final_ensure_alerts, _d7final_text, _d7final_home_filter, _d7final_tables, _d7final_energy_power, _d7final_cols, _d7final_alert, _d7final_is_energy, _d7final_is_door, _d7final_home_values, _d7final_val
    _d7final_ensure_alerts(conn)
    home_sql, params = _d7final_home_filter(conn, home)
    values = _d7final_home_values(home)
    alerts = []

    if "system_logs" in _d7final_tables(conn):
        rows = conn.execute(
            f"SELECT * FROM system_logs WHERE 1=1 {home_sql} ORDER BY COALESCE(timestamp, created_at, '') DESC, id DESC LIMIT 150",
            params,
        ).fetchall()

        for row in rows:
            row_id = _d7final_s(_d7final_val(row, "id"))
            text = _d7final_text(row)
            ts = _d7final_val(row, "timestamp", "created_at")
            severity = _d7final_s(_d7final_val(row, "severity", default="INFO")).lower()
            details = _d7final_s(_d7final_val(row, "details"))
            action = _d7final_s(_d7final_val(row, "action_taken"))
            event = _d7final_s(_d7final_val(row, "event_type"))
            item = None

            text_lower = str(text).lower()
            action_lower = str(action).lower()
            details_lower = str(details).lower()
            event_lower = str(event).lower()

            unknown_pending_alert = (
                "unknown face detected" in action_lower
                or (
                    "unknown face" in details_lower
                    and ("waiting" in details_lower or "pending" in details_lower)
                )
                or (
                    "unknown face" in text_lower
                    and ("waiting" in text_lower or "pending" in text_lower)
                )
                or (
                    "face recognition" in event_lower
                    and "unknown face detected" in text_lower
                    and not any(
                        key in text_lower
                        for key in [
                            "opened once",
                            "denied by",
                            "unknown denied",
                            "unknown open once",
                            "after family add",
                            "family member added",
                            "access granted",
                            "access denied",
                        ]
                    )
                )
            )

            unknown_decision_log = any(
                key in text_lower
                for key in [
                    "unknown person opened once",
                    "unknown person denied",
                    "unknown open once",
                    "unknown denied",
                    "door opened after family add",
                    "new family member added",
                    "family member added",
                    "access granted",
                    "access denied",
                ]
            )

            if unknown_pending_alert and not unknown_decision_log:
                item = _d7final_alert(
                    conn,
                    f"system_logs:{row_id}",
                    "Unknown Face Detected",
                    details or "Unknown person detected at the door.",
                    "security",
                    "unknownFace",
                    "warning",
                    ts,
                    "system_logs",
                    row_id,
                    {"camera": "Smart Door"},
                )

            elif "password recovery" in text or "otp" in text:

                # D7M16_PASSWORD_RECOVERY_ALERT_TS_FIX

                ts = _d7final_val(row, "created_at", "timestamp") or ts
                item = _d7final_alert(
                    conn,
                    f"system_logs:{row_id}",
                    "Password Recovery OTP",
                    details or "Password recovery code generated.",
                    "security",
                    "passwordRecovery",
                    "warning",
                    ts,
                    "system_logs",
                    row_id,
                )

            elif _d7final_is_energy(row):
                if any(key in text for key in ["enable", "disable", "restart", "offline", "fault", "warning"]):
                    if "enable" in text:
                        title = "Energy Monitor Enabled"
                    elif "disable" in text:
                        title = "Energy Monitor Disabled"
                    elif "restart" in text:
                        title = "Energy Monitor Restarted"
                    else:
                        title = "Energy Monitor Warning"

                    item = _d7final_alert(
                        conn,
                        f"system_logs:{row_id}",
                        title,
                        details or action or event,
                        "system",
                        "energyMonitor",
                        "warning",
                        ts,
                        "system_logs",
                        row_id,
                    )

            elif _d7final_is_door(row):
                # Final decision:
                # Door Enable/Disable/Restart from Dashboard = Dashboard Logs + Door Access Log only.
                # Alerts only for Unknown Face, offline/fault, or real warning.
                if "offline" in text or "fault" in text:
                    item = _d7final_alert(
                        conn,
                        f"system_logs:{row_id}",
                        "Smart Door Offline",
                        details or action or event,
                        "security",
                        "deviceOffline",
                        "warning",
                        ts,
                        "system_logs",
                        row_id,
                    )
                elif "access denied" in text and "unknown" in text:
                    item = _d7final_alert(
                        conn,
                        f"system_logs:{row_id}",
                        "Access Denied",
                        details or "Unknown person was denied.",
                        "security",
                        "doorEvent",
                        "warning",
                        ts,
                        "system_logs",
                        row_id,
                    )

            elif severity in {"error", "critical"} or "mqtt" in text or "api error" in text or "server" in text:
                item = _d7final_alert(
                    conn,
                    f"system_logs:{row_id}",
                    "Server / Device Status",
                    details or action or event,
                    "system",
                    "system",
                    "warning",
                    ts,
                    "system_logs",
                    row_id,
                )

            if item:
                alerts.append(item)

    if "devices" in _d7final_tables(conn):
        dcols = _d7final_cols(conn, "devices")
        conditions = []
        params2 = []

        if values["home_id"] and "home_id" in dcols:
            conditions.append("CAST(home_id AS TEXT) = ?")
            params2.append(values["home_id"])

        sql = "SELECT * FROM devices"
        if conditions:
            sql += " WHERE " + " OR ".join(conditions)

        try:
            for row in conn.execute(sql, params2).fetchall():
                status = _d7final_s(_d7final_val(row, "status")).lower()
                enabled = _d7final_s(_d7final_val(row, "enabled", default="1")).lower()
                dtype = _d7final_s(_d7final_val(row, "device_type", "type")).lower()
                name = _d7final_s(_d7final_val(row, "device_name", "name", default="Device"))
                device_id = _d7final_s(_d7final_val(row, "device_id", "id"))

                is_energy = "energy" in dtype or "meter" in dtype
                is_door = "door" in dtype or "camera" in dtype

                should_alert = False
                title = ""
                category = "system"
                typ = "system"

                if is_energy and (enabled in {"0", "false", "no"} or status in {"offline", "fault", "disabled", "error"}):
                    should_alert = True
                    title = "Energy Device Disabled" if enabled in {"0", "false", "no"} or status == "disabled" else "Energy Device Offline"
                    category = "system"
                    typ = "energyMonitor"

                if is_door and status in {"offline", "fault", "error"}:
                    should_alert = True
                    title = "Smart Door Offline"
                    category = "security"
                    typ = "deviceOffline"

                if not should_alert:
                    continue

                item = _d7final_alert(
                    conn,
                    f"device:{device_id}",
                    title,
                    f"{name} is offline, disabled, or not reporting.",
                    category,
                    typ,
                    "warning",
                    _d7final_val(row, "last_seen", "last_seen_at", "updated_at"),
                    "devices",
                    device_id,
                )
                if item:
                    alerts.append(item)
        except Exception:
            pass

    watts, ts, sid = _d7final_energy_power(conn)
    if watts >= 2500:
        item = _d7final_alert(
            conn,
            "energy:high-usage",
            "High Energy Usage",
            f"Current power is {watts:.0f} W, higher than normal.",
            "system",
            "highEnergy",
            "warning",
            ts,
            "energy_readings",
            sid,
        )
        if item:
            alerts.append(item)

    seen = set()
    clean = []
    for item in alerts:
        key = item.get("id")
        if key in seen:
            continue
        seen.add(key)
        clean.append(item)

    clean.sort(key=lambda item: _d7final_s(item.get("timestamp")), reverse=True)
    return clean

def _d7m16_role_text(value):
    value = str(value or "").strip().lower()
    return "user" if value == "user" else "admin"

_d7m16_original_d7final_alerts_for_home = _d7final_alerts_for_home

def _d7final_alerts_for_home(conn, home):
    alerts = _d7m16_original_d7final_alerts_for_home(conn, home)
    clean_alerts = []

    blocked_unknown_decision_words = [
        "unknown denied",
        "unknown face denied",
        "unknown person denied",
        "unknown open once",
        "unknown face opened once",
        "unknown person opened once",
        "opened once by admin",
        "denied by admin",
        "door opened after family add",
        "family member added",
        "access granted",
        "access denied",
    ]

    for item in alerts:
        alert_type = str(item.get("type") or "").strip().lower()
        combined = " ".join(
            str(item.get(key) or "")
            for key in [
                "id",
                "title",
                "message",
                "details",
                "description",
                "status",
                "action",
                "result",
            ]
        ).lower()

        if alert_type == "unknownface" and any(word in combined for word in blocked_unknown_decision_words):
            continue

        clean_alerts.append(item)

    return clean_alerts

@router.get("/api/app/alerts-final")
def d7final_get_alerts(home_id: str = "", home_code: str = "", admin_login: str = "", viewer_role: str = "admin"):
    from edge.main import _d7m16_viewer_scope, _d7final_find_home, _d7final_conn
    conn = _d7final_conn()
    try:
        home = _d7final_find_home(conn, home_id, home_code, admin_login)

        import edge.main
        edge.main._D7M16_ALERT_SCOPE = _d7m16_viewer_scope(home, viewer_role, admin_login)
        try:
            alerts = _d7final_alerts_for_home(conn, home)
        finally:
            edge.main._D7M16_ALERT_SCOPE = ""

        active_count = sum(1 for item in alerts if not item.get("isResolved"))
        return {"success": True, "alerts": alerts, "active_count": active_count}
    finally:
        conn.close()

@router.post("/api/app/alerts-final/clear")
def d7final_clear_alerts(payload: dict = _D7FinalBody(default_factory=dict)):
    from edge.main import _d7m16_viewer_scope, _d7final_s, _d7m16_state_key, _d7final_ensure_alerts, _d7final_now, _d7final_find_home, _d7final_conn, _d7final_home_values
    conn = _d7final_conn()
    try:
        home = _d7final_find_home(conn, _d7final_s(payload.get("home_id")), _d7final_s(payload.get("home_code")), _d7final_s(payload.get("admin_login")))
        values = _d7final_home_values(home)
        viewer_scope = _d7m16_viewer_scope(home, _d7final_s(payload.get("viewer_role", "admin")), _d7final_s(payload.get("admin_login")))

        import edge.main
        edge.main._D7M16_ALERT_SCOPE = viewer_scope
        try:
            alerts = _d7final_alerts_for_home(conn, home)
        finally:
            edge.main._D7M16_ALERT_SCOPE = ""

        _d7final_ensure_alerts(conn)
        now = _d7final_now()
        for alert in alerts:
            conn.execute(
                """
                INSERT INTO app_alert_states(alert_key, home_id, category, is_resolved, hidden, updated_at)
                VALUES (?, ?, ?, 1, 1, ?)
                ON CONFLICT(alert_key) DO UPDATE SET is_resolved=1, hidden=1, updated_at=excluded.updated_at
                """,
                (_d7m16_state_key(alert["id"], viewer_scope), values["home_id"], alert.get("category", ""), now),
            )
        conn.commit()
        return {"success": True, "cleared": len(alerts)}
    finally:
        conn.close()

@router.post("/api/app/alerts-final/{alert_key}/resolve")
def d7final_resolve_alert(
    alert_key: str,
    home_id: str = "",
    home_code: str = "",
    admin_login: str = "",
    viewer_role: str = "admin",
):
    from edge.main import _d7m16_viewer_scope, _d7m16_state_key, _d7final_ensure_alerts, _d7final_now, _d7final_find_home, _d7final_conn
    conn = _d7final_conn()
    try:
        _d7final_ensure_alerts(conn)
        home = _d7final_find_home(conn, home_id, home_code, admin_login)
        viewer_scope = _d7m16_viewer_scope(home, viewer_role, admin_login)
        scoped_key = _d7m16_state_key(alert_key, viewer_scope)

        conn.execute(
            """
            INSERT INTO app_alert_states(alert_key, is_resolved, hidden, updated_at)
            VALUES (?, 1, 0, ?)
            ON CONFLICT(alert_key) DO UPDATE SET is_resolved=1, hidden=0, updated_at=excluded.updated_at
            """,
            (scoped_key, _d7final_now()),
        )
        conn.commit()
        return {"success": True}
    finally:
        conn.close()

@router.delete("/api/app/alerts-final/{alert_key}")
def d7final_hide_alert(
    alert_key: str,
    home_id: str = "",
    home_code: str = "",
    admin_login: str = "",
    viewer_role: str = "admin",
):
    from edge.main import _d7m16_viewer_scope, _d7m16_state_key, _d7final_ensure_alerts, _d7final_now, _d7final_find_home, _d7final_conn
    conn = _d7final_conn()
    try:
        _d7final_ensure_alerts(conn)
        home = _d7final_find_home(conn, home_id, home_code, admin_login)
        viewer_scope = _d7m16_viewer_scope(home, viewer_role, admin_login)
        scoped_key = _d7m16_state_key(alert_key, viewer_scope)

        conn.execute(
            """
            INSERT INTO app_alert_states(alert_key, is_resolved, hidden, updated_at)
            VALUES (?, 1, 1, ?)
            ON CONFLICT(alert_key) DO UPDATE SET is_resolved=1, hidden=1, updated_at=excluded.updated_at
            """,
            (scoped_key, _d7final_now()),
        )

        conn.commit()
        return {"success": True, "hidden": 1}
    finally:
        conn.close()
