import json
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.models.device import Device
from database.models.home import Home
from database.repositories.device_repository import DeviceRepository

from services.face_ai_service import FaceAIService





_face_ai = FaceAIService()


def process_uploaded_image(
    image_path: str,
    device_id: str,
    home_id: int
):
    result = _face_ai.recognize_image(
        image_path,
        home_id=home_id,
        device_id=device_id
    )

    print(
        f"[FACE AI] "
        f"device={device_id} "
        f"home={home_id} "
        f"result={result}"
    )

    return result


def publish_device_event(
    device_id: str,
    event_type: str,
    payload: dict
):
    """
    FUTURE INTEGRATION HOOK:
    MQTT & Flutter Notifications
    """
    pass


class ImageUploadService:

    @staticmethod
    def upload_image(
        db: Session,
        token: str,
        file: UploadFile
    ) -> dict:

        # 1. Validate device token
        device = DeviceRepository.get_device_by_token(
            db,
            token
        )

        if not device:
            raise HTTPException(
                status_code=401,
                detail="Invalid device token"
            )

        if not getattr(device, "enabled", True):
            raise HTTPException(
                status_code=403,
                detail="Device is disabled"
            )

        # 2. Resolve associated home
        home_id = device.home_id

        home_obj = (
            db.query(Home)
            .filter(Home.id == home_id)
            .first()
        )

        home_label = "System"

        if home_obj:
            if home_obj.apartment_number:
                home_label = (
                    f"Apartment "
                    f"{home_obj.apartment_number}"
                )

            elif home_obj.home_code:
                home_label = home_obj.home_code

            else:
                home_label = f"Home {home_obj.id}"

        # 3. Create upload directory
        edge_dir = Path(__file__).resolve().parents[1]

        upload_dir = (
            edge_dir /
            "uploads" /
            f"home_{home_id}"
        )

        upload_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        # 4. Generate image path
        timestamp_str = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        filename = f"{timestamp_str}.jpg"

        file_path = upload_dir / filename

        relative_path = (
            f"uploads/home_{home_id}/{filename}"
        )

        # 5. Save image
        try:
            content = file.file.read()

            with open(file_path, "wb") as f:
                f.write(content)

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to save uploaded image: "
                    f"{str(e)}"
                )
            )

        # 6. Event Logging
        details_dict = {
            "device_id": device.device_id,
            "home_id": home_id,
            "timestamp": datetime.now().isoformat(),
            "image_path": relative_path,
        }

        try:
            db.execute(
                text("""
                    INSERT INTO system_logs (
                        timestamp,
                        severity,
                        home,
                        event_type,
                        details,
                        action_taken
                    )
                    VALUES (
                        :timestamp,
                        :severity,
                        :home,
                        :event_type,
                        :details,
                        :action_taken
                    )
                """),
                {
                    "timestamp": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "severity": "info",
                    "home": home_label,
                    "event_type": "IMAGE_RECEIVED",
                    "details": json.dumps(details_dict),
                    "action_taken": "IMAGE_UPLOAD",
                },
            )

            db.commit()

        except Exception as log_error:
            print(
                "[LOGGING ERROR] "
                f"Failed to record IMAGE_RECEIVED "
                f"event: {log_error}"
            )

                # 7. Face Recognition Hook
        face_result = None

        try:

            face_result = process_uploaded_image(
                str(file_path),
                device.device_id,
                home_id
            )

            # Save Face Event + Door Action
            if (
                face_result
                and face_result.get("success")
            ):

                if face_result.get("matched"):

                    print(
                        f"[DOOR] Unlock requested "
                        f"for {face_result.get('person_name')} (via new engine)"
                    )

                else:

                    print(
                        "[DOOR] Access denied - "
                        "unknown person (via new engine)"
                    )

            publish_device_event(
                device.device_id,
                "IMAGE_RECEIVED",
                {
                    "image_path": relative_path,
                    "home_id": home_id,
                    "face_result": face_result,
                }
            )

        except Exception as hook_error:

            print(
                f"[HOOK ERROR] "
                f"Future integration hook failed: "
                f"{hook_error}"
            )
            
        # 8. Return result
        return {
            "success": True,
            "device_id": device.device_id,
            "home_id": str(home_id),
            "image_path": relative_path,
            "face_recognition": face_result,
        }