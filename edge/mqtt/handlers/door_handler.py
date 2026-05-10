import json
import logging

logger = logging.getLogger(__name__)

def handle_door_status(topic: str, payload: str):
    """
    Process door lock/unlock status.
    topic format e.g.: home/front_door/door/status
    """
    try:
        data = json.loads(payload)
        status = data.get("status")
        
        if not status:
            logger.warning(f"Invalid door payload on {topic}: {payload}")
            return
            
        logger.info(f"Door Status Update on {topic}: {status}")
        
        # TODO: Forward data to service layer
        # door_service.update_door_status(topic, status)
        
    except json.JSONDecodeError:
        logger.error(f"Failed to decode door payload on {topic}")
    except Exception as e:
        logger.error(f"Error processing door data: {e}")
