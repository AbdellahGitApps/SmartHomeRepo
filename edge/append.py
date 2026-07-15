EXTRA_ROUTERS = """
from services.energy_monitoring_service import (
    get_latest_energy_reading,
    get_energy_logs,
)
from ai.energy_model.energy_aggregation import get_today_consumption

@router.get("/security-logs-data")
@router.get("/logs")
def get_security_logs(limit: int = 100, conn: sqlite3.Connection = Depends(get_db_connection)):
    cur = conn.cursor()
    logs = [dict(r) for r in cur.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
    return {"success": True, "logs": logs}

@router.get("/final-qa/homes-lite")
def get_homes_lite(conn: sqlite3.Connection = Depends(get_db_connection)):
    cur = conn.cursor()
    homes = [dict(r) for r in cur.execute("SELECT id, name, home_code, apartment_number FROM homes").fetchall()]
    return {"success": True, "homes": homes}

@router.get("/energy-page-data-v2")
def get_energy_page_data(conn: sqlite3.Connection = Depends(get_db_connection)):

    cur = conn.cursor()

    homes = [
        dict(r)
        for r in cur.execute(
            "SELECT * FROM homes ORDER BY id"
        ).fetchall()
    ]

    energy_records = []

    for home in homes:

        device = cur.execute(
            '''
            SELECT device_id, device_name
            FROM devices
            WHERE home_id = ?
            AND device_type = 'energy_monitor'
            LIMIT 1
            ''',
            (home["id"],),
        ).fetchone()

        if device is None:
            continue

        device = dict(device)

        latest = get_latest_energy_reading(device["device_id"])
        history = get_energy_logs(
    limit=20,
    device_id=device["device_id"],
)
        today = get_today_consumption(device["device_id"])

        energy_records.append(
            {
                "home_id": home["id"],
                "home_name": home["name"],
                "device_id": device["device_id"],
                "device_name": device["device_name"],
                "apartment_number": home.get("apartment_number"),
                "current_power_w": latest.get("watts", 0) if latest else 0,
                "current_voltage": latest.get("voltage", 0) if latest else 0,
                "current_current": latest.get("current", 0) if latest else 0,
                "latest_timestamp": latest.get("timestamp") if latest else None,
                "latest_timestamp_label": latest.get("timestamp") if latest else "No readings yet",
                "monthly_forecast_kwh": round(today * 30, 2),
                "has_readings": latest is not None,
                "daily_kwh": today,
                "history": history,
            }
        )

    return {
        "success": True,
        "devices": energy_records,
        "selected_device_id": energy_records[0]["device_id"] if energy_records else None,
        "homes_count": len(homes),
    }

@router.post("/devices/{device_id}/actions/{action}")
@router.post("/final-devices/{device_id}/actions/{action}")
@router.post("/final-devices-v3/{device_id}/actions/{action}")
@router.post("/final-devices-v4/{device_id}/actions/{action}")
@router.post("/final-devices-v6/{device_id}/actions/{action}")
@router.post("/d7-final-device-action/{device_id}/{action}")
@router.post("/d7r2-device-action/{device_id}/{action}")
@router.post("/final-devices-v5/{device_id}/remove")
def device_action(device_id: str, action: str = "remove", conn: sqlite3.Connection = Depends(get_db_connection)):
    action = action.lower().strip()
    if action == "delete": action = "remove"
    if action not in {"restart", "enable", "disable", "remove"}:
        raise HTTPException(status_code=400, detail="Unsupported device action")
        
    cur = conn.cursor()
    devices = cur.execute("SELECT rowid, * FROM devices WHERE device_id = ? OR id = ?", (device_id, device_id)).fetchall()
    if not devices:
        return {"success": False, "message": "Device not found"}
        
    first = dict(devices[0])
    rowid = first["rowid"]
    name = first.get("device_name") or device_id
    
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if action == "remove":
        cur.execute("DELETE FROM devices WHERE rowid = ?", (rowid,))
        cur.execute("INSERT INTO system_logs (timestamp, severity, event_type, details, action_taken) VALUES (?, ?, ?, ?, ?)",
                    (now, "WARNING", "Device Remove", f"Remove command sent to {name}", "MQTT REMOVE"))
        conn.commit()
        return {"success": True, "message": "Device removed from system.", "device_id": device_id, "action": action}
        
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
    cur.execute("INSERT INTO system_logs (timestamp, severity, event_type, details, action_taken) VALUES (?, ?, ?, ?, ?)",
                (now, severity, f"Device {action.title()}", f"{action.title()} command sent to {name}", f"MQTT {action.upper()}"))
    conn.commit()
    
    return {"success": True, "message": f"{action.upper()} completed.", "device_id": device_id, "action": action}

@router.post("/final-devices/normalize-demo-status")
def normalize_demo_status(conn: sqlite3.Connection = Depends(get_db_connection)):
    cur = conn.cursor()
    cur.execute("UPDATE devices SET status = 'online', enabled = 1")
    conn.commit()
    return {"success": True, "message": "Devices normalized to online/enabled"}

@router.post("/homes-v3/{home_key}/delete")
@router.post("/homes-v4/{home_key}/delete")
def delete_home_route(home_key: str, conn: sqlite3.Connection = Depends(get_db_connection)):
    cur = conn.cursor()
    cur.execute("DELETE FROM homes WHERE id = ? OR home_code = ?", (home_key, home_key))
    cur.execute("DELETE FROM devices WHERE home_id = ?", (home_key,))
    conn.commit()
    return {"success": True, "message": "Home deleted successfully"}

@router.delete("/logs/{log_id}")
@router.delete("/logs-final/{log_id}")
@router.delete("/security-logs/{log_id}")
def delete_log(log_id: str, conn: sqlite3.Connection = Depends(get_db_connection)):
    cur = conn.cursor()
    cur.execute("DELETE FROM system_logs WHERE id = ?", (log_id,))
    conn.commit()
    return {"success": True}

@router.delete("/logs/bulk")
@router.delete("/logs-final/bulk")
@router.post("/logs-final/bulk")
@router.post("/security-logs/delete-filtered")
def delete_logs_bulk(conn: sqlite3.Connection = Depends(get_db_connection)):
    cur = conn.cursor()
    cur.execute("DELETE FROM system_logs")
    conn.commit()
    return {"success": True, "message": "Logs cleared"}
"""

import re

# Append to routers/dashboard.py
with open("e:/SmartHomeMobileApp/edge/routers/dashboard.py", "a", encoding="utf-8") as f:
    f.write(EXTRA_ROUTERS)

# Read main.py
with open("e:/SmartHomeMobileApp/edge/main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace active routes with -old
replacements = [
    (r'@app.get\("/api/dashboard/security-logs-data"\)', '@app.get("/api/dashboard/security-logs-data-old")'),
    (r'@app.get\("/api/dashboard/logs"\)', '@app.get("/api/dashboard/logs-old")'),
    (r'@app.post\("/api/dashboard/devices/\{device_id\}/actions/\{action\}"\)', '@app.post("/api/dashboard/devices/{device_id}/actions/{action}-old")'),
    (r'@app.post\("/api/dashboard/final-devices/\{device_id\}/actions/\{action\}"\)', '@app.post("/api/dashboard/final-devices/{device_id}/actions/{action}-old")'),
    (r'@app.post\("/api/dashboard/final-devices/normalize-demo-status"\)', '@app.post("/api/dashboard/final-devices/normalize-demo-status-old")'),
    (r'@app.post\("/api/dashboard/final-devices-v3/\{device_key\}/actions/\{action\}"\)', '@app.post("/api/dashboard/final-devices-v3/{device_key}/actions/{action}-old")'),
    (r'@app.post\("/api/dashboard/homes-v3/\{home_key\}/delete"\)', '@app.post("/api/dashboard/homes-v3/{home_key}/delete-old")'),
    (r'@app.post\("/api/dashboard/final-devices-v4/\{device_key\}/actions/\{action\}"\)', '@app.post("/api/dashboard/final-devices-v4/{device_key}/actions/{action}-old")'),
    (r'@app.post\("/api/dashboard/homes-v4/\{home_key\}/delete"\)', '@app.post("/api/dashboard/homes-v4/{home_key}/delete-old")'),
    (r'@app.post\("/api/dashboard/final-devices-v5/\{device_key\}/remove"\)', '@app.post("/api/dashboard/final-devices-v5/{device_key}/remove-old")'),
    (r'@app.post\("/api/dashboard/final-devices-v6/\{device_key\}/actions/\{action\}"\)', '@app.post("/api/dashboard/final-devices-v6/{device_key}/actions/{action}-old")'),
    (r'@app.get\("/api/dashboard/final-qa/homes-lite"\)', '@app.get("/api/dashboard/final-qa/homes-lite-old")'),
    (r'@app.post\("/api/dashboard/d7-final-device-action/\{device_key\}/\{action\}"\)', '@app.post("/api/dashboard/d7-final-device-action/{device_key}/{action}-old")'),
    (r'@app.post\("/api/dashboard/d7r2-device-action/\{device_key\}/\{action\}"\)', '@app.post("/api/dashboard/d7r2-device-action/{device_key}/{action}-old")'),
    (r'@app.get\("/api/dashboard/energy-page-data-v2"\)', '@app.get("/api/dashboard/energy-page-data-v2-old")'),
    (r'@app.delete\("/api/dashboard/logs/\{log_id\}"\)', '@app.delete("/api/dashboard/logs/{log_id}-old")'),
    (r'@app.delete\("/api/dashboard/logs/bulk"\)', '@app.delete("/api/dashboard/logs/bulk-old")'),
    (r'@app.delete\("/api/dashboard/logs-final/\{log_id\}"\)', '@app.delete("/api/dashboard/logs-final/{log_id}-old")'),
    (r'@app.delete\("/api/dashboard/logs-final/bulk"\)', '@app.delete("/api/dashboard/logs-final/bulk-old")'),
    (r'@app.delete\("/api/dashboard/security-logs/\{log_id\}"\)', '@app.delete("/api/dashboard/security-logs/{log_id}-old")'),
    (r'@app.post\("/api/dashboard/security-logs/delete-filtered"\)', '@app.post("/api/dashboard/security-logs/delete-filtered-old")'),
    (r'@app.post\("/api/dashboard/logs-final/bulk"\)', '@app.post("/api/dashboard/logs-final/bulk-old")'),
]

for old, new in replacements:
    content = re.sub(old, new, content)

with open("e:/SmartHomeMobileApp/edge/main.py", "w", encoding="utf-8") as f:
    f.write(content)
