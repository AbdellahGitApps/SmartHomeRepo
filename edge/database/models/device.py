import uuid
import random
import string
from sqlalchemy import Column, Integer, String, ForeignKey
from database.connection.database import Base


def generate_claim_code():
    # Format: HOME-XXXXX where XXXXX is 5 random uppercase alphanumeric chars
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"HOME-{suffix}"


def generate_device_token():
    return f"tok_{uuid.uuid4().hex[:14]}"


def generate_device_id():
    return f"dev_{uuid.uuid4().hex[:14]}"


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    home_id = Column(Integer, ForeignKey("homes.id"), nullable=False)
    device_id = Column(String, unique=True, nullable=False, default=generate_device_id)
    device_name = Column(String, nullable=False)
    device_type = Column(String, nullable=False)  # ONLY: smart_door | energy_monitor
    device_token = Column(String, unique=True, nullable=False, default=generate_device_token)
    mqtt_topic = Column(String, unique=True, nullable=False)
    status = Column(String, default="offline")
    claim_code = Column(String, unique=True, nullable=True, default=generate_claim_code)
    claim_status = Column(String, default="pending")

