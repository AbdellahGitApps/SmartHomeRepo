import json
import logging

logger = logging.getLogger(__name__)

def handle_device_status(topic: str, payload: str):
    """
    Handle device online/offline status.
    topic format e.g.: device/esp32_01/status
    """
    try:
        data = json.loads(payload)
        state = data.get("state") or data.get("status") or ""
        state = state.lower().strip()
        
        parts = topic.split("/")
        if len(parts) < 3 or parts[0] != "device" or parts[2] != "status":
            return
        topic_ref = parts[1]
        
        logger.info(f"Device Status Update on {topic}: {state}")
        
        from core_database import get_database_path
        import sqlite3
        from datetime import datetime
        
        db_path = get_database_path()
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        try:
            device_row = cur.execute("SELECT * FROM devices WHERE device_id = ? OR id = ? OR device_token = ?", (topic_ref, topic_ref, topic_ref)).fetchone()
            if not device_row:
                payload_token = data.get("device_token")
                if payload_token:
                    device_row = cur.execute("SELECT * FROM devices WHERE device_token = ?", (payload_token,)).fetchone()
            
            if not device_row:
                logger.warning(f"Device status update received for unknown device/token: {topic_ref}")
                return
                
            device = dict(device_row)
            device_id = device.get("device_id")
            current_status = str(device.get("status") or "").lower().strip()
            device_name = device.get("device_name") or device_id
            home_id = device.get("home_id")
            
            if current_status == "restarting" and state == "online":
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 1. Update status to online in database
                cur.execute(
                    "UPDATE devices SET status = 'online', last_seen = ?, last_seen_at = ?, updated_at = ? WHERE device_id = ? OR id = ?",
                    (now, now, now, device_id, device_id)
                )
                
                # 2. Insert Security Log
                cur.execute(
                    "INSERT INTO system_logs (timestamp, severity, event_type, details, action_taken, device_id, device_name, home_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (now, "INFO", "Device Restarted", f"Device {device_name} restarted successfully.", "MQTT RESTART", device_id, device_name, home_id)
                )
                conn.commit()
                
                # 3. Publish Mobile Notification
                try:
                    from ..publishers.notification_publisher import publish_notification
                    publish_notification("info", f"Device {device_name} restarted successfully.")
                except Exception as e:
                    logger.error(f"Failed to publish notification: {e}")
            elif state:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cur.execute(
                    "UPDATE devices SET status = ?, last_seen = ?, last_seen_at = ?, updated_at = ? WHERE device_id = ? OR id = ?",
                    (state, now, now, now, device_id, device_id)
                )
                conn.commit()
                
        finally:
            conn.close()
            
    except json.JSONDecodeError:
        logger.error(f"Failed to decode status payload on {topic}")
    except Exception as e:
        logger.error(f"Error processing status data: {e}")


def handle_device_register(topic: str, payload: str):
    """
    Handle device registration/handshake.
    Expected payload:
    {
      "device_id": "...",
      "device_token": "...",
      "home_code": "..."
    }
    """
    try:
        data = json.loads(payload)
        device_id = data.get("device_id")
        device_token = data.get("device_token")
        
        if not device_token:
            logger.warning(f"Invalid registration payload: {payload}")
            return
            
        logger.info(f"Registering device {device_id or device_token}")
        
        from database.connection.database import SessionLocal
        import services.device_service as device_service
        
        db = SessionLocal()
        try:
            if device_id:
                success = device_service.register_device(db, device_id, device_token)
            else:
                success = device_service.register_device_by_token(db, device_token)
                
            if success:
                logger.info(f"Device {device_id or device_token} successfully authenticated and is online.")
            else:
                logger.warning(f"Device {device_id or device_token} authentication failed (invalid token or id).")
        finally:
            db.close()
            
    except json.JSONDecodeError:
        logger.error(f"Failed to decode registration payload: {payload}")
    except Exception as e:
        logger.error(f"Error registering device: {e}")


def handle_device_heartbeat(topic: str, payload: str):
    """
    Handle periodic device heartbeat.
    Expected payload:
    {
      "device_id": "...",
      "timestamp": "..."
    }
    """
    try:
        data = json.loads(payload)
        device_id = data.get("device_id")
        device_token = data.get("device_token")
        
        if not device_id and not device_token:
            logger.warning(f"Invalid heartbeat payload: {payload}")
            return
            
        logger.debug(f"Heartbeat received from device {device_id or device_token}")
        
        from database.connection.database import SessionLocal
        import services.device_service as device_service
        
        db = SessionLocal()
        try:
            if device_token:
                success = device_service.heartbeat_device_by_token(db, device_token)
            else:
                success = device_service.heartbeat_device(db, device_id)
                
            if not success:
                logger.warning(f"Heartbeat received for unregistered device {device_id or device_token}")
        finally:
            db.close()
            
    except json.JSONDecodeError:
        logger.error(f"Failed to decode heartbeat payload: {payload}")
    except Exception as e:
        logger.error(f"Error processing heartbeat: {e}")

