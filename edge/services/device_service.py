
def _home_id_code_for_device(home) -> str:
    apartment_number = getattr(home, "apartment_number", None)
    digits = "".join(ch for ch in str(apartment_number or "") if ch.isdigit())

    if digits:
        return f"HOME-{int(digits):03d}"

    return f"HOME-{int(getattr(home, 'id', 0) or 0):03d}"

import secrets
import random
import string
from sqlalchemy.orm import Session
from database.models.home import Home
from database.models.device import Device


def generate_device_id(
    db: Session = None,
    home_id: int = None,
    home_code: str = None,
    device_type: str = None,
) -> str:
    """
    Generate device_id in the format: {TYPE}-{HOME}-{INDEX}
    Example: DOOR-HOME36-001
    """
    type_prefix = "DOOR" if device_type == "smart_door" else "METER"
    home_clean = (home_code or "HOME").replace("-", "").upper()

    if db and home_id and device_type:
        existing_devices = (
            db.query(Device.device_id)
            .filter(Device.home_id == home_id, Device.device_type == device_type)
            .all()
        )
        max_seq = 0
        for (did,) in existing_devices:
            if did:
                parts = str(did).split("-")
                if len(parts) >= 3 and parts[-1].isdigit():
                    seq_val = int(parts[-1])
                    if seq_val > max_seq:
                        max_seq = seq_val
        count = max_seq
    else:
        count = 0

    index_str = f"{count + 1:03d}"
    return f"{type_prefix}-{home_clean}-{index_str}"


def generate_device_token() -> str:
    """
    Generate a secure random token for the device.
    """
    return f"tok_{secrets.token_hex(8)}"


def generate_claim_code(home_code: str) -> str:
    """
    Generate a claim code in the format: HOME36-9K2P
    """
    home_clean = home_code.replace("-", "").upper()
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{home_clean}-{suffix}"


def generate_mqtt_topic(home_code: str, device_type: str, device_id: str) -> str:
    """
    Generate the MQTT topic in the format: home/{home_code}/{device_type}/{device_id}
    """
    return f"home/{home_code}/{device_type}/{device_id}"


def create_device(
    db: Session, home_id: int, device_name: str, device_type: str
) -> Device:
    """
    Full device provisioning logic. Reject invalid types, query home_code,
    generate all unique identifiers and tokens, and insert Device into DB.
    """
    if device_type not in ["smart_door", "energy_monitor"]:
        raise ValueError(
            "Invalid device type. Allowed types: smart_door, energy_monitor"
        )

    home = db.query(Home).filter(Home.id == home_id).first()
    if not home:
        raise ValueError(f"Home with id {home_id} not found")

    device_id = generate_device_id(db, home_id, _home_id_code_for_device(home), device_type)
    device_token = generate_device_token()
    claim_code = generate_claim_code(_home_id_code_for_device(home))
    mqtt_topic = generate_mqtt_topic(_home_id_code_for_device(home), device_type, device_id)

    db_device = Device(
        home_id=home_id,
        device_id=device_id,
        device_name=device_name,
        device_type=device_type,
        device_token=device_token,
        mqtt_topic=mqtt_topic,
        status="offline",
        claim_code=claim_code,
        claim_status="pending",
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


def get_all_devices(db: Session):
    from database.repositories.device_repository import DeviceRepository
    return DeviceRepository.get_all(db)


def get_devices_by_home_id(db: Session, home_id: int):
    from database.repositories.device_repository import DeviceRepository
    return DeviceRepository.get_by_home_id(db, home_id)


def register_device(db: Session, device_id: str, device_token: str) -> bool:
    """
    Validate device token and set status to online, updating last_seen.
    """
    from datetime import datetime
    from database.repositories.device_repository import DeviceRepository
    
    device = DeviceRepository.get_by_device_id(db, device_id)
    if not device:
        return False
    if device.device_token != device_token:
        return False
        
    device.status = "online"
    device.last_seen = datetime.now()
    db.commit()
    return True


def heartbeat_device(db: Session, device_id: str) -> bool:
    """
    Update last_seen on heartbeat to keep device online.
    """
    from datetime import datetime
    from database.repositories.device_repository import DeviceRepository
    
    device = DeviceRepository.get_by_device_id(db, device_id)
    if not device:
        return False
        
    device.status = "online"
    device.last_seen = datetime.now()
    db.commit()
    return True


def mark_inactive_devices_offline(db: Session) -> int:
    """
    Find all devices that haven't been seen in the last 2 minutes and mark them offline.
    """
    from datetime import datetime, timedelta
    
    cutoff = datetime.now() - timedelta(minutes=2)
    
    devices = db.query(Device).filter(Device.status == "online").all()
    count = 0
    for device in devices:
        if not device.last_seen or device.last_seen < cutoff:
            device.status = "offline"
            count += 1
            
    if count > 0:
        db.commit()
    return count




CAMERA_DEVICE_TYPES = {
    "smart_door",
    "esp32_cam",
    "door_camera",
    "camera",
}


def is_camera_device(device_type):
    if not device_type:
        return False
    return str(device_type).strip().lower() in CAMERA_DEVICE_TYPES


def build_camera_urls(device_ip, device_type):
    if not device_ip or not is_camera_device(device_type):
        return {
            "camera_stream_url": None,
            "camera_capture_url": None,
        }

    clean_ip = str(device_ip).strip().replace("http://", "").replace("https://", "").strip("/")

    return {
        "camera_stream_url": f"http://{clean_ip}/stream",
        "camera_capture_url": f"http://{clean_ip}/capture",
    }


def apply_device_network_fields(
    device,
    device_ip=None,
    mac_address=None,
    firmware_version=None,
):
    if device_ip:
        device.device_ip = device_ip
        urls = build_camera_urls(device_ip, getattr(device, "device_type", None))
        device.camera_stream_url = urls["camera_stream_url"]
        device.camera_capture_url = urls["camera_capture_url"]

    if mac_address:
        device.mac_address = mac_address

    if firmware_version:
        device.firmware_version = firmware_version

    return device


def validate_device_token(db: Session, token: str) -> bool:
    """
    Validate if a device exists with the given token and is enabled.
    """
    from database.repositories.device_repository import DeviceRepository
    device = DeviceRepository.get_device_by_token(db, token)
    return device is not None and getattr(device, "enabled", True)


def get_device_from_token(db: Session, token: str) -> Device:
    """
    Retrieve the Device object associated with the given token.
    """
    from database.repositories.device_repository import DeviceRepository
    return DeviceRepository.get_device_by_token(db, token)
