from pathlib import Path
import cv2

from api.face_recognition_flow import (
    _detect_largest_face,
    _preprocess_face,
    _extract_embedding,
    _recognize_embedding,
)


class FaceAIService:

    def __init__(self):
        pass

    def recognize_image(
        self,
        image_path: str,
        home_id: int = 1,
        device_id: str = "test",
    ) -> dict:

        image_path = Path(image_path)

        if not image_path.exists():

            return {
                "success": False,
                "reason": "image_not_found"
            }

        image = cv2.imread(
            str(image_path)
        )

        if image is None:

            return {
                "success": False,
                "reason": "invalid_image"
            }

        box = _detect_largest_face(
            image
        )

        if box is None:

            return {
                "success": True,
                "matched": False,
                "reason": "no_face_detected"
            }

        try:

            face = _preprocess_face(
                image,
                box
            )

            embedding = _extract_embedding(
                face
            )

        except Exception as exc:

            return {
                "success": False,
                "reason": f"embedding_failed: {exc}"
            }

        result = _recognize_embedding(
            embedding=embedding,
            source="esp32_cam",
            snapshot_path=str(image_path),
            home_id=home_id,
        )

        return {
            "success": result.get("success", False),
            "matched": result.get("recognized", False),
            "person_id": result.get("person", {}).get("id") if result.get("person") else None,
            "person_name": result.get("person", {}).get("name") if result.get("person") else None,
            "score": result.get("score"),
            "snapshot_path": result.get("snapshot_path"),
        }