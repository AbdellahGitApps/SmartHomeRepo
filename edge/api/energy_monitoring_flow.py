from typing import Optional

from fastapi import (
    APIRouter,
    Request,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from pydantic import BaseModel

from database.connection.database import get_db
from services.device_service import get_device_from_token

from services.energy_monitoring_service import (
    record_energy_payload,
    get_latest_energy_reading,
    get_energy_logs,
    get_energy_status,
)

router = APIRouter()


class EnergyIngestRequest(BaseModel):
    device_id: Optional[str] = None
    voltage: Optional[float] = None
    current: Optional[float] = None
    watts: Optional[float] = None
    power: Optional[float] = None
    power_w: Optional[float] = None
    kwh_today: Optional[float] = None
    consumption_kwh: Optional[float] = None
    reading_date: Optional[str] = None
    timestamp: Optional[str] = None
    source: str = "api"


@router.get("/api/energy/status")
def api_energy_status():
    return get_energy_status()


@router.post("/api/energy/ingest")
def api_energy_ingest(
    request: Request,
    request_data: EnergyIngestRequest,
    db: Session = Depends(get_db),
):

    device_token = request.headers.get("device_token")

    if not device_token:
        raise HTTPException(
            status_code=400,
            detail="device_token is required",
        )

    device = get_device_from_token(db, device_token)

    if device is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid device token",
        )

    if not getattr(device, "enabled", True):
        raise HTTPException(
            status_code=403,
            detail="Device is disabled",
        )

    if device.device_type != "energy_monitor":
        raise HTTPException(
            status_code=400,
            detail="Invalid device type",
        )

    payload = request_data.model_dump()

    # Never trust the ESP32 identity
    payload["device_id"] = device.device_id
    payload["home_id"] = device.home_id

    return record_energy_payload(
        payload,
        source=request_data.source,
    )


@router.get("/api/energy/latest")
def api_energy_latest():
    return {
        "success": True,
        "latest": get_latest_energy_reading(),
    }


@router.get("/api/energy/logs")
def api_energy_logs(limit: int = 50):
    return {
        "success": True,
        "logs": get_energy_logs(limit),
    }


@router.post("/energy/ingest")
def legacy_energy_ingest(
    request: Request,
    request_data: EnergyIngestRequest,
    db: Session = Depends(get_db),
):

    device_token = request.headers.get("device_token")

    if not device_token:
        raise HTTPException(
            status_code=400,
            detail="device_token is required",
        )

    device = get_device_from_token(db, device_token)

    if device is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid device token",
        )

    if not getattr(device, "enabled", True):
        raise HTTPException(
            status_code=403,
            detail="Device is disabled",
        )

    if device.device_type != "energy_monitor":
        raise HTTPException(
            status_code=400,
            detail="Invalid device type",
        )

    payload = request_data.model_dump()

    payload["device_id"] = device.device_id
    payload["home_id"] = device.home_id

    return record_energy_payload(
        payload,
        source=request_data.source,
    )


@router.get("/energy/latest")
def legacy_energy_latest():
    return {
        "success": True,
        "latest": get_latest_energy_reading(),
    }


@router.get("/energy/logs")
def legacy_energy_logs(limit: int = 50):
    return {
        "success": True,
        "logs": get_energy_logs(limit),
    }