import time
import logging
import paho.mqtt.client as mqtt
from typing import Callable, Dict

from .config import MQTTConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MQTTClient:
    """
    Central MQTT Client for Smart Home Edge System
    Handles connection, subscriptions, publishing, and routing.
    """

    def __init__(self):
        self.client = mqtt.Client(client_id=MQTTConfig.CLIENT_ID)

        # Optional authentication
        if MQTTConfig.USERNAME and MQTTConfig.PASSWORD:
            self.client.username_pw_set(
                MQTTConfig.USERNAME,
                MQTTConfig.PASSWORD
            )

        # Callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        # topic -> callback
        self.callbacks: Dict[str, Callable] = {}

        self._connected = False

    # =========================
    # CONNECTION EVENTS
    # =========================

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            logger.info(
                f"Connected to MQTT Broker at "
                f"{MQTTConfig.BROKER_HOST}:{MQTTConfig.BROKER_PORT}"
            )

            # Resubscribe after reconnect
            for topic in self.callbacks.keys():
                self.client.subscribe(topic)
                logger.info(f"Subscribed: {topic}")

        else:
            logger.error(f"MQTT connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        logger.warning(f"MQTT disconnected (code {rc})")

        if rc != 0:
            logger.info("Auto-reconnecting...")
            self._reconnect()

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode("utf-8")

        logger.debug(f"[MQTT] {topic} → {payload}")

        # Direct match
        if topic in self.callbacks:
            try:
                self.callbacks[topic](topic, payload)
            except Exception as e:
                logger.error(f"Handler error ({topic}): {e}")
            return

        # Wildcard match
        for sub_topic, callback in self.callbacks.items():
            if mqtt.topic_matches_sub(sub_topic, topic):
                try:
                    callback(topic, payload)
                except Exception as e:
                    logger.error(f"Wildcard handler error ({topic}): {e}")

    # =========================
    # CORE FUNCTIONS
    # =========================

    def connect(self):
        try:
            logger.info("Connecting to MQTT broker...")
            self.client.connect(
                MQTTConfig.BROKER_HOST,
                MQTTConfig.BROKER_PORT,
                MQTTConfig.KEEPALIVE
            )
            self.client.loop_start()

        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
            self._reconnect()

    def _reconnect(self):
        while True:
            try:
                time.sleep(MQTTConfig.RECONNECT_DELAY)
                self.client.reconnect()
                logger.info("Reconnected successfully")
                break
            except Exception as e:
                logger.error(f"Reconnect failed: {e}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        self._connected = False
        logger.info("MQTT disconnected cleanly")

    # =========================
    # SUBSCRIBE / PUBLISH
    # =========================

    def subscribe(self, topic: str, callback: Callable):
        self.callbacks[topic] = callback

        if self._connected:
            self.client.subscribe(topic)
            logger.info(f"Subscribed to {topic}")

    def subscribe_all(self):
        """
        Placeholder for future topic grouping system
        (used by main.py)
        """
        logger.info("subscribe_all() called - implement in routes/handlers")

    def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False):
        if self._connected:
            self.client.publish(topic, payload, qos, retain)
            logger.debug(f"Published → {topic}: {payload}")
        else:
            logger.error("Publish failed: MQTT not connected")

    # =========================
    # STATUS
    # =========================

    def is_connected(self) -> bool:
        return self._connected