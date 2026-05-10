import json
import logging
from .. import mqtt_client
from ..topics import HOME_DOOR_CONTROL_TOPIC

logger = logging.getLogger(__name__)

def publish_door_command(door_id: str, command: str):
    """
    Publish unlock/lock commands to a specific door.
    command should be 'lock' or 'unlock'
    """
    topic = HOME_DOOR_CONTROL_TOPIC.replace('+', door_id)
    payload = json.dumps({"command": command})
    
    logger.info(f"Sending door command to {topic}: {command}")
    mqtt_client.publish(topic, payload)
