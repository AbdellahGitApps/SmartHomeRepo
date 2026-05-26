import json
import uuid
from datetime import datetime, timezone


def _device_to_dict(device):
    if device is None:
        return {}

    if isinstance(device, dict):
        return dict(device)

    try:
        return dict(device)
    except Exception:
        pass

    data = {}
    for key in [
        "id",
        "home_id",
        "device_id",
        "device_name",
        "name",
        "device_type",
        "mqtt_topic",
        "status",
        "enabled",
    ]:
        try:
            data[key] = device[key]
        except Exception:
            try:
                data[key] = getattr(device, key)
            except Exception:
                pass

    return data


def _publish_raw(mqtt_client, topic, payload_text):
    if mqtt_client is None:
        return False, "mqtt_client is None"

    try:
        if hasattr(mqtt_client, "publish"):
            result = mqtt_client.publish(topic, payload_text)
            return True, str(result)

        if hasattr(mqtt_client, "client") and hasattr(mqtt_client.client, "publish"):
            result = mqtt_client.client.publish(topic, payload_text)
            return True, str(result)

        if hasattr(mqtt_client, "mqtt_client") and hasattr(mqtt_client.mqtt_client, "publish"):
            result = mqtt_client.mqtt_client.publish(topic, payload_text)
            return True, str(result)
    except Exception as error:
        return False, str(error)

    return False, "No publish method found on mqtt_client"


def publish_device_command(
    mqtt_client,
    device,
    command,
    source="dashboard",
    actor_role="system_owner",
    extra=None,
):
    device_data = _device_to_dict(device)
    command = str(command or "").strip().lower()
    device_id = str(device_data.get("device_id") or device_data.get("id") or "").strip()
    base_topic = str(device_data.get("mqtt_topic") or "").strip()

    request_id = uuid.uuid4().hex[:12]
    now = datetime.now(timezone.utc).isoformat()

    payload = {
        "request_id": request_id,
        "command": command,
        "source": source,
        "actor_role": actor_role,
        "device_id": device_id,
        "device_type": device_data.get("device_type"),
        "home_id": device_data.get("home_id"),
        "timestamp": now,
    }

    if extra:
        payload.update(extra)

    topics = []

    if base_topic:
        topics.append(f"{base_topic}/cmd")
        topics.append(f"{base_topic}/control")

    if device_id:
        topics.append(f"device/{device_id}/cmd")
        topics.append(f"device/{device_id}/control")

    topics = list(dict.fromkeys(topics))
    payload_text = json.dumps(payload, ensure_ascii=False)

    results = []

    for topic in topics:
        published, result = _publish_raw(mqtt_client, topic, payload_text)
        results.append(
            {
                "topic": topic,
                "published": published,
                "result": result,
            }
        )

    return {
        "published": any(item["published"] for item in results),
        "request_id": request_id,
        "command": command,
        "topics": topics,
        "results": results,
        "payload": payload,
    }
