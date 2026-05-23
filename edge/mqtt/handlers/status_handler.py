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
        state = data.get("state")
        
        logger.info(f"Device Status Update on {topic}: {state}")
        
        # TODO: Forward data to service layer
        # device_service.update_device_presence(topic, state)
        
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
        
        if not device_id or not device_token:
            logger.warning(f"Invalid registration payload: {payload}")
            return
            
        logger.info(f"Registering device {device_id}")
        
        from database.connection.database import SessionLocal
        import services.device_service as device_service
        
        db = SessionLocal()
        try:
            success = device_service.register_device(db, device_id, device_token)
            if success:
                logger.info(f"Device {device_id} successfully authenticated and is online.")
            else:
                logger.warning(f"Device {device_id} authentication failed (invalid token or id).")
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
        
        if not device_id:
            logger.warning(f"Invalid heartbeat payload: {payload}")
            return
            
        logger.debug(f"Heartbeat received from device {device_id}")
        
        from database.connection.database import SessionLocal
        import services.device_service as device_service
        
        db = SessionLocal()
        try:
            success = device_service.heartbeat_device(db, device_id)
            if not success:
                logger.warning(f"Heartbeat received for unregistered device {device_id}")
        finally:
            db.close()
            
    except json.JSONDecodeError:
        logger.error(f"Failed to decode heartbeat payload: {payload}")
    except Exception as e:
        logger.error(f"Error processing heartbeat: {e}")

