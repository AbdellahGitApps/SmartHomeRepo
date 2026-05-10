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
