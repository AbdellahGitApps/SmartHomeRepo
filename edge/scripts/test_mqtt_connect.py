import time

from mqtt import mqtt_client

mqtt_client.connect()

time.sleep(3)

print(
    "Connected:",
    mqtt_client.is_connected()
)