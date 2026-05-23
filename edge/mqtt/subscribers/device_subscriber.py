from ..topics import HOME_DOOR_STATUS_TOPIC, HOME_NOTIFICATION_TOPIC
from ..handlers.door_handler import handle_door_status
from ..handlers.notification_handler import handle_notification
from ..handlers.status_handler import handle_device_register, handle_device_heartbeat

def setup_device_subscriptions(mqtt_client):
    """
    Subscribe to various device topics like door and notifications.
    """
    mqtt_client.subscribe(HOME_DOOR_STATUS_TOPIC, handle_door_status)
    mqtt_client.subscribe(HOME_NOTIFICATION_TOPIC, handle_notification)
    mqtt_client.subscribe("device/register", handle_device_register)
    mqtt_client.subscribe("device/heartbeat", handle_device_heartbeat)

