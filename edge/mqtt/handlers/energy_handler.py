import json
import logging

logger = logging.getLogger(__name__)

def handle_energy_data(topic: str, payload: str):
    """
    Process energy sensor data from ESP32.
    topic format e.g.: home/living_room/energy
    """
    try:
        data = json.loads(payload)
        # Validate payload
        if "voltage" not in data or "current" not in data:
            logger.warning(f"Invalid energy payload on {topic}: {payload}")
            return
            
        logger.info(f"Energy Data Received on {topic}: {data}")
        
        # TODO: Forward data to service layer
        # energy_service.process_reading(topic, data)
        
    except json.JSONDecodeError:
        logger.error(f"Failed to decode energy payload on {topic}")
    except Exception as e:
        logger.error(f"Error processing energy data: {e}")
