import logging
from .mqtt_client import MQTTClient
from .subscribers.energy_subscriber import setup_energy_subscriptions
from .subscribers.status_subscriber import setup_status_subscriptions
from .subscribers.device_subscriber import setup_device_subscriptions

logger = logging.getLogger(__name__)

mqtt_client = MQTTClient()

def start_mqtt():
    """
    Initialize MQTT, setup subscriptions, and connect.
    """
    logger.info("Initializing MQTT Module...")
    setup_energy_subscriptions(mqtt_client)
    setup_status_subscriptions(mqtt_client)
    setup_device_subscriptions(mqtt_client)
    mqtt_client.connect()
    
def stop_mqtt():
    """
    Disconnect MQTT gracefully.
    """
    logger.info("Stopping MQTT Module...")
    mqtt_client.disconnect()

__all__ = ["start_mqtt", "stop_mqtt", "mqtt_client"]
