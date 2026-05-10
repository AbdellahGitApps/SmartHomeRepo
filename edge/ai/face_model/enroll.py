import time
import cv2
import numpy as np
from typing import List, Tuple
from .face_detector import FaceDetector, preprocess_for_arcface
from .face_embedder import FaceEmbedder
from .emb_utils import l2_normalize

def collect_embeddings_from_camera(
    camera_index=0,
    seconds=7,
    max_samples=12,
    min_face_size=80
) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    cap = cv2.VideoCapture(camera_index)
    det = FaceDetector()
    embedder = FaceEmbedder()

    collected_embeddings: List[np.ndarray] = []
    collected_face_images: List[np.ndarray] = []

    start = time.time()

    while time.time() - start < seconds and len(collected_embeddings) < max_samples:
        ok, frame = cap.read()
        if not ok:
            continue

        box = det.detect_largest_face(frame)
        if not box:
            continue

        x1, y1, x2, y2 = box

        if (x2 - x1) < min_face_size or (y2 - y1) < min_face_size:
            continue

        face_crop_bgr = frame[y1:y2, x1:x2].copy()
        if face_crop_bgr.size == 0:
            continue

        face_for_model = preprocess_for_arcface(frame, box)
        vec = embedder.embed(face_for_model)

        collected_embeddings.append(vec)
        collected_face_images.append(face_crop_bgr)

        time.sleep(0.15)

    cap.release()
    return collected_embeddings, collected_face_images

def average_embedding(vectors: List[np.ndarray]) -> np.ndarray:
    if not vectors:
        raise ValueError("No embeddings collected")

    avg = np.mean(np.stack(vectors, axis=0), axis=0)
    return l2_normalize(avg)