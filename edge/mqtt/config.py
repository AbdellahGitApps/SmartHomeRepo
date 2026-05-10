import os

class MQTTConfig:
    BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "127.0.0.1")
    BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", 1883))
    CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "edge_backend_client")
    USERNAME = os.getenv("MQTT_USERNAME", None)
    PASSWORD = os.getenv("MQTT_PASSWORD", None)
    KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", 60))
    RECONNECT_DELAY = int(os.getenv("MQTT_RECONNECT_DELAY", 5))
