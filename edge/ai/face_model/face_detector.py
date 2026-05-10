import cv2
import numpy as np
from typing import Optional, Tuple

class FaceDetector:
    def __init__(self, scale_factor: float = 1.1, min_neighbors: int = 5, min_size=(80, 80)):
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.detector = cv2.CascadeClassifier(cascade_path)
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors
        self.min_size = min_size

        if self.detector.empty():
            raise RuntimeError(f"Failed to load Haar cascade from: {cascade_path}")

    def detect_largest_face(self, bgr_frame: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)

        faces = self.detector.detectMultiScale(
            gray,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=self.min_size
        )

        if len(faces) == 0:
            return None

        best = None
        best_area = 0
        for (x, y, w, h) in faces:
            area = w * h
            if area > best_area:
                best_area = area
                best = (x, y, x + w, y + h)

        return best

def preprocess_for_arcface(bgr_frame: np.ndarray, box: Tuple[int, int, int, int], size: int = 112) -> np.ndarray:
    x1, y1, x2, y2 = box
    face = bgr_frame[y1:y2, x1:x2]
    if face.size == 0:
        raise ValueError("Empty face crop")

    face = cv2.resize(face, (size, size), interpolation=cv2.INTER_LINEAR)
    face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB).astype(np.float32)
    face = (face - 127.5) / 128.0
    face = np.expand_dims(face, axis=0)
    return face