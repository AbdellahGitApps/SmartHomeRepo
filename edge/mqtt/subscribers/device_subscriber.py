from ..topics import HOME_DOOR_STATUS_TOPIC, HOME_NOTIFICATION_TOPIC
from ..handlers.door_handler import handle_door_status
from ..handlers.notification_handler import handle_notification

def setup_device_subscriptions(mqtt_client):
    """
    Subscribe to various device topics like door and notifications.
    """
    mqtt_client.subscribe(HOME_DOOR_STATUS_TOPIC, handle_door_status)
    mqtt_client.subscribe(HOME_NOTIFICATION_TOPIC, handle_notification)
