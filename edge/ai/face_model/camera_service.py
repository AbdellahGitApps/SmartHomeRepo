import time
import os
import cv2
from datetime import datetime

from app.core.config import (
    SNAPSHOTS_DIR,
    KNOWN_COOLDOWN_SEC,
    UNKNOWN_COOLDOWN_SEC,
    UNKNOWN_CONFIRM_COUNT,
)
from app.core.db import SessionLocal
from app.core.models import FaceEvent

from .face_detector import FaceDetector, preprocess_for_arcface
from .face_embedder import FaceEmbedder
from .recognizer import FaceRecognizer

def save_snapshot(frame) -> str:
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = str(SNAPSHOTS_DIR / f"{ts}.jpg")
    cv2.imwrite(path, frame)
    return path

def run(camera_index: int = 0):
    cap = cv2.VideoCapture(camera_index)
    det = FaceDetector()
    embedder = FaceEmbedder()
    recog = FaceRecognizer()

    gallery = recog.load_gallery()
    last_reload = time.time()

    last_known = 0.0
    last_unknown = 0.0
    unknown_counter = 0

    print("Recognition loop started. Press Ctrl+C to stop.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.1)
                continue

            if time.time() - last_reload > 30:
                gallery = recog.load_gallery()
                last_reload = time.time()

            box = det.detect_largest_face(frame)
            if not box:
                continue

            face = preprocess_for_arcface(frame, box)
            emb = embedder.embed(face)
            pid, score = recog.match(emb, gallery)

            now = time.time()
            db = SessionLocal()

            if pid is not None:
                unknown_counter = 0

                if now - last_known > KNOWN_COOLDOWN_SEC:
                    person = recog.get_person(pid)
                    db.add(FaceEvent(event_type="known", person_id=pid, score=score, snapshot_path=None))
                    db.commit()
                    print(f"[KNOWN] {person.name if person else pid} score={score:.3f}")
                    last_known = now

            else:
                unknown_counter += 1
                print(f"[UNKNOWN_CANDIDATE] score={score:.3f} count={unknown_counter}/{UNKNOWN_CONFIRM_COUNT}")

                if unknown_counter >= UNKNOWN_CONFIRM_COUNT:
                    if now - last_unknown > UNKNOWN_COOLDOWN_SEC:
                        snap = save_snapshot(frame)
                        db.add(FaceEvent(event_type="unknown", person_id=None, score=score, snapshot_path=snap))
                        db.commit()
                        print(f"[UNKNOWN_CONFIRMED] score={score:.3f} snapshot={snap}")
                        last_unknown = now

                    unknown_counter = 0

            db.close()

    except KeyboardInterrupt:
        print("\nStopped by user.")

    finally:
        cap.release()
        cv2.destroyAllWindows()