import json
import logging

logger = logging.getLogger(__name__)

def handle_notification(topic: str, payload: str):
    """
    Handle alerts and system notifications.
    topic format e.g.: home/notifications
    """
    try:
        data = json.loads(payload)
        level = data.get("level", "info")
        message = data.get("message", "")
        
        logger.info(f"System Notification [{level}]: {message}")
        
        # TODO: Forward data to service layer
        # notification_service.log_alert(level, message)
        
    except json.JSONDecodeError:
        logger.error(f"Failed to decode notification payload on {topic}")
    except Exception as e:
        logger.error(f"Error processing notification data: {e}")
