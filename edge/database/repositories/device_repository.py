from sqlalchemy.orm import Session

from database.models.device import Device


class DeviceRepository:

    @staticmethod
    def create(db: Session, device: Device):
        db.add(device)
        db.commit()
        db.refresh(device)
        return device

    @staticmethod
    def get_by_device_id(db: Session, device_id: str):
        return (
            db.query(Device)
            .filter(Device.device_id == device_id)
            .first()
        )

    @staticmethod
    def get_all(db: Session):
        return db.query(Device).all()

    @staticmethod
    def get_by_home_id(db: Session, home_id: int):
        return (
            db.query(Device)
            .filter(Device.home_id == home_id)
            .all()
        )

    @staticmethod
    def get_device_by_token(db: Session, token: str):
        return (
            db.query(Device)
            .filter(Device.device_token == token)
            .first()
        )

    @staticmethod
    def get_device_by_device_id(db: Session, device_id: str):
        return (
            db.query(Device)
            .filter(Device.device_id == device_id)
            .first()
        )

