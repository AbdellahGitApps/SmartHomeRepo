from ..topics import HOME_ENERGY_TOPIC
from ..handlers.energy_handler import handle_energy_data

def setup_energy_subscriptions(mqtt_client):
    """
    Subscribe to energy-related topics.
    """
    mqtt_client.subscribe(HOME_ENERGY_TOPIC, handle_energy_data)
