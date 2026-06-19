from fastapi import APIRouter, Depends, HTTPException, Request
import sqlite3
from typing import Dict, Any
from core_database import get_db_connection

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

def _safe_str(val: Any) -> str:
    return str(val) if val is not None else ""

def _format_device(d: sqlite3.Row) -> dict:
    device = dict(d)
    is_door = "door" in _safe_str(device.get("device_type")).lower()
    is_energy = "energy" in _safe_str(device.get("device_type")).lower()
    online = _safe_str(device.get("status")).lower() == "online"
    enabled = bool(device.get("enabled"))
    
    stream = device.get("camera_stream_url")
    stream_available = bool(is_door and online and enabled and stream and "not available" not in str(stream).lower())
    
    return {
        "id": device.get("device_id") or device.get("id"),
        "name": device.get("device_name", "Device"),
        "device_name": device.get("device_name", "Device"),
        "type": device.get("device_type", "device"),
        "device_type": device.get("device_type", "device"),
        "status": "Online" if online else "Offline",
        "online": online,
        "enabled": enabled,
        "claim_status": device.get("claim_status", "--"),
        "claim_code": device.get("claim_code", "--"),
        "device_token": device.get("device_token", ""),
        "last_seen": device.get("last_seen") or device.get("updated_at") or "Not available yet",
        "device_ip": device.get("device_ip", "Not available yet"),
        "mac_address": device.get("mac_address", "Not available yet"),
        "mqtt_topic": device.get("mqtt_topic", "Not available yet"),
        "camera_stream_url": stream or "Not available yet",
        "camera_capture_url": device.get("camera_capture_url") or "Not available yet",
        "is_door": is_door,
        "is_energy": is_energy,
        "stream_available": stream_available,
    }

def _build_home_summary(h: dict, devices: list, conn: sqlite3.Connection) -> dict:
    home_id = h["id"]
    apt = h.get("apartment_number") or ""
    home_code = h.get("home_code", "")
    padded = f"{int(apt):03d}" if apt and str(apt).isdigit() else ""
    
    home_devices = []
    for d in devices:
        d_home = d.get("home_id")
        did = _safe_str(d.get("device_id")).upper()
        topic = _safe_str(d.get("mqtt_topic")).upper()
        text = f"{did} {topic}"
        
        if str(d_home) == str(home_id):
            home_devices.append(d)
        elif home_code and home_code.upper() in text:
            home_devices.append(d)
        elif padded and (f"HOME{padded}" in text or f"HOME-{padded}" in text):
            home_devices.append(d)

    any_online = any(_safe_str(d.get("status")).lower() == "online" for d in home_devices)
    
    # Members count
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM family_members WHERE home_id = ?", (home_id,))
        members_count = cur.fetchone()[0]
    except sqlite3.OperationalError as e:
        print(f"[WARNING] Missing table family_members. Returning default values. Error: {e}")
        members_count = 0

    return {
        "raw_id": home_id,
        "name": h.get("name") or f"Apartment {apt}" or home_code,
        "apartment_number": apt or "--",
        "owner_name": h.get("owner_name") or "--",
        "owner_email": h.get("owner_email") or "--",
        "owner_phone": h.get("owner_phone") or "--",
        "home_id": str(home_code),
        "home_code": home_code,
        "registered_at": h.get("last_login_at") or "Not available yet",
        "devices_count": len(home_devices),
        "members_count": members_count,
        "home_status": "Online" if any_online else "Offline",
        "search_text": f"{h.get('name', '')} {home_code} {apt} {h.get('owner_name', '')} {h.get('owner_email', '')}".lower(),
    }

@router.get("/home-overview-data")
def get_home_overview_data(conn: sqlite3.Connection = Depends(get_db_connection)):
    print("[MIGRATION LOG] SUCCESS: Hitting NEW routers/dashboard.py -> get_home_overview_data")
    cur = conn.cursor()
    try:
        homes = [dict(r) for r in cur.execute("SELECT * FROM homes").fetchall()]
    except sqlite3.OperationalError as e:
        print(f"[WARNING] Missing table homes. Returning default values. Error: {e}")
        homes = []

    try:
        devices = [dict(r) for r in cur.execute("SELECT * FROM devices").fetchall()]
    except sqlite3.OperationalError as e:
        print(f"[WARNING] Missing table devices. Returning default values. Error: {e}")
        devices = []

    try:
        logs = [dict(r) for r in cur.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT 500").fetchall()]
    except sqlite3.OperationalError as e:
        print(f"[WARNING] Missing table system_logs. Returning default values. Error: {e}")
        logs = []

    system_errors = sum(1 for l in logs if _safe_str(l.get("severity")).upper() in {"ERROR", "CRITICAL"})
    
    summaries = [_build_home_summary(h, devices, conn) for h in homes]

    return {
        "success": True,
        "stats": {
            "total_homes": len(homes),
            "total_devices": len(devices),
            "online_devices": sum(1 for d in devices if _safe_str(d.get("status")).lower() == "online"),
            "system_errors": system_errors,
        },
        "homes": summaries,
    }

@router.get("/home-details-data")
def get_home_details_data(home_id: str, conn: sqlite3.Connection = Depends(get_db_connection)):
    cur = conn.cursor()
    try:
        homes = [dict(r) for r in cur.execute("SELECT * FROM homes").fetchall()]
    except sqlite3.OperationalError as e:
        print(f"[WARNING] Missing table homes. Returning default values. Error: {e}")
        homes = []
    
    home = next((h for h in homes if str(h["id"]) == home_id or h["home_code"] == home_id), None)
    if not home:
        raise HTTPException(status_code=404, detail="Home not found")

    try:
        devices = [dict(r) for r in cur.execute("SELECT * FROM devices").fetchall()]
    except sqlite3.OperationalError as e:
        print(f"[WARNING] Missing table devices. Returning default values. Error: {e}")
        devices = []
    
    apt = home.get("apartment_number") or ""
    home_code = home.get("home_code", "")
    padded = f"{int(apt):03d}" if apt and str(apt).isdigit() else ""
    
    home_devices_raw = []
    for d in devices:
        d_home = d.get("home_id")
        did = _safe_str(d.get("device_id")).upper()
        topic = _safe_str(d.get("mqtt_topic")).upper()
        text = f"{did} {topic}"
        
        if str(d_home) == str(home["id"]) or (home_code and home_code.upper() in text) or (padded and (f"HOME{padded}" in text or f"HOME-{padded}" in text)):
            home_devices_raw.append(d)

    home_devices = [_format_device(d) for d in home_devices_raw]
    
    try:
        logs = [dict(r) for r in cur.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT 100").fetchall()]
    except sqlite3.OperationalError as e:
        print(f"[WARNING] Missing table system_logs. Returning default values. Error: {e}")
        logs = []

    try:
        door_logs = [dict(r) for r in cur.execute("SELECT * FROM door_events WHERE home_id = ? ORDER BY id DESC LIMIT 10", (home["id"],)).fetchall()]
    except sqlite3.OperationalError as e:
        print(f"[WARNING] Missing table door_events. Returning default values. Error: {e}")
        door_logs = []
    
    recent_logs = []
    for log in logs + door_logs:
        log_home = str(log.get("home_id") or log.get("apartment_number") or log.get("home") or "")
        if str(home["id"]) == log_home or str(apt) == log_home:
            recent_logs.append({
                "timestamp": log.get("timestamp") or log.get("created_at") or "",
                "event_type": log.get("event_type", "Event"),
                "details": log.get("details", log.get("message", "Event Details")),
                "action_taken": log.get("action_taken", "--"),
                "severity": log.get("severity", "INFO"),
            })

    door_status = {"status": "Unknown", "last_opened": "No door events yet"}
    for log in door_logs:
        txt = f"{log.get('event_type')} {log.get('details')} {log.get('action_taken')}".lower()
        if "open" in txt or "unlock" in txt:
            door_status = {"status": "Unlocked", "last_opened": log.get("timestamp") or "Known door event"}
            break
        elif "lock" in txt:
            door_status = {"status": "Locked", "last_opened": log.get("timestamp") or "No open time"}
            break

    summary = _build_home_summary(home, devices, conn)
    
    return {
        "success": True,
        "home": summary,
        "devices": home_devices,
        "door_status": door_status,
        "energy": None,
        "recent_logs": recent_logs[:5],
    }

@router.post("/homes/{home_id_param}/edit")
async def edit_home(home_id_param: int, request: Request, conn: sqlite3.Connection = Depends(get_db_connection)):
    payload = await request.json()
    cur = conn.cursor()
    
    allowed = ["owner_name", "owner_email", "owner_phone", "apartment_number"]
    updates = []
    values = []
    
    for key in allowed:
        if key in payload and payload[key] is not None:
            updates.append(f"{key} = ?")
            values.append(payload[key])
            
    if not updates:
        return {"success": False, "message": "No editable columns found."}
        
    values.append(home_id_param)
    cur.execute(f"UPDATE homes SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    
    return {"success": True, "message": "Home updated successfully."}

@router.post("/homes/{home_id_param}/devices")
async def add_device(home_id_param: int, request: Request, conn: sqlite3.Connection = Depends(get_db_connection)):
    payload = await request.json()
    cur = conn.cursor()
    
    home_row = cur.execute("SELECT * FROM homes WHERE id = ?", (home_id_param,)).fetchone()
    if not home_row:
        raise HTTPException(status_code=404, detail="Home not found")
    home = dict(home_row)
        
    device_name = payload.get("device_name", "New Device").strip()
    device_type = payload.get("device_type", "smart_door").strip().lower()
    if device_type not in {"smart_door", "energy_monitor"}:
        device_type = "smart_door"
        
    apt = home.get("apartment_number") or ""
    padded = f"{int(apt):03d}" if apt and str(apt).isdigit() else "000"
    
    device_ids = cur.execute("SELECT device_id FROM devices WHERE home_id = ? AND device_type = ?", (home["id"], device_type)).fetchall()
    max_seq = 0
    for row in device_ids:
        did = str(row[0] or "")
        parts = did.split("-")
        if len(parts) >= 3 and parts[-1].isdigit():
            seq_val = int(parts[-1])
            if seq_val > max_seq:
                max_seq = seq_val
    seq = max_seq + 1
    
    prefix = "METER" if device_type == "energy_monitor" else "DOOR"
    device_id = f"{prefix}-HOME{padded}-{seq:03d}"
    mqtt_topic = f"home/HOME-{padded}/{device_type}/{device_id}"
    
    import secrets
    claim_code = f"HOME{padded}-{secrets.token_hex(2).upper()}"
    device_token = secrets.token_urlsafe(24)
    
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cur.execute("""
        INSERT INTO devices 
        (home_id, device_id, device_name, device_type, device_token, mqtt_topic, status, claim_code, claim_status, enabled, last_seen, updated_at, last_seen_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (home["id"], device_id, device_name, device_type, device_token, mqtt_topic, "online", claim_code, "claimed", 1, now, now, now))
    
    conn.commit()
    return {"success": True, "message": "Device added successfully.", "device_id": device_id}


@router.get("/security-logs-data")
@router.get("/logs")
def get_security_logs(limit: int = 100, conn: sqlite3.Connection = Depends(get_db_connection)):
    cur = conn.cursor()
    try:
        logs = [dict(r) for r in cur.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
    except sqlite3.OperationalError as e:
        print(f"[WARNING] Missing table system_logs. Returning default values. Error: {e}")
        logs = []
    return {"success": True, "logs": logs}

@router.get("/final-qa/homes-lite")
def get_homes_lite(conn: sqlite3.Connection = Depends(get_db_connection)):
    cur = conn.cursor()
    try:
        homes = [dict(r) for r in cur.execute("SELECT id, name, home_code, apartment_number FROM homes").fetchall()]
    except sqlite3.OperationalError as e:
        print(f"[WARNING] Missing table homes. Returning default values. Error: {e}")
        homes = []
    return {"success": True, "homes": homes}

@router.get("/energy-page-data-v2")
def get_energy_page_data(conn: sqlite3.Connection = Depends(get_db_connection)):
    cur = conn.cursor()
    try:
        homes = [dict(r) for r in cur.execute("SELECT * FROM homes").fetchall()]
    except sqlite3.OperationalError as e:
        homes = []

    try:
        devices = [dict(r) for r in cur.execute("SELECT * FROM devices WHERE device_type LIKE '%energy%' OR device_type LIKE '%meter%'").fetchall()]
    except sqlite3.OperationalError as e:
        devices = []

    energy_records = []
    for d in devices:
        home = next((h for h in homes if str(h.get("id")) == str(d.get("home_id"))), {})
        
        reading = {}
        try:
            row = cur.execute("SELECT * FROM energy_readings WHERE device_id = ? ORDER BY id DESC LIMIT 1", (d.get("device_id"),)).fetchone()
            if row: reading = dict(row)
        except Exception:
            pass
            
        history_rows = []
        try:
            history_rows = [dict(r) for r in cur.execute("SELECT * FROM energy_readings WHERE device_id = ? ORDER BY id DESC LIMIT 20", (d.get("device_id"),)).fetchall()]
        except Exception:
            pass
            
        history = []
        for hr in reversed(history_rows):
            history.append({
                "kwh": hr.get("total_kwh") or hr.get("consumption_kwh") or hr.get("kwh_today", 0.0),
                "timestamp_label": hr.get("timestamp", "N/A")
            })

        kwh = reading.get("total_kwh") or reading.get("consumption_kwh") or reading.get("kwh_today", 0.0)
            
        energy_records.append({
            "device_id": d.get("device_id"),
            "device_name": d.get("device_name") or d.get("name") or "Energy Monitor",
            "apartment_number": home.get("apartment_number") or d.get("home_id", "-"),
            "daily_kwh": kwh,
            "monthly_forecast_kwh": float(kwh) * 30.0 if kwh else 0.0,
            "current_power_w": reading.get("power_w") or reading.get("power") or reading.get("watts", 0.0),
            "has_readings": bool(reading),
            "latest_timestamp_label": reading.get("timestamp") or d.get("last_seen", "N/A"),
            "history": history
        })

    return {"success": True, "devices": energy_records, "homes_count": len(homes)}

@router.post("/devices/{device_id}/actions/{action}")
@router.post("/final-devices/{device_id}/actions/{action}")
@router.post("/final-devices-v3/{device_id}/actions/{action}")
@router.post("/final-devices-v4/{device_id}/actions/{action}")
@router.post("/final-devices-v6/{device_id}/actions/{action}")
@router.post("/d7-final-device-action/{device_id}/{action}")
@router.post("/d7r2-device-action/{device_id}/{action}")
@router.post("/final-devices-v5/{device_id}/remove")
def device_action(device_id: str, action: str = "remove", conn: sqlite3.Connection = Depends(get_db_connection)):
    try:
        action = action.lower().strip()
        if action == "delete": action = "remove"
        if action not in {"restart", "enable", "disable", "remove"}:
            raise HTTPException(status_code=400, detail="Unsupported device action")
            
        cur = conn.cursor()
        devices = cur.execute("SELECT rowid, * FROM devices WHERE device_id = ? OR id = ?", (device_id, device_id)).fetchall()
        if not devices:
            return {"success": False, "message": "Device not found"}
            
        first = dict(devices[0])
        rowid = first.get("rowid") or first.get("id")
    except Exception as big_e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"System Error: {str(big_e)}"}
    name = first.get("device_name") or device_id
    
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if action == "restart":
        try:
            cur.execute("UPDATE devices SET status = 'restarting', updated_at = ? WHERE rowid = ?", (now, rowid))
            cur.execute("INSERT INTO system_logs (timestamp, severity, event_type, details, action_taken, device_id, device_name, home_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (now, "INFO", "Device Restart", f"Restart command sent to {name}", "MQTT RESTART", first.get("device_id"), name, first.get("home_id")))
            conn.commit()
            
            try:
                from mqtt import mqtt_client
                from mqtt.publishers.device_command_publisher import publish_device_command
                publish_device_command(mqtt_client, first, "restart")
            except Exception as e:
                print(f"[MQTT ERROR] Failed to publish restart: {e}")
                
            return {"success": True, "message": "RESTART command sent.", "device_id": device_id, "action": action}
        except Exception as backend_e:
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"Backend Error: {str(backend_e)}"}
        
    if action == "remove":
        cur.execute("DELETE FROM devices WHERE rowid = ?", (rowid,))
        cur.execute("INSERT INTO system_logs (timestamp, severity, event_type, details, action_taken, device_id, device_name, home_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (now, "WARNING", "Device Removed", f"Device {name} was permanently removed.", "MQTT REMOVE", first.get("device_id"), name, first.get("home_id")))
        conn.commit()
        
        try:
            from mqtt import mqtt_client
            from mqtt.publishers.device_command_publisher import publish_device_command
            publish_device_command(mqtt_client, first, action)
        except Exception as e:
            print(f"[MQTT ERROR] Failed to publish {action}: {e}")
            
        return {"success": True, "message": "Device permanently removed. MQTT published.", "device_id": device_id, "action": action}
        
    updates = []
    values = []
    severity = "INFO"
    
    if action == "disable":
        updates.append("enabled = ?")
        values.append(0)
        severity = "WARNING"
    elif action == "enable":
        updates.append("enabled = ?")
        values.append(1)
        
    updates.extend(["status = ?", "claim_status = ?", "last_seen = ?", "last_seen_at = ?", "updated_at = ?"])
    values.extend(["online", "claimed", now, now, now])
    
    cur.execute(f"UPDATE devices SET {', '.join(updates)} WHERE rowid = ?", values + [rowid])
    
    cur.execute("INSERT INTO system_logs (timestamp, severity, event_type, details, action_taken, device_id, device_name, home_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (now, severity, f"Device {action.title()}", f"Device {name} was {action}d successfully.", f"MQTT {action.upper()}", first.get("device_id"), name, first.get("home_id")))
    conn.commit()
    
    try:
        from mqtt import mqtt_client
        from mqtt.publishers.device_command_publisher import publish_device_command
        publish_device_command(mqtt_client, first, action)
    except Exception as e:
        print(f"[MQTT ERROR] Failed to publish {action}: {e}")
        
    return {"success": True, "message": f"{action.upper()} completed. MQTT published.", "device_id": device_id, "action": action}

@router.post("/final-devices/normalize-demo-status")
def normalize_demo_status(conn: sqlite3.Connection = Depends(get_db_connection)):
    cur = conn.cursor()
    cur.execute("UPDATE devices SET status = 'online', enabled = 1")
    conn.commit()
    return {"success": True, "message": "Devices normalized to online/enabled"}

@router.get("/final-devices/{device_id}/info")
def get_device_info(device_id: str, conn: sqlite3.Connection = Depends(get_db_connection)):
    try:
        cur = conn.cursor()
        device_row = cur.execute("SELECT * FROM devices WHERE device_id = ? OR id = ?", (device_id, device_id)).fetchone()
        if not device_row:
            return {"success": False, "message": "Device not found in database"}
        
        device = dict(device_row)
        return {
            "success": True,
            "data": {
                "Device Name": device.get("device_name", "N/A"),
                "Device ID": device.get("device_id", "N/A"),
                "Device Type": device.get("device_type", "N/A"),
                "Status": device.get("status", "N/A"),
                "Enabled": "Yes" if device.get("enabled") else "No",
                "Home ID": device.get("home_id", "N/A"),
                "Last Seen": device.get("last_seen", "N/A"),
                "Updated At": device.get("updated_at", "N/A"),
                "MQTT Topic": device.get("mqtt_topic", "Not available"),
                "IP Address": device.get("device_ip", "Not available"),
                "MAC Address": device.get("mac_address", "Not available"),
                "Firmware Version": device.get("firmware_version", "Not available"),
                "Camera Stream URL": device.get("camera_stream_url", "Not available"),
                "Camera Capture URL": device.get("camera_capture_url", "Not available"),
                "Claim Status": device.get("claim_status", "N/A"),
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"System Error: {str(e)}"}

@router.post("/homes-v3/{home_key}/delete")
@router.post("/homes-v4/{home_key}/delete")
def delete_home_route(home_key: str, conn: sqlite3.Connection = Depends(get_db_connection)):
    cur = conn.cursor()

    home = cur.execute(
        "SELECT id FROM homes WHERE id = ? OR home_code = ?",
        (home_key, home_key)
    ).fetchone()

    if not home:
        return {"success": False, "message": "Home not found"}

    actual_home_id = home[0]

    # Delete child records first
    cur.execute(
        "DELETE FROM devices WHERE home_id = ?",
        (actual_home_id,)
    )
    conn.commit()

    try:
        from database.connection.database import SessionLocal
        from database.models.family import FamilyMember
        db = SessionLocal()
        try:
            db.query(FamilyMember).filter(FamilyMember.home_id == actual_home_id).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()

        cur.execute(
            "DELETE FROM door_events WHERE home_id = ?",
            (actual_home_id,)
        )

        cur.execute(
            "DELETE FROM face_events WHERE home_id = ?",
            (actual_home_id,)
        )

        cur.execute(
            "DELETE FROM persons WHERE home_id = ?",
            (actual_home_id,)
        )

        cur.execute(
            "DELETE FROM energy_readings WHERE home_id = ?",
            (actual_home_id,)
        )

    except sqlite3.OperationalError:
        pass

    # Finally delete the home
    cur.execute(
        "DELETE FROM homes WHERE id = ?",
        (actual_home_id,)
    )

    conn.commit()

    return {
        "success": True,
        "message": "Home deleted successfully"
    }
        
    # 3. Finally, delete the parent
    cur.execute("DELETE FROM homes WHERE id = ?", (actual_home_id,))
    
    conn.commit()
    return {"success": True, "message": "Home deleted successfully"}

@router.delete("/logs/{log_id}")
@router.delete("/logs-final/{log_id}")
@router.delete("/security-logs/{log_id}")
def delete_log(log_id: str, conn: sqlite3.Connection = Depends(get_db_connection)):
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM system_logs WHERE id = ?", (log_id,))
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"[WARNING] Missing table system_logs on delete. Error: {e}")
    return {"success": True}

@router.delete("/logs/bulk")
@router.delete("/logs-final/bulk")
@router.post("/logs-final/bulk")
@router.post("/security-logs/delete-filtered")
async def delete_logs_bulk(request: Request, conn: sqlite3.Connection = Depends(get_db_connection)):
    try:
        payload = await request.json()
    except Exception:
        payload = {}
        
    search = payload.get("search", "").strip()
    date_filter = payload.get("date", "").strip()
    actor_filter = payload.get("actor", "").strip()
    event_filter = payload.get("event_type", "").strip()
    severity_filter = payload.get("severity", "").strip()
    
    cur = conn.cursor()
    try:
        logs = [dict(r) for r in cur.execute("SELECT * FROM system_logs").fetchall()]
    except sqlite3.OperationalError as e:
        print(f"[WARNING] Missing table system_logs on bulk delete. Error: {e}")
        return {"success": False, "message": "Missing table"}
        
    def lower(val):
        return str(val or "").strip().lower()

    def get_device_id(text):
        import re
        match = re.search(r'\b(?:DOOR|METER|CAM)-HOME[0-9]+-\d+\b', text, re.IGNORECASE)
        return match.group(0).upper() if match else ""

    def get_apartment(device_id):
        import re
        match = re.search(r'(?:DOOR|METER|CAM)-HOME0*([0-9]+)-', str(device_id or ""), re.IGNORECASE)
        return str(int(match.group(1))) if match else ""

    def get_actor_bucket(val):
        raw = lower(val)
        if not raw: return ""
        if "system owner" in raw or "system_owner" in raw or "dashboard" in raw: return "System Owner"
        if "admin app" in raw or "flutter" in raw or "owner app" in raw or "app settings" in raw or "family management" in raw: return "Admin App"
        if "server" in raw or "esp32" in raw or "device" in raw or "face recognition" in raw or "energy warning" in raw or "system security" in raw or "system error" in raw: return "Server"
        return val

    ids_to_delete = []
    is_number_search = search.isdigit()
    search_lower = lower(search)

    for log in logs:
        action = str(log.get("action_taken") or "").upper()
        event_type = str(log.get("event_type") or "")
        actor_raw = str(log.get("actor") or "")
        severity = str(log.get("severity") or "")
        
        # normalize actor like frontend
        if lower(actor_raw) == "server" and "command" in event_type.lower() and action.startswith("MQTT"):
            actor_raw = "System Owner"
            
        text_for_device = f"{log.get('details') or ''} {log.get('action_taken') or ''} {log.get('event_type') or ''}"
        device_id = get_device_id(text_for_device)
        apt = get_apartment(device_id)
        
        apartment = apt if apt else str(log.get("apartment_number") or log.get("home") or log.get("home_id") or "")
        actor = get_actor_bucket(actor_raw)
        
        text_full = f"{log.get('details') or ''} {log.get('action_taken') or ''} {log.get('event_type') or ''}".upper()
        if "APP SETTINGS UPDATED" in text_full or "APP ADMIN REGISTERED" in text_full or "APP PASSWORD RESET" in text_full:
            actor = "Admin App"
        
        matches_search = True
        if search:
            if is_number_search:
                matches_search = (lower(apartment) == search_lower)
            else:
                matches_search = (search_lower in lower(actor))
                
        t_val = str(log.get("timestamp") or log.get("created_at") or "").strip()
        date_key = t_val[:10] if len(t_val) >= 10 else ""
        
        matches_date = (not date_filter) or (date_key == date_filter)
        matches_actor = (not actor_filter) or (actor == actor_filter)
        matches_event = (not event_filter) or (event_type == event_filter)
        matches_severity = (not severity_filter) or (severity == severity_filter)
        
        if matches_search and matches_date and matches_actor and matches_event and matches_severity:
            ids_to_delete.append(log["id"])

    if ids_to_delete:
        for i in range(0, len(ids_to_delete), 100):
            chunk = ids_to_delete[i:i + 100]
            placeholders = ",".join("?" for _ in chunk)
            cur.execute(f"DELETE FROM system_logs WHERE id IN ({placeholders})", chunk)
        conn.commit()
        
    return {"success": True, "message": f"Deleted {len(ids_to_delete)} logs", "deleted": len(ids_to_delete)}
