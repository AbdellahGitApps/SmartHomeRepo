import json
import logging

logger = logging.getLogger(__name__)


def handle_energy_data(topic: str, payload: str):
    try:
        data = json.loads(payload)

        if "voltage" not in data or "current" not in data:
            logger.warning(f"Invalid energy payload on {topic}: {payload}")
            return

        logger.info(f"Energy Data Received on {topic}: {data}")

        try:
            from services.energy_monitoring_service import record_energy_payload
            record_energy_payload(data, source="mqtt", topic=topic)
        except Exception as exc:
            logger.error(f"Failed to store energy reading: {exc}")

    except json.JSONDecodeError:
        logger.error(f"Failed to decode energy payload on {topic}")
    except Exception as e:
        logger.error(f"Error processing energy data: {e}")
