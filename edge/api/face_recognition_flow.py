from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import json
import sqlite3
import urllib.request

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter()


class FaceVerifyRequest(BaseModel):
    face_embedding: list[float]
    source: str = "backend_face_adapter"


class FaceCaptureRecognizeRequest(BaseModel):
    capture_url: Optional[str] = None
    source: str = "esp32_cam"
    save_unknown_snapshot: bool = True


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ai_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "ai"


def _model_db_path() -> Path:
    candidates = [
        _ai_dir() / "smart_home_models.db",
        Path(__file__).resolve().parents[1] / "smart_home_models.db",
        Path.cwd() / "smart_home_models.db",
    ]

    for path in candidates:
        if path.exists():
            return path

    return _ai_dir() / "smart_home_models.db"


def _arcface_path() -> Path:
    return _ai_dir() / "storage" / "face" / "models" / "arcface.onnx"


def _snapshots_dir() -> Path:
    path = _ai_dir() / "storage" / "face" / "snapshots"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _connect_model_db():
    path = _model_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_face_tables(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT DEFAULT 'resident',
            created_at TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS face_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            embedding_json TEXT NOT NULL,
            created_at TEXT,
            FOREIGN KEY(person_id) REFERENCES persons(id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS face_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            event_type TEXT NOT NULL,
            person_id INTEGER,
            score REAL,
            snapshot_path TEXT,
            source TEXT,
            FOREIGN KEY(person_id) REFERENCES persons(id)
        )
        """
    )

    conn.commit()


def _load_gallery(conn):
    rows = conn.execute(
        """
        SELECT fe.person_id, fe.embedding_json, p.name, p.role
        FROM face_embeddings fe
        LEFT JOIN persons p ON p.id = fe.person_id
        """
    ).fetchall()

    gallery = []

    for row in rows:
        try:
            emb = json.loads(row["embedding_json"])
            gallery.append(
                {
                    "person_id": row["person_id"],
                    "name": row["name"],
                    "role": row["role"],
                    "embedding": [float(x) for x in emb],
                }
            )
        except Exception:
            continue

    return gallery


def _cosine_similarity(a, b):
    import math

    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0

    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y

    if norm_a == 0 or norm_b == 0:
        return -1.0

    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


def _match_embedding(embedding, gallery, threshold=0.60):
    best = None
    best_score = -1.0

    for item in gallery:
        score = _cosine_similarity(embedding, item["embedding"])
        if score > best_score:
            best_score = score
            best = item

    if best and best_score >= threshold:
        return best, best_score

    return None, best_score


def _insert_face_event(conn, event_type, person_id, score, snapshot_path, source):
    conn.execute(
        """
        INSERT INTO face_events (
            timestamp, event_type, person_id, score, snapshot_path, source
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (_now_iso(), event_type, person_id, score, snapshot_path, source),
    )
    conn.commit()


def _recognize_embedding(embedding, source, snapshot_path=None):
    conn = _connect_model_db()

    try:
        _ensure_face_tables(conn)
        gallery = _load_gallery(conn)

        if not gallery:
            return {
                "success": True,
                "recognized": False,
                "event_type": "unknown",
                "message": "No registered face embeddings found",
                "person": None,
                "score": None,
                "gallery_count": 0,
            }

        person, score = _match_embedding(embedding, gallery)
        event_type = "known" if person else "unknown"
        person_id = person["person_id"] if person else None

        _insert_face_event(conn, event_type, person_id, score, snapshot_path, source)

        return {
            "success": True,
            "recognized": person is not None,
            "event_type": event_type,
            "person": {
                "id": person["person_id"],
                "name": person["name"],
                "role": person["role"],
            } if person else None,
            "score": score,
            "gallery_count": len(gallery),
            "snapshot_path": snapshot_path,
        }
    finally:
        conn.close()


def _fetch_image_from_url(url: str):
    import numpy as np
    import cv2

    with urllib.request.urlopen(url, timeout=10) as response:
        image_bytes = response.read()

    data = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(data, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(status_code=400, detail="Could not decode image from capture URL")

    return frame


def _detect_largest_face(frame):
    import cv2

    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(cascade_path)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80),
    )

    if len(faces) == 0:
        return None

    return max(faces, key=lambda item: item[2] * item[3])


def _preprocess_face(frame, box):
    import numpy as np
    import cv2

    x, y, w, h = box
    face = frame[y:y + h, x:x + w]

    if face.size == 0:
        raise HTTPException(status_code=400, detail="Empty face crop")

    face = cv2.resize(face, (112, 112), interpolation=cv2.INTER_LINEAR)
    face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB).astype("float32")
    face = (face - 127.5) / 128.0
    face = np.expand_dims(face, axis=0)

    return face


def _extract_embedding(face):
    import numpy as np
    import onnxruntime as ort

    model_path = _arcface_path()

    if not model_path.exists():
        raise HTTPException(status_code=500, detail=f"ArcFace model not found: {model_path}")

    session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name

    output = session.run([output_name], {input_name: face})[0]
    emb = output[0].astype("float32")

    norm = np.linalg.norm(emb)

    if norm == 0:
        raise HTTPException(status_code=500, detail="Invalid zero face embedding")

    return (emb / norm).tolist()


def _save_snapshot(frame):
    import cv2

    path = _snapshots_dir() / f"api_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg"
    cv2.imwrite(str(path), frame)
    return str(path)


@router.get("/api/face/status")
def face_status():
    conn = _connect_model_db()

    try:
        _ensure_face_tables(conn)

        persons = conn.execute("SELECT COUNT(*) AS c FROM persons").fetchone()["c"]
        embeddings = conn.execute("SELECT COUNT(*) AS c FROM face_embeddings").fetchone()["c"]
        events = conn.execute("SELECT COUNT(*) AS c FROM face_events").fetchone()["c"]

        return {
            "success": True,
            "model_db": str(_model_db_path()),
            "arcface_model": str(_arcface_path()),
            "arcface_model_exists": _arcface_path().exists(),
            "persons": persons,
            "embeddings": embeddings,
            "events": events,
        }
    finally:
        conn.close()


@router.post("/api/face/verify")
def verify_face(request_data: FaceVerifyRequest):
    if not request_data.face_embedding:
        raise HTTPException(status_code=400, detail="face_embedding is required")

    return _recognize_embedding(
        request_data.face_embedding,
        source=request_data.source,
    )


@router.post("/api/face/recognize-capture")
def recognize_from_capture(request_data: FaceCaptureRecognizeRequest):
    if not request_data.capture_url:
        raise HTTPException(status_code=400, detail="capture_url is required")

    frame = _fetch_image_from_url(request_data.capture_url)
    box = _detect_largest_face(frame)

    if box is None:
        raise HTTPException(status_code=404, detail="No face detected in captured image")

    face = _preprocess_face(frame, box)
    embedding = _extract_embedding(face)

    result = _recognize_embedding(
        embedding,
        source=request_data.source,
        snapshot_path=None,
    )

    if request_data.save_unknown_snapshot and not result["recognized"]:
        snapshot = _save_snapshot(frame)
        result["snapshot_path"] = snapshot

    return result


@router.get("/api/face/events")
def face_events(limit: int = 20):
    conn = _connect_model_db()

    try:
        _ensure_face_tables(conn)

        rows = conn.execute(
            """
            SELECT fe.id, fe.timestamp, fe.event_type, fe.person_id, fe.score,
                   fe.snapshot_path, fe.source, p.name, p.role
            FROM face_events fe
            LEFT JOIN persons p ON p.id = fe.person_id
            ORDER BY fe.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return {
            "success": True,
            "events": [dict(row) for row in rows],
        }
    finally:
        conn.close()
