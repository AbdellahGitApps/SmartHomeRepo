import os
SERVER_PUBLIC_URL = os.getenv("SERVER_PUBLIC_URL", "http://smarthome.local:8000")
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "smarthome.local")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
