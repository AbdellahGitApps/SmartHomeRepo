import json
import logging
from .. import mqtt_client
from ..topics import HOME_ENERGY_SYNC_TOPIC

logger = logging.getLogger(__name__)

def publish_energy_sync_request(device_id: str):
    """
    Request energy sync or calibration from a specific device.
    """
    topic = HOME_ENERGY_SYNC_TOPIC.replace('+', device_id)
    payload = json.dumps({"action": "sync"})
    
    logger.info(f"Sending energy sync request to {topic}")
    mqtt_client.publish(topic, payload)
