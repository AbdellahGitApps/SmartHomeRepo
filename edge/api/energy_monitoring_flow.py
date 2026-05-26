from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

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
def api_energy_ingest(request_data: EnergyIngestRequest):
    return record_energy_payload(
        request_data.model_dump(),
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
def legacy_energy_ingest(request_data: EnergyIngestRequest):
    return record_energy_payload(
        request_data.model_dump(),
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
