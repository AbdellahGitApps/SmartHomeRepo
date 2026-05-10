from ..topics import HOME_STATUS_TOPIC, DEVICE_STATUS_TOPIC
from ..handlers.status_handler import handle_device_status

def setup_status_subscriptions(mqtt_client):
    """
    Subscribe to device and home status topics.
    """
    mqtt_client.subscribe(HOME_STATUS_TOPIC, handle_device_status)
    mqtt_client.subscribe(DEVICE_STATUS_TOPIC, handle_device_status)
