from typing import Optional, Tuple, List
import numpy as np
from app.core.db import SessionLocal
from app.core.models import FaceEmbedding, Person
from app.core.config import SIM_THRESHOLD
from .emb_utils import json_to_emb, cosine_sim

class FaceRecognizer:
    def __init__(self):
        self.threshold = SIM_THRESHOLD

    def load_gallery(self) -> List[Tuple[int, np.ndarray]]:
        db = SessionLocal()
        rows = db.query(FaceEmbedding).all()
        gallery = [(r.person_id, json_to_emb(r.embedding_json)) for r in rows]
        db.close()
        return gallery

    def match(self, emb: np.ndarray, gallery: List[Tuple[int, np.ndarray]]) -> Tuple[Optional[int], float]:
        best_id = None
        best_score = -1.0
        for pid, gemb in gallery:
            score = cosine_sim(emb, gemb)
            if score > best_score:
                best_score = score
                best_id = pid

        if best_score >= self.threshold:
            return best_id, best_score
        return None, best_score

    def get_person(self, person_id: int) -> Optional[Person]:
        db = SessionLocal()
        p = db.query(Person).filter(Person.id == person_id).first()
        db.close()
        return p