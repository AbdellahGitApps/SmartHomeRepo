# Base topics
HOME_BASE = "home"
DEVICE_BASE = "device"

# Energy topics
HOME_ENERGY_TOPIC = f"{HOME_BASE}/+/energy"
HOME_ENERGY_SYNC_TOPIC = f"{HOME_BASE}/+/energy/sync"

# Door control topics
HOME_DOOR_STATUS_TOPIC = f"{HOME_BASE}/+/door/status"
HOME_DOOR_CONTROL_TOPIC = f"{HOME_BASE}/+/door/control"

# Status and Notifications
HOME_STATUS_TOPIC = f"{HOME_BASE}/status"
DEVICE_STATUS_TOPIC = f"{DEVICE_BASE}/+/status"
HOME_NOTIFICATION_TOPIC = f"{HOME_BASE}/notifications"

def get_device_control_topic(device_id: str) -> str:
    return f"{DEVICE_BASE}/{device_id}/control"
