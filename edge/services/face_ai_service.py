from pathlib import Path

import cv2

from ai.face_model.face_detector import (
    FaceDetector,
    preprocess_for_arcface,
)

from ai.face_model.face_embedder import FaceEmbedder

from ai.face_model.recognizer import FaceRecognizer


class FaceAIService:

    def __init__(self):

        self.detector = FaceDetector()

        self.embedder = FaceEmbedder()

        self.recognizer = FaceRecognizer()

    def recognize_image(
        self,
        image_path: str,
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

        box = self.detector.detect_largest_face(
            image
        )

        if box is None:

            return {

                "success": True,

                "matched": False,

                "reason": "no_face_detected"

            }

        try:

            face = preprocess_for_arcface(
                image,
                box
            )

            embedding = self.embedder.embed(
                face
            )

        except Exception as exc:

            return {

                "success": False,

                "reason": f"embedding_failed: {exc}"

            }

        gallery = self.recognizer.load_gallery()

        if len(gallery) == 0:

            return {

                "success": True,

                "matched": False,

                "reason": "empty_gallery"

            }

        person_id, score = self.recognizer.match(

            embedding,

            gallery

        )

        if person_id is None:

            return {

                "success": True,

                "matched": False,

                "score": float(score)

            }

        person = self.recognizer.get_person(
            person_id
        )

        return {

            "success": True,

            "matched": True,

            "person_id": person_id,

            "person_name": person.name if person else None,

            "score": float(score),

        }