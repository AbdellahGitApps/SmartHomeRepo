import json
import logging
from .. import mqtt_client
from ..topics import HOME_NOTIFICATION_TOPIC

logger = logging.getLogger(__name__)

def publish_notification(level: str, message: str):
    """
    Send alerts or system notifications.
    """
    payload = json.dumps({
        "level": level,
        "message": message
    })
    
    logger.info(f"Publishing system notification: {level} - {message}")
    mqtt_client.publish(HOME_NOTIFICATION_TOPIC, payload)
